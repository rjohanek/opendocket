"""Change history endpoints — feed and per-document history."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import Optional
import asyncio
import json

from app.core.database import get_db
from app.core.config import get_settings
from app.models.change_history import ChangeHistory
from app.models.document import Document

router = APIRouter()
settings = get_settings()


@router.get("/feed")
async def change_feed(
    release: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest changes across all documents."""
    release_slug = release or settings.active_release

    query = (
        select(ChangeHistory)
        .join(Document)
        .where(Document.release_slug == release_slug)
        .order_by(ChangeHistory.timestamp.desc())
    )

    if action:
        query = query.where(ChangeHistory.action == action)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.options(joinedload(ChangeHistory.document)).limit(limit).offset(offset)
    result = await db.execute(query)
    changes = result.scalars().unique().all()

    return {
        "total": total,
        "changes": [
            {
                "id": ch.id,
                "doc_id": ch.doc_id,
                "doc_title": ch.document.title if ch.document else None,
                "action": ch.action,
                "timestamp": ch.timestamp.isoformat() if ch.timestamp else None,
                "note": ch.note,
                "detected_by": ch.detected_by,
                "archive_url": ch.archive_url,
            }
            for ch in changes
        ],
    }


@router.get("/stats")
async def change_stats(
    release: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate change statistics."""
    release_slug = release or settings.active_release

    result = await db.execute(
        select(ChangeHistory.action, func.count(ChangeHistory.id))
        .join(Document)
        .where(Document.release_slug == release_slug)
        .group_by(ChangeHistory.action)
    )
    stats = {row[0]: row[1] for row in result.all()}
    return {
        "added": stats.get("added", 0),
        "removed": stats.get("removed", 0),
        "modified": stats.get("modified", 0),
        "restored": stats.get("restored", 0),
        "total_events": sum(stats.values()),
    }


@router.get("/stream")
async def change_stream(
    release: Optional[str] = Query(None),
):
    """Server-Sent Events stream for real-time change notifications.

    Connect to this endpoint to receive push notifications when
    documents are added, removed, or modified.
    """
    async def event_generator():
        # In production, this would listen to Redis pub/sub
        # For now, send a heartbeat every 30s
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
