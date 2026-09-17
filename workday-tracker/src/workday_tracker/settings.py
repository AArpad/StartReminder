"""Application settings persistence and Windows autostart (registry) handling."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .storage import SETTINGS_FILENAME, StorageError, _atomic_write_json, _load_json

logger = logging.getLogger("workday_tracker")

SETTINGS_VERSION = 1

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "WorkDayTracker"

THEME_MODES = ("dark", "light", "system")
DEFAULT_COLOR_SCHEME = "default"
COLOR_SCHEMES = ("default", "solarized", "nord", "high_contrast")

DEFAULT_WINDOW_WIDTH = 780
DEFAULT_WINDOW_HEIGHT = 460
MIN_WINDOW_WIDTH = 480
MIN_WINDOW_HEIGHT = 360

try:
    import winreg
except ImportError:  # non-Windows platforms (e.g. running tests on Linux/CI)
    winreg = None  # type: ignore[assignment]


@dataclass
class Settings:
    """User-configurable settings, stored in startreminder_settings.json."""

    autostart: bool = False
    theme_mode: str = "system"
    color_scheme: str = DEFAULT_COLOR_SCHEME
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT

    def to_dict(self) -> dict:
        return {
            "version": SETTINGS_VERSION,
            "autostart": self.autostart,
            "theme_mode": self.theme_mode,
            "color_scheme": self.color_scheme,
            "window_width": self.window_width,
            "window_height": self.window_height,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        theme_mode = data.get("theme_mode", "system")
        if theme_mode not in THEME_MODES:
            theme_mode = "system"
        color_scheme = data.get("color_scheme", DEFAULT_COLOR_SCHEME)
        if color_scheme not in COLOR_SCHEMES:
            color_scheme = DEFAULT_COLOR_SCHEME
        window_width = _coerce_dimension(
            data.get("window_width"), DEFAULT_WINDOW_WIDTH, MIN_WINDOW_WIDTH
        )
        window_height = _coerce_dimension(
            data.get("window_height"), DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_HEIGHT
        )
        return cls(
            autostart=bool(data.get("autostart", False)),
            theme_mode=theme_mode,
            color_scheme=color_scheme,
            window_width=window_width,
            window_height=window_height,
        )


def _coerce_dimension(value: object, default: int, minimum: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


class SettingsStore:
    """Loads/saves Settings and keeps the autostart registry entry in sync."""

    def __init__(self, data_dir: Path, executable_path: Optional[Path] = None):
        self.path = data_dir / SETTINGS_FILENAME
        self.executable_path = executable_path or _default_executable_path()
        self.was_corrupt = False
        self.settings = self._load()
        # The registry is the source of truth for autostart, not the JSON file.
        self.settings.autostart = is_autostart_enabled()

    def _load(self) -> Settings:
        raw, corrupt = _load_json(self.path, {"version": SETTINGS_VERSION})
        self.was_corrupt = corrupt
        return Settings.from_dict(raw)

    def save(self) -> None:
        try:
            _atomic_write_json(self.path, self.settings.to_dict())
        except OSError as exc:
            logger.error("Failed to save settings: %s", exc)
            raise StorageError(
                "Nem sikerült menteni a beállításokat. Ellenőrizd, hogy az "
                "adatkönyvtár írható-e."
            ) from exc

    def set_autostart(self, enabled: bool) -> None:
        try:
            if enabled:
                enable_autostart(self.executable_path)
            else:
                disable_autostart()
            self.settings.autostart = is_autostart_enabled()
            self.save()
        except OSError as exc:
            logger.error("Failed to update autostart registry entry: %s", exc)
            raise StorageError(
                "Nem sikerült módosítani a Windows automatikus indítás "
                "beállítását a rendszerleíró adatbázisban."
            ) from exc

    def set_theme_mode(self, mode: str) -> None:
        if mode not in THEME_MODES:
            raise ValueError(f"Invalid theme mode: {mode}")
        self.settings.theme_mode = mode
        self.save()

    def set_color_scheme(self, scheme: str) -> None:
        if scheme not in COLOR_SCHEMES:
            raise ValueError(f"Invalid color scheme: {scheme}")
        self.settings.color_scheme = scheme
        self.save()

    def set_window_size(self, width: int, height: int) -> None:
        self.settings.window_width = max(width, MIN_WINDOW_WIDTH)
        self.settings.window_height = max(height, MIN_WINDOW_HEIGHT)
        self.save()


def _default_executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.executable).resolve()


def is_autostart_enabled() -> bool:
    """Read the actual registry state (not cached settings)."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, RUN_VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        logger.error("Failed to read autostart registry key: %s", exc)
        return False


def enable_autostart(executable_path: Path) -> None:
    if winreg is None:
        raise OSError("winreg is only available on Windows")
    quoted_path = f'"{executable_path}"'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
        winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, quoted_path)


def disable_autostart() -> None:
    if winreg is None:
        raise OSError("winreg is only available on Windows")
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, RUN_VALUE_NAME)
    except FileNotFoundError:
        pass  # Already disabled.


def detect_system_uses_light_theme() -> bool:
    """Read HKCU AppsUseLightTheme. Defaults to True (light) if unavailable."""
    if winreg is None:
        return True
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return bool(value)
    except OSError:
        return True
