"""
LogSentinel — Pydantic Schemas
Request/response models for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Enums ──
class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    SANITIZING = "sanitizing"
    ENRICHING = "enriching"
    LLM_ANALYSIS = "llm_analysis"
    COMPLETED = "completed"
    FAILED = "failed"


# ── API Responses ──
class UploadResponse(BaseModel):
    task_id: str
    status: str = "processing"
    message: str = "Log file accepted. Sanitization and AI analysis initiated."
    file_hash: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum
    progress_stage: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class Incident(BaseModel):
    severity: SeverityLevel
    attack_type: str
    target_endpoint: str
    actor_hash: str
    description: str


class SecurityReport(BaseModel):
    """Schema the LLM must output."""
    summary: str = Field(description="A 2-paragraph high-level markdown summary of the security posture and immediate threats.")
    incidents: list[Incident] = Field(default_factory=list, description="List of detected security incidents.")
    waf_rule_suggestions: list[str] = Field(default_factory=list, description="Actionable WAF rules or NGINX configurations.")


class ReportResponse(BaseModel):
    task_id: str
    timestamp: datetime
    original_filename: str
    file_hash: str
    log_format: Optional[str] = None
    line_count: Optional[int] = None
    sampled: Optional[int] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    report: SecurityReport


class HistoryItem(BaseModel):
    task_id: str
    status: TaskStatusEnum
    original_filename: str
    file_hash: str
    log_format: Optional[str] = None
    line_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    incident_count: Optional[int] = None
    top_severity: Optional[str] = None
