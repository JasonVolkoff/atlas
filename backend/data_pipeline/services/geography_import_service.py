from __future__ import annotations

import logging
import os
import tempfile
import zipfile
from pathlib import Path

import requests
from django.contrib.gis.gdal import DataSource, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.db import transaction

from geography.models import Geography

logger = logging.getLogger(__name__)


def _tiger_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


TIGER_ZCTA_URL = "https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip"
TIGER_COUNTY_URL = "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip"
WGS84 = SpatialReference("EPSG:4326")


class GeographyImportService:
    @staticmethod
    def import_all(data_dir: str | None = None) -> dict[str, int]:
        """Import both ZCTA and county boundaries. Returns counts of imported records."""
        work_dir = data_dir or tempfile.mkdtemp(prefix="atlas_geo_")
        counts = {}
        counts["zipcodes"] = GeographyImportService.import_zctas(work_dir)
        counts["counties"] = GeographyImportService.import_counties(work_dir)
        return counts

    @staticmethod
    def _download_and_extract(url: str, work_dir: str) -> str:
        """Download a zip file and extract it. Returns the directory containing the shapefile."""
        zip_name = url.split("/")[-1]
        zip_path = os.path.join(work_dir, zip_name)
        extract_dir = os.path.join(work_dir, zip_name.replace(".zip", ""))

        if not os.path.exists(zip_path):
            logger.info("Downloading %s...", url)
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Downloaded to %s", zip_path)

        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            logger.info("Extracted to %s", extract_dir)

        shp_files = list(Path(extract_dir).rglob("*.shp"))
        if not shp_files:
            raise FileNotFoundError(f"No .shp file found in {extract_dir}")
        return str(shp_files[0])

    @staticmethod
    def _ensure_multipolygon(geom: GEOSGeometry) -> MultiPolygon:
        """Convert a Polygon to MultiPolygon if needed."""
        if geom.geom_type == "Polygon":
            return MultiPolygon(geom)
        elif geom.geom_type == "MultiPolygon":
            return geom
        raise ValueError(f"Unexpected geometry type: {geom.geom_type}")

    @staticmethod
    def _geom_to_wgs84(feature_geom: object) -> GEOSGeometry | None:
        """Convert GDAL feature geometry to WGS84 GEOSGeometry. Returns None if invalid."""
        try:
            geom = feature_geom.clone()
            if geom.srs and str(geom.srs) != str(WGS84):
                geom.transform(WGS84)
            geos_geom = GEOSGeometry(geom.wkt)
            geos_geom.srid = 4326
            return geos_geom
        except AttributeError:
            try:
                geos_geom = GEOSGeometry(feature_geom.wkt)
                geos_geom.srid = 4326
                return geos_geom
            except Exception as e:
                logger.warning("Skipping invalid geometry: %s", e)
                return None
        except Exception as e:
            logger.warning("Skipping invalid geometry: %s", e)
            return None

    @staticmethod
    def import_zctas(work_dir: str) -> int:
        """Import ZCTA (zip code) boundaries from TIGER/Line shapefiles."""
        shp_path = GeographyImportService._download_and_extract(TIGER_ZCTA_URL, work_dir)
        ds = DataSource(shp_path)
        layer = ds[0]
        logger.info("Processing %s ZCTA features...", len(layer))

        batch: list[Geography] = []
        skipped = 0
        for feature in layer:
            zcta = feature.get("ZCTA5CE20")
            if not zcta or not str(zcta).strip():
                skipped += 1
                continue
            zcta = str(zcta).strip()
            geos_geom = GeographyImportService._geom_to_wgs84(feature.geom)
            if geos_geom is None:
                skipped += 1
                continue
            try:
                multi = GeographyImportService._ensure_multipolygon(geos_geom)
            except ValueError:
                skipped += 1
                continue
            batch.append(
                Geography(
                    geo_type=Geography.GeoType.ZIPCODE,
                    geo_id=zcta,
                    name=zcta,
                    state_code="",
                    geometry=multi,
                    centroid=multi.centroid,
                    properties={},
                )
            )

        with transaction.atomic():
            Geography.objects.filter(geo_type=Geography.GeoType.ZIPCODE).delete()
            Geography.objects.bulk_create(batch, batch_size=1000)
        count = len(batch)
        if skipped:
            logger.warning("Skipped %s ZCTA features", skipped)
        logger.info("Imported %s ZCTA boundaries.", count)
        return count

    @staticmethod
    def import_counties(work_dir: str) -> int:
        """Import county boundaries from TIGER/Line shapefiles."""
        shp_path = GeographyImportService._download_and_extract(TIGER_COUNTY_URL, work_dir)
        ds = DataSource(shp_path)
        layer = ds[0]
        logger.info("Processing %s county features...", len(layer))

        batch: list[Geography] = []
        skipped = 0
        for feature in layer:
            geoid = feature.get("GEOID")
            name = feature.get("NAMELSAD")
            state_fips = feature.get("STATEFP")
            if not geoid or not str(geoid).strip():
                skipped += 1
                continue
            geoid = str(geoid).strip()
            name = (name or "").strip() or geoid
            state_fips = (state_fips or "").strip()[:2]
            aland = feature.get("ALAND")
            awater = feature.get("AWATER")
            countyfp = feature.get("COUNTYFP")
            props = {
                "geoid": geoid,
                "namelsad": name,
                "state_fips": state_fips,
                "countyfp": str(countyfp).strip() if countyfp is not None else "",
                "aland": _tiger_int(aland),
                "awater": _tiger_int(awater),
            }
            geos_geom = GeographyImportService._geom_to_wgs84(feature.geom)
            if geos_geom is None:
                skipped += 1
                continue
            try:
                multi = GeographyImportService._ensure_multipolygon(geos_geom)
            except ValueError:
                skipped += 1
                continue
            batch.append(
                Geography(
                    geo_type=Geography.GeoType.COUNTY,
                    geo_id=geoid,
                    name=name,
                    state_code=state_fips,
                    geometry=multi,
                    centroid=multi.centroid,
                    properties=props,
                )
            )

        with transaction.atomic():
            Geography.objects.filter(geo_type=Geography.GeoType.COUNTY).delete()
            Geography.objects.bulk_create(batch, batch_size=1000)
        count = len(batch)
        if skipped:
            logger.warning("Skipped %s county features", skipped)
        logger.info("Imported %s county boundaries.", count)
        return count
