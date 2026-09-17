"""Tests for settings persistence and registry-backed autostart (winreg mocked)."""

from pathlib import Path

import pytest

import workday_tracker.settings as settings_module
from workday_tracker.settings import Settings, SettingsStore


class FakeWinReg:
    """Minimal in-memory stand-in for the winreg module used in tests."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.values: dict[str, str] = {}

    def CreateKey(self, hive, path):
        return _FakeKey(self)

    def OpenKey(self, hive, path, reserved=0, access=0):
        if "WorkDayTracker" not in self.values and access == self.KEY_READ:
            # Simulate FileNotFoundError only when queried for the value below;
            # opening the key itself succeeds (matches real registry behavior
            # for an always-present Run key).
            pass
        return _FakeKey(self)

    def SetValueEx(self, key, name, reserved, value_type, value):
        self.values[name] = value

    def QueryValueEx(self, key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], self.REG_SZ

    def DeleteValue(self, key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]


class _FakeKey:
    def __init__(self, registry: FakeWinReg):
        self._registry = registry

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture()
def fake_winreg(monkeypatch):
    fake = FakeWinReg()
    monkeypatch.setattr(settings_module, "winreg", fake)
    return fake


def test_autostart_disabled_by_default(fake_winreg):
    assert settings_module.is_autostart_enabled() is False


def test_enable_autostart_writes_quoted_path(fake_winreg):
    settings_module.enable_autostart(Path("C:/Program Files/WorkDayTracker/WorkDayTracker.exe"))
    assert settings_module.is_autostart_enabled() is True
    assert fake_winreg.values["WorkDayTracker"] == '"C:\\Program Files\\WorkDayTracker\\WorkDayTracker.exe"'


def test_disable_autostart_removes_value(fake_winreg):
    settings_module.enable_autostart(Path("C:/app.exe"))
    settings_module.disable_autostart()
    assert settings_module.is_autostart_enabled() is False


def test_disable_autostart_is_idempotent(fake_winreg):
    # Disabling when nothing is set must not raise.
    settings_module.disable_autostart()
    assert settings_module.is_autostart_enabled() is False


def test_settings_store_reads_registry_as_source_of_truth(tmp_path, fake_winreg):
    settings_module.enable_autostart(Path("C:/app.exe"))
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    assert store.settings.autostart is True


def test_settings_store_set_autostart_updates_registry_and_json(tmp_path, fake_winreg):
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    store.set_autostart(True)
    assert settings_module.is_autostart_enabled() is True
    assert store.path.exists()

    store.set_autostart(False)
    assert settings_module.is_autostart_enabled() is False


def test_settings_roundtrip_theme_and_color_scheme(tmp_path, fake_winreg):
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    store.set_theme_mode("dark")
    store.set_color_scheme("nord")

    reloaded = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    assert reloaded.settings.theme_mode == "dark"
    assert reloaded.settings.color_scheme == "nord"


def test_settings_store_persists_window_size(tmp_path, fake_winreg):
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    store.set_window_size(1600, 900)

    reloaded = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    assert reloaded.settings.window_width == 1600
    assert reloaded.settings.window_height == 900


def test_settings_window_size_clamped_to_minimum(tmp_path, fake_winreg):
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    store.set_window_size(10, 10)
    assert store.settings.window_width == settings_module.MIN_WINDOW_WIDTH
    assert store.settings.window_height == settings_module.MIN_WINDOW_HEIGHT


def test_settings_from_dict_falls_back_to_default_window_size_when_invalid():
    s = Settings.from_dict({"window_width": "not-a-number", "window_height": -5})
    assert s.window_width == settings_module.DEFAULT_WINDOW_WIDTH
    assert s.window_height == settings_module.DEFAULT_WINDOW_HEIGHT


def test_settings_from_dict_rejects_unknown_theme_mode():
    s = Settings.from_dict({"theme_mode": "not-a-real-mode", "color_scheme": "bogus"})
    assert s.theme_mode == "system"
    assert s.color_scheme == "default"


def test_settings_set_invalid_theme_mode_raises(tmp_path, fake_winreg):
    store = SettingsStore(tmp_path, executable_path=Path("C:/app.exe"))
    with pytest.raises(ValueError):
        store.set_theme_mode("neon")
