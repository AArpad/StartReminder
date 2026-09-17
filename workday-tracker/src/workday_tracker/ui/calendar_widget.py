"""Monthly calendar grid widget and the per-day status editing dialog."""

from __future__ import annotations

import calendar as calendar_module
from datetime import date

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..models import DayRecord, DayStatus
from ..stats import is_weekend
from ..storage import CalendarStore
from ..theming.palettes import Palette

WEEKDAY_LABELS_HU = ["H", "K", "Sze", "Cs", "P", "Szo", "V"]
MONTH_LABELS_HU = [
    "Január", "Február", "Március", "Április", "Május", "Június",
    "Július", "Augusztus", "Szeptember", "Október", "November", "December",
]

_STATUS_ORDER = [
    DayStatus.OFFICE,
    DayStatus.HOME_OFFICE,
    DayStatus.VACATION,
    DayStatus.SICK_LEAVE,
    DayStatus.PUBLIC_HOLIDAY,
]

_NO_STATUS_LABEL = "Nincs rögzítve"
_CELL_SIZE = 24


def _contrasting_text_color(bg: QColor) -> str:
    """Pick black-ish or white-ish text so it stays readable on any fill color."""
    luminance = 0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()
    return "#141414" if luminance > 150 else "#f5f5f5"


class DayCell(QFrame):
    """A single day square in the calendar grid.

    The whole cell background is filled with the day's status color (split
    diagonally for a half-day); only the day number is drawn on top of it,
    centered and colored for contrast against that fill.
    """

    clicked = Signal(date)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("calendarDayCell")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedSize(_CELL_SIZE, _CELL_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._day: date | None = None
        self._record = DayRecord()
        self._palette: Palette | None = None
        self._in_current_month = True
        self._is_today = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._number_label = QLabel("", self)
        self._number_label.setObjectName("dayNumberLabel")
        self._number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self._number_label.font()
        font.setBold(True)
        self._number_label.setFont(font)
        layout.addWidget(self._number_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_data(
        self,
        day: date,
        record: DayRecord,
        is_today: bool,
        in_current_month: bool,
        palette: Palette,
    ) -> None:
        self._day = day
        self._record = record
        self._palette = palette
        self._in_current_month = in_current_month
        self._is_today = is_today
        self._number_label.setText(str(day.day))

        weekend = is_weekend(day)
        bg_color = self._primary_fill_color(weekend)
        text_color = _contrasting_text_color(bg_color) if bg_color is not None else palette.text

        if not in_current_month:
            self._number_label.setStyleSheet("color: rgba(128,128,128,120); background: transparent;")
        elif weekend and self._record.is_empty:
            self._number_label.setStyleSheet(f"color: {palette.text_muted}; background: transparent;")
        else:
            self._number_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        self.setVisible(True)
        self.update()

    def _primary_fill_color(self, weekend: bool) -> QColor | None:
        """The color the day number sits on top of, used to pick a readable text color."""
        if self._palette is None:
            return None
        if self._record.is_empty:
            return QColor(self._palette.weekend_bg if weekend else self._palette.surface_bg)
        if self._record.is_uniform:
            return QColor(self._palette.status_color(self._record.am))
        # Half-day split: the number sits in the middle, roughly on the boundary
        # between the two triangles, so blend both colors for the contrast check.
        am_color = QColor(self._palette.status_color(self._record.am))
        pm_color = QColor(self._palette.status_color(self._record.pm))
        return QColor(
            (am_color.red() + pm_color.red()) // 2,
            (am_color.green() + pm_color.green()) // 2,
            (am_color.blue() + pm_color.blue()) // 2,
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._day is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._day)
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._palette is None or self._day is None:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        radius = 3
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        weekend = is_weekend(self._day)

        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(clip_path)

        if self._record.is_empty:
            bg_color = QColor(self._palette.weekend_bg if weekend else self._palette.surface_bg)
            painter.fillRect(self.rect(), bg_color)
        elif self._record.is_uniform:
            painter.fillRect(self.rect(), QColor(self._palette.status_color(self._record.am)))
        else:
            am_color = QColor(self._palette.status_color(self._record.am))
            pm_color = QColor(self._palette.status_color(self._record.pm))
            r = self.rect()
            top_left = QPointF(r.left(), r.top())
            top_right = QPointF(r.right(), r.top())
            bottom_left = QPointF(r.left(), r.bottom())
            bottom_right = QPointF(r.right(), r.bottom())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(am_color)
            painter.drawPolygon(QPolygonF([top_left, top_right, bottom_left]))
            painter.setBrush(pm_color)
            painter.drawPolygon(QPolygonF([top_right, bottom_right, bottom_left]))

        painter.setClipping(False)

        border_width = 2 if self._is_today else 1
        border_color = QColor(
            self._palette.today_border if self._is_today else self._palette.border
        )
        pen = painter.pen()
        pen.setWidth(border_width)
        pen.setColor(border_color)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

        painter.end()


class CalendarWidget(QWidget):
    """Month grid with navigation, backed by CalendarStore/MessageStore."""

    day_activated = Signal(date)
    month_changed = Signal(int, int)

    def __init__(
        self,
        calendar_store: CalendarStore,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._calendar_store = calendar_store
        self._palette: Palette | None = None

        today = date.today()
        self._year = today.year
        self._month = today.month

        outer = QVBoxLayout(self)

        nav_bar = QHBoxLayout()
        self._prev_button = QPushButton("◀")
        self._prev_button.setFixedWidth(36)
        self._prev_button.clicked.connect(self.go_previous_month)
        self._next_button = QPushButton("▶")
        self._next_button.setFixedWidth(36)
        self._next_button.clicked.connect(self.go_next_month)
        # The month title itself jumps back to the current month when clicked,
        # so the nav bar stays symmetric (prev - title - next) and the grid
        # below lines up centered exactly between the two paging buttons.
        self._month_button = QPushButton("")
        self._month_button.setObjectName("monthJumpButton")
        self._month_button.setFlat(True)
        self._month_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._month_button.setToolTip("Ugrás a mai hónapra")
        self._month_button.clicked.connect(self.go_today)
        font = self._month_button.font()
        font.setPointSize(font.pointSize() + 3)
        font.setBold(True)
        self._month_button.setFont(font)

        nav_bar.addWidget(self._prev_button)
        nav_bar.addWidget(self._month_button, 1)
        nav_bar.addWidget(self._next_button)
        outer.addLayout(nav_bar)
        self._nav_bar_layout = nav_bar

        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._grid = QGridLayout(grid_container)
        self._grid.setSpacing(2)
        center_row = QHBoxLayout()
        center_row.addStretch(1)
        center_row.addWidget(grid_container)
        center_row.addStretch(1)
        outer.addLayout(center_row)
        outer.addStretch(1)

        for col, label in enumerate(WEEKDAY_LABELS_HU):
            header = QLabel(label)
            header.setFixedWidth(_CELL_SIZE)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setProperty("muted", True)
            header_font = header.font()
            header_font.setPointSize(max(header_font.pointSize() - 2, 6))
            header.setFont(header_font)
            self._grid.addWidget(header, 0, col)

        self._cells: list[DayCell] = []
        for row in range(1, 7):
            for col in range(7):
                cell = DayCell()
                cell.clicked.connect(self.day_activated.emit)
                self._grid.addWidget(cell, row, col)
                self._cells.append(cell)


    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    def grid_top_offset(self) -> int:
        """Vertical space the nav bar (+ layout spacing) takes above the day grid.

        Lets sibling widgets (e.g. the monthly stats panel) line their top up
        with the day cells instead of the nav bar above them.
        """
        layout = self.layout()
        spacing = layout.spacing() if layout is not None else 0
        return self._nav_bar_layout.sizeHint().height() + spacing

    def set_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.refresh()

    def go_previous_month(self) -> None:
        if self._month == 1:
            self._year -= 1
            self._month = 12
        else:
            self._month -= 1
        self._on_month_changed()

    def go_next_month(self) -> None:
        if self._month == 12:
            self._year += 1
            self._month = 1
        else:
            self._month += 1
        self._on_month_changed()

    def go_today(self) -> None:
        today = date.today()
        self._year, self._month = today.year, today.month
        self._on_month_changed()

    def _on_month_changed(self) -> None:
        self.refresh()
        self.month_changed.emit(self._year, self._month)

    def refresh(self) -> None:
        """Re-read data from the stores and repaint the grid for the current month."""
        self._month_button.setText(f"{self._year}. {MONTH_LABELS_HU[self._month - 1]}")

        first_weekday, days_in_month = calendar_module.monthrange(self._year, self._month)
        today = date.today()

        cell_index = 0
        leading_blanks = first_weekday  # Monday = 0, matches our Monday-first grid.
        current = date(self._year, self._month, 1)

        for _ in range(leading_blanks):
            prev_day = _shift_days(current, -(leading_blanks - cell_index))
            self._paint_cell(cell_index, prev_day, today, in_current_month=False)
            cell_index += 1

        for day_num in range(1, days_in_month + 1):
            d = date(self._year, self._month, day_num)
            self._paint_cell(cell_index, d, today, in_current_month=True)
            cell_index += 1

        trailing = date(self._year, self._month, days_in_month)
        offset = 1
        while cell_index < len(self._cells):
            next_day = _shift_days(trailing, offset)
            self._paint_cell(cell_index, next_day, today, in_current_month=False)
            cell_index += 1
            offset += 1

    def _paint_cell(self, index: int, day: date, today: date, in_current_month: bool) -> None:
        if self._palette is None:
            return
        record = self._calendar_store.get(day)
        self._cells[index].set_data(
            day=day,
            record=record,
            is_today=(day == today),
            in_current_month=in_current_month,
            palette=self._palette,
        )


def _shift_days(d: date, offset: int) -> date:
    from datetime import timedelta

    return d + timedelta(days=offset)


class DayStatusDialog(QDialog):
    """Popup for editing a single day's status (full-day or half-day split)."""

    def __init__(self, day: date, record: DayRecord, parent: QWidget | None = None):
        super().__init__(parent)
        self._day = day
        self.result_record: DayRecord | None = None
        self.setWindowTitle(f"Napi státusz — {day.isoformat()}")

        layout = QVBoxLayout(self)

        info_label = QLabel(_format_day_title(day))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        self._full_day_group = QGroupBox("Egész napos státusz")
        full_layout = QGridLayout(self._full_day_group)
        self._full_buttons: dict[DayStatus, QPushButton] = {}
        for i, status in enumerate(_STATUS_ORDER):
            btn = QPushButton(status.label_hu)
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _checked, s=status: self._apply_full_day(s))
            full_layout.addWidget(btn, i // 2, i % 2)
            self._full_buttons[status] = btn
        layout.addWidget(self._full_day_group)

        self._half_day_group = QGroupBox("Félnapos bontás")
        half_layout = QHBoxLayout(self._half_day_group)
        am_col = QVBoxLayout()
        am_col.addWidget(QLabel("Délelőtt"))
        self._am_combo = _build_status_combo(record.am)
        am_col.addWidget(self._am_combo)
        pm_col = QVBoxLayout()
        pm_col.addWidget(QLabel("Délután"))
        self._pm_combo = _build_status_combo(record.pm)
        pm_col.addWidget(self._pm_combo)
        half_layout.addLayout(am_col)
        half_layout.addLayout(pm_col)
        layout.addWidget(self._half_day_group)

        apply_half_button = QPushButton("Félnapos bontás alkalmazása")
        apply_half_button.clicked.connect(self._apply_half_day)
        layout.addWidget(apply_half_button)

        clear_button = QPushButton("Törlés / nincs rögzítve")
        clear_button.setObjectName("dangerButton")
        clear_button.clicked.connect(self._clear)
        layout.addWidget(clear_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_full_day(self, status: DayStatus) -> None:
        self.result_record = DayRecord(am=status, pm=status)
        self.accept()

    def _apply_half_day(self) -> None:
        am = _combo_to_status(self._am_combo)
        pm = _combo_to_status(self._pm_combo)
        self.result_record = DayRecord(am=am, pm=pm)
        self.accept()

    def _clear(self) -> None:
        self.result_record = DayRecord(am=None, pm=None)
        self.accept()


def _build_status_combo(current: DayStatus | None) -> QComboBox:
    combo = QComboBox()
    combo.addItem(_NO_STATUS_LABEL, None)
    for status in _STATUS_ORDER:
        combo.addItem(status.label_hu, status.value)
    if current is not None:
        idx = combo.findData(current.value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
    return combo


def _combo_to_status(combo: QComboBox) -> DayStatus | None:
    value = combo.currentData()
    return DayStatus.from_value(value)


def _format_day_title(day: date) -> str:
    weekday_names = [
        "Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap",
    ]
    return f"{day.year}. {MONTH_LABELS_HU[day.month - 1]} {day.day}. ({weekday_names[day.weekday()]})"
