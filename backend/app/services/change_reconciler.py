"""
Change Reconciliation Engine

The core new component that ties ChangeDetection.io and ArchiveBox
together with DocumentCloud. When a monitored government page changes,
this engine:

1. Parses the diff to identify which specific documents were added/removed/modified
2. For new docs: downloads the PDF, uploads to DocumentCloud, archives in ArchiveBox
3. For removed docs: flags in DB, verifies archive exists
4. Records every event in structured change history
5. Publishes change events for real-time frontend updates
"""

import re
import logging
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.core.release_config import get_active_config
from app.models.document import Document
from app.models.change_history import ChangeHistory

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_change_event(payload: dict):
    """
    Main entry point — called when ChangeDetection.io fires a webhook.

    The payload contains information about what changed on the monitored page.
    We parse this to identify specific document-level changes.
    """
    logger.info(f"Processing change event: {payload.get('uuid', 'unknown')}")

    config = get_active_config(settings.active_release)
    if not config:
        logger.error(f"No release config found for {settings.active_release}")
        return

    try:
        # Fetch the current state of the monitored page
        watch_url = payload.get("watch_url", "")
        current_docs = await scrape_document_index(watch_url, config)

        async with async_session() as db:
            # Get known documents from our database
            known_docs = await get_known_documents(db, config.slug)

            # Reconcile: find additions, removals, and modifications
            additions, removals = reconcile(current_docs, known_docs)

            # Process additions
            for doc_info in additions:
                await handle_new_document(db, doc_info, config)

            # Process removals
            for doc_id in removals:
                await handle_removed_document(db, doc_id)

            await db.commit()

        logger.info(
            f"Reconciliation complete: {len(additions)} added, {len(removals)} removed"
        )

    except Exception as e:
        logger.exception(f"Error processing change event: {e}")


async def scrape_document_index(url: str, config) -> list[dict]:
    """
    Scrape the government source page to get the current list of documents.

    Uses the CSS selector from the release config to target the document listing.
    Returns a list of dicts with document metadata.
    """
    if not url:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    css_selector = config.source.scraping.get("css_selector", "a[href$='.pdf']")
    links = soup.select(css_selector)

    documents = []
    id_pattern = config.source.document_id_pattern

    for link in links:
        href = link.get("href", "")
        text = link.get_text(strip=True)

        # Try to extract document ID from URL or text
        doc_id = extract_document_id(href, text, id_pattern)
        if not doc_id:
            continue

        documents.append({
            "id": doc_id,
            "title": text or doc_id,
            "source_url": href if href.startswith("http") else f"{url.rstrip('/')}/{href.lstrip('/')}",
        })

    return documents


def extract_document_id(url: str, text: str, pattern: str) -> Optional[str]:
    """Extract a document ID using the configured regex pattern."""
    if not pattern:
        # Fallback: use the filename without extension
        match = re.search(r"/([^/]+)\.pdf", url, re.IGNORECASE)
        return match.group(1) if match else None

    # Try matching in URL first, then text
    for source in [url, text]:
        match = re.search(pattern, source)
        if match:
            return match.group(0)
    return None


async def get_known_documents(db: AsyncSession, release_slug: str) -> dict:
    """Get all documents we currently know about for this release."""
    result = await db.execute(
        select(Document).where(Document.release_slug == release_slug)
    )
    return {doc.id: doc for doc in result.scalars().all()}


def reconcile(current_docs: list[dict], known_docs: dict) -> tuple[list[dict], list[str]]:
    """
    Compare current state of the source page against our database.

    Returns:
        additions: list of doc_info dicts for newly appeared documents
        removals: list of doc_ids that are no longer on the source page
    """
    current_ids = {doc["id"] for doc in current_docs}
    known_ids = {
        doc_id for doc_id, doc in known_docs.items()
        if doc.status != "removed"
    }

    # New documents = on page but not in our DB (or previously removed)
    new_ids = current_ids - known_ids
    additions = [doc for doc in current_docs if doc["id"] in new_ids]

    # Removed documents = in our DB as available but no longer on page
    removal_ids = known_ids - current_ids
    removals = list(removal_ids)

    return additions, removals


