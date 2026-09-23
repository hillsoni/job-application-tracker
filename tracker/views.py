from typing import Any

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import JobApplication
from .serializers import JobApplicationSerializer

CACHE_TTL = 300  # 5 minutes


def _app_cache_key(user_id: int) -> str:
    """Build cache key for a user's application list."""
    return f"applications_user_{user_id}"


def _stats_cache_key(user_id: int) -> str:
    """Build cache key for a user's dashboard stats."""
    return f"dashboard_stats_user_{user_id}"


def _clear_user_cache(user_id: int) -> None:
    """Invalidate both list and stats cache after any CUD operation."""
    cache.delete(_app_cache_key(user_id))
    cache.delete(_stats_cache_key(user_id))


class JobApplicationViewSet(viewsets.ModelViewSet):
    """CRUD viewset for job applications, scoped to the logged-in user.

    Supports filtering by status via ?status=<value> query param.
    List responses are cached per user for 5 minutes.
    """

    serializer_class = JobApplicationSerializer

    def get_queryset(self) -> Any:
        """Return only the current user's applications, with optional status filter."""
        qs = JobApplication.objects.filter(user=self.request.user)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return cached list when no status filter is applied."""
        if request.query_params.get("status"):
            return super().list(request, *args, **kwargs)

        key = _app_cache_key(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, CACHE_TTL)
        return response

    def perform_create(self, serializer: JobApplicationSerializer) -> None:
        """Assign the logged-in user as the owner and bust cache."""
        serializer.save(user=self.request.user)
        _clear_user_cache(self.request.user.id)

    def perform_update(self, serializer: JobApplicationSerializer) -> None:
        """Save changes and bust cache."""
        serializer.save()
        _clear_user_cache(self.request.user.id)

    def perform_destroy(self, instance: JobApplication) -> None:
        """Delete the application and bust cache."""
        user_id = instance.user_id
        instance.delete()
        _clear_user_cache(user_id)

    @action(detail=False, methods=["get"])
    def dashboard_stats(self, request: Request) -> Response:
        """Return application counts grouped by status (cached for 5 min)."""
        key = _stats_cache_key(request.user.id)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        qs = JobApplication.objects.filter(user=request.user)
        stats = {
            status: qs.filter(status=status).count()
            for status, _ in JobApplication.Status.choices
        }
        stats["total"] = qs.count()

        cache.set(key, stats, CACHE_TTL)
        return Response(stats)


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Show the logged-in user's dashboard with summary stats and application table."""
    applications = JobApplication.objects.filter(user=request.user)
    
    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)

    key = _stats_cache_key(request.user.id)
    stats = cache.get(key)
    if stats is None:
        stats = {
            status: applications.filter(status=status).count()
            for status, _ in JobApplication.Status.choices
        }
        stats["total"] = applications.count()
        cache.set(key, stats, CACHE_TTL)

    return render(
        request,
        "tracker/dashboard.html",
        {"applications": applications, "stats": stats},
    )


@login_required
def application_form_view(request: HttpRequest, pk: str | None = None) -> HttpResponse:
    """Handle create and edit for a job application via HTML form."""
    instance = get_object_or_404(JobApplication, pk=pk, user=request.user) if pk else None

    if request.method == "POST":
        if request.POST.get("action") == "delete" and instance:
            user_id = instance.user_id
            instance.delete()
            _clear_user_cache(user_id)
            return redirect("dashboard")

        company_name = request.POST.get("company_name", "").strip()
        role = request.POST.get("role", "").strip()
        status = request.POST.get("status")
        applied_date = request.POST.get("applied_date")
        notes = request.POST.get("notes", "").strip()

        if instance:
            instance.company_name = company_name
            instance.role = role
            instance.status = status
            instance.applied_date = applied_date
            instance.notes = notes
        else:
            instance = JobApplication(
                user=request.user,
                company_name=company_name,
                role=role,
                status=status,
                applied_date=applied_date,
                notes=notes,
            )

        try:
            instance.full_clean()
        except ValidationError as exc:
            error = ", ".join(
                msg for messages in exc.message_dict.values() for msg in messages
            )
            return render(
                request,
                "tracker/form.html",
                {
                    "instance": instance,
                    "status_choices": JobApplication.Status.choices,
                    "error": error,
                },
            )

        instance.save()
        _clear_user_cache(request.user.id)
        return redirect("dashboard")

    return render(
        request,
        "tracker/form.html",
        {"instance": instance, "status_choices": JobApplication.Status.choices},
    )