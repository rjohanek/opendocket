"""
Celery application — scheduled background tasks for OpenDocket.

Tasks:
- Discourse collection pipeline (every 6 hours)
- Glossary term occurrence updates (daily)
- Document score recalculation (daily)
"""

import asyncio
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "opendocket",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Scheduled Tasks ───────────────────────────────────────────────────────────

celery_app.conf.beat_schedule = {
    "collect-discourse": {
        "task": "app.workers.celery_app.collect_discourse_task",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "options": {"queue": "discourse"},
    },
    "update-glossary-occurrences": {
        "task": "app.workers.celery_app.update_glossary_task",
        "schedule": crontab(minute=0, hour=3),  # Daily at 3am
        "options": {"queue": "glossary"},
    },
}


def _run_async(coro):
    """Helper to run async functions from sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Task Definitions ──────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.celery_app.collect_discourse_task", bind=True, max_retries=3)
def collect_discourse_task(self):
    """Run the full discourse collection pipeline."""
    try:
        from app.services.discourse.pipeline import run_discourse_pipeline
        _run_async(run_discourse_pipeline())
        return {"status": "success"}
    except Exception as exc:
        self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.workers.celery_app.update_glossary_task")
def update_glossary_task():
    """Update glossary term occurrence counts."""
    from app.services.glossary_engine import update_term_occurrences
    _run_async(update_term_occurrences(settings.active_release))
    return {"status": "success"}


@celery_app.task(name="app.workers.celery_app.auto_detect_glossary_task")
def auto_detect_glossary_task(doc_id: str):
    """Auto-detect glossary terms in a newly added document."""
    from app.services.glossary_engine import auto_detect_terms
    _run_async(auto_detect_terms(doc_id))
    return {"status": "success", "doc_id": doc_id}


@celery_app.task(name="app.workers.celery_app.seed_glossary_task")
def seed_glossary_task(release_slug: str, seed_terms: list[dict]):
    """Seed glossary with terms from the release config."""
    from app.services.glossary_engine import seed_glossary
    _run_async(seed_glossary(release_slug, seed_terms))
    return {"status": "success"}
