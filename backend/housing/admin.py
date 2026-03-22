from __future__ import annotations

from django.contrib import admin

from housing.models import MetricData, Property, PropertyEvent


@admin.register(MetricData)
class MetricDataAdmin(admin.ModelAdmin):
    list_display = ("geography", "metric", "period", "value")
    list_filter = ("metric",)
    search_fields = ("geography__name", "geography__geo_id")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("address", "city", "state_code", "zipcode", "property_type")
    search_fields = ("address", "zipcode")


@admin.register(PropertyEvent)
class PropertyEventAdmin(admin.ModelAdmin):
    list_display = ("property", "event_type", "event_date", "price")
    list_filter = ("event_type",)
