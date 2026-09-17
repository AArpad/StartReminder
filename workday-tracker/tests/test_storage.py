"""Tests for JSON storage: atomic writes, corrupt-file recovery, path resolution."""

import json
import os
from pathlib import Path

import pytest

from workday_tracker.models import DayRecord, DayStatus
from workday_tracker.storage import (
    CalendarStore,
    MessageStore,
    _atomic_write_json,
    _is_writable,
    _load_json,
    resolve_data_dir,
)


def test_atomic_write_creates_valid_json(tmp_path: Path):
    target = tmp_path / "data.json"
    _atomic_write_json(target, {"version": 1, "value": 42})
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {"version": 1, "value": 42}


def test_atomic_write_leaves_no_temp_files(tmp_path: Path):
    target = tmp_path / "data.json"
    _atomic_write_json(target, {"a": 1})
    remaining = list(tmp_path.iterdir())
    assert remaining == [target]


def test_corrupt_json_is_quarantined_and_default_used(tmp_path: Path):
    target = tmp_path / "data.json"
    target.write_text("{not valid json", encoding="utf-8")
    data, was_corrupt = _load_json(target, {"version": 1, "days": {}})
    assert was_corrupt is True
    assert data == {"version": 1, "days": {}}
    assert not target.exists()
    corrupt_files = list(tmp_path.glob("data.json.corrupt-*"))
    assert len(corrupt_files) == 1


def test_missing_file_uses_default_without_corruption_flag(tmp_path: Path):
    target = tmp_path / "missing.json"
    data, was_corrupt = _load_json(target, {"version": 1, "days": {}})
    assert was_corrupt is False
    assert data == {"version": 1, "days": {}}


def test_calendar_store_reads_version_field(tmp_path: Path):
    calendar_path = tmp_path / "startreminder_calendar.json"
    calendar_path.write_text(
        json.dumps(
            {
                "version": 1,
                "days": {"2026-09-17": {"am": "office", "pm": "home_office"}},
            }
        ),
        encoding="utf-8",
    )
    store = CalendarStore(tmp_path)
    from datetime import date

    record = store.get(date(2026, 9, 17))
    assert record.am == DayStatus.OFFICE
    assert record.pm == DayStatus.HOME_OFFICE


def test_calendar_store_set_and_persist_roundtrip(tmp_path: Path):
    from datetime import date

    store = CalendarStore(tmp_path)
    store.set(date(2026, 9, 18), DayRecord(am=DayStatus.VACATION, pm=DayStatus.VACATION))

    reloaded = CalendarStore(tmp_path)
    record = reloaded.get(date(2026, 9, 18))
    assert record.am == DayStatus.VACATION
    assert record.pm == DayStatus.VACATION


def test_calendar_store_set_empty_record_removes_entry(tmp_path: Path):
    from datetime import date

    store = CalendarStore(tmp_path)
    d = date(2026, 9, 18)
    store.set(d, DayRecord(am=DayStatus.OFFICE, pm=DayStatus.OFFICE))
    store.set(d, DayRecord(am=None, pm=None))
    assert store.get(d).is_empty


def test_message_store_empty_text_deletes_message(tmp_path: Path):
    from datetime import date

    store = MessageStore(tmp_path)
    d = date(2026, 9, 19)
    store.set(d, "## Hello")
    assert store.get(d) is not None
    store.set(d, "   ")
    assert store.get(d) is None


def test_new_message_defaults_to_unseen(tmp_path: Path):
    from datetime import date

    store = MessageStore(tmp_path)
    d = date(2026, 9, 19)
    store.set(d, "## Hello")
    assert store.get(d).seen is False


def test_set_seen_marks_message_and_persists(tmp_path: Path):
    from datetime import date

    store = MessageStore(tmp_path)
    d = date(2026, 9, 19)
    store.set(d, "## Hello")
    store.set_seen(d, True)
    assert store.get(d).seen is True

    reloaded = MessageStore(tmp_path)
    assert reloaded.get(d).seen is True


def test_editing_message_text_preserves_seen_flag(tmp_path: Path):
    from datetime import date

    store = MessageStore(tmp_path)
    d = date(2026, 9, 19)
    store.set(d, "## Hello")
    store.set_seen(d, True)
    store.set(d, "## Hello, updated")
    assert store.get(d).seen is True


def test_set_seen_on_missing_message_is_a_no_op(tmp_path: Path):
    from datetime import date

    store = MessageStore(tmp_path)
    store.set_seen(date(2026, 9, 20), True)
    assert store.get(date(2026, 9, 20)) is None


def test_malformed_calendar_json_recovers_with_warning(tmp_path: Path):
    calendar_path = tmp_path / "startreminder_calendar.json"
    calendar_path.write_text("not json at all", encoding="utf-8")
    store = CalendarStore(tmp_path)
    assert store.was_corrupt is True
    assert store.days == {}
    assert list(tmp_path.glob("startreminder_calendar.json.corrupt-*"))


def test_is_writable_true_for_normal_dir(tmp_path: Path):
    assert _is_writable(tmp_path) is True


def test_resolve_data_dir_prefers_executable_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("workday_tracker.storage.get_executable_dir", lambda: tmp_path)
    data_dir, used_fallback = resolve_data_dir()
    assert data_dir == tmp_path
    assert used_fallback is False


def test_resolve_data_dir_falls_back_when_unwritable(monkeypatch, tmp_path: Path):
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    monkeypatch.setattr("workday_tracker.storage.get_executable_dir", lambda: unwritable)
    monkeypatch.setattr("workday_tracker.storage._is_writable", lambda directory: directory != unwritable)
    fallback_root = tmp_path / "fallback_appdata"
    monkeypatch.setenv("LOCALAPPDATA", str(fallback_root))
    data_dir, used_fallback = resolve_data_dir()
    assert used_fallback is True
    assert data_dir == fallback_root / "WorkDayTracker"
