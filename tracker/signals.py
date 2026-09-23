from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import JobApplication
from .tasks import notify_status_change


@receiver(post_save, sender=JobApplication)
def detect_status_change(
    sender: type, instance: JobApplication, created: bool, **kwargs: Any
) -> None:
    """Trigger a Celery notification task when an existing application's status changes."""
    if created:
        return

    old_status = getattr(instance, "_JobApplication__original_status", instance.status)

    if old_status != instance.status:
        transaction.on_commit(
            lambda: notify_status_change.delay(
                application_id=str(instance.pk),
                old_status=old_status,
                new_status=instance.status,
            )
        )
        # Update tracked status to prevent redundant triggers
        instance._JobApplication__original_status = instance.status