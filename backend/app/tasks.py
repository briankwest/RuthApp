"""
Celery tasks and configuration for Ruth Platform
"""
from celery import Celery
from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "ruth",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks from all installed apps
celery_app.autodiscover_tasks(['app.services'])


# Example tasks that can be used later
@celery_app.task(name="app.tasks.test_task")
def test_task(message: str):
    """
    Test task to verify Celery is working
    """
    print(f"Test task executed: {message}")
    return {"status": "success", "message": message}


@celery_app.task(name="app.tasks.send_verification_email")
def send_verification_email(user_email: str, verification_token: str):
    """
    Send email verification link to user

    TODO: Implement email sending via Amazon SES
    """
    print(f"Sending verification email to {user_email} with token {verification_token}")
    return {"status": "queued", "email": user_email}


@celery_app.task(name="app.tasks.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """
    Periodic task to clean up expired password reset and verification tokens

    TODO: Implement token cleanup
    """
    print("Cleaning up expired tokens...")
    return {"status": "completed", "deleted": 0}


@celery_app.task(name="app.tasks.cleanup_expired_geocoding_cache")
def cleanup_expired_geocoding_cache():
    """
    Periodic task to clean up expired geocoding cache entries

    TODO: Implement cache cleanup
    """
    print("Cleaning up expired geocoding cache...")
    return {"status": "completed", "deleted": 0}


# Configure periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'app.tasks.cleanup_expired_tokens',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-expired-geocoding-cache': {
        'task': 'app.tasks.cleanup_expired_geocoding_cache',
        'schedule': 86400.0,  # Every 24 hours
    },
}
