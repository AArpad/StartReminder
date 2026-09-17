"""Main application window: calendar, monthly stats and the message list."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..settings import SettingsStore
from ..stats import compute_monthly_stats
from ..storage import CalendarStore, MessageStore, StorageError
from ..theming.theme_manager import ThemeManager
from .calendar_widget import CalendarWidget, DayStatusDialog
from .message_editor import MessageEditorDialog
from .message_list import MessageListPanel
from .settings_dialog import SettingsDialog
from .stats_panel import StatsPanel

logger = logging.getLogger("workday_tracker")


class MainWindow(QMainWindow):
    """The application's main window, shown after the startup dialog closes."""

    def __init__(
        self,
        calendar_store: CalendarStore,
        message_store: MessageStore,
        settings_store: SettingsStore,
        theme_manager: ThemeManager,
        data_dir: Path,
        used_fallback_dir: bool,
    ):
        super().__init__()
        self._calendar_store = calendar_store
        self._message_store = message_store
        self._settings_store = settings_store
        self._theme_manager = theme_manager
        self._data_dir = data_dir
        self._used_fallback_dir = used_fallback_dir

        self.setWindowTitle("WorkDay Tracker")
        self.resize(settings_store.settings.window_width, settings_store.settings.window_height)

        self._resize_save_timer = QTimer(self)
        self._resize_save_timer.setSingleShot(True)
        self._resize_save_timer.setInterval(500)
        self._resize_save_timer.timeout.connect(self._persist_window_size)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        splitter = QSplitter()

        left_panel = QWidget()
        left_layout = QHBoxLayout(left_panel)
        self._calendar_widget = CalendarWidget(calendar_store)
        self._calendar_widget.day_activated.connect(self._on_day_activated)
        self._calendar_widget.month_changed.connect(self._on_month_changed)
        left_layout.addWidget(self._calendar_widget, 0, Qt.AlignmentFlag.AlignTop)

        # Line the stats box up with the day grid (the cells), not with the
        # nav bar (the paging buttons) above it.
        stats_wrapper = QWidget()
        stats_wrapper_layout = QVBoxLayout(stats_wrapper)
        stats_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        stats_wrapper_layout.addSpacing(self._calendar_widget.grid_top_offset())
        self._stats_panel = StatsPanel()
        stats_wrapper_layout.addWidget(self._stats_panel)
        stats_wrapper_layout.addStretch(1)
        left_layout.addWidget(stats_wrapper, 0, Qt.AlignmentFlag.AlignTop)

        left_layout.addStretch(1)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self._message_list = MessageListPanel(message_store)
        self._message_list.edit_requested.connect(self._open_message_editor_for)
        self._message_list.message_deleted.connect(lambda _d: self._calendar_widget.refresh())
        right_layout.addWidget(self._message_list, 1)

        button_row = QHBoxLayout()
        new_message_button = QPushButton("Új üzenet")
        new_message_button.setObjectName("accentButton")
        new_message_button.clicked.connect(self._open_new_message_editor)
        button_row.addWidget(new_message_button)
        settings_button = QPushButton("Beállítások")
        settings_button.clicked.connect(self._open_settings)
        button_row.addWidget(settings_button)
        right_layout.addLayout(button_row)

        splitter.addWidget(right_panel)
        splitter.setSizes([420, 340])
        root_layout.addWidget(splitter)

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._open_new_message_editor)

        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed()

        today = date.today()
        self._message_list.set_month(today.year, today.month)
        self._refresh_stats(today.year, today.month)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        self._resize_save_timer.start()

    def _persist_window_size(self) -> None:
        if self.isMaximized() or self.isFullScreen():
            return
        try:
            self._settings_store.set_window_size(self.width(), self.height())
        except StorageError as exc:
            logger.error("Failed to persist window size: %s", exc)

    def apply_window_size(self, width: int, height: int) -> None:
        """Resize the window (used when the size is changed from Settings)."""
        self.resize(width, height)

    def refresh_all(self) -> None:
        """Re-pull calendar/message data and recompute stats for the shown month."""
        self._calendar_widget.refresh()
        self._message_list.refresh()
        self._refresh_stats(self._calendar_widget.year, self._calendar_widget.month)

    def _on_theme_changed(self) -> None:
        self._calendar_widget.set_palette(self._theme_manager.palette)

    def _on_month_changed(self, year: int, month: int) -> None:
        self._message_list.set_month(year, month)
        self._refresh_stats(year, month)

    def _refresh_stats(self, year: int, month: int) -> None:
        stats = compute_monthly_stats(year, month, self._calendar_store.days)
        self._stats_panel.update_stats(stats)

    def _on_day_activated(self, day: date) -> None:
        record = self._calendar_store.get(day)
        dialog = DayStatusDialog(day, record, self)
        if dialog.exec() == DayStatusDialog.DialogCode.Accepted and dialog.result_record is not None:
            try:
                self._calendar_store.set(day, dialog.result_record)
            except StorageError as exc:
                QMessageBox.critical(self, "Hiba", str(exc))
                return
            self._calendar_widget.refresh()
            self._refresh_stats(self._calendar_widget.year, self._calendar_widget.month)

    def _open_new_message_editor(self) -> None:
        dialog = MessageEditorDialog(self._message_store, self)
        if dialog.exec() == MessageEditorDialog.DialogCode.Accepted:
            self._message_list.refresh()
            self._calendar_widget.refresh()

    def _open_message_editor_for(self, day: date) -> None:
        dialog = MessageEditorDialog(self._message_store, self, initial_date=day)
        if dialog.exec() == MessageEditorDialog.DialogCode.Accepted:
            self._message_list.refresh()
            self._calendar_widget.refresh()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            self._settings_store,
            self._theme_manager,
            self._data_dir,
            self._used_fallback_dir,
            main_window=self,
            parent=self,
        )
        dialog.exec()
