from rest_framework import serializers

from .models import JobApplication


class JobApplicationSerializer(serializers.ModelSerializer):
    """Handles read/write for JobApplication instances.

    The user field is read-only — it gets set from the request in the view
    so clients can never assign applications to other users.
    """

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "user",
            "company_name",
            "role",
            "status",
            "applied_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]