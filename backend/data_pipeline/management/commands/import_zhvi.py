from __future__ import annotations

from django.core.management.base import BaseCommand

from data_pipeline.services.zhvi_import_service import ZhviImportService


class Command(BaseCommand):
    help = "Import Zillow Home Value Index (ZHVI) data at the zip code level."

    def add_arguments(self, parser: object) -> None:
        parser.add_argument(
            "--data-dir",
            type=str,
            default=None,
            help=("Directory to store downloaded CSV. Uses a temp dir if not set."),
        )

    def handle(self, *args: object, **options: object) -> None:
        data_dir = options.get("data_dir")
        self.stdout.write("Starting ZHVI import...")
        count = ZhviImportService.import_zhvi(data_dir=data_dir)
        self.stdout.write(self.style.SUCCESS(f"Done! Imported {count} ZHVI data points."))
