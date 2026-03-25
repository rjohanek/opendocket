"""Change history model — tracks additions, removals, and modifications."""

from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class ChangeHistory(Base):
    __tablename__ = "change_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Text, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(Text, nullable=False)  # added, removed, modified, restored
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    note = Column(Text)
    diff_details = Column(JSONB)
    detected_by = Column(Text, default="system")
    archive_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="changes")
