from __future__ import annotations

from django.urls import path

from housing.api.v1.views import (
    CountyMapDataView,
    MapDataView,
    MetricsListView,
    TimeSeriesView,
    ZipMapDataInCountyView,
)

urlpatterns = [
    path("map-data/", MapDataView.as_view(), name="housing-map-data"),
    path(
        "county-map-data/",
        CountyMapDataView.as_view(),
        name="housing-county-map-data",
    ),
    path(
        "counties/<int:county_geography_id>/zip-map-data/",
        ZipMapDataInCountyView.as_view(),
        name="housing-county-zip-map-data",
    ),
    path("metrics/", MetricsListView.as_view(), name="housing-metrics"),
    path(
        "<int:geography_id>/time-series/",
        TimeSeriesView.as_view(),
        name="housing-time-series",
    ),
]
