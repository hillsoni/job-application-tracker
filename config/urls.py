"""Project-level URL configuration."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Built-in auth views. LoginView looks for registration/login.html by
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Convenience redirect so visiting "/" sends you straight to the dashboard.
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),

    # tracker.urls owns "api/", "dashboard/", "applications/..."
    path("", include("tracker.urls")),
]