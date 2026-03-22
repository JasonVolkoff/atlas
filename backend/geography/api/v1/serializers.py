from __future__ import annotations

from rest_framework import serializers

from geography.models import Geography


class GeographySerializer(serializers.ModelSerializer):
    class Meta:
        model = Geography
        fields = ("id", "geo_type", "geo_id", "name", "state_code", "properties")


class GeographySearchSerializer(serializers.ModelSerializer):
    bbox = serializers.SerializerMethodField()

    class Meta:
        model = Geography
        fields = ("id", "geo_type", "geo_id", "name", "state_code", "bbox")

    def get_bbox(self, obj: Geography) -> list[float] | None:
        if obj.geometry:
            return list(obj.geometry.extent)
        return None
