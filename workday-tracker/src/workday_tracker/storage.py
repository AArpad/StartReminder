"""JSON persistence layer: atomic writes, corrupt-file recovery, path resolution."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from .models import DayRecord, Message, date_key

CALENDAR_FILENAME = "startreminder_calendar.json"
MESSAGES_FILENAME = "startreminder_messages.json"
SETTINGS_FILENAME = "startreminder_settings.json"
LOG_FILENAME = "workday_tracker.log"

CALENDAR_VERSION = 1
MESSAGES_VERSION = 1

logger = logging.getLogger("workday_tracker")


def get_executable_dir() -> Path:
    """Directory the EXE (or the script, when running from source) lives in."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def _is_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".writetest_{os.getpid()}.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def resolve_data_dir() -> tuple[Path, bool]:
    """Return (data_dir, used_fallback).

    Prefers the executable's own directory. If it is not writable, falls back
    to %LOCALAPPDATA%\\WorkDayTracker (or ~/.workday_tracker on non-Windows).
    """
    primary = get_executable_dir()
    if _is_writable(primary):
        return primary, False

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        fallback = Path(local_app_data) / "WorkDayTracker"
    else:
        fallback = Path.home() / ".workday_tracker"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback, True


def setup_logging(data_dir: Path) -> None:
    """Configure file logging into the data directory. Never raises."""
    try:
        log_path = data_dir / LOG_FILENAME
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except OSError:
        # Logging itself must never crash the application.
        pass


def _atomic_write_json(path: Path, data: dict) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _quarantine_corrupt_file(path: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    corrupt_path = path.with_name(f"{path.name}.corrupt-{timestamp}")
    try:
        os.replace(path, corrupt_path)
        logger.warning("Corrupt file quarantined: %s -> %s", path, corrupt_path)
    except OSError as exc:
        logger.error("Failed to quarantine corrupt file %s: %s", path, exc)


def _load_json(path: Path, default: dict) -> tuple[dict, bool]:
    """Load JSON from path. Returns (data, was_corrupt)."""
    if not path.exists():
        return dict(default), False
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Top-level JSON value must be an object")
        return data, False
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to read %s: %s", path, exc)
        _quarantine_corrupt_file(path)
        return dict(default), True


class CalendarStore:
    """Persists day statuses."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / CALENDAR_FILENAME
        self.days: dict[str, DayRecord] = {}
        self.was_corrupt = False
        self._load()

    def _load(self) -> None:
        raw, corrupt = _load_json(self.path, {"version": CALENDAR_VERSION, "days": {}})
        self.was_corrupt = corrupt
        self.days = {}
        for key, value in raw.get("days", {}).items():
            try:
                self.days[key] = DayRecord.from_dict(value)
            except (TypeError, AttributeError) as exc:
                logger.error("Skipping malformed day record %s: %s", key, exc)

    def get(self, d: date) -> DayRecord:
        return self.days.get(date_key(d), DayRecord())

    def set(self, d: date, record: DayRecord) -> None:
        key = date_key(d)
        if record.is_empty:
            self.days.pop(key, None)
        else:
            self.days[key] = record
        self.save()

    def save(self) -> None:
        try:
            data = {
                "version": CALENDAR_VERSION,
                "days": {key: rec.to_dict() for key, rec in self.days.items()},
            }
            _atomic_write_json(self.path, data)
        except OSError as exc:
            logger.error("Failed to save calendar data: %s", exc)
            raise StorageError(
                "Nem sikerült menteni a naptár adatait. Ellenőrizd, hogy az "
                "adatkönyvtár írható-e."
            ) from exc


class MessageStore:
    """Persists per-day markdown messages."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / MESSAGES_FILENAME
        self.messages: dict[str, Message] = {}
        self.was_corrupt = False
        self._load()

    def _load(self) -> None:
        raw, corrupt = _load_json(self.path, {"version": MESSAGES_VERSION, "messages": {}})
        self.was_corrupt = corrupt
        self.messages = {}
        for key, value in raw.get("messages", {}).items():
            try:
                self.messages[key] = Message.from_dict(value)
            except (TypeError, AttributeError) as exc:
                logger.error("Skipping malformed message %s: %s", key, exc)

    def get(self, d: date) -> Optional[Message]:
        return self.messages.get(date_key(d))

    def set(self, d: date, text: str) -> None:
        key = date_key(d)
        text = text.strip("\n")
        if not text.strip():
            self.messages.pop(key, None)
        else:
            existing = self.messages.get(key)
            now = datetime.now()
            created = existing.created_at if existing else now
            seen = existing.seen if existing else False
            self.messages[key] = Message(text=text, created_at=created, updated_at=now, seen=seen)
        self.save()

    def delete(self, d: date) -> None:
        self.messages.pop(date_key(d), None)
        self.save()

    def set_seen(self, d: date, seen: bool) -> None:
        """Mark a message as seen/unseen, e.g. once it has been shown to the user."""
        message = self.messages.get(date_key(d))
        if message is None or message.seen == seen:
            return
        message.seen = seen
        self.save()

    def save(self) -> None:
        try:
            data = {
                "version": MESSAGES_VERSION,
                "messages": {key: msg.to_dict() for key, msg in self.messages.items()},
            }
            _atomic_write_json(self.path, data)
        except OSError as exc:
            logger.error("Failed to save message data: %s", exc)
            raise StorageError(
                "Nem sikerült menteni az üzenetet. Ellenőrizd, hogy az "
                "adatkönyvtár írható-e."
            ) from exc


class StorageError(Exception):
    """Raised when a storage operation fails, with a Hungarian user-facing message."""
