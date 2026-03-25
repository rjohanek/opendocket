"""Release config endpoints."""

from fastapi import APIRouter, HTTPException
from app.core.release_config import list_release_configs, load_release_config

router = APIRouter()


@router.get("/releases")
async def get_releases():
    """List all available release configurations."""
    return list_release_configs()


@router.get("/releases/{slug}")
async def get_release(slug: str):
    """Get a specific release configuration."""
    config = load_release_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail=f"Release config '{slug}' not found")
    return config.model_dump()
