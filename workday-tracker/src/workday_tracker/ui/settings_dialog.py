"""Settings dialog: autostart and appearance (theme mode + color scheme)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..settings import COLOR_SCHEMES, MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, SettingsStore
from ..theming.palettes import COLOR_SCHEME_LABELS_HU
from ..theming.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Lets the user configure autostart and appearance."""

    def __init__(
        self,
        settings_store: SettingsStore,
        theme_manager: ThemeManager,
        data_dir: Path,
        used_fallback_dir: bool,
        main_window: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._settings_store = settings_store
        self._theme_manager = theme_manager
        self._main_window = main_window
        self.setWindowTitle("Beállítások")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        startup_group = QGroupBox("Indítás")
        startup_layout = QVBoxLayout(startup_group)
        self._autostart_checkbox = QCheckBox("Induljon automatikusan a Windowsszal")
        self._autostart_checkbox.setChecked(settings_store.settings.autostart)
        self._autostart_checkbox.toggled.connect(self._on_autostart_toggled)
        startup_layout.addWidget(self._autostart_checkbox)
        layout.addWidget(startup_group)

        data_group = QGroupBox("Adatok helye")
        data_layout = QVBoxLayout(data_group)
        path_label = QLabel(str(data_dir))
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(
            path_label.textInteractionFlags() | path_label.textInteractionFlags().TextSelectableByMouse
        )
        data_layout.addWidget(path_label)
        if used_fallback_dir:
            fallback_notice = QLabel(
                "Az alkalmazás könyvtára nem írható, ezért az adatok a fenti "
                "tartalék helyre kerülnek mentésre."
            )
            fallback_notice.setWordWrap(True)
            fallback_notice.setProperty("muted", True)
            data_layout.addWidget(fallback_notice)
        layout.addWidget(data_group)

        appearance_group = QGroupBox("Megjelenés")
        appearance_layout = QVBoxLayout(appearance_group)

        appearance_layout.addWidget(QLabel("Téma mód:"))
        self._theme_dark = QRadioButton("Sötét")
        self._theme_light = QRadioButton("Világos")
        self._theme_system = QRadioButton("Rendszertől veszi át")
        current_mode = settings_store.settings.theme_mode
        self._theme_dark.setChecked(current_mode == "dark")
        self._theme_light.setChecked(current_mode == "light")
        self._theme_system.setChecked(current_mode == "system")
        for radio, mode in (
            (self._theme_dark, "dark"),
            (self._theme_light, "light"),
            (self._theme_system, "system"),
        ):
            radio.toggled.connect(
                lambda checked, m=mode: checked and self._on_theme_mode_changed(m)
            )
            appearance_layout.addWidget(radio)

        appearance_layout.addWidget(QLabel("Színvilág:"))
        self._color_scheme_combo = QComboBox()
        for scheme in COLOR_SCHEMES:
            self._color_scheme_combo.addItem(COLOR_SCHEME_LABELS_HU[scheme], scheme)
        current_scheme = settings_store.settings.color_scheme
        idx = self._color_scheme_combo.findData(current_scheme)
        if idx >= 0:
            self._color_scheme_combo.setCurrentIndex(idx)
        self._color_scheme_combo.currentIndexChanged.connect(self._on_color_scheme_changed)
        appearance_layout.addWidget(self._color_scheme_combo)

        layout.addWidget(appearance_group)

        window_group = QGroupBox("Ablakméret")
        window_layout = QHBoxLayout(window_group)
        window_layout.addWidget(QLabel("Szélesség:"))
        self._width_spin = QSpinBox()
        self._width_spin.setRange(MIN_WINDOW_WIDTH, 7680)
        self._width_spin.setValue(settings_store.settings.window_width)
        self._width_spin.valueChanged.connect(self._on_window_size_changed)
        window_layout.addWidget(self._width_spin)
        window_layout.addWidget(QLabel("Magasság:"))
        self._height_spin = QSpinBox()
        self._height_spin.setRange(MIN_WINDOW_HEIGHT, 4320)
        self._height_spin.setValue(settings_store.settings.window_height)
        self._height_spin.valueChanged.connect(self._on_window_size_changed)
        window_layout.addWidget(self._height_spin)
        layout.addWidget(window_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Bezárás")
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _on_autostart_toggled(self, checked: bool) -> None:
        try:
            self._settings_store.set_autostart(checked)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(self, "Hiba", str(exc))
            self._autostart_checkbox.blockSignals(True)
            self._autostart_checkbox.setChecked(self._settings_store.settings.autostart)
            self._autostart_checkbox.blockSignals(False)

    def _on_theme_mode_changed(self, mode: str) -> None:
        try:
            self._settings_store.set_theme_mode(mode)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(self, "Hiba", str(exc))
            return
        self._theme_manager.apply(mode, self._settings_store.settings.color_scheme)

    def _on_color_scheme_changed(self, _index: int) -> None:
        scheme = self._color_scheme_combo.currentData()
        try:
            self._settings_store.set_color_scheme(scheme)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            QMessageBox.critical(self, "Hiba", str(exc))
            return
        self._theme_manager.apply(self._settings_store.settings.theme_mode, scheme)

    def _on_window_size_changed(self, _value: int) -> None:
        width = self._width_spin.value()
        height = self._height_spin.value()
        if self._main_window is not None:
            self._main_window.apply_window_size(width, height)
        else:
            try:
                self._settings_store.set_window_size(width, height)
            except Exception as exc:  # noqa: BLE001 - surfaced to the user
                QMessageBox.critical(self, "Hiba", str(exc))
