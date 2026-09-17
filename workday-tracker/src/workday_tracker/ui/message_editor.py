"""Message editor dialog: date picker, markdown source + live preview."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..storage import MessageStore

_PREVIEW_DELAY_MS = 300


class MessageEditorDialog(QDialog):
    """Create or edit the markdown message attached to a single day."""

    def __init__(
        self,
        message_store: MessageStore,
        parent: QWidget | None = None,
        initial_date: date | None = None,
    ):
        super().__init__(parent)
        self._message_store = message_store
        self.setWindowTitle("Üzenet szerkesztése")
        self.resize(760, 480)

        layout = QVBoxLayout(self)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Dátum:"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setMinimumWidth(130)
        self._date_edit.setMinimumHeight(28)
        default_date = initial_date or (date.today() + timedelta(days=1))
        self._date_edit.setDate(QDate(default_date.year, default_date.month, default_date.day))
        self._date_edit.dateChanged.connect(self._on_date_changed)
        date_row.addWidget(self._date_edit)
        date_row.addStretch(1)
        layout.addLayout(date_row)

        self._overwrite_warning = QLabel(
            "Erre a napra már van mentett üzenet — a mentés felülírja."
        )
        self._overwrite_warning.setObjectName("overwriteWarning")
        self._overwrite_warning.setStyleSheet("color: #d1445a;")
        self._overwrite_warning.setVisible(False)
        layout.addWidget(self._overwrite_warning)

        toolbar_row = QHBoxLayout()
        self._add_toolbar_button(toolbar_row, "B", "Félkövér", bold=True, action=lambda: self._wrap_selection("**", "**"))
        self._add_toolbar_button(toolbar_row, "I", "Dőlt", italic=True, action=lambda: self._wrap_selection("*", "*"))
        self._add_toolbar_button(toolbar_row, "H1", "Címsor", action=lambda: self._prefix_lines("# "))
        self._add_toolbar_button(toolbar_row, "• Lista", "Felsorolás", action=lambda: self._prefix_lines("- "))
        self._add_toolbar_button(toolbar_row, "1. Lista", "Számozott lista", action=lambda: self._prefix_lines("1. "))
        self._add_toolbar_button(toolbar_row, "Idézet", "Idézet", action=lambda: self._prefix_lines("> "))
        self._add_toolbar_button(toolbar_row, "Kód", "Kód", action=lambda: self._wrap_selection("`", "`"))
        self._add_toolbar_button(toolbar_row, "Link", "Hivatkozás", action=self._insert_link)
        toolbar_row.addStretch(1)
        layout.addLayout(toolbar_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._source_edit = QPlainTextEdit()
        mono_font = QFont("Consolas")
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        mono_font.setPointSize(11)
        self._source_edit.setFont(mono_font)
        self._source_edit.setPlaceholderText("Írd ide az üzenetet Markdown formátumban...")
        self._source_edit.textChanged.connect(self._schedule_preview_update)
        splitter.addWidget(self._source_edit)

        self._preview = QTextBrowser()
        splitter.addWidget(self._preview)
        splitter.setSizes([380, 380])
        layout.addWidget(splitter, 1)

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(_PREVIEW_DELAY_MS)
        self._preview_timer.timeout.connect(self._update_preview)

        button_row = QHBoxLayout()
        self._delete_button = QPushButton("Törlés")
        self._delete_button.setObjectName("dangerButton")
        self._delete_button.clicked.connect(self._delete)
        button_row.addWidget(self._delete_button)
        button_row.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("accentButton")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        button_row.addWidget(buttons)
        layout.addLayout(button_row)

        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._save)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.reject)

        self._load_for_current_date()

    def _add_toolbar_button(
        self,
        row: QHBoxLayout,
        text: str,
        tooltip: str,
        action,
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        if bold or italic:
            font = button.font()
            font.setBold(bold)
            font.setItalic(italic)
            button.setFont(font)
        button.clicked.connect(action)
        row.addWidget(button)

    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        cursor = self._source_edit.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            for _ in range(len(suffix)):
                cursor.movePosition(QTextCursor.MoveOperation.Left)
        self._source_edit.setTextCursor(cursor)
        self._source_edit.setFocus()

    def _prefix_lines(self, prefix: str) -> None:
        cursor = self._source_edit.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.beginEditBlock()
        while True:
            cursor.insertText(prefix)
            end += len(prefix)
            if cursor.position() >= end or not cursor.movePosition(
                QTextCursor.MoveOperation.NextBlock
            ):
                break
        cursor.endEditBlock()
        self._source_edit.setFocus()

    def _insert_link(self) -> None:
        cursor = self._source_edit.textCursor()
        selected = cursor.selectedText()
        link_text = selected if selected else "szöveg"
        cursor.insertText(f"[{link_text}](url)")
        self._source_edit.setTextCursor(cursor)
        self._source_edit.setFocus()

    def _current_date(self) -> date:
        qd = self._date_edit.date()
        return date(qd.year(), qd.month(), qd.day())

    def _on_date_changed(self, _qdate: QDate) -> None:
        self._load_for_current_date()

    def _load_for_current_date(self) -> None:
        d = self._current_date()
        existing = self._message_store.get(d)
        has_existing = existing is not None
        self._overwrite_warning.setVisible(has_existing)
        self._delete_button.setEnabled(has_existing)
        self._source_edit.blockSignals(True)
        self._source_edit.setPlainText(existing.text if existing else "")
        self._source_edit.blockSignals(False)
        self._update_preview()

    def _schedule_preview_update(self) -> None:
        self._preview_timer.start()

    def _update_preview(self) -> None:
        self._preview.setMarkdown(self._source_edit.toPlainText())

    def _save(self) -> None:
        d = self._current_date()
        text = self._source_edit.toPlainText()
        try:
            self._message_store.set(d, text)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(self, "Hiba", str(exc))
            return
        self.accept()

    def _delete(self) -> None:
        d = self._current_date()
        answer = QMessageBox.question(
            self,
            "Üzenet törlése",
            f"Biztosan törlöd a(z) {d.isoformat()} napi üzenetet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._message_store.delete(d)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(self, "Hiba", str(exc))
            return
        self.accept()
