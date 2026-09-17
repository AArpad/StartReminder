"""Tests for monthly statistics computation."""

from datetime import date

import pytest

from workday_tracker.models import DayRecord, DayStatus
from workday_tracker.stats import compute_monthly_stats, days_in_month, is_weekend


def test_is_weekend():
    assert is_weekend(date(2026, 9, 19)) is True  # Saturday
    assert is_weekend(date(2026, 9, 20)) is True  # Sunday
    assert is_weekend(date(2026, 9, 21)) is False  # Monday


def test_days_in_month_full_range():
    days = days_in_month(2026, 9)
    assert days[0] == date(2026, 9, 1)
    assert days[-1] == date(2026, 9, 30)
    assert len(days) == 30


def test_half_day_split_office_and_home_office():
    days = {"2026-09-21": DayRecord(am=DayStatus.OFFICE, pm=DayStatus.HOME_OFFICE)}
    stats = compute_monthly_stats(2026, 9, days)
    assert stats.office == 0.5
    assert stats.home_office == 0.5


def test_uniform_full_day_counts_as_one():
    days = {"2026-09-21": DayRecord(am=DayStatus.VACATION, pm=DayStatus.VACATION)}
    stats = compute_monthly_stats(2026, 9, days)
    assert stats.vacation == 1.0


def test_weekend_excluded_from_unrecorded_and_totals():
    # September 2026: weekdays = 22 (Mon-Fri) days, weekends excluded entirely.
    stats = compute_monthly_stats(2026, 9, {})
    weekday_count = sum(1 for d in days_in_month(2026, 9) if not is_weekend(d))
    assert stats.unrecorded_workdays == float(weekday_count)
    assert stats.office == 0.0


def test_weekend_can_be_explicitly_recorded():
    # 2026-09-19 is a Saturday; explicitly recording it should still count.
    days = {"2026-09-19": DayRecord(am=DayStatus.OFFICE, pm=DayStatus.OFFICE)}
    stats = compute_monthly_stats(2026, 9, days)
    assert stats.office == 1.0


def test_unrecorded_workdays_counts_half_missing_half():
    days = {"2026-09-21": DayRecord(am=DayStatus.OFFICE, pm=None)}
    stats = compute_monthly_stats(2026, 9, days)
    assert stats.office == 0.5
    weekday_count = sum(1 for d in days_in_month(2026, 9) if not is_weekend(d))
    assert stats.unrecorded_workdays == weekday_count - 0.5


def test_month_boundary_february_leap_year():
    days = days_in_month(2024, 2)
    assert len(days) == 29
    assert days[-1] == date(2024, 2, 29)


def test_month_boundary_february_non_leap_year():
    days = days_in_month(2026, 2)
    assert len(days) == 28
