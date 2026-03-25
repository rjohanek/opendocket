"""
Glossary Auto-Detection Engine

Scans new documents for unusual terms, recurring phrases, and potential
euphemisms. Uses LLM-assisted analysis to propose glossary entries.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.models.document import Document
from app.models.glossary import GlossaryTerm

logger = logging.getLogger(__name__)
settings = get_settings()


async def auto_detect_terms(doc_id: str):
    """
    Analyze a document's text/summary to detect potential jargon or code words.
    Proposes new glossary entries for review.
    """
    if not settings.anthropic_api_key:
        return

    async with async_session() as db:
        doc = (await db.execute(
            select(Document).where(Document.id == doc_id)
        )).scalar_one_or_none()
        if not doc or not doc.ai_summary:
            return

        # Get existing glossary terms to avoid duplicates
        existing = (await db.execute(
            select(GlossaryTerm.term)
            .where(GlossaryTerm.release_slug == doc.release_slug)
        )).scalars().all()
        existing_terms = {t.lower() for t in existing}

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": f"""Analyze this government document summary for potential jargon, code words, euphemisms, or insider terminology that a member of the public might not understand.

Document: {doc.id} — "{doc.title}"
Category: {doc.category}
Summary: {doc.ai_summary}

For each term you identify, provide:
1. The exact term or phrase
2. Your best interpretation of what it means in context
3. Your confidence level (high, medium, or low)

Already known terms (do NOT include these): {', '.join(sorted(existing_terms)[:50])}

Respond in this exact format, one per line:
TERM: [term] | MEANING: [meaning] | CONFIDENCE: [high/medium/low]

Only include terms that are genuinely opaque or potentially coded. Skip ordinary words."""}],
            )

            text = response.content[0].text
            new_terms = _parse_llm_response(text)

            for term_data in new_terms:
                term_lower = term_data["term"].lower()
                if term_lower in existing_terms:
                    continue

                term = GlossaryTerm(
                    release_slug=doc.release_slug,
                    term=term_data["term"],
                    decoded_meaning=term_data["meaning"],
                    confidence=term_data["confidence"],
                    occurrences=1,
                    source_documents=[doc.id],
                    proposed_by="auto-detect",
                    approved=False,
                )
                db.add(term)
                existing_terms.add(term_lower)

            await db.commit()
            logger.info(f"Auto-detected {len(new_terms)} potential glossary terms from {doc.id}")

        except Exception as e:
            logger.error(f"Glossary auto-detection failed for {doc.id}: {e}")


async def update_term_occurrences(release_slug: str):
    """Scan all documents to count how many times each glossary term appears."""
    async with async_session() as db:
        terms = (await db.execute(
            select(GlossaryTerm).where(GlossaryTerm.release_slug == release_slug)
        )).scalars().all()

        documents = (await db.execute(
            select(Document).where(Document.release_slug == release_slug)
        )).scalars().all()

        for term in terms:
            count = 0
            source_docs = []
            term_lower = term.term.lower()

            for doc in documents:
                text = f"{doc.title or ''} {doc.ai_summary or ''}".lower()
                if term_lower in text:
                    count += 1
                    source_docs.append(doc.id)

            term.occurrences = count
            term.source_documents = source_docs

        await db.commit()


async def seed_glossary(release_slug: str, seed_terms: list[dict]):
    """Seed the glossary with known terms from the release config."""
    async with async_session() as db:
        for seed in seed_terms:
            existing = (await db.execute(
                select(GlossaryTerm)
                .where(GlossaryTerm.release_slug == release_slug)
                .where(GlossaryTerm.term == seed["term"])
            )).scalar_one_or_none()

            if not existing:
                term = GlossaryTerm(
                    release_slug=release_slug,
                    term=seed["term"],
                    decoded_meaning=seed["meaning"],
                    confidence=seed.get("confidence", "confirmed"),
                    proposed_by="seed",
                    approved=True,
                )
                db.add(term)

        await db.commit()


def _parse_llm_response(text: str) -> list[dict]:
    """Parse the LLM's structured response into term dicts."""
    terms = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("TERM:"):
            continue

        parts = line.split("|")
        if len(parts) < 3:
            continue

        try:
            term = parts[0].replace("TERM:", "").strip()
            meaning = parts[1].replace("MEANING:", "").strip()
            confidence = parts[2].replace("CONFIDENCE:", "").strip().lower()

            if confidence not in ("high", "medium", "low"):
                confidence = "low"

            if term and meaning:
                terms.append({
                    "term": term,
                    "meaning": meaning,
                    "confidence": confidence,
                })
        except (IndexError, ValueError):
            continue

    return terms
