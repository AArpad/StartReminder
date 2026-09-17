"""Color palette definitions for all theme/color-scheme combinations."""

from __future__ import annotations

from dataclasses import dataclass

from ..models import DayStatus


@dataclass(frozen=True)
class Palette:
    """A full set of colors needed to render the QSS template and the calendar."""

    name: str
    is_dark: bool

    window_bg: str
    surface_bg: str
    base_bg: str
    border: str
    text: str
    text_muted: str

    accent: str
    accent_text: str

    button_bg: str
    button_hover_bg: str
    button_pressed_bg: str
    button_text: str

    selection_bg: str
    selection_text: str

    weekend_bg: str
    today_border: str

    status_office: str
    status_home_office: str
    status_vacation: str
    status_sick_leave: str
    status_public_holiday: str
    status_empty: str

    danger: str

    def status_color(self, status: DayStatus | None) -> str:
        if status is None:
            return self.status_empty
        return {
            DayStatus.OFFICE: self.status_office,
            DayStatus.HOME_OFFICE: self.status_home_office,
            DayStatus.VACATION: self.status_vacation,
            DayStatus.SICK_LEAVE: self.status_sick_leave,
            DayStatus.PUBLIC_HOLIDAY: self.status_public_holiday,
        }[status]


_DEFAULT_DARK = Palette(
    name="default_dark",
    is_dark=True,
    window_bg="#1e2126",
    surface_bg="#262a31",
    base_bg="#2d323a",
    border="#3c4149",
    text="#e6e9ef",
    text_muted="#9aa2af",
    accent="#4c8bf5",
    accent_text="#ffffff",
    button_bg="#333943",
    button_hover_bg="#3d4450",
    button_pressed_bg="#2a2f37",
    button_text="#e6e9ef",
    selection_bg="#4c8bf5",
    selection_text="#ffffff",
    weekend_bg="#25282e",
    today_border="#4c8bf5",
    status_office="#4c8bf5",
    status_home_office="#3fb886",
    status_vacation="#f5b942",
    status_sick_leave="#e5606d",
    status_public_holiday="#9b6ef3",
    status_empty="#454b55",
    danger="#e5606d",
)

_DEFAULT_LIGHT = Palette(
    name="default_light",
    is_dark=False,
    window_bg="#f5f6f8",
    surface_bg="#ffffff",
    base_bg="#ffffff",
    border="#d3d7de",
    text="#1c1f24",
    text_muted="#5b6270",
    accent="#2f6fed",
    accent_text="#ffffff",
    button_bg="#eceef2",
    button_hover_bg="#e1e4ea",
    button_pressed_bg="#d3d7de",
    button_text="#1c1f24",
    selection_bg="#2f6fed",
    selection_text="#ffffff",
    weekend_bg="#eceef2",
    today_border="#2f6fed",
    status_office="#2f6fed",
    status_home_office="#28966a",
    status_vacation="#c98a1a",
    status_sick_leave="#d1445a",
    status_public_holiday="#7c4fd6",
    status_empty="#d3d7de",
    danger="#d1445a",
)

_SOLARIZED_BASE03 = "#002b36"
_SOLARIZED_BASE02 = "#073642"
_SOLARIZED_BASE01 = "#586e75"
_SOLARIZED_BASE00 = "#657b83"
_SOLARIZED_BASE0 = "#839496"
_SOLARIZED_BASE1 = "#93a1a1"
_SOLARIZED_BASE2 = "#eee8d5"
_SOLARIZED_BASE3 = "#fdf6e3"
_SOLARIZED_YELLOW = "#b58900"
_SOLARIZED_ORANGE = "#cb4b16"
_SOLARIZED_RED = "#dc322f"
_SOLARIZED_MAGENTA = "#d33682"
_SOLARIZED_VIOLET = "#6c71c4"
_SOLARIZED_BLUE = "#268bd2"
_SOLARIZED_CYAN = "#2aa198"
_SOLARIZED_GREEN = "#859900"

_SOLARIZED_DARK = Palette(
    name="solarized_dark",
    is_dark=True,
    window_bg=_SOLARIZED_BASE03,
    surface_bg=_SOLARIZED_BASE02,
    base_bg=_SOLARIZED_BASE02,
    border=_SOLARIZED_BASE01,
    text=_SOLARIZED_BASE0,
    text_muted=_SOLARIZED_BASE01,
    accent=_SOLARIZED_BLUE,
    accent_text=_SOLARIZED_BASE3,
    button_bg=_SOLARIZED_BASE02,
    button_hover_bg="#0a4152",
    button_pressed_bg="#062b35",
    button_text=_SOLARIZED_BASE1,
    selection_bg=_SOLARIZED_BLUE,
    selection_text=_SOLARIZED_BASE3,
    weekend_bg="#032027",
    today_border=_SOLARIZED_CYAN,
    status_office=_SOLARIZED_BLUE,
    status_home_office=_SOLARIZED_GREEN,
    status_vacation=_SOLARIZED_YELLOW,
    status_sick_leave=_SOLARIZED_RED,
    status_public_holiday=_SOLARIZED_VIOLET,
    status_empty=_SOLARIZED_BASE01,
    danger=_SOLARIZED_RED,
)

