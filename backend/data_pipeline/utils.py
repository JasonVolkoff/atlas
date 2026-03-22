from __future__ import annotations

from decimal import Decimal, InvalidOperation


def safe_float(value: str | float | None) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_decimal(value: str | float | None) -> Decimal | None:
    """Safely convert a value to Decimal, returning None on failure."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split a list into chunks of the given size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]
