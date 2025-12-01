from celery import Celery
from celery.schedules import crontab

from infrastructure.config.settings import settings

celery_app = Celery(
    "marketplace",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

celery_app.conf.beat_schedule = {
    "send-booking-reminders": {
        "task": "infrastructure.celery.tasks.send_booking_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
}

celery_app.autodiscover_tasks(["infrastructure.celery"])
