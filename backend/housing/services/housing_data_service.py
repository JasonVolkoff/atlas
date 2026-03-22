from __future__ import annotations

import json
import logging
from datetime import date

from django.contrib.gis.geos import Polygon

from geography.models import Geography
from housing.models import MetricData

logger = logging.getLogger(__name__)

MAX_FEATURES = 500
MAX_ZIPS_PER_COUNTY = 2000
ALL_COUNTIES_SIMPLIFY_TOLERANCE = 0.012


class HousingDataService:
    @staticmethod
    def _features_for_geo_map(
        geo_map: dict[int, Geography],
        metric: str,
        time_start: date,
        time_end: date,
        simplify_tolerance: float,
    ) -> list[dict]:
        if not geo_map:
            return []

        metric_qs = (
            MetricData.objects.filter(
                geography_id__in=geo_map.keys(),
                metric=metric,
                period__gte=time_start,
                period__lte=time_end,
            )
            .only("geography_id", "period", "value")
            .order_by("geography_id", "period")
        )

        geo_data: dict[int, dict[str, float]] = {}
        for md in metric_qs:
            gid = md.geography_id
            if gid not in geo_data:
                geo_data[gid] = {}
            period_key = md.period.strftime("%Y-%m")
            geo_data[gid][period_key] = round(float(md.value), 2)

        features: list[dict] = []
        baseline_key = time_start.strftime("%Y-%m")
        for gid in sorted(geo_map.keys()):
            geo = geo_map[gid]
            ts = geo_data.get(gid, {})

            if ts:
                baseline = ts.get(baseline_key)
                growth: dict[str, float | None] = {}
                for period_key, value in ts.items():
                    if baseline and baseline != 0:
                        growth[period_key] = round(((value - baseline) / baseline) * 100, 2)
                    else:
                        growth[period_key] = None
                properties: dict[str, object] = {
                    "id": geo.id,
                    "name": geo.name,
                    "geo_type": geo.geo_type,
                    "geo_id": geo.geo_id,
                    "state_code": geo.state_code,
                    "time_series": ts,
                    "growth": growth,
                    "has_metric_data": True,
                }
            else:
                properties = {
                    "id": geo.id,
                    "name": geo.name,
                    "geo_type": geo.geo_type,
                    "geo_id": geo.geo_id,
                    "state_code": geo.state_code,
                    "time_series": {},
                    "growth": {},
                    "has_metric_data": False,
                }

            if simplify_tolerance > 0:
                simple = geo.geometry.simplify(
                    simplify_tolerance,
                    preserve_topology=True,
                )
            else:
                simple = geo.geometry
            geojson_str = simple.geojson

            features.append(
                {
                    "type": "Feature",
                    "id": geo.id,
                    "geometry": json.loads(geojson_str),
                    "properties": properties,
                }
            )
        return features

    @staticmethod
    def get_map_data(
        metric: str,
        geo_type: str,
        bounds: tuple[float, float, float, float],
        time_start: date,
        time_end: date,
        zoom: float = 5.0,
        exclude_geography_ids: list[int] | None = None,
    ) -> list[dict]:
        """Return GeoJSON-ready features for the given viewport and time range.

        Applies geometry simplification and caps feature count to keep
        response payloads manageable. Optional exclude_geography_ids skips
        already-loaded geographies so clients can delta-fill the viewport.
        """
        west, south, east, north = bounds
        bbox = Polygon.from_bbox((west, south, east, north))
        bbox.srid = 4326

        tolerance = HousingDataService._simplify_tolerance(zoom)

        geographies_qs = (
            Geography.objects.filter(
                geo_type=geo_type,
                geometry__intersects=bbox,
            )
            .only("id", "geo_type", "geo_id", "name", "state_code", "geometry")
            .order_by("id")
        )
        if exclude_geography_ids:
            geographies_qs = geographies_qs.exclude(id__in=exclude_geography_ids)

        geographies = list(geographies_qs[:MAX_FEATURES])
        if len(geographies) == MAX_FEATURES:
            logger.warning(
                "Viewport %s features capped at %s (more may exist)",
                geo_type,
                MAX_FEATURES,
            )

        geo_map: dict[int, Geography] = {}
        for geo in geographies:
            geo_map[geo.id] = geo

        return HousingDataService._features_for_geo_map(
            geo_map,
            metric,
            time_start,
            time_end,
            tolerance,
        )

    @staticmethod
    def get_all_counties_map_data(
        metric: str,
        time_start: date,
        time_end: date,
    ) -> list[dict]:
        """Return all US county features with moderate simplification for one response."""
        geographies = list(
            Geography.objects.filter(
                geo_type=Geography.GeoType.COUNTY,
            )
            .only("id", "geo_type", "geo_id", "name", "state_code", "geometry")
            .order_by("id")
        )
        geo_map = {geo.id: geo for geo in geographies}
        return HousingDataService._features_for_geo_map(
            geo_map,
            metric,
            time_start,
            time_end,
            ALL_COUNTIES_SIMPLIFY_TOLERANCE,
        )

    @staticmethod
    def get_zip_map_data_in_county(
        county_geography_id: int,
        metric: str,
        time_start: date,
        time_end: date,
    ) -> list[dict]:
        """Zip (ZCTA) features intersecting the county; full-resolution geometry."""
        county = (
            Geography.objects.filter(
                id=county_geography_id,
                geo_type=Geography.GeoType.COUNTY,
            )
            .only("id", "geometry")
            .first()
        )
        if county is None:
            return []

        geographies = list(
            Geography.objects.filter(
                geo_type=Geography.GeoType.ZIPCODE,
                geometry__intersects=county.geometry,
            )
            .only("id", "geo_type", "geo_id", "name", "state_code", "geometry")
            .order_by("id")[:MAX_ZIPS_PER_COUNTY]
        )
        if len(geographies) == MAX_ZIPS_PER_COUNTY:
            logger.warning(
                "County %s zips capped at %s (more may intersect)",
                county_geography_id,
                MAX_ZIPS_PER_COUNTY,
            )

        geo_map = {geo.id: geo for geo in geographies}
        return HousingDataService._features_for_geo_map(
            geo_map,
            metric,
            time_start,
            time_end,
            0.0,
        )

    @staticmethod
    def _simplify_tolerance(zoom: float) -> float:
        """Return geometry simplification tolerance based on zoom level.

        Higher zoom = less simplification (more detail needed).
        """
        if zoom >= 10:
            return 0.0005
        elif zoom >= 8:
            return 0.001
        elif zoom >= 6:
            return 0.005
        else:
            return 0.01

    @staticmethod
    def get_time_series(
        geography_id: int,
        metric: str,
    ) -> list[dict]:
        """Return the full time-series for a single geography and metric."""
        qs = MetricData.objects.filter(
            geography_id=geography_id,
            metric=metric,
        ).order_by("period")

        return [
            {
                "period": md.period.strftime("%Y-%m"),
                "value": float(md.value),
            }
            for md in qs
        ]

    @staticmethod
    def get_available_metrics() -> list[dict]:
        """Return a list of available metrics with metadata."""
        metrics = MetricData.objects.values_list("metric", flat=True).distinct()
        metric_info = {
            "zhvi": {
                "id": "zhvi",
                "name": "Home Value (ZHVI)",
                "description": "Zillow Home Value Index - typical home value",
                "unit": "USD",
            },
        }
        return [
            metric_info.get(m, {"id": m, "name": m, "description": "", "unit": ""})
            for m in metrics
        ]
