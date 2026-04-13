"""
LogSentinel — SQLAlchemy ORM Models
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Enum as SAEnum,
    ForeignKey, JSON, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress_stage = Column(String(50), default="QUEUED")
    file_hash = Column(String(64), nullable=False)  # SHA-256
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    log_format = Column(String(20), nullable=True)  # nginx, apache, jsonl
    line_count = Column(Integer, nullable=True)
    sampled = Column(Integer, nullable=True)  # lines after sampling
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    report = relationship("AnalysisReport", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisTask {self.id} [{self.status}]>"


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    incidents = Column(JSON, default=list)
    waf_suggestions = Column(JSON, default=list)
    llm_provider = Column(String(20), nullable=True)
    llm_model = Column(String(50), nullable=True)
    token_usage = Column(JSON, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    task = relationship("AnalysisTask", back_populates="report")

    def __repr__(self):
        return f"<AnalysisReport {self.id} for task {self.task_id}>"
