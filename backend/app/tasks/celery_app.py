"""
Celery 应用配置
"""

from celery import Celery
from ..config import settings

celery_app = Celery(
    "stock_analysis",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.analysis_tasks", "app.tasks.email_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.hermes_timeout + 60,
    task_soft_time_limit=settings.hermes_timeout,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
