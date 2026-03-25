"""
Release Configuration Loader

Loads YAML release configs that parameterize OpenDocket for different
government document releases. This is what makes the platform generalizable.
"""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from functools import lru_cache


class SourceConfig(BaseModel):
    type: str = "government_webpage"
    urls: list[dict] = []
    document_id_pattern: str = ""
    scraping: dict = {}


class SupplementarySource(BaseModel):
    type: str
    base_url: str = ""
    datasets: list[str] = []


class DocumentCloudConfig(BaseModel):
    project_prefix: str = ""
    access: str = "public"


class DiscourseConfig(BaseModel):
    search_queries: list[str] = []
    subreddits: list[str] = []
    youtube_channels: list[str] = []
    news_outlets_rss: list[str] = []
    courtlistener_queries: list[str] = []


class GlossarySeedTerm(BaseModel):
    term: str
    meaning: str
    confidence: str = "confirmed"


class GlossaryConfig(BaseModel):
    seed_terms: list[GlossarySeedTerm] = []
    auto_detect_enabled: bool = True


class ReleaseConfig(BaseModel):
    name: str
    slug: str
    description: str = ""
    source: SourceConfig = SourceConfig()
    supplementary_sources: list[SupplementarySource] = []
    documentcloud: DocumentCloudConfig = DocumentCloudConfig()
    discourse: DiscourseConfig = DiscourseConfig()
    glossary: GlossaryConfig = GlossaryConfig()


CONFIGS_DIR = Path("/app/configs/releases")


def load_release_config(slug: str) -> Optional[ReleaseConfig]:
    """Load a release config by slug from the configs directory."""
    config_path = CONFIGS_DIR / f"{slug}.yaml"
    if not config_path.exists():
        # Also check without the slug prefix
        for path in CONFIGS_DIR.glob("*.yaml"):
            with open(path) as f:
                data = yaml.safe_load(f)
            if data.get("release", {}).get("slug") == slug:
                return _parse_config(data)
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f)
    return _parse_config(data)


def list_release_configs() -> list[dict]:
    """List all available release configurations."""
    configs = []
    if not CONFIGS_DIR.exists():
        return configs
    for path in CONFIGS_DIR.glob("*.yaml"):
        with open(path) as f:
            data = yaml.safe_load(f)
        release = data.get("release", {})
        configs.append({
            "slug": release.get("slug", path.stem),
            "name": release.get("name", path.stem),
            "description": release.get("description", ""),
        })
    return configs


def _parse_config(data: dict) -> ReleaseConfig:
    """Parse a raw YAML dict into a ReleaseConfig."""
    release = data.get("release", {})
    return ReleaseConfig(
        name=release.get("name", ""),
        slug=release.get("slug", ""),
        description=release.get("description", ""),
        source=SourceConfig(**data.get("source", {})),
        supplementary_sources=[
            SupplementarySource(**s) for s in data.get("supplementary_sources", [])
        ],
        documentcloud=DocumentCloudConfig(**data.get("documentcloud", {})),
        discourse=DiscourseConfig(**data.get("discourse", {})),
        glossary=GlossaryConfig(
            seed_terms=[
                GlossarySeedTerm(**t)
                for t in data.get("glossary", {}).get("seed_terms", [])
            ],
            auto_detect_enabled=data.get("glossary", {}).get("auto_detect_enabled", True),
        ),
    )


@lru_cache()
def get_active_config(slug: str) -> Optional[ReleaseConfig]:
    return load_release_config(slug)
