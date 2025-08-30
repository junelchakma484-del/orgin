"""
Celery Application for Face Mask Detection System
Distributed task processing with Redis backend for message queue optimization
"""

from celery import Celery
from ..config import config
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'face_mask_detection',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    include=['src.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'src.workers.tasks.process_frame': {'queue': 'video_processing'},
        'src.workers.tasks.send_alert': {'queue': 'alerts'},
        'src.workers.tasks.save_detection': {'queue': 'database'},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Task settings
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Queue settings
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Performance settings
    worker_concurrency=config.MAX_WORKERS,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task annotations for monitoring
celery_app.conf.task_annotations = {
    'src.workers.tasks.process_frame': {
        'rate_limit': '100/m',  # 100 tasks per minute
        'time_limit': 30,       # 30 seconds timeout
        'soft_time_limit': 25,  # 25 seconds soft timeout
    },
    'src.workers.tasks.send_alert': {
        'rate_limit': '10/m',   # 10 alerts per minute
        'time_limit': 10,
        'soft_time_limit': 8,
    },
    'src.workers.tasks.save_detection': {
        'rate_limit': '200/m',  # 200 saves per minute
        'time_limit': 15,
        'soft_time_limit': 12,
    }
}

# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Health check task for monitoring"""
    return {
        'status': 'healthy',
        'worker_id': self.request.id,
        'timestamp': self.request.eta
    }

# Task monitoring
@celery_app.task(bind=True)
def monitor_task(self, task_name, **kwargs):
    """Monitor task execution"""
    logger.info(f"Task {task_name} started with ID {self.request.id}")
    return {
        'task_name': task_name,
        'task_id': self.request.id,
        'status': 'completed'
    }

if __name__ == '__main__':
    celery_app.start()
