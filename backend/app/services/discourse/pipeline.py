"""
Discourse Pipeline Orchestrator

Coordinates the full flow: Collect → Match → Store → Summarize
This runs as a Celery task on a schedule (every 6 hours by default).
"""

import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import async_session
from app.core.config import get_settings
from app.core.release_config import get_active_config
from app.models.document import Document
from app.models.discourse import DiscourseItem, CoMention, DiscourseSummary
from app.services.discourse.collectors import collect_all
from app.services.discourse.matcher import DocumentMatcher
from app.services.discourse.summarizer import generate_discourse_summary

logger = logging.getLogger(__name__)
settings = get_settings()

# Minimum confidence threshold for storing a match
MIN_MATCH_CONFIDENCE = 0.5


async def run_discourse_pipeline():
    """
    Full discourse collection pipeline:
    1. Load the active release config and document index
    2. Run all collectors in parallel
    3. Match discourse hits to documents
    4. Store new discourse items
    5. Update co-mention network
    6. Regenerate summaries for documents with new discourse
    """
    config = get_active_config(settings.active_release)
    if not config:
        logger.error(f"No release config for {settings.active_release}")
        return

    logger.info(f"Starting discourse pipeline for '{config.name}'")

    async with async_session() as db:
        # Step 1: Load document index for the matcher
        result = await db.execute(
            select(Document).where(Document.release_slug == config.slug)
        )
        documents = result.scalars().all()

        if not documents:
            logger.warning("No documents in database — skipping discourse collection")
            return

        doc_index = [
            {
                "id": d.id,
                "title": d.title,
                "category": d.category,
                "entities": d.entities or [],
            }
            for d in documents
        ]
        matcher = DocumentMatcher(doc_index, config.source.document_id_pattern)

        # Step 2: Collect from all sources
        logger.info("Collecting discourse from all sources...")
        hits = await collect_all(config)
        logger.info(f"Collected {len(hits)} total discourse hits")

        # Step 3: Match hits to documents
        matched_count = 0
        docs_with_new_discourse = set()
        co_mention_pairs = []

        for hit in hits:
            matches = matcher.match_discourse_hit(hit)
            confident_matches = [m for m in matches if m.confidence >= MIN_MATCH_CONFIDENCE]

            if not confident_matches:
                continue

            # Store a discourse item for each matched document
            for match in confident_matches:
                # Check for duplicates (same URL + doc)
                existing = (await db.execute(
                    select(DiscourseItem)
                    .where(DiscourseItem.doc_id == match.doc_id)
                    .where(DiscourseItem.url == hit.url)
                )).scalar_one_or_none()

                if existing:
                    # Update engagement score if it changed
                    if hit.engagement_score > existing.engagement_score:
                        existing.engagement_score = hit.engagement_score
                    continue

                item = DiscourseItem(
                    doc_id=match.doc_id,
                    platform=hit.platform,
                    source_name=hit.source_name,
                    title=hit.title,
                    url=hit.url,
                    text_excerpt=hit.text[:500],
                    author=hit.author,
                    date=hit.date,
                    engagement_score=hit.engagement_score,
                    type=hit.type,
                    raw_data=hit.raw_data,
                )
                db.add(item)
                matched_count += 1
                docs_with_new_discourse.add(match.doc_id)

            # Track co-mentions (when a single hit matches multiple documents)
            if len(confident_matches) >= 2:
                doc_ids = sorted([m.doc_id for m in confident_matches])
                for i in range(len(doc_ids)):
                    for j in range(i + 1, len(doc_ids)):
                        co_mention_pairs.append((doc_ids[i], doc_ids[j], hit.url))

        logger.info(f"Matched {matched_count} items to {len(docs_with_new_discourse)} documents")

        # Step 4: Update co-mention network
        await _update_co_mentions(db, co_mention_pairs)

        # Step 5: Update document mention counts and discourse scores
        await _update_document_scores(db, config.slug)

        await db.commit()

        # Step 6: Regenerate summaries for documents with new discourse
        logger.info(f"Regenerating summaries for {len(docs_with_new_discourse)} documents...")
        for doc_id in docs_with_new_discourse:
            await _regenerate_summary(db, doc_id)

        await db.commit()

    logger.info("Discourse pipeline complete")


async def _update_co_mentions(db, pairs: list[tuple[str, str, str]]):
    """Update the co-mention network from new pairs."""
    # Aggregate pairs
    pair_counts = {}
    for id1, id2, url in pairs:
        key = (id1, id2) if id1 < id2 else (id2, id1)
        if key not in pair_counts:
            pair_counts[key] = {"count": 0, "urls": []}
        pair_counts[key]["count"] += 1
        pair_counts[key]["urls"].append(url)

    for (id1, id2), data in pair_counts.items():
        existing = (await db.execute(
            select(CoMention)
            .where(CoMention.doc_id_1 == id1)
            .where(CoMention.doc_id_2 == id2)
        )).scalar_one_or_none()

        if existing:
            existing.co_mention_count += data["count"]
            existing_sources = existing.sources or []
            existing.sources = existing_sources + data["urls"][:5]
        else:
            db.add(CoMention(
                doc_id_1=id1,
                doc_id_2=id2,
                co_mention_count=data["count"],
                sources=data["urls"][:10],
            ))


async def _update_document_scores(db, release_slug: str):
    """Recalculate mention counts and discourse scores for all documents."""
    result = await db.execute(
        select(Document).where(Document.release_slug == release_slug)
    )
    documents = result.scalars().all()

    for doc in documents:
        # Count total discourse items
        count_result = await db.execute(
            select(func.count(DiscourseItem.id))
            .where(DiscourseItem.doc_id == doc.id)
        )
        mention_count = count_result.scalar() or 0

        # Calculate discourse score (0-100) based on mention count and engagement
        engagement_result = await db.execute(
            select(func.coalesce(func.sum(DiscourseItem.engagement_score), 0))
            .where(DiscourseItem.doc_id == doc.id)
        )
        total_engagement = engagement_result.scalar() or 0

        # Simple scoring: log-scale of mentions * engagement factor
        import math
        if mention_count > 0:
            score = min(100, math.log(mention_count + 1, 2) * 10 + math.log(total_engagement + 1, 10) * 5)
        else:
            score = 0

        doc.mention_count = mention_count
        doc.discourse_score = round(score, 1)


async def _regenerate_summary(db, doc_id: str):
    """Regenerate the discourse summary for a specific document."""
    doc = (await db.execute(
        select(Document).where(Document.id == doc_id)
    )).scalar_one_or_none()
    if not doc:
        return

    # Get all discourse items for this document
    result = await db.execute(
        select(DiscourseItem)
        .where(DiscourseItem.doc_id == doc_id)
        .order_by(DiscourseItem.engagement_score.desc())
        .limit(50)
    )
    items = result.scalars().all()

    if not items:
        return

    items_data = [
        {
            "platform": item.platform,
            "source_name": item.source_name,
            "title": item.title,
            "text_excerpt": item.text_excerpt,
            "date": item.date.isoformat() if item.date else None,
            "engagement_score": item.engagement_score,
        }
        for item in items
    ]

    summary_text = await generate_discourse_summary(doc_id, doc.title, items_data)
    if summary_text:
        summary = DiscourseSummary(
            doc_id=doc_id,
            summary=summary_text,
            source_count=len(items),
            model_used="claude-sonnet-4-6",
        )
        db.add(summary)
