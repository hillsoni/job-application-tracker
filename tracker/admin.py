from django.contrib import admin

from .models import ApplicationStatusLog, JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "role",
        "status",
        "user",
        "applied_date",
        "created_at",
    )
    list_filter = ("status", "applied_date")
    search_fields = ("company_name", "role", "user__username")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ApplicationStatusLog)
class ApplicationStatusLogAdmin(admin.ModelAdmin):
    list_display = ("application", "old_status", "new_status", "changed_at")
    list_filter = ("old_status", "new_status")
    ordering = ("-changed_at",)
    readonly_fields = ("changed_at",)