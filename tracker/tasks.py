import logging

from celery import shared_task

logger = logging.getLogger("tracker.notifications")


@shared_task
def notify_status_change(application_id: str, old_status: str, new_status: str) -> None:
    """Log a simulated notification and create an ApplicationStatusLog entry.

    Called asynchronously via Celery whenever a job application's status is updated.
    """
    from .models import ApplicationStatusLog, JobApplication

    try:
        application = JobApplication.objects.get(id=application_id)
    except JobApplication.DoesNotExist:
        logger.warning("JobApplication %s not found, skipping notification", application_id)
        return

    logger.info(
        '[NOTIFICATION] Application at "%s" moved from \'%s\' → \'%s\'',
        application.company_name,
        old_status,
        new_status,
    )

    ApplicationStatusLog.objects.create(
        application=application,
        old_status=old_status,
        new_status=new_status,
    )