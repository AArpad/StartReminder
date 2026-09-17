"""Right-hand panel: a narrow list of messages (date + seen checkmark), with a
markdown preview panel to its right and edit/delete actions below."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..storage import MessageStore

_DATE_ROLE = Qt.ItemDataRole.UserRole
_LIST_WIDTH = 130


class MessageListPanel(QWidget):
    """Lists messages (current month or all), previews and edits/deletes them."""

    edit_requested = Signal(date)
    message_deleted = Signal(date)

    def __init__(self, message_store: MessageStore, parent: QWidget | None = None):
        super().__init__(parent)
        self._message_store = message_store
        self._year = date.today().year
        self._month = date.today().month
        self._show_all = False

        outer_layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("Üzenetek"))
        header.addStretch(1)
        self._scope_button = QPushButton("Összes üzenet")
        self._scope_button.setCheckable(True)
        self._scope_button.clicked.connect(self._toggle_scope)
        header.addWidget(self._scope_button)
        outer_layout.addLayout(header)

        content_row = QHBoxLayout()
        self._list = QListWidget()
        self._list.setFixedWidth(_LIST_WIDTH)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        self._list.itemChanged.connect(self._on_item_changed)
        content_row.addWidget(self._list)

        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)
        content_row.addWidget(self._preview, 1)
        outer_layout.addLayout(content_row, 1)

        action_row = QHBoxLayout()
        self._edit_button = QPushButton("Szerkesztés")
        self._edit_button.clicked.connect(self._edit_selected)
        self._delete_button = QPushButton("Törlés")
        self._delete_button.setObjectName("dangerButton")
        self._delete_button.clicked.connect(self._delete_selected)
        action_row.addWidget(self._edit_button)
        action_row.addWidget(self._delete_button)
        outer_layout.addLayout(action_row)

        self._update_action_state()

    def set_month(self, year: int, month: int) -> None:
        self._year = year
        self._month = month
        self.refresh()

    def _toggle_scope(self, checked: bool) -> None:
        self._show_all = checked
        self._scope_button.setText("Csak ez a hónap" if checked else "Összes üzenet")
        self.refresh()

    def refresh(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for key in sorted(self._message_store.messages.keys()):
            try:
                d = date.fromisoformat(key)
            except ValueError:
                continue
            if not self._show_all and not (d.year == self._year and d.month == self._month):
                continue
            message = self._message_store.get(d)
            if message is None:
                continue
            item = QListWidgetItem(d.isoformat())
            item.setData(_DATE_ROLE, d)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if message.seen else Qt.CheckState.Unchecked)
            self._list.addItem(item)
        self._list.blockSignals(False)
        self._preview.clear()
        self._update_action_state()

    def _current_date(self) -> date | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.data(_DATE_ROLE)

    def _on_selection_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if current is None:
            self._preview.clear()
            self._update_action_state()
            return
        d: date = current.data(_DATE_ROLE)
        message = self._message_store.get(d)
        if message is not None:
            self._preview.setMarkdown(message.text)
        else:
            self._preview.clear()
        self._update_action_state()

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        d = item.data(_DATE_ROLE)
        if d is None:
            return
        seen = item.checkState() == Qt.CheckState.Checked
        self._message_store.set_seen(d, seen)

    def _update_action_state(self) -> None:
        has_selection = self._current_date() is not None
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _edit_selected(self) -> None:
        d = self._current_date()
        if d is not None:
            self.edit_requested.emit(d)

    def _delete_selected(self) -> None:
        d = self._current_date()
        if d is None:
            return
        answer = QMessageBox.question(
            self,
            "Üzenet törlése",
            f"Biztosan törlöd a(z) {d.isoformat()} napi üzenetet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._message_store.delete(d)
            self.message_deleted.emit(d)
            self.refresh()
