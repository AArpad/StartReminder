"""Panel showing the monthly aggregated statistics."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from ..stats import MonthlyStats

_PANEL_WIDTH = 230
_TITLE_WIDTH = 160
_VALUE_WIDTH = 45  # fits up to 3 digits plus a ",5" half-day suffix


def _format_count(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:g}".replace(".", ",")


class StatsPanel(QGroupBox):
    """Displays counters for the currently shown month.

    The panel has a fixed size so it never resizes as the numbers (and their
    digit counts) change between months.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Havi összesítés", parent)
        self.setFixedWidth(_PANEL_WIDTH)
        layout = QGridLayout(self)
        layout.setVerticalSpacing(2)
        layout.setHorizontalSpacing(8)

        self._office_label = self._add_row(layout, 0, "Irodai napok")
        self._home_office_label = self._add_row(layout, 1, "Home Office napok")
        self._travel_label = self._add_row(layout, 2, "Utazási napok")
        self._vacation_label = self._add_row(layout, 3, "Szabadság")
        self._sick_leave_label = self._add_row(layout, 4, "Betegszabadság")
        self._public_holiday_label = self._add_row(layout, 5, "Ünnepnap")
        self._unrecorded_label = self._add_row(layout, 6, "Rögzítetlen munkanapok")

    def _add_row(self, layout: QGridLayout, row: int, title: str) -> QLabel:
        title_label = QLabel(title + ":")
        title_label.setProperty("muted", True)
        title_label.setFixedWidth(_TITLE_WIDTH)
        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setFixedWidth(_VALUE_WIDTH)
        layout.addWidget(title_label, row, 0)
        layout.addWidget(value_label, row, 1)
        return value_label

    def update_stats(self, stats: MonthlyStats) -> None:
        self._office_label.setText(_format_count(stats.office))
        self._home_office_label.setText(_format_count(stats.home_office))
        self._travel_label.setText(str(stats.travel_days))
        self._vacation_label.setText(_format_count(stats.vacation))
        self._sick_leave_label.setText(_format_count(stats.sick_leave))
        self._public_holiday_label.setText(_format_count(stats.public_holiday))
        self._unrecorded_label.setText(_format_count(stats.unrecorded_workdays))
