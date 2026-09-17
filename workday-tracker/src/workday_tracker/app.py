"""Application bootstrap: single-instance guard, startup flow, main window."""

from __future__ import annotations

import logging
import sys
from datetime import date

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from .models import DayRecord
from .settings import SettingsStore
from .stats import is_weekend
from .storage import CalendarStore, MessageStore, resolve_data_dir, setup_logging
from .theming.theme_manager import ThemeManager
from .ui.main_window import MainWindow
from .ui.startup_dialog import StartupDialog

logger = logging.getLogger("workday_tracker")

_IPC_SERVER_NAME = "WorkDayTrackerIPC"
_SHARED_MEMORY_KEY = "WorkDayTrackerSingleInstance"


class SingleInstanceGuard(QObject):
    """Ensures only one instance runs; forwards a 'show' request to the primary one."""

    show_requested = Signal()

    def __init__(self):
        super().__init__()
        from PySide6.QtCore import QSharedMemory

        self._shared_memory = QSharedMemory(_SHARED_MEMORY_KEY)
        self.is_primary = self._shared_memory.create(1)
        self._server: QLocalServer | None = None

    def notify_existing_instance(self) -> None:
        socket = QLocalSocket()
        socket.connectToServer(_IPC_SERVER_NAME)
        if socket.waitForConnected(300):
            socket.write(b"show")
            socket.flush()
            socket.waitForBytesWritten(300)
            socket.disconnectFromServer()

    def start_server(self) -> None:
        QLocalServer.removeServer(_IPC_SERVER_NAME)
        self._server = QLocalServer()
        self._server.newConnection.connect(self._on_new_connection)
        if not self._server.listen(_IPC_SERVER_NAME):
            logger.error("Failed to start single-instance IPC server: %s", self._server.errorString())

    def _on_new_connection(self) -> None:
        socket = self._server.nextPendingConnection() if self._server else None
        if socket is not None:
            socket.readyRead.connect(lambda: self.show_requested.emit())


def run() -> int:
    """Application entry point. Returns the process exit code."""
    data_dir, used_fallback_dir = resolve_data_dir()
    setup_logging(data_dir)

    app = QApplication(sys.argv)
    app.setApplicationName("WorkDay Tracker")
    app.setQuitOnLastWindowClosed(True)

    guard = SingleInstanceGuard()
    if not guard.is_primary:
        guard.notify_existing_instance()
        return 0

    try:
        calendar_store = CalendarStore(data_dir)
        message_store = MessageStore(data_dir)
        settings_store = SettingsStore(data_dir)
    except Exception as exc:  # noqa: BLE001 - must never crash on startup
        logger.exception("Failed to initialize storage")
        QMessageBox.critical(
            None,
            "Hiba",
            "Az alkalmazás adatai nem tölthetők be:\n"
            f"{exc}\n\nAz alkalmazás nem tud elindulni.",
        )
        return 1

    theme_manager = ThemeManager(app)
    theme_manager.apply(settings_store.settings.theme_mode, settings_store.settings.color_scheme)

    _warn_if_corrupt(calendar_store.was_corrupt, "naptár")
    _warn_if_corrupt(message_store.was_corrupt, "üzenetek")
    _warn_if_corrupt(settings_store.was_corrupt, "beállítások")

    main_window = MainWindow(
        calendar_store, message_store, settings_store, theme_manager, data_dir, used_fallback_dir
    )
    guard.show_requested.connect(lambda: _bring_to_front(main_window))

    _run_startup_flow(calendar_store, message_store, main_window)

    main_window.show()
    return app.exec()


def _bring_to_front(window) -> None:
    window.showNormal()
    window.raise_()
    window.activateWindow()


def _warn_if_corrupt(was_corrupt: bool, label: str) -> None:
    if was_corrupt:
        QMessageBox.warning(
            None,
            "Sérült adatfájl",
            f"A(z) {label} adatfájl sérült volt, ezért az alkalmazás egy "
            "biztonsági másolatot (.corrupt-... kiterjesztéssel) készített róla, "
            "és üres adatokkal indult el.",
        )


def compute_startup_decision(
    is_weekend_day: bool,
    existing_record: DayRecord,
    has_unseen_message: bool,
) -> tuple[bool, bool]:
    """Decide whether to ask about today's status and/or show the startup dialog.

    Two independent checks, both re-evaluated fresh on every launch:
      - the status question is shown whenever today is still undefined
        (and it is a weekday); shown means shown - defined means not shown,
        with no other exception.
      - the message is shown whenever it exists and is not yet marked seen;
        once seen, it is never shown again.
    """
    should_prompt_status = not is_weekend_day and existing_record.is_empty
    show_dialog = has_unseen_message or should_prompt_status
    return should_prompt_status, show_dialog


def _run_startup_flow(
    calendar_store: CalendarStore,
    message_store: MessageStore,
    main_window: MainWindow,
) -> None:
    today = date.today()
    existing_record = calendar_store.get(today)
    message = message_store.get(today)
    message_to_show = message if (message is not None and not message.seen) else None

    should_prompt_status, show_dialog = compute_startup_decision(
        is_weekend(today),
        existing_record,
        message_to_show is not None,
    )

    if not show_dialog:
        return

    dialog = StartupDialog(
        today=today,
        message=message_to_show,
        existing_record=existing_record,
        should_prompt_status=should_prompt_status,
        parent=main_window,
    )
    dialog.exec()

    if message_to_show is not None:
        try:
            message_store.set_seen(today, True)
            main_window.refresh_all()
        except Exception as exc:  # noqa: BLE001 - surfaced, non-fatal
            logger.error("Failed to mark today's message as seen: %s", exc)

    if dialog.result_record is not None:
        try:
            calendar_store.set(today, dialog.result_record)
            main_window.refresh_all()
        except Exception as exc:  # noqa: BLE001 - surfaced, non-fatal
            logger.error("Failed to save today's status: %s", exc)
            QMessageBox.critical(main_window, "Hiba", str(exc))
