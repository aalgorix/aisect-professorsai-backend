"""
Celery Application Configuration
Production-grade distributed task queue for handling background jobs
"""

from celery import Celery
import os
import ssl
from kombu import Exchange, Queue
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Redis connection (will be configured via environment variables)
# Option 1: Use REDIS_URL directly (recommended for Upstash)
REDIS_URL = os.getenv('REDIS_URL', None)

# Debug: Print Redis URL (mask password)
if REDIS_URL:
    masked_url = REDIS_URL.split('@')[0].split(':')[0:2]
    print(f"✅ Celery: Using Redis URL: {masked_url[0]}://...@{REDIS_URL.split('@')[-1]}")
else:
    print("⚠️ Celery: REDIS_URL not found in environment, using localhost")

# Option 2: Build from individual components (fallback)
if REDIS_URL:
    # Use the full Redis URL (supports rediss:// for SSL)
    # Add SSL cert requirements for rediss:// URLs
    if REDIS_URL.startswith('rediss://'):
        if '?' in REDIS_URL:
            BROKER_URL = f"{REDIS_URL}&ssl_cert_reqs=none"
            BACKEND_URL = f"{REDIS_URL}&ssl_cert_reqs=none"
        else:
            BROKER_URL = f"{REDIS_URL}?ssl_cert_reqs=none"
            BACKEND_URL = f"{REDIS_URL}?ssl_cert_reqs=none"
    else:
        BROKER_URL = REDIS_URL
        BACKEND_URL = REDIS_URL
else:
    # Build from individual components
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_DB = os.getenv('REDIS_DB', '0')
    REDIS_USERNAME = os.getenv('REDIS_USERNAME', 'default')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_USE_SSL = os.getenv('REDIS_USE_SSL', 'false').lower() == 'true'
    
    # Build Redis URL
    protocol = 'rediss' if REDIS_USE_SSL else 'redis'
    if REDIS_PASSWORD:
        # Include username in URL (required for Redis Labs and some cloud providers)
        BROKER_URL = f'{protocol}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    else:
        BROKER_URL = f'{protocol}://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    BACKEND_URL = BROKER_URL

# Initialize Celery
celery_app = Celery(
    'profai',
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=['tasks.pdf_processing', 'tasks.quiz_generation']
)

# Celery Configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'tasks.pdf_processing.*': {'queue': 'pdf_processing'},
        'tasks.quiz_generation.*': {'queue': 'quiz_generation'},
    },
    
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    
    # Task time limits
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Task result backend
    result_expires=86400,  # Results expire after 24 hours
    
    # Broker heartbeat - CRITICAL for long-running CPU-intensive tasks (PDF extraction)
    # Large PDFs (16MB+) can take 5+ minutes for PyPDF2 to extract text,
    # during which the worker process is blocked and can't send heartbeats.
    # Without these settings, Celery thinks the worker is dead and kills the task.
    broker_heartbeat=0,  # Disable broker heartbeats (prevents false "worker lost" detection)
    broker_transport_options={
        'visibility_timeout': 7200,  # 2 hours - how long a task can be "invisible" before redelivery
    },
    
    # Worker heartbeat configuration
    worker_lost_wait=600,  # Wait 10 minutes before considering a worker lost (default is 10s)
    
    # Redis/Broker connection options (for Redis Labs SSL)
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    } if REDIS_URL and REDIS_URL.startswith('rediss://') else None,
    
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    } if REDIS_URL and REDIS_URL.startswith('rediss://') else None,
    
    # Worker configuration (optimized for 5 workers @ concurrency=1 each)
    worker_prefetch_multiplier=1,  # Fetch one task at a time (critical for memory management)
    worker_max_tasks_per_child=20,  # Restart worker after 20 tasks (aggressive memory cleanup)
    
    # Task acknowledgment
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    
    # Task retries - REMOVED task_autoretry_for to avoid double retries
    # The task already has its own retry logic via self.retry() in tasks/pdf_processing.py
    # Having both causes infinite retry loops where progress gets stuck
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Priority queues
    task_default_priority=5,
    task_queue_max_priority=10,
    
    # Beat schedule (for periodic tasks if needed)
    beat_schedule={},
)

# Define queues with priorities
celery_app.conf.task_queues = (
    Queue(
        'pdf_processing',
        Exchange('pdf_processing'),
        routing_key='pdf_processing',
        queue_arguments={'x-max-priority': 10}
    ),
    Queue(
        'quiz_generation',
        Exchange('quiz_generation'),
        routing_key='quiz_generation',
        queue_arguments={'x-max-priority': 10}
    ),
)

if __name__ == '__main__':
    celery_app.start()
