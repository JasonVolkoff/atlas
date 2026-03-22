from __future__ import annotations

import csv
import logging
import os
import tempfile
from datetime import datetime

import requests
from django.db import transaction

from data_pipeline.utils import chunk_list, safe_decimal
from geography.models import Geography
from housing.models import MetricData

logger = logging.getLogger(__name__)

ZHVI_ZIP_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

INSERT_BATCH_SIZE = 5000


class ZhviImportService:
    @staticmethod
    def import_zhvi(data_dir: str | None = None) -> int:
        """Download and import ZHVI zip-code-level data. Returns count of records inserted."""
        work_dir = data_dir or tempfile.mkdtemp(prefix="atlas_zhvi_")
        csv_path = ZhviImportService._download_csv(work_dir)
        return ZhviImportService._ingest_csv(csv_path)

    @staticmethod
    def _download_csv(work_dir: str) -> str:
        """Download the ZHVI CSV if not already present."""
        csv_path = os.path.join(work_dir, "zhvi_zip.csv")
        if not os.path.exists(csv_path):
            logger.info("Downloading ZHVI data from %s...", ZHVI_ZIP_URL)
            response = requests.get(ZHVI_ZIP_URL, timeout=120)
            response.raise_for_status()
            with open(csv_path, "wb") as f:
                f.write(response.content)
            logger.info("Downloaded to %s", csv_path)
        return csv_path

    @staticmethod
    def _ingest_csv(csv_path: str) -> int:
        """Parse the ZHVI CSV and bulk-insert into MetricData in chunks to limit memory."""
        geo_lookup = ZhviImportService._build_geo_lookup()
        if not geo_lookup:
            logger.warning("No zip code geographies found. Run import_geographies first.")
            return 0

        logger.info("Parsing ZHVI CSV...")
        total_rows = 0
        total_inserted = 0
        skipped_zips = 0
        date_columns: list[str] = []

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            date_columns = [col for col in (reader.fieldnames or []) if col and col[0].isdigit()]

            with transaction.atomic():
                MetricData.objects.filter(metric="zhvi").delete()

                records: list[MetricData] = []
                for row in reader:
                    total_rows += 1
                    zipcode = (row.get("RegionName") or "").strip()
                    geo = geo_lookup.get(zipcode)
                    if not geo:
                        skipped_zips += 1
                        continue

                    for col in date_columns:
                        value = safe_decimal(row.get(col))
                        if value is None:
                            continue
                        try:
                            period = datetime.strptime(col, "%Y-%m-%d").date().replace(day=1)
                        except ValueError:
                            continue
                        records.append(
                            MetricData(
                                geography_id=geo.id,
                                metric="zhvi",
                                period=period,
                                value=value,
                            )
                        )

                    if len(records) >= INSERT_BATCH_SIZE * 2:
                        for batch in chunk_list(records, INSERT_BATCH_SIZE):
                            MetricData.objects.bulk_create(batch, batch_size=INSERT_BATCH_SIZE)
                            total_inserted += len(batch)
                        records.clear()
                        logger.info("  Inserted %s records...", total_inserted)

                if records:
                    for batch in chunk_list(records, INSERT_BATCH_SIZE):
                        MetricData.objects.bulk_create(batch, batch_size=INSERT_BATCH_SIZE)
                        total_inserted += len(batch)

        logger.info(
            "Parsed %s rows, %s data points, skipped %s unmatched zips.",
            total_rows,
            total_inserted,
            skipped_zips,
        )
        logger.info("Import complete: %s ZHVI records.", total_inserted)
        return total_inserted

    @staticmethod
    def _build_geo_lookup() -> dict[str, Geography]:
        """Build a lookup dict from zip code string to Geography instance."""
        return {
            geo.geo_id: geo
            for geo in Geography.objects.filter(geo_type=Geography.GeoType.ZIPCODE).only(
                "id", "geo_id"
            )
        }
