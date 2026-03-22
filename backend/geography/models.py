from __future__ import annotations

from django.contrib.gis.db import models


class Geography(models.Model):
    class GeoType(models.TextChoices):
        ZIPCODE = "zipcode", "Zip Code"
        COUNTY = "county", "County"
        CITY = "city", "City"
        METRO = "metro", "Metro"
        STATE = "state", "State"

    geo_type = models.CharField(max_length=20, choices=GeoType.choices, db_index=True)
    geo_id = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255)
    state_code = models.CharField(max_length=2, blank=True, db_index=True)
    geometry = models.MultiPolygonField(srid=4326)
    centroid = models.PointField(srid=4326, null=True, blank=True)
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = "geographies"
        indexes = [
            models.Index(fields=["geo_type", "geo_id"]),
            models.Index(fields=["geo_type", "state_code"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["geo_type", "geo_id"],
                name="unique_geo_type_geo_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.geo_type}:{self.geo_id})"

    def save(self, *args: object, **kwargs: object) -> None:
        if self.geometry and not self.centroid:
            self.centroid = self.geometry.centroid
        super().save(*args, **kwargs)
