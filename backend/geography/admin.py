from __future__ import annotations

from django.contrib.gis import admin

from geography.models import Geography


@admin.register(Geography)
class GeographyAdmin(admin.GISModelAdmin):
    list_display = ("name", "geo_type", "geo_id", "state_code")
    list_filter = ("geo_type", "state_code")
    search_fields = ("name", "geo_id")
