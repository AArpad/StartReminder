"""Resolves the active theme (system detection + QSS generation)."""

from __future__ import annotations

import logging
from pathlib import Path
from string import Template

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from ..settings import detect_system_uses_light_theme
from .palettes import Palette, get_palette

logger = logging.getLogger("workday_tracker")

_TEMPLATE_PATH = Path(__file__).with_name("style.qss.tmpl")


def resolve_is_dark(theme_mode: str) -> bool:
    """Resolve the effective dark/light state for a given theme_mode setting."""
    if theme_mode == "dark":
        return True
    if theme_mode == "light":
        return False
    # "system"
    try:
        return not detect_system_uses_light_theme()
    except OSError as exc:
        logger.error("Failed to detect system theme, defaulting to light: %s", exc)
        return False


def build_stylesheet(palette: Palette) -> str:
    """Render the QSS template with the given palette's colors."""
    try:
        template_text = _TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to read QSS template: %s", exc)
        return ""
    template = Template(template_text)
    mapping = {
        "window_bg": palette.window_bg,
        "surface_bg": palette.surface_bg,
        "base_bg": palette.base_bg,
        "border": palette.border,
        "text": palette.text,
        "text_muted": palette.text_muted,
        "accent": palette.accent,
        "accent_text": palette.accent_text,
        "button_bg": palette.button_bg,
        "button_hover_bg": palette.button_hover_bg,
        "button_pressed_bg": palette.button_pressed_bg,
        "button_text": palette.button_text,
        "selection_bg": palette.selection_bg,
        "selection_text": palette.selection_text,
        "weekend_bg": palette.weekend_bg,
        "today_border": palette.today_border,
        "danger": palette.danger,
    }
    return template.safe_substitute(mapping)


class ThemeManager(QObject):
    """Applies the active theme to the QApplication and notifies listeners on change."""

    theme_changed = Signal()

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._theme_mode = "system"
        self._color_scheme = "default"
        self._palette: Palette = get_palette("default", False)

    @property
    def palette(self) -> Palette:
        return self._palette

    def apply(self, theme_mode: str, color_scheme: str) -> None:
        """Recompute the palette and re-apply the stylesheet to the application."""
        self._theme_mode = theme_mode
        self._color_scheme = color_scheme
        is_dark = resolve_is_dark(theme_mode)
        self._palette = get_palette(color_scheme, is_dark)
        stylesheet = build_stylesheet(self._palette)
        self._app.setStyleSheet(stylesheet)
        self.theme_changed.emit()

    def refresh_if_system(self) -> None:
        """Re-evaluate the system theme (e.g. on a timer) if mode is 'system'."""
        if self._theme_mode == "system":
            self.apply(self._theme_mode, self._color_scheme)
