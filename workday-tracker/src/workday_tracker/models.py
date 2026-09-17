"""Data models used throughout the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class DayStatus(str, Enum):
    """Possible status values for a half-day."""

    OFFICE = "office"
    HOME_OFFICE = "home_office"
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    PUBLIC_HOLIDAY = "public_holiday"

    @property
    def label_hu(self) -> str:
        """Human readable Hungarian label."""
        return _STATUS_LABELS_HU[self]

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional["DayStatus"]:
        """Parse a raw JSON value into a DayStatus, returning None for null/unknown."""
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            return None


_STATUS_LABELS_HU: dict[DayStatus, str] = {
    DayStatus.OFFICE: "Iroda",
    DayStatus.HOME_OFFICE: "Home Office",
    DayStatus.VACATION: "Szabadság",
    DayStatus.SICK_LEAVE: "Betegszabadság",
    DayStatus.PUBLIC_HOLIDAY: "Ünnepnap",
}


@dataclass
class DayRecord:
    """Status of a single calendar day, split into morning (am) and afternoon (pm)."""

    am: Optional[DayStatus] = None
    pm: Optional[DayStatus] = None

    @property
    def is_empty(self) -> bool:
        return self.am is None and self.pm is None

    @property
    def is_uniform(self) -> bool:
        """True if the whole day has a single status (or is fully empty)."""
        return self.am == self.pm

    def to_dict(self) -> dict:
        return {
            "am": self.am.value if self.am else None,
            "pm": self.pm.value if self.pm else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DayRecord":
        return cls(
            am=DayStatus.from_value(data.get("am")),
            pm=DayStatus.from_value(data.get("pm")),
        )


@dataclass
class Message:
    """A markdown message attached to a calendar day."""

    text: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    seen: bool = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "seen": self.seen,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            text=data.get("text", ""),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            seen=bool(data.get("seen", False)),
        )


def _parse_datetime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.now()


def date_key(d: date) -> str:
    """Canonical ISO string key used in JSON files."""
    return d.isoformat()
