"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "changeme"
    active_release: str = "epstein-files"

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://opendocket:changeme_in_production@db:5432/opendocket"

    # ── Redis ─────────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── DocumentCloud ─────────────────────────────────────────────────
    documentcloud_username: str = ""
    documentcloud_password: str = ""

    # ── Reddit ────────────────────────────────────────────────────────
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "OpenDocket/1.0"

    # ── YouTube ───────────────────────────────────────────────────────
    youtube_api_key: str = ""

    # ── CourtListener ─────────────────────────────────────────────────
    courtlistener_api_key: str = ""

    # ── LLM ───────────────────────────────────────────────────────────
    anthropic_api_key: str = ""

    # ── ChangeDetection.io ────────────────────────────────────────────
    changedetection_url: str = "http://changedetection:5000"
    changedetection_api_key: str = ""

    # ── ArchiveBox ────────────────────────────────────────────────────
    archivebox_url: str = "http://archivebox:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
