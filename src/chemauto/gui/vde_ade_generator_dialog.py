from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QCheckBox, QPlainTextEdit, QMessageBox, QLabel
)

from chemauto.core.vde_ade_generator import generate_vde_ade_jobs, resolve_gjf
from chemauto.gui.widgets import DropPathLineEdit


class VDEADEGeneratorDialog(QDialog):
    def __init__(self, parent=None, initial_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Generate VDE / ADE Gaussian inputs")
        self.resize(820, 520); self.setAcceptDrops(True)
        self._history: list[tuple[str, str]] = []
        root = QVBoxLayout(self); form = QFormLayout()

        self.input_edit = DropPathLineEdit(initial_path, suffixes={".gjf", ".com", ".log", ".out"}, allow_directory=True)
        self.input_edit.pathDropped.connect(self._set_input)
        input_row = QHBoxLayout(); input_row.addWidget(self.input_edit, 1)
        browse = QPushButton("Browse…"); browse.clicked.connect(self._browse_input); input_row.addWidget(browse)
        clear = QPushButton("Clear"); clear.clicked.connect(self._clear_input); input_row.addWidget(clear)
        form.addRow("Source directory / .gjf / .log:", input_row)

        self.output_edit = QLineEdit("")
        out_row = QHBoxLayout(); out_row.addWidget(self.output_edit, 1)
        out_browse = QPushButton("Browse…"); out_browse.clicked.connect(self._browse_output); out_row.addWidget(out_browse)
        auto = QPushButton("Use verified default"); auto.clicked.connect(self._set_default_output); out_row.addWidget(auto)
        form.addRow("Output root:", out_row)
        root.addLayout(form)

        modes = QHBoxLayout(); self.vde = QCheckBox("Generate two VDE jobs (N−1, N+1)"); self.ade = QCheckBox("Generate two ADE jobs (N−1, N+1)")
        self.vde.setChecked(True); self.ade.setChecked(True); modes.addWidget(self.vde); modes.addWidget(self.ade); modes.addStretch(1); root.addLayout(modes)
        note = QLabel(
            "The verified directory and naming logic is retained. By default, job folders are created beside the source calculation directory "
            "as <stem>-VDE-M<m> and <stem>-ADE-M<m>. If the original .chk exists, ChemAuto uses the verified %oldchk/ChkBasis workflow. "
            "If it is missing, ChemAuto extracts the optimized coordinates from the matching .log and preserves the primary .gjf method, basis and custom Gen/GenECP tail. "
            "Drop a directory, .gjf/.com, or .log/.out file here. Ctrl+Z restores the previous selection."
        ); note.setWordWrap(True); root.addWidget(note)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); root.addWidget(self.log, 1)
        buttons = QHBoxLayout(); run = QPushButton("Generate"); open_out = QPushButton("Open Output Root"); close = QPushButton("Close")
        run.clicked.connect(self.generate); open_out.clicked.connect(self._open_output); close.clicked.connect(self.close)
        buttons.addStretch(1); buttons.addWidget(run); buttons.addWidget(open_out); buttons.addWidget(close); root.addLayout(buttons)
        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self); self._undo_shortcut.activated.connect(self._undo)
        if initial_path: self._set_input(initial_path)

    def _remember(self):
        state = (self.input_edit.text(), self.output_edit.text())
        if not self._history or self._history[-1] != state: self._history.append(state)

    def _undo(self):
        if not self._history: return
        i, o = self._history.pop(); self.input_edit.setText(i); self.output_edit.setText(o)

    def _set_input(self, raw: str):
        self._remember(); self.input_edit.setText(raw)
        try:
            gjf = resolve_gjf(raw); self.output_edit.setText(str(gjf.parent.parent))
        except Exception:
            p = Path(raw); self.output_edit.setText(str(p.parent if p.is_file() else p.parent))

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .gjf/.log", self.input_edit.text(), "Gaussian files (*.gjf *.com *.log *.out);;All files (*)")
        if path: self._set_input(path); return
        folder = QFileDialog.getExistingDirectory(self, "Or select calculation directory", self.input_edit.text())
        if folder: self._set_input(folder)

    def _browse_output(self):
        p = QFileDialog.getExistingDirectory(self, "Select output root", self.output_edit.text())
        if p: self._remember(); self.output_edit.setText(p)

    def _set_default_output(self):
        try:
            self._remember(); gjf = resolve_gjf(self.input_edit.text().strip()); self.output_edit.setText(str(gjf.parent.parent))
        except Exception as exc: QMessageBox.warning(self, "VDE/ADE Inputs", str(exc))

    def _clear_input(self): self._remember(); self.input_edit.clear(); self.output_edit.clear()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls: self._set_input(urls[0].toLocalFile()); event.acceptProposedAction()

    def generate(self):
        modes = (["VDE"] if self.vde.isChecked() else []) + (["ADE"] if self.ade.isChecked() else [])
        if not modes: QMessageBox.warning(self, "VDE/ADE Inputs", "Select VDE and/or ADE."); return
        raw = self.input_edit.text().strip(); out = self.output_edit.text().strip() or None
        try:
            jobs = generate_vde_ade_jobs(raw, modes, output_root=out)
        except Exception as exc:
            QMessageBox.critical(self, "VDE/ADE Inputs", str(exc)); return
        self.log.setPlainText("\n".join(f"[{j.job_type} M{j.multiplicity}; {j.source_mode}] {j.gjf}" for j in jobs))
        if jobs: self.output_edit.setText(str(jobs[0].directory.parent))
        QMessageBox.information(self, "VDE/ADE Inputs", f"Generated {len(jobs)} job(s).")

    def _open_output(self):
        p = Path(self.output_edit.text().strip())
        if p.is_dir():
            import os; os.startfile(str(p))
