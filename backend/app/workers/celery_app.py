from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "intelligence_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-monitored-companies": {
        "task": "app.workers.tasks.check_all_monitored_companies",
        "schedule": 3600.0 * settings.MONITORING_INTERVAL_HOURS,  # Run every N hours
    },
    "cleanup-old-snapshots": {
        "task": "app.workers.tasks.cleanup_old_snapshots",
        "schedule": 86400.0,  # Run daily
    },
}