"""
LogSentinel — SQLAlchemy ORM Models
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Enum as SAEnum,
    ForeignKey, JSON, BigInteger
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


def _uuid_column(**kwargs):
    """
    Returns a UUID primary key column compatible with both
    PostgreSQL (native UUID type) and SQLite (String fallback).
    """
    from app.config import settings
    if "postgresql" in settings.DATABASE_URL:
        from sqlalchemy.dialects.postgresql import UUID
        return Column(UUID(as_uuid=True), **kwargs)
    return Column(String(36), **kwargs)


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    SANITIZING = "sanitizing"
    ENRICHING = "enriching"
    LLM_ANALYSIS = "llm_analysis"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress_stage = Column(String(50), default="QUEUED")
    file_hash = Column(String(64), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    log_format = Column(String(20), nullable=True)
    line_count = Column(Integer, nullable=True)
    sampled = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    report = relationship("AnalysisReport", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisTask {self.id} [{self.status}]>"


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    incidents = Column(JSON, default=list)
    waf_suggestions = Column(JSON, default=list)
    llm_provider = Column(String(20), nullable=True)
    llm_model = Column(String(50), nullable=True)
    token_usage = Column(JSON, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = relationship("AnalysisTask", back_populates="report")

    def __repr__(self):
        return f"<AnalysisReport {self.id} for task {self.task_id}>"
