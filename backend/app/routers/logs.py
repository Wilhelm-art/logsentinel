"""
LogSentinel — Logs Router
Handles file upload, task status, report retrieval, and SSE tailing.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import AnalysisTask, AnalysisReport, TaskStatus
from app.schemas import (
    UploadResponse, TaskStatusResponse, ReportResponse,
    SecurityReport, HistoryItem, Incident
)
from app.routers.auth import verify_auth_token

router = APIRouter()

ALLOWED_MIMES = {
    "text/plain",
    "application/octet-stream",
    "text/x-log",
    "application/x-ndjson",
    "application/jsonl",
    "application/json",
}

ALLOWED_EXTENSIONS = {".log", ".txt", ".jsonl", ".json"}


@router.post("/upload", response_model=UploadResponse)
async def upload_log_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    email: str = Depends(verify_auth_token),
):
    """
    Upload a log file for AI security analysis.
    Returns a task_id to poll for progress.
    """
    # Validate file extension
    filename = file.filename or "unknown.log"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Read file into memory (no disk I/O)
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Compute SHA-256 hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Create task record
    task_id = str(uuid.uuid4())
    task = AnalysisTask(
        id=task_id,
        status=TaskStatus.PENDING,
        progress_stage="QUEUED",
        file_hash=file_hash,
        original_filename=filename,
        file_size=file_size,
    )
    db.add(task)
    await db.flush()

    from app.tasks import analyze_logs
    background_tasks.add_task(analyze_logs, task_id, content.decode("utf-8", errors="replace"), filename)

    return UploadResponse(
        task_id=str(task_id),
        status="processing",
        message="Log file accepted. Sanitization and AI analysis initiated.",
        file_hash=file_hash,
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    email: str = Depends(verify_auth_token),
):
    """Poll the status of an analysis task."""
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return TaskStatusResponse(
        task_id=str(task.id),
        status=task.status,
        progress_stage=task.progress_stage,
        created_at=task.created_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
    )


@router.get("/report/{task_id}", response_model=ReportResponse)
async def get_report(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    email: str = Depends(verify_auth_token),
):
    """Retrieve the completed security analysis report."""
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task.status == TaskStatus.FAILED:
        raise HTTPException(
            status_code=422,
            detail=f"Analysis failed: {task.error_message or 'Unknown error'}",
        )

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=202,
            detail="Analysis still in progress.",
        )

    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.task_id == task_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Build response
    incidents = [Incident(**i) for i in (report.incidents or [])]

    return ReportResponse(
        task_id=str(task.id),
        timestamp=report.created_at,
        original_filename=task.original_filename,
        file_hash=task.file_hash,
        log_format=task.log_format,
        line_count=task.line_count,
        sampled=task.sampled,
        llm_provider=report.llm_provider,
        llm_model=report.llm_model,
        processing_time_seconds=report.processing_time_seconds,
        report=SecurityReport(
            summary=report.summary or "",
            incidents=incidents,
            waf_rule_suggestions=report.waf_suggestions or [],
        ),
    )


@router.get("/history")
async def get_analysis_history(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    email: str = Depends(verify_auth_token),
):
    """Get recent analysis history."""
    result = await db.execute(
        select(AnalysisTask)
        .order_by(desc(AnalysisTask.created_at))
        .limit(limit)
    )
    tasks = result.scalars().all()

    history = []
    for task in tasks:
        # Count incidents if report exists
        incident_count = None
        top_severity = None
        if task.report:
            incidents = task.report.incidents or []
            incident_count = len(incidents)
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            if incidents:
                sorted_inc = sorted(
                    incidents,
                    key=lambda x: severity_order.get(x.get("severity", "LOW"), 4)
                )
                top_severity = sorted_inc[0].get("severity")

        history.append(HistoryItem(
            task_id=str(task.id),
            status=task.status,
            original_filename=task.original_filename,
            file_hash=task.file_hash,
            log_format=task.log_format,
            line_count=task.line_count,
            created_at=task.created_at,
            completed_at=task.completed_at,
            incident_count=incident_count,
            top_severity=top_severity,
        ))

    return {"history": history, "total": len(history)}


@router.get("/tail")
async def tail_logs(
    email: str = Depends(verify_auth_token),
):
    """
    SSE endpoint for real-time log tailing.
    Streams log data without AI processing.
    """
    import asyncio

    async def event_stream():
        """Generate SSE events. In production this would tail a file or stream."""
        yield "data: {\"type\": \"connected\", \"message\": \"SSE stream established\"}\n\n"

        # Keep connection alive with heartbeats
        while True:
            await asyncio.sleep(15)
            yield "data: {\"type\": \"heartbeat\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
