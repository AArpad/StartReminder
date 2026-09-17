"""Daily startup dialog: shows today's message and asks for today's status."""

from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..models import DayRecord, DayStatus, Message

_STATUS_ORDER = [
    DayStatus.OFFICE,
    DayStatus.HOME_OFFICE,
    DayStatus.VACATION,
    DayStatus.SICK_LEAVE,
    DayStatus.PUBLIC_HOLIDAY,
]

_NO_STATUS_LABEL = "Nincs rögzítve"


class StartupDialog(QDialog):
    """Shown once per day on startup (subject to the rules in app.py).

    Only ever asked to display two things, either or both: today's message,
    and the status question (only when the day is not yet recorded).
    """

    def __init__(
        self,
        today: date,
        message: Message | None,
        existing_record: DayRecord,
        should_prompt_status: bool,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._today = today
        self.result_record: DayRecord | None = None

        self.setWindowTitle("WorkDay Tracker — napindító")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)

        if message is not None:
            title = QLabel(f"Üzenet a mai napra ({today.isoformat()})")
            title.setStyleSheet("font-weight: bold;")
            layout.addWidget(title)
            browser = QTextBrowser()
            browser.setMarkdown(message.text)
            browser.setMaximumHeight(200)
            layout.addWidget(browser)
            if should_prompt_status:
                separator = QFrame()
                separator.setObjectName("separatorLine")
                separator.setFrameShape(QFrame.Shape.HLine)
                layout.addWidget(separator)

        if should_prompt_status:
            question_label = QLabel("Mi volt / mi lesz a mai nap státusza?")
            question_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(question_label)

            button_grid = QGridLayout()
            for i, status in enumerate(_STATUS_ORDER):
                btn = QPushButton(status.label_hu)
                btn.setMinimumHeight(44)
                btn.clicked.connect(lambda _checked, s=status: self._choose_full_day(s))
                button_grid.addWidget(btn, i // 2, i % 2)
            layout.addLayout(button_grid)

            self._half_day_button = QPushButton("Félnap...")
            self._half_day_button.clicked.connect(self._toggle_half_day_panel)
            layout.addWidget(self._half_day_button)

            self._half_day_group = QGroupBox("Félnapos bontás")
            self._half_day_group.setVisible(False)
            half_layout = QHBoxLayout(self._half_day_group)
            am_col = QVBoxLayout()
            am_col.addWidget(QLabel("Délelőtt"))
            self._am_combo = _build_status_combo(existing_record.am)
            am_col.addWidget(self._am_combo)
            pm_col = QVBoxLayout()
            pm_col.addWidget(QLabel("Délután"))
            self._pm_combo = _build_status_combo(existing_record.pm)
            pm_col.addWidget(self._pm_combo)
            half_layout.addLayout(am_col)
            half_layout.addLayout(pm_col)
            layout.addWidget(self._half_day_group)

            apply_half_button = QPushButton("Félnapos bontás mentése")
            apply_half_button.clicked.connect(self._choose_half_day)
            layout.addWidget(apply_half_button)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self._continue_button = QPushButton("Tovább")
        self._continue_button.setObjectName("accentButton")
        self._continue_button.setDefault(True)
        self._continue_button.clicked.connect(self.accept)
        bottom_row.addWidget(self._continue_button)
        layout.addLayout(bottom_row)

    def _toggle_half_day_panel(self) -> None:
        self._half_day_group.setVisible(not self._half_day_group.isVisible())

    def _choose_full_day(self, status: DayStatus) -> None:
        self.result_record = DayRecord(am=status, pm=status)
        self.accept()

    def _choose_half_day(self) -> None:
        am = DayStatus.from_value(self._am_combo.currentData())
        pm = DayStatus.from_value(self._pm_combo.currentData())
        self.result_record = DayRecord(am=am, pm=pm)
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
