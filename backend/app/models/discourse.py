"""Discourse models — items, co-mentions, and summaries."""

from sqlalchemy import Column, Text, Integer, DateTime, Real, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class DiscourseItem(Base):
    __tablename__ = "discourse_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Text, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(Text, nullable=False)  # Reddit, YouTube, News, Legal, X, Bluesky
    source_name = Column(Text)               # subreddit, outlet, channel, etc.
    title = Column(Text, nullable=False)
    url = Column(Text)
    text_excerpt = Column(Text)
    author = Column(Text)
    date = Column(DateTime, index=True)
    engagement_score = Column(Integer, default=0)
    type = Column(Text)                      # social, news, legal
    raw_data = Column(JSONB)
    collected_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="discourse_items")


class CoMention(Base):
    __tablename__ = "co_mentions"

    doc_id_1 = Column(Text, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    doc_id_2 = Column(Text, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    co_mention_count = Column(Integer, default=1)
    sources = Column(JSONB, default=[])
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("doc_id_1 < doc_id_2", name="co_mentions_ordering"),
    )


class DiscourseSummary(Base):
    __tablename__ = "discourse_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Text, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    source_count = Column(Integer)
    model_used = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="summaries")
