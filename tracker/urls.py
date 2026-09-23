"""URL routing for the tracker app (API + HTML views)."""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import JobApplicationViewSet, application_form_view, dashboard_view

router = DefaultRouter()
router.register(r"applications", JobApplicationViewSet, basename="application")

urlpatterns = [
    # API
    path("api/", include(router.urls)),
    path("api/auth-token/", obtain_auth_token, name="api-token-auth"),

    # HTML dashboard
    path("dashboard/", dashboard_view, name="dashboard"),
    path("applications/create/", application_form_view, name="application-create"),
    path("applications/<uuid:pk>/edit/", application_form_view, name="application-edit"),
]