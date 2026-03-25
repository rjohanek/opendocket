"""
Webhook endpoints — receives notifications from ChangeDetection.io
and triggers the Change Reconciliation Engine.
"""

from fastapi import APIRouter, Request, BackgroundTasks
from app.services.change_reconciler import process_change_event

router = APIRouter()


@router.post("/change-detected")
async def change_detected(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for ChangeDetection.io.

    When a monitored government page changes, ChangeDetection.io sends
    a POST here with diff details. The Change Reconciliation Engine
    then determines which specific documents were added/removed/modified.
    """
    payload = await request.json()

    # Queue the reconciliation as a background task
    background_tasks.add_task(process_change_event, payload)

    return {
        "status": "accepted",
        "message": "Change event queued for processing",
    }
