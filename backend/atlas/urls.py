from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/geography/", include("geography.api.v1.urls")),
    path("api/v1/housing/", include("housing.api.v1.urls")),
]
