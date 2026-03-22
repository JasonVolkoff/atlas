from __future__ import annotations

from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geography.models import Geography
from housing.api.v1.serializers import (
    CountyMapDataRequestSerializer,
    MapDataRequestSerializer,
    MetricInfoSerializer,
    TimeSeriesPointSerializer,
    ZipMapDataInCountyRequestSerializer,
)
from housing.services.housing_data_service import HousingDataService


class MapDataView(APIView):
    def get(self, request: Request) -> Response:
        serializer = MapDataRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return self._map_data_response(serializer.validated_data)

    def post(self, request: Request) -> Response:
        serializer = MapDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._map_data_response(serializer.validated_data)

    def _map_data_response(self, data: dict) -> Response:
        exclude_ids = data.get("exclude_geography_ids") or []
        features = HousingDataService.get_map_data(
            metric=data["metric"],
            geo_type=data["geo_type"],
            bounds=data["bounds"],
            time_start=data["time_start"],
            time_end=data["time_end"],
            zoom=data.get("zoom", 5.0),
            exclude_geography_ids=exclude_ids,
        )

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }
        return Response(geojson)


class CountyMapDataView(APIView):
    def get(self, request: Request) -> Response:
        serializer = CountyMapDataRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        features = HousingDataService.get_all_counties_map_data(
            metric=data["metric"],
            time_start=data["time_start"],
            time_end=data["time_end"],
        )
        return Response(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        )


class ZipMapDataInCountyView(APIView):
    def get(self, request: Request, county_geography_id: int) -> Response:
        serializer = ZipMapDataInCountyRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        exists = Geography.objects.filter(
            id=county_geography_id,
            geo_type=Geography.GeoType.COUNTY,
        ).exists()
        if not exists:
            raise NotFound("County not found")
        features = HousingDataService.get_zip_map_data_in_county(
            county_geography_id=county_geography_id,
            metric=data["metric"],
            time_start=data["time_start"],
            time_end=data["time_end"],
        )
        return Response(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        )


class MetricsListView(APIView):
    def get(self, request: Request) -> Response:
        metrics = HousingDataService.get_available_metrics()
        serializer = MetricInfoSerializer(metrics, many=True)
        return Response(serializer.data)


class TimeSeriesView(APIView):
    def get(self, request: Request, geography_id: int) -> Response:
        metric = request.query_params.get("metric", "zhvi")
        data = HousingDataService.get_time_series(
            geography_id=geography_id,
            metric=metric,
        )
        serializer = TimeSeriesPointSerializer(data, many=True)
        return Response(serializer.data)
