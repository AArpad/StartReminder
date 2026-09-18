"""Monthly statistics computation, counting half-days as 0.5."""

from __future__ import annotations

import calendar as calendar_module
from dataclasses import dataclass, field
from datetime import date

from .models import DayRecord, DayStatus


@dataclass
class MonthlyStats:
    """Aggregated counters for one calendar month. Half-days count as 0.5."""

    office: float = 0.0
    home_office: float = 0.0
    vacation: float = 0.0
    sick_leave: float = 0.0
    public_holiday: float = 0.0
    unrecorded_workdays: float = 0.0
    # Days that required a commute: a whole day each, even if only the
    # morning or the afternoon was office - unlike `office`, which counts
    # half-days as 0.5.
    travel_days: int = 0


_STATUS_FIELD: dict[DayStatus, str] = {
    DayStatus.OFFICE: "office",
    DayStatus.HOME_OFFICE: "home_office",
    DayStatus.VACATION: "vacation",
    DayStatus.SICK_LEAVE: "sick_leave",
    DayStatus.PUBLIC_HOLIDAY: "public_holiday",
}


def is_weekend(d: date) -> bool:
    """True for Saturday/Sunday."""
    return d.weekday() >= 5


def days_in_month(year: int, month: int) -> list[date]:
    """All calendar dates belonging to the given year/month."""
    _, last_day = calendar_module.monthrange(year, month)
    return [date(year, month, day) for day in range(1, last_day + 1)]


def compute_monthly_stats(
    year: int, month: int, days: dict[str, DayRecord]
) -> MonthlyStats:
    """Compute aggregated counters for a given month.

    Weekends are excluded from the statistics entirely (unless explicitly
    recorded, in which case they still contribute like any other day, since
    the user deliberately overrode the default).
    """
    stats = MonthlyStats()
    for d in days_in_month(year, month):
        record = days.get(d.isoformat()) or DayRecord()
        weekend = is_weekend(d)
        for half_status in (record.am, record.pm):
            if half_status is None:
                if not weekend:
                    stats.unrecorded_workdays += 0.5
                continue
            _apply_half(stats, half_status)
        if DayStatus.OFFICE in (record.am, record.pm):
            stats.travel_days += 1

    return stats


def _apply_half(stats: MonthlyStats, status: DayStatus) -> None:
    field_name = _STATUS_FIELD.get(status)
    if field_name is None:
        return
    current = getattr(stats, field_name)
    setattr(stats, field_name, current + 0.5)
