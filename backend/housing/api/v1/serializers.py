from __future__ import annotations

from rest_framework import serializers


class ExcludeGeographyIdsField(serializers.Field):
    """Accept JSON list (POST) or comma-separated string (GET query)."""

    def to_internal_value(self, data: object) -> list[int]:
        if data is None:
            return []
        if isinstance(data, list):
            try:
                return [int(x) for x in data]
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(
                    "exclude_geography_ids must be a list of integers"
                ) from exc
        if isinstance(data, str):
            text = data.strip()
            if not text:
                return []
            out: list[int] = []
            for part in text.split(","):
                piece = part.strip()
                if piece:
                    out.append(int(piece))
            return out
        raise serializers.ValidationError("Invalid exclude_geography_ids")


class CountyMapDataRequestSerializer(serializers.Serializer):
    metric = serializers.CharField(default="zhvi")
    time_start = serializers.DateField()
    time_end = serializers.DateField()


class ZipMapDataInCountyRequestSerializer(serializers.Serializer):
    metric = serializers.CharField(default="zhvi")
    time_start = serializers.DateField()
    time_end = serializers.DateField()


class MapDataRequestSerializer(serializers.Serializer):
    metric = serializers.CharField(default="zhvi")
    geo_type = serializers.ChoiceField(
        choices=["zipcode", "county"],
        default="county",
    )
    time_start = serializers.DateField()
    time_end = serializers.DateField()
    bounds = serializers.CharField(
        help_text="Comma-separated: west,south,east,north",
    )
    zoom = serializers.FloatField(required=False, default=5.0)
    exclude_geography_ids = ExcludeGeographyIdsField(required=False)

    def validate_bounds(self, value: str) -> tuple[float, float, float, float]:
        try:
            parts = [float(x.strip()) for x in value.split(",")]
            if len(parts) != 4:
                raise ValueError
            return (parts[0], parts[1], parts[2], parts[3])
        except (ValueError, AttributeError):
            raise serializers.ValidationError(
                "Bounds must be 4 comma-separated floats: west,south,east,north"
            )


class TimeSeriesPointSerializer(serializers.Serializer):
    period = serializers.CharField()
    value = serializers.FloatField()


class MetricInfoSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    unit = serializers.CharField()
