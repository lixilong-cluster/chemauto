from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QDoubleSpinBox, QPlainTextEdit, QMessageBox, QLabel
)

from chemauto.features.pes_exporter import PesExporter
from chemauto.infra.config import load_user_config
from chemauto.gui.widgets import DropPathLineEdit


class _PESWorker(QObject):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, fchk: str, out_dir: str, vde: float, fwhm: float, hv: float):
        super().__init__(); self.args = (fchk, out_dir, vde, fwhm, hv)

    @pyqtSlot()
    def run(self):
        fchk, out_dir, vde, fwhm, hv = self.args
        try:
            PesExporter().process_file(
                vde=vde, fchk_file_path=fchk, save_path=out_dir,
                PES_FWHM=fwhm, hv_energy=hv
            )
            stem = Path(fchk).stem
            self.finished.emit(
                f"Created:\n{Path(out_dir, stem + '_curve.txt')}\n"
                f"{Path(out_dir, stem + '_line.txt')}"
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class PESDialog(QDialog):
    def __init__(self, parent=None, initial_fchk: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Generate PES Data")
        self.resize(760, 470)
        self.setAcceptDrops(True)
        self._thread = None; self._worker = None
        self._history: list[tuple[str, str]] = []
        cfg = load_user_config()

        root = QVBoxLayout(self); form = QFormLayout()
        self.fchk = DropPathLineEdit(initial_fchk, suffixes={".fchk", ".fch"}, allow_directory=False)
        self.fchk.pathDropped.connect(self._set_fchk)
        form.addRow("fchk file:", self._path_row(self.fchk, self._pick_fchk, "Clear", self._clear_fchk))
        initial_out = str(Path(initial_fchk).parent) if initial_fchk else ""
        self.out_dir = QLineEdit(initial_out)
        form.addRow("Output folder:", self._path_row(self.out_dir, self._pick_folder, "Use fchk folder", self._use_fchk_folder))

        self.vde = QDoubleSpinBox(); self.vde.setRange(0, 1000); self.vde.setDecimals(6); self.vde.setValue(2.000000)
        self.fwhm = QDoubleSpinBox(); self.fwhm.setRange(0.0001, 10); self.fwhm.setDecimals(2); self.fwhm.setValue(float(cfg.get("PES_FWHM", 0.2)))
        self.hv = QDoubleSpinBox(); self.hv.setRange(0.0001, 1000); self.hv.setDecimals(3); self.hv.setValue(float(cfg.get("default_photon_energy", 3.493)))
        form.addRow("VDE (eV):", self.vde)
        form.addRow("FWHM (eV):", self.fwhm)
        form.addRow("Photon energy hν (eV):", self.hv)
        root.addLayout(form)

        preset = QHBoxLayout(); preset.addWidget(QLabel("Wavelength presets:"))
        for label, value in (("355 nm", 3.493), ("532 nm", 2.331), ("1064 nm", 1.165), ("1500 nm", 0.827)):
            b = QPushButton(label); b.clicked.connect(lambda checked=False, v=value: self.hv.setValue(v)); preset.addWidget(b)
        preset.addStretch(1); root.addLayout(preset)

        info = QLabel(
            "Drop an .fchk/.fch file anywhere in this window. Output defaults to the fchk directory. "
            "The original normalization logic is retained: the curve maximum between 0 and hν is scaled to PES_scale. "
            "Ctrl+Z restores the previous file/output selection."
        )
        info.setWordWrap(True); root.addWidget(info)
        root.addWidget(QLabel("Output naming is fixed as <name>_curve.txt and <name>_line.txt for strict DOS pairing."))
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); root.addWidget(self.log, 1)

        row = QHBoxLayout(); self.run_btn = QPushButton("Generate PES Data"); close = QPushButton("Close")
        self.run_btn.clicked.connect(self.run_job); close.clicked.connect(self.close)
        row.addStretch(1); row.addWidget(self.run_btn); row.addWidget(close); root.addLayout(row)
        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self); self._undo_shortcut.activated.connect(self._undo)

    def _path_row(self, edit, callback, second_text=None, second_callback=None):
        w = QHBoxLayout(); b = QPushButton("Browse…"); b.clicked.connect(callback); w.addWidget(edit, 1); w.addWidget(b)
        if second_text and second_callback:
            b2 = QPushButton(second_text); b2.clicked.connect(second_callback); w.addWidget(b2)
        return w

    def _remember(self):
        state = (self.fchk.text(), self.out_dir.text())
        if not self._history or self._history[-1] != state: self._history.append(state)
        if len(self._history) > 20: self._history.pop(0)

    def _undo(self):
        if not self._history: return
        fchk, out = self._history.pop(); self.fchk.setText(fchk); self.out_dir.setText(out)

    def _set_fchk(self, path: str):
        self._remember(); self.fchk.setText(path); self.out_dir.setText(str(Path(path).parent))

    def _pick_fchk(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select fchk", self.fchk.text(), "Formatted checkpoint (*.fchk *.fch)")
        if p: self._set_fchk(p)

    def _pick_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Select output folder", self.out_dir.text())
        if p: self._remember(); self.out_dir.setText(p)

    def _use_fchk_folder(self):
        p = Path(self.fchk.text().strip())
        if p.is_file(): self._remember(); self.out_dir.setText(str(p.parent))

    def _clear_fchk(self):
        self._remember(); self.fchk.clear(); self.out_dir.clear()

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if any(Path(u.toLocalFile()).suffix.lower() in {'.fchk', '.fch'} for u in urls): event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in {'.fchk', '.fch'} and p.is_file():
                self._set_fchk(str(p)); event.acceptProposedAction(); return

    def run_job(self):
        fchk = Path(self.fchk.text().strip()); out_text = self.out_dir.text().strip()
        if not fchk.is_file(): QMessageBox.warning(self, "PES", "Select a valid fchk file."); return
        out = Path(out_text) if out_text else fchk.parent
        out.mkdir(parents=True, exist_ok=True); self.out_dir.setText(str(out))
        self.run_btn.setEnabled(False); self.log.setPlainText("Generating PES data…")
        self._thread = QThread(self); self._worker = _PESWorker(str(fchk), str(out), self.vde.value(), self.fwhm.value(), self.hv.value())
        self._worker.moveToThread(self._thread); self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._done); self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._thread.quit); self._worker.failed.connect(self._thread.quit); self._thread.start()

    def _done(self, msg):
        self.log.setPlainText(msg); self.run_btn.setEnabled(True)
        answer = QMessageBox.question(
            self, "PES data created",
            msg + "\n\nOpen the DOS plotting window now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes and self.parent() is not None and hasattr(self.parent(), "open_dos_dialog"):
            self.parent().open_dos_dialog(self.out_dir.text().strip())

    def _failed(self, msg):
        self.log.setPlainText("ERROR: " + msg); self.run_btn.setEnabled(True)
