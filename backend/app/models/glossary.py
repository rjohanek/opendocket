"""Glossary model — jargon and code word decoder."""

from sqlalchemy import Column, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.models.base import Base


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    release_slug = Column(Text, nullable=False, index=True)
    term = Column(Text, nullable=False)
    decoded_meaning = Column(Text, nullable=False)
    confidence = Column(Text, default="low")  # confirmed, high, medium, low
    occurrences = Column(Integer, default=0)
    source_documents = Column(JSONB, default=[])
    external_sources = Column(JSONB, default=[])
    proposed_by = Column(Text, default="system")
    approved = Column(Boolean, default=False)
    edit_history = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
