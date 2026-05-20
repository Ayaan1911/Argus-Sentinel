import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery(
    'argus_sentinel',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks.pipeline'],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=10,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
