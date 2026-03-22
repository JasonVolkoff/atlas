from __future__ import annotations

from django.contrib.gis.geos import Polygon
from django.db.models import QuerySet

from geography.models import Geography


class GeographyService:
    @staticmethod
    def get_by_bounds(
        bounds: tuple[float, float, float, float],
        geo_type: str,
    ) -> QuerySet[Geography]:
        """Return geographies whose geometry intersects the given bounding box.

        Args:
            bounds: (west, south, east, north) in WGS84 degrees.
            geo_type: One of Geography.GeoType values.
        """
        west, south, east, north = bounds
        bbox = Polygon.from_bbox((west, south, east, north))
        bbox.srid = 4326
        return Geography.objects.filter(
            geo_type=geo_type,
            geometry__intersects=bbox,
        )

    @staticmethod
    def search(query: str) -> list[Geography]:
        """Search geographies by name (case-insensitive contains)."""
        return list(
            Geography.objects.filter(name__icontains=query).order_by("geo_type", "name")[:20]
        )
