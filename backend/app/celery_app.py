"""
LogSentinel — Celery Application Configuration
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "logsentinel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Time limits
    task_time_limit=300,       # Hard limit: 5 minutes
    task_soft_time_limit=240,  # Soft limit: 4 minutes

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # Result expiry
    result_expires=3600,  # 1 hour

    # Timezone
    timezone="UTC",
    enable_utc=True,
)
