"""Document model — the core entity in OpenDocket."""

from sqlalchemy import Column, Text, Integer, Real, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Text, primary_key=True)
    release_slug = Column(Text, nullable=False, index=True)
    documentcloud_id = Column(Text)
    archivebox_snapshot_id = Column(Text)
    jmail_id = Column(Text)
    title = Column(Text, nullable=False)
    category = Column(Text, index=True)
    status = Column(Text, default="available")
    page_count = Column(Integer)
    date_released = Column(Date)
    date_removed = Column(Date)
    source_url = Column(Text)
    ai_summary = Column(Text)
    entities = Column(JSONB, default=[])
    jargon_terms = Column(JSONB, default=[])
    discourse_score = Column(Real, default=0)
    mention_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    changes = relationship("ChangeHistory", back_populates="document", lazy="selectin")
    discourse_items = relationship("DiscourseItem", back_populates="document", lazy="noload")
    summaries = relationship("DiscourseSummary", back_populates="document", lazy="noload")
