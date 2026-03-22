from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geography.api.v1.serializers import GeographySearchSerializer, GeographySerializer
from geography.models import Geography
from geography.services.geography_service import GeographyService


class GeographySearchView(APIView):
    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"error": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        results = GeographyService.search(query)
        serializer = GeographySearchSerializer(results, many=True)
        return Response(serializer.data)


class GeographyDetailView(APIView):
    def get(self, request: Request, pk: int) -> Response:
        try:
            geography = Geography.objects.get(pk=pk)
        except Geography.DoesNotExist:
            return Response(
                {"error": "Geography not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = GeographySerializer(geography)
        return Response(serializer.data)
