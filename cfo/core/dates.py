"""Shared date helpers."""

from datetime import date as date_cls


def window_cutoff(months: int) -> str:
    """First day of the month `months - 1` months before this one (inclusive window).

    Used to bound rolling-average windows for forecasting inputs.
    """
    today = date_cls.today()
    year, month = today.year, today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    return date_cls(year, month, 1).isoformat()
