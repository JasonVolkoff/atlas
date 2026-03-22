from __future__ import annotations

from django.urls import path

from geography.api.v1.views import GeographyDetailView, GeographySearchView

urlpatterns = [
    path("search/", GeographySearchView.as_view(), name="geography-search"),
    path("<int:pk>/", GeographyDetailView.as_view(), name="geography-detail"),
]
