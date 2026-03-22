from __future__ import annotations

from django.core.management.base import BaseCommand

from data_pipeline.services.geography_import_service import GeographyImportService


class Command(BaseCommand):
    help = (
        "Import geographic boundaries (ZCTA zip codes and counties) "
        "from Census TIGER/Line shapefiles."
    )

    def add_arguments(self, parser: object) -> None:
        parser.add_argument(
            "--data-dir",
            type=str,
            default=None,
            help=("Directory to store downloaded shapefiles. Uses a temp dir if not set."),
        )

    def handle(self, *args: object, **options: object) -> None:
        data_dir = options.get("data_dir")
        self.stdout.write("Starting geography import...")
        counts = GeographyImportService.import_all(data_dir=data_dir)
        msg = f"Done! Imported {counts['zipcodes']} zip codes and {counts['counties']} counties."
        self.stdout.write(self.style.SUCCESS(msg))
