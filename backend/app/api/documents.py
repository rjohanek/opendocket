"""Document endpoints — list, search, detail, with filtering and sorting."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.core.database import get_db
from app.core.config import get_settings
from app.models.document import Document
from app.models.change_history import ChangeHistory

router = APIRouter()
settings = get_settings()


@router.get("")
async def list_documents(
    q: Optional[str] = Query(None, description="Search by title, ID, entity, or keyword"),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort: str = Query("discourse", enum=["discourse", "mentions", "date", "title"]),
    release: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List and search documents with filtering and sorting."""
    release_slug = release or settings.active_release

    query = select(Document).where(Document.release_slug == release_slug)

    # Filters
    if q:
        search = f"%{q}%"
        query = query.where(
            or_(
                Document.id.ilike(search),
                Document.title.ilike(search),
                Document.ai_summary.ilike(search),
                Document.entities.cast(str).ilike(search),
            )
        )
    if category:
        query = query.where(Document.category == category)
    if status:
        query = query.where(Document.status == status)

    # Sorting
    if sort == "discourse":
        query = query.order_by(Document.discourse_score.desc())
    elif sort == "mentions":
        query = query.order_by(Document.mention_count.desc())
    elif sort == "date":
        query = query.order_by(Document.date_released.desc())
    elif sort == "title":
        query = query.order_by(Document.title.asc())

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [_serialize_doc(d) for d in documents],
    }


@router.get("/categories")
async def list_categories(
    release: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all document categories for the active release."""
    release_slug = release or settings.active_release
    result = await db.execute(
        select(Document.category, func.count(Document.id))
        .where(Document.release_slug == release_slug)
        .group_by(Document.category)
        .order_by(func.count(Document.id).desc())
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]


@router.get("/stats")
async def document_stats(
    release: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate statistics for the active release."""
    release_slug = release or settings.active_release
    base = select(Document).where(Document.release_slug == release_slug)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    available = (await db.execute(
        select(func.count()).select_from(
            base.where(Document.status == "available").subquery()
        )
    )).scalar()
    removed = (await db.execute(
        select(func.count()).select_from(
            base.where(Document.status == "removed").subquery()
        )
    )).scalar()
    total_mentions = (await db.execute(
        select(func.coalesce(func.sum(Document.mention_count), 0))
        .where(Document.release_slug == release_slug)
    )).scalar()

    return {
        "total": total,
        "available": available,
        "removed": removed,
        "total_mentions": total_mentions,
    }


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single document with full detail including change history."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    return _serialize_doc(doc, include_changes=True)


def _serialize_doc(doc: Document, include_changes: bool = False) -> dict:
    """Serialize a Document ORM object to a dict."""
    data = {
        "id": doc.id,
        "release_slug": doc.release_slug,
        "documentcloud_id": doc.documentcloud_id,
        "title": doc.title,
        "category": doc.category,
        "status": doc.status,
        "page_count": doc.page_count,
        "date_released": doc.date_released.isoformat() if doc.date_released else None,
        "date_removed": doc.date_removed.isoformat() if doc.date_removed else None,
        "source_url": doc.source_url,
        "ai_summary": doc.ai_summary,
        "entities": doc.entities or [],
        "jargon_terms": doc.jargon_terms or [],
        "discourse_score": doc.discourse_score,
        "mention_count": doc.mention_count,
        "documentcloud_url": (
            f"https://www.documentcloud.org/documents/{doc.documentcloud_id}"
            if doc.documentcloud_id else None
        ),
    }
    if include_changes and doc.changes:
        data["change_history"] = [
            {
                "action": ch.action,
                "timestamp": ch.timestamp.isoformat() if ch.timestamp else None,
                "note": ch.note,
                "detected_by": ch.detected_by,
                "archive_url": ch.archive_url,
            }
            for ch in sorted(doc.changes, key=lambda c: c.timestamp)
        ]
    return data
