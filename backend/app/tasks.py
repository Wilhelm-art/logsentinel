"""
LogSentinel — Celery Background Tasks
Main analysis pipeline: Parse -> Sample -> Sanitize -> Enrich -> LLM -> Persist
"""

import gc
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import AnalysisTask, AnalysisReport, TaskStatus

logger = logging.getLogger(__name__)


def _get_sync_session() -> tuple:
    """Create a sync engine and session lazily to avoid startup failures."""
    engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal()


def _update_task_status(db: Session, task_id: str, status: TaskStatus, stage: str):
    """Update task status and progress stage."""
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if task:
        task.status = status
        task.progress_stage = stage
        db.commit()
        logger.info(f"Task {task_id}: {stage}")


def analyze_logs(task_id: str, raw_content: str, filename: str):
    """
    Main analysis pipeline.

    Steps:
    1. Parse raw logs -> structured dicts
    2. Sample if exceeding threshold
    3. Sanitize PII (The Air-Gap)
    4. Enrich with threat intelligence
    5. Dispatch to LLM
    6. Persist report
    7. Cleanup
    """
    start_time = time.time()
    sync_engine, db = _get_sync_session()

    try:
        _update_task_status(db, task_id, TaskStatus.PARSING, "PARSING")

        from app.services.parser import LogParser
        entries, log_format, total_lines = LogParser.parse(raw_content)

        if not entries:
            raise ValueError("No parseable log entries found in the file.")

        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.log_format = log_format
            task.line_count = total_lines
            db.commit()

        logger.info(f"Parsed {len(entries)} entries from {filename} ({log_format})")

        from app.services.sampler import Sampler
        sampled_count = None

        if Sampler.should_sample(len(entries)):
            entries, original_count = Sampler.sample(entries)
            sampled_count = len(entries)
            logger.info(f"Sampled {original_count} -> {sampled_count} entries")

            if task:
                task.sampled = sampled_count
                db.commit()

        _update_task_status(db, task_id, TaskStatus.SANITIZING, "SANITIZING")

        from app.services.sanitizer import Sanitizer
        sanitizer = Sanitizer()
        sanitized_entries, ip_map = sanitizer.sanitize_entries(entries)

        del entries
        gc.collect()

        logger.info(f"Sanitized {len(sanitized_entries)} entries, {len(ip_map)} unique IPs")
        _update_task_status(db, task_id, TaskStatus.ENRICHING, "ENRICHING")

        from app.services.threat_intel import ThreatIntelService
        threat_service = ThreatIntelService()
        enriched_entries = threat_service.enrich_entries(sanitized_entries, ip_map)

        del ip_map
        gc.collect()

        _update_task_status(db, task_id, TaskStatus.LLM_ANALYSIS, "LLM_ANALYSIS")

        from app.services.llm import analyze_logs_with_llm
        report, llm_metadata = analyze_logs_with_llm(enriched_entries)

        del enriched_entries
        del sanitized_entries
        gc.collect()

        elapsed = int(time.time() - start_time)

        analysis_report = AnalysisReport(
            task_id=task_id,
            summary=report.summary,
            incidents=[inc.model_dump() for inc in report.incidents],
            waf_suggestions=report.waf_rule_suggestions,
            llm_provider=llm_metadata.get("provider"),
            llm_model=llm_metadata.get("model"),
            token_usage=llm_metadata.get("token_usage"),
            processing_time_seconds=elapsed,
        )
        db.add(analysis_report)

        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.progress_stage = "COMPLETED"
            task.completed_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(
            f"Task {task_id} completed in {elapsed}s. "
            f"{len(report.incidents)} incidents found."
        )

        del report
        del llm_metadata
        del raw_content
        gc.collect()

        return {"task_id": task_id, "status": "completed", "processing_time": elapsed}

    except Exception as e:
        logger.exception(f"Task {task_id} failed: {e}")

        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.progress_stage = "FAILED"
                task.error_message = str(e)[:1000]
                task.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()

        raise

    finally:
        db.close()
        sync_engine.dispose()
        gc.collect()