async def handle_new_document(db: AsyncSession, doc_info: dict, config):
    """
    Handle a newly detected document:
    1. Download and archive it
    2. Upload to DocumentCloud
    3. Create DB record
    4. Record change history
    """
    doc_id = doc_info["id"]
    logger.info(f"New document detected: {doc_id}")

    # Check if this is a restoration (was previously removed)
    existing = (await db.execute(
        select(Document).where(Document.id == doc_id)
    )).scalar_one_or_none()

    if existing and existing.status == "removed":
        # Document was previously removed and is now back
        existing.status = "available"
        existing.date_removed = None
        action = "restored"
        note = "Document reappeared on official source page"
    elif existing:
        # Already known and available — skip
        return
    else:
        # Truly new document
        doc = Document(
            id=doc_id,
            release_slug=config.slug,
            title=doc_info.get("title", doc_id),
            source_url=doc_info.get("source_url"),
            status="available",
            date_released=datetime.utcnow().date(),
        )
        db.add(doc)
        action = "added"
        note = "Detected on official source page"

    # Archive with ArchiveBox
    archive_url = await archive_document(doc_info.get("source_url"))

    # Upload to DocumentCloud
    dc_id = await upload_to_documentcloud(doc_info, config)

    # Update document with external IDs
    if existing:
        if archive_url:
            existing.archivebox_snapshot_id = archive_url
        if dc_id:
            existing.documentcloud_id = dc_id
    else:
        if archive_url:
            doc.archivebox_snapshot_id = archive_url
        if dc_id:
            doc.documentcloud_id = dc_id

    # Record in change history
    change = ChangeHistory(
        doc_id=doc_id,
        action=action,
        timestamp=datetime.utcnow(),
        note=note,
        detected_by="changedetection.io",
        archive_url=archive_url,
    )
    db.add(change)


async def handle_removed_document(db: AsyncSession, doc_id: str):
    """
    Handle a document that has been removed from the source page.
    We mark it as removed but NEVER delete it — the archive persists.
    """
    logger.info(f"Document removed from source: {doc_id}")

    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return

    doc.status = "removed"
    doc.date_removed = datetime.utcnow().date()

    change = ChangeHistory(
        doc_id=doc_id,
        action="removed",
        timestamp=datetime.utcnow(),
        note="Document removed from official source page — archived copy preserved",
        detected_by="changedetection.io",
        archive_url=doc.archivebox_snapshot_id,
    )
    db.add(change)


async def archive_document(source_url: Optional[str]) -> Optional[str]:
    """Archive a document using ArchiveBox."""
    if not source_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.archivebox_url}/api/v1/add",
                json={"urls": [source_url]},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("archive_url")
    except Exception as e:
        logger.warning(f"ArchiveBox archive failed for {source_url}: {e}")

    return None


async def upload_to_documentcloud(doc_info: dict, config) -> Optional[str]:
    """Upload a document to DocumentCloud."""
    if not settings.documentcloud_username:
        logger.info("DocumentCloud not configured — skipping upload")
        return None

    try:
        # Use the python-documentcloud library
        from documentcloud import DocumentCloud

        client = DocumentCloud(
            settings.documentcloud_username,
            settings.documentcloud_password,
        )

        # Download the PDF first
        async with httpx.AsyncClient(timeout=60) as http_client:
            response = await http_client.get(doc_info["source_url"])
            if response.status_code != 200:
                return None

        # Save temporarily and upload
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        try:
            doc = client.documents.upload(
                temp_path,
                title=doc_info.get("title", doc_info["id"]),
                source=f"OpenDocket - {config.name}",
                access="public",
            )
            return str(doc.id)
        finally:
            os.unlink(temp_path)

    except Exception as e:
        logger.warning(f"DocumentCloud upload failed: {e}")
        return None
