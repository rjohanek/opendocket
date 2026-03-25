"""Discourse endpoints — per-document discourse, trending, co-mentions."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional

from app.core.database import get_db
from app.core.config import get_settings
from app.models.document import Document
from app.models.discourse import DiscourseItem, CoMention, DiscourseSummary

router = APIRouter()
settings = get_settings()


@router.get("/trending")
async def trending_documents(
    release: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get the most-discussed documents ranked by mention count."""
    release_slug = release or settings.active_release

    result = await db.execute(
        select(Document)
        .where(Document.release_slug == release_slug)
        .where(Document.mention_count > 0)
        .order_by(Document.mention_count.desc())
        .limit(limit)
    )
    docs = result.scalars().all()

    return [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "status": d.status,
            "discourse_score": d.discourse_score,
            "mention_count": d.mention_count,
        }
        for d in docs
    ]


@router.get("/co-mentions")
async def co_mention_network(
    release: Optional[str] = Query(None),
    min_count: int = Query(2),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get document co-mention network — pairs of documents discussed together."""
    result = await db.execute(
        select(CoMention)
        .where(CoMention.co_mention_count >= min_count)
        .order_by(CoMention.co_mention_count.desc())
        .limit(limit)
    )
    pairs = result.scalars().all()

    return [
        {
            "doc_id_1": p.doc_id_1,
            "doc_id_2": p.doc_id_2,
            "co_mention_count": p.co_mention_count,
        }
        for p in pairs
    ]


@router.get("/{doc_id}")
async def document_discourse(
    doc_id: str,
    type: Optional[str] = Query(None, description="Filter by type: social, news, legal"),
    platform: Optional[str] = Query(None, description="Filter by platform: Reddit, YouTube, etc."),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get discourse items for a specific document."""
    # Verify document exists
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Build query
    query = (
        select(DiscourseItem)
        .where(DiscourseItem.doc_id == doc_id)
        .order_by(DiscourseItem.engagement_score.desc())
    )
    if type:
        query = query.where(DiscourseItem.type == type)
    if platform:
        query = query.where(DiscourseItem.platform == platform)

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar()

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    # Get latest summary
    summary_result = await db.execute(
        select(DiscourseSummary)
        .where(DiscourseSummary.doc_id == doc_id)
        .order_by(DiscourseSummary.generated_at.desc())
        .limit(1)
    )
    summary = summary_result.scalar_one_or_none()

    return {
        "doc_id": doc_id,
        "total": total,
        "summary": {
            "text": summary.summary if summary else None,
            "source_count": summary.source_count if summary else 0,
            "generated_at": summary.generated_at.isoformat() if summary else None,
        },
        "items": [
            {
                "id": item.id,
                "platform": item.platform,
                "source_name": item.source_name,
                "title": item.title,
                "url": item.url,
                "text_excerpt": item.text_excerpt,
                "author": item.author,
                "date": item.date.isoformat() if item.date else None,
                "engagement_score": item.engagement_score,
                "type": item.type,
            }
            for item in items
        ],
    }
