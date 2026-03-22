from __future__ import annotations

from django.contrib.gis.db import models

from geography.models import Geography


class MetricData(models.Model):
    geography = models.ForeignKey(
        Geography,
        on_delete=models.CASCADE,
        related_name="metric_data",
    )
    metric = models.CharField(max_length=50, db_index=True)
    period = models.DateField(db_index=True)
    value = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=["geography", "metric", "period"]),
            models.Index(fields=["metric", "period"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["geography", "metric", "period"],
                name="unique_geography_metric_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.geography} | {self.metric} | {self.period}: {self.value}"


class Property(models.Model):
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state_code = models.CharField(max_length=2, blank=True)
    zipcode = models.CharField(max_length=10, blank=True, db_index=True)
    location = models.PointField(srid=4326)
    property_type = models.CharField(max_length=50, blank=True)
    geography = models.ForeignKey(
        Geography,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties_set",
    )
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = "properties"

    def __str__(self) -> str:
        return f"{self.address}, {self.city}, {self.state_code} {self.zipcode}"


class PropertyEvent(models.Model):
    class EventType(models.TextChoices):
        SALE = "sale", "Sale"
        LISTING = "listing", "Listing"
        ASSESSMENT = "assessment", "Assessment"

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    event_date = models.DateField(db_index=True)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    source = models.CharField(max_length=50, blank=True)
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["property", "event_type", "event_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.property} | {self.event_type} | {self.event_date}: ${self.price}"