_SOLARIZED_LIGHT = Palette(
    name="solarized_light",
    is_dark=False,
    window_bg=_SOLARIZED_BASE3,
    surface_bg=_SOLARIZED_BASE2,
    base_bg=_SOLARIZED_BASE3,
    border=_SOLARIZED_BASE1,
    text=_SOLARIZED_BASE00,
    text_muted=_SOLARIZED_BASE1,
    accent=_SOLARIZED_BLUE,
    accent_text=_SOLARIZED_BASE3,
    button_bg=_SOLARIZED_BASE2,
    button_hover_bg="#e4ddc8",
    button_pressed_bg="#d8d0b8",
    button_text=_SOLARIZED_BASE00,
    selection_bg=_SOLARIZED_BLUE,
    selection_text=_SOLARIZED_BASE3,
    weekend_bg="#e4ddc8",
    today_border=_SOLARIZED_CYAN,
    status_office=_SOLARIZED_BLUE,
    status_home_office=_SOLARIZED_GREEN,
    status_vacation=_SOLARIZED_YELLOW,
    status_sick_leave=_SOLARIZED_RED,
    status_public_holiday=_SOLARIZED_VIOLET,
    status_empty=_SOLARIZED_BASE1,
    danger=_SOLARIZED_RED,
)

_NORD_DARK = Palette(
    name="nord_dark",
    is_dark=True,
    window_bg="#2e3440",
    surface_bg="#3b4252",
    base_bg="#434c5e",
    border="#4c566a",
    text="#eceff4",
    text_muted="#d8dee9",
    accent="#88c0d0",
    accent_text="#2e3440",
    button_bg="#434c5e",
    button_hover_bg="#4c566a",
    button_pressed_bg="#3b4252",
    button_text="#eceff4",
    selection_bg="#88c0d0",
    selection_text="#2e3440",
    weekend_bg="#272c36",
    today_border="#88c0d0",
    status_office="#5e81ac",
    status_home_office="#a3be8c",
    status_vacation="#ebcb8b",
    status_sick_leave="#bf616a",
    status_public_holiday="#b48ead",
    status_empty="#4c566a",
    danger="#bf616a",
)

_NORD_LIGHT = Palette(
    name="nord_light",
    is_dark=False,
    window_bg="#eceff4",
    surface_bg="#e5e9f0",
    base_bg="#ffffff",
    border="#d8dee9",
    text="#2e3440",
    text_muted="#4c566a",
    accent="#5e81ac",
    accent_text="#eceff4",
    button_bg="#e5e9f0",
    button_hover_bg="#d8dee9",
    button_pressed_bg="#c9d1e0",
    button_text="#2e3440",
    selection_bg="#5e81ac",
    selection_text="#eceff4",
    weekend_bg="#d8dee9",
    today_border="#5e81ac",
    status_office="#5e81ac",
    status_home_office="#a3be8c",
    status_vacation="#d08770",
    status_sick_leave="#bf616a",
    status_public_holiday="#b48ead",
    status_empty="#d8dee9",
    danger="#bf616a",
)

_HIGH_CONTRAST_DARK = Palette(
    name="high_contrast_dark",
    is_dark=True,
    window_bg="#000000",
    surface_bg="#0a0a0a",
    base_bg="#000000",
    border="#ffffff",
    text="#ffffff",
    text_muted="#e0e0e0",
    accent="#ffd400",
    accent_text="#000000",
    button_bg="#1a1a1a",
    button_hover_bg="#2b2b2b",
    button_pressed_bg="#000000",
    button_text="#ffffff",
    selection_bg="#ffd400",
    selection_text="#000000",
    weekend_bg="#141414",
    today_border="#ffd400",
    status_office="#3aa8ff",
    status_home_office="#38e07a",
    status_vacation="#ffd400",
    status_sick_leave="#ff4d4d",
    status_public_holiday="#c76bff",
    status_empty="#5a5a5a",
    danger="#ff4d4d",
)

_HIGH_CONTRAST_LIGHT = Palette(
    name="high_contrast_light",
    is_dark=False,
    window_bg="#ffffff",
    surface_bg="#ffffff",
    base_bg="#ffffff",
    border="#000000",
    text="#000000",
    text_muted="#1a1a1a",
    accent="#0047ab",
    accent_text="#ffffff",
    button_bg="#f0f0f0",
    button_hover_bg="#dddddd",
    button_pressed_bg="#c0c0c0",
    button_text="#000000",
    selection_bg="#0047ab",
    selection_text="#ffffff",
    weekend_bg="#e6e6e6",
    today_border="#0047ab",
    status_office="#0047ab",
    status_home_office="#006400",
    status_vacation="#a15c00",
    status_sick_leave="#b00020",
    status_public_holiday="#5a189a",
    status_empty="#808080",
    danger="#b00020",
)


PALETTES: dict[str, dict[str, Palette]] = {
    "default": {"dark": _DEFAULT_DARK, "light": _DEFAULT_LIGHT},
    "solarized": {"dark": _SOLARIZED_DARK, "light": _SOLARIZED_LIGHT},
    "nord": {"dark": _NORD_DARK, "light": _NORD_LIGHT},
    "high_contrast": {"dark": _HIGH_CONTRAST_DARK, "light": _HIGH_CONTRAST_LIGHT},
}

COLOR_SCHEME_LABELS_HU: dict[str, str] = {
    "default": "Alapértelmezett",
    "solarized": "Solarized",
    "nord": "Nord",
    "high_contrast": "Nagy kontraszt",
}


def get_palette(color_scheme: str, is_dark: bool) -> Palette:
    """Look up a palette, falling back to 'default' for unknown scheme names."""
    scheme = PALETTES.get(color_scheme, PALETTES["default"])
    return scheme["dark"] if is_dark else scheme["light"]
