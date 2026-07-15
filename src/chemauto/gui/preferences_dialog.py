from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QDialogButtonBox, QSpinBox, QLabel, QMessageBox, QTabWidget,
    QWidget, QDoubleSpinBox, QCheckBox, QGroupBox
)

from chemauto.infra.config import load_user_config, save_user_config
from chemauto.core.external_open import WINDOWS_NOTEPAD, SYSTEM_DEFAULT, windows_notepad_path, detect_gaussview


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ChemAuto Preferences")
        self.resize(760, 590)
        self.cfg = load_user_config()

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_spectra_tab(), "PES / DOS")
        tabs.addTab(self._build_apps_tab(), "Applications")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _path_row(self, edit: QLineEdit, picker, clear=True):
        row = QHBoxLayout()
        browse = QPushButton("Browse…")
        browse.clicked.connect(picker)
        row.addWidget(edit, 1)
        row.addWidget(browse)
        if clear:
            btn_clear = QPushButton("Clear")
            btn_clear.clicked.connect(edit.clear)
            row.addWidget(btn_clear)
        return row

    def _build_general_tab(self):
        w = QWidget(); root = QVBoxLayout(w); form = QFormLayout()
        self.template_edit = QLineEdit(str(self.cfg.get("gjf_template_path", "")))
        form.addRow("Default .gjf template:", self._path_row(self.template_edit, self._browse_template))

        self.workers = QSpinBox(); self.workers.setRange(1, 16)
        self.workers.setValue(int(self.cfg.get("log_parse_workers", 4)))
        self.workers.setToolTip("Number of Gaussian log files parsed concurrently. 4 is a safe default.")
        form.addRow("Log parser workers:", self.workers)
        root.addLayout(form)

        note = QLabel(
            "The .gjf template keeps its Link0, route, title and tail sections. "
            "ChemAuto replaces the first molecule block with the selected optimized coordinates "
            "and updates %chk to the output file name."
        )
        note.setWordWrap(True); root.addWidget(note); root.addStretch(1)
        return w

    @staticmethod
    def _spin(value: float, minimum=-1000.0, maximum=1000.0, decimals=6):
        s = QDoubleSpinBox(); s.setRange(minimum, maximum); s.setDecimals(decimals); s.setValue(float(value))
        return s

    def _build_spectra_tab(self):
        w = QWidget(); root = QVBoxLayout(w)

        pes_box = QGroupBox("PES data generation")
        pes_form = QFormLayout(pes_box)
        self.pes_fwhm = self._spin(self.cfg.get("PES_FWHM", 0.2), 0.000001, 20, 2)
        self.pes_hv = self._spin(self.cfg.get("default_photon_energy", 3.493), 0.000001, 1000, 3)
        self.pes_xlow = self._spin(self.cfg.get("PES_Xlow", 0.0))
        self.pes_xhigh = self._spin(self.cfg.get("PES_Xhigh", 5.0))
        self.pes_scale = self._spin(self.cfg.get("PES_scale", 5.0), 0.000001, 100000)
        self.pes_strength = self._spin(self.cfg.get("PES_str", 1.0), 0.000001, 100000)
        self.pes_npoints = QSpinBox(); self.pes_npoints.setRange(100, 1000000); self.pes_npoints.setValue(int(self.cfg.get("npoints", 5000)))
        pes_form.addRow("Default FWHM (eV):", self.pes_fwhm)
        pes_form.addRow("Default photon energy hν (eV):", self.pes_hv)
        pes_form.addRow("Energy grid minimum (eV):", self.pes_xlow)
        pes_form.addRow("Energy grid maximum (eV):", self.pes_xhigh)
        pes_form.addRow("Curve normalization maximum:", self.pes_scale)
        pes_form.addRow("Gaussian integrated strength:", self.pes_strength)
        pes_form.addRow("Grid points:", self.pes_npoints)
        root.addWidget(pes_box)

        dos_box = QGroupBox("Origin DOS plotting")
        dos_form = QFormLayout(dos_box)
        xr = self.cfg.get("default_x_range", [0, 3.3]); yr = self.cfg.get("default_y_range", [-0.03, 6.5])
        self.dos_xmin = self._spin(xr[0]); self.dos_xmax = self._spin(xr[1])
        self.dos_ymin = self._spin(yr[0]); self.dos_ymax = self._spin(yr[1])
        xrow = QHBoxLayout(); xrow.addWidget(self.dos_xmin); xrow.addWidget(QLabel("to")); xrow.addWidget(self.dos_xmax)
        yrow = QHBoxLayout(); yrow.addWidget(self.dos_ymin); yrow.addWidget(QLabel("to")); yrow.addWidget(self.dos_ymax)
        dos_form.addRow("Default X range:", xrow); dos_form.addRow("Default Y range:", yrow)
        self.show_origin = QCheckBox("Show Origin while plotting")
        self.show_origin.setChecked(bool(self.cfg.get("show_graph", False)))
        dos_form.addRow("Origin window:", self.show_origin)
        self.dos_template = QLineEdit(str(self.cfg.get("dos_template_path", "")))
        self.dos_template.setPlaceholderText("Blank = bundled DOS-default.otpu")
        dos_form.addRow("Custom Origin template:", self._path_row(self.dos_template, self._browse_dos_template))
        root.addWidget(dos_box); root.addStretch(1)
        return w

    def _app_row(self, edit: QLineEdit, *, notepad=False, gaussview=False):
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(lambda: self._browse_exe(edit))
        row.addWidget(browse)
        system = QPushButton("System default")
        system.clicked.connect(lambda: edit.setText(SYSTEM_DEFAULT))
        row.addWidget(system)
        if notepad:
            btn = QPushButton("Windows Notepad")
            btn.clicked.connect(lambda: edit.setText(WINDOWS_NOTEPAD))
            row.addWidget(btn)
        if gaussview:
            btn = QPushButton("Find GaussView")
            btn.clicked.connect(lambda: self._set_detected_gaussview(edit))
            row.addWidget(btn)
        return row

    def _build_apps_tab(self):
        w = QWidget(); root = QVBoxLayout(w); form = QFormLayout()
        self.text_editor = QLineEdit(str(self.cfg.get("text_editor_path", WINDOWS_NOTEPAD) or WINDOWS_NOTEPAD))
        self.log_viewer = QLineEdit(str(self.cfg.get("log_viewer_path", SYSTEM_DEFAULT) or SYSTEM_DEFAULT))
        self.fchk_viewer = QLineEdit(str(self.cfg.get("fchk_viewer_path", SYSTEM_DEFAULT) or SYSTEM_DEFAULT))
        self.xyz_viewer = QLineEdit(str(self.cfg.get("xyz_viewer_path", SYSTEM_DEFAULT) or SYSTEM_DEFAULT))
        form.addRow("Default application for opening TXT/.gjf:", self._app_row(self.text_editor, notepad=True))
        form.addRow("Default application for opening .log/.out:", self._app_row(self.log_viewer, notepad=True))
        form.addRow("Default application for opening .fchk/.fch:", self._app_row(self.fchk_viewer, gaussview=True))
        form.addRow("Default application for opening .xyz:", self._app_row(self.xyz_viewer, gaussview=True))
        root.addLayout(form)
        note = QLabel(
            "ChemAuto uses Windows Notepad for TXT/.gjf by default, so users do not need to locate notepad.exe. "
            "Choose System default to use the current Windows file association, Browse for a custom program, "
            "or Find GaussView for formatted checkpoint/XYZ files. Binary .chk files are never opened directly."
        )
        note.setWordWrap(True); root.addWidget(note); root.addStretch(1)
        return w

    def _set_detected_gaussview(self, edit: QLineEdit):
        path = detect_gaussview()
        if path:
            edit.setText(path)
        else:
            QMessageBox.information(self, "Applications", "GaussView was not found automatically. Use Browse to select it, or keep System default.")

    def _browse_template(self):
        current = self.template_edit.text().strip(); start = str(Path(current).parent) if current else ""
        path, _ = QFileDialog.getOpenFileName(self, "Select Gaussian input template", start, "Gaussian input (*.gjf *.com);;All files (*)")
        if path: self.template_edit.setText(path)

    def _browse_dos_template(self):
        current = self.dos_template.text().strip(); start = str(Path(current).parent) if current else ""
        path, _ = QFileDialog.getOpenFileName(self, "Select Origin graph template", start, "Origin template (*.otpu *.otp);;All files (*)")
        if path: self.dos_template.setText(path)

    def _browse_exe(self, edit: QLineEdit):
        current = edit.text().strip(); start = str(Path(current).parent) if current else ""
        path, _ = QFileDialog.getOpenFileName(self, "Select application", start, "Programs (*.exe);;All files (*)")
        if path: edit.setText(path)

    def _save(self):
        template = self.template_edit.text().strip().strip('"')
        custom_dos_template = self.dos_template.text().strip().strip('"')
        if template and not Path(template).is_file():
            QMessageBox.warning(self, "Preferences", "The selected gjf template does not exist."); return
        if custom_dos_template and not Path(custom_dos_template).is_file():
            QMessageBox.warning(self, "Preferences", "The selected Origin template does not exist."); return
        if self.pes_xlow.value() >= self.pes_xhigh.value():
            QMessageBox.warning(self, "Preferences", "PES energy-grid minimum must be smaller than maximum."); return
        if self.dos_xmin.value() >= self.dos_xmax.value() or self.dos_ymin.value() >= self.dos_ymax.value():
            QMessageBox.warning(self, "Preferences", "DOS axis minima must be smaller than maxima."); return
        for edit in (self.text_editor, self.log_viewer, self.fchk_viewer, self.xyz_viewer):
            value = edit.text().strip().strip('"')
            if value and value not in {WINDOWS_NOTEPAD, SYSTEM_DEFAULT} and not Path(value).is_file():
                QMessageBox.warning(self, "Preferences", f"Application does not exist:\n{value}"); return

        cfg = load_user_config()
        cfg.update({
            "gjf_template_path": template,
            "log_parse_workers": int(self.workers.value()),
            "PES_FWHM": float(self.pes_fwhm.value()),
            "default_photon_energy": float(self.pes_hv.value()),
            "PES_Xlow": float(self.pes_xlow.value()),
            "PES_Xhigh": float(self.pes_xhigh.value()),
            "PES_scale": float(self.pes_scale.value()),
            "PES_str": float(self.pes_strength.value()),
            "npoints": int(self.pes_npoints.value()),
            "default_x_range": [float(self.dos_xmin.value()), float(self.dos_xmax.value())],
            "default_y_range": [float(self.dos_ymin.value()), float(self.dos_ymax.value())],
            "show_graph": bool(self.show_origin.isChecked()),
            "dos_template_path": custom_dos_template,
            "text_editor_path": self.text_editor.text().strip().strip('"'),
            "log_viewer_path": self.log_viewer.text().strip().strip('"'),
            "fchk_viewer_path": self.fchk_viewer.text().strip().strip('"'),
            "xyz_viewer_path": self.xyz_viewer.text().strip().strip('"'),
        })
        save_user_config(cfg)
        self.accept()
