import uuid

import datetime
from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


def validate_not_in_future(value: datetime.date) -> None:
    if value > datetime.date.today():
        raise ValidationError("Applied date cannot be in the future.")


class JobApplication(models.Model):
    """Tracks a single job application for a user."""

    class Status(models.TextChoices):
        APPLIED = "Applied"
        SCREENING = "Screening"
        INTERVIEW = "Interview"
        OFFER = "Offer"
        REJECTED = "Rejected"
        WITHDRAWN = "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="Owner of the application",
    )
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, help_text="Job title/role applied for")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
        help_text="Choices: Applied, Screening, Interview, Offer, Rejected, Withdrawn",
    )
    applied_date = models.DateField(validators=[validate_not_in_future])
    notes = models.TextField(blank=True, help_text="Optional")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.role} @ {self.company_name} ({self.status})"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__original_status = self.status

class ApplicationStatusLog(models.Model):
    """Records each status change on a JobApplication."""

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self) -> str:
        return f"{self.application_id}: {self.old_status} → {self.new_status}"