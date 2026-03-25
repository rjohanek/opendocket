"""Glossary endpoints — jargon decoder with community editing."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.config import get_settings
from app.models.glossary import GlossaryTerm

router = APIRouter()
settings = get_settings()


class GlossaryProposal(BaseModel):
    term: str
    decoded_meaning: str
    confidence: str = "low"
    external_sources: list[str] = []
    proposed_by: str = "community"


class GlossaryEdit(BaseModel):
    decoded_meaning: Optional[str] = None
    confidence: Optional[str] = None
    external_sources: Optional[list[str]] = None


@router.get("")
async def list_glossary(
    release: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    sort: str = Query("occurrences", enum=["occurrences", "term", "confidence"]),
    q: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List all glossary terms for the active release."""
    release_slug = release or settings.active_release

    query = select(GlossaryTerm).where(GlossaryTerm.release_slug == release_slug)

    if confidence:
        query = query.where(GlossaryTerm.confidence == confidence)
    if q:
        search = f"%{q}%"
        query = query.where(
            GlossaryTerm.term.ilike(search) | GlossaryTerm.decoded_meaning.ilike(search)
        )

    if sort == "occurrences":
        query = query.order_by(GlossaryTerm.occurrences.desc())
    elif sort == "term":
        query = query.order_by(GlossaryTerm.term.asc())
    elif sort == "confidence":
        # Order: confirmed > high > medium > low
        query = query.order_by(
            func.array_position(
                func.cast(["confirmed", "high", "medium", "low"], type_=None),
                GlossaryTerm.confidence,
            )
        )

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar()

    result = await db.execute(query.limit(limit).offset(offset))
    terms = result.scalars().all()

    return {
        "total": total,
        "terms": [_serialize_term(t) for t in terms],
    }


@router.post("")
async def propose_term(
    proposal: GlossaryProposal,
    release: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Propose a new glossary term (community contribution)."""
    release_slug = release or settings.active_release

    # Check if term already exists
    existing = (await db.execute(
        select(GlossaryTerm)
        .where(GlossaryTerm.release_slug == release_slug)
        .where(func.lower(GlossaryTerm.term) == proposal.term.lower())
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Term '{proposal.term}' already exists (id={existing.id})"
        )

    term = GlossaryTerm(
        release_slug=release_slug,
        term=proposal.term,
        decoded_meaning=proposal.decoded_meaning,
        confidence=proposal.confidence,
        external_sources=proposal.external_sources,
        proposed_by=proposal.proposed_by,
        approved=False,
        edit_history=[{
            "action": "created",
            "by": proposal.proposed_by,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    )
    db.add(term)
    await db.flush()

    return {"id": term.id, "status": "proposed", "message": "Term submitted for review"}


@router.patch("/{term_id}")
async def edit_term(
    term_id: int,
    edit: GlossaryEdit,
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing glossary term."""
    result = await db.execute(select(GlossaryTerm).where(GlossaryTerm.id == term_id))
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=404, detail=f"Glossary term {term_id} not found")

    changes = {}
    if edit.decoded_meaning is not None:
        changes["decoded_meaning"] = {"old": term.decoded_meaning, "new": edit.decoded_meaning}
        term.decoded_meaning = edit.decoded_meaning
    if edit.confidence is not None:
        changes["confidence"] = {"old": term.confidence, "new": edit.confidence}
        term.confidence = edit.confidence
    if edit.external_sources is not None:
        term.external_sources = edit.external_sources

    # Record edit in history
    history = term.edit_history or []
    history.append({
        "action": "edited",
        "changes": changes,
        "timestamp": datetime.utcnow().isoformat(),
    })
    term.edit_history = history

    return _serialize_term(term)


@router.get("/{term_id}")
async def get_term(term_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single glossary term with full detail."""
    result = await db.execute(select(GlossaryTerm).where(GlossaryTerm.id == term_id))
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=404, detail=f"Glossary term {term_id} not found")
    return _serialize_term(term)


def _serialize_term(term: GlossaryTerm) -> dict:
    return {
        "id": term.id,
        "term": term.term,
        "decoded_meaning": term.decoded_meaning,
        "confidence": term.confidence,
        "occurrences": term.occurrences,
        "source_documents": term.source_documents or [],
        "external_sources": term.external_sources or [],
        "proposed_by": term.proposed_by,
        "approved": term.approved,
        "edit_history": term.edit_history or [],
    }
