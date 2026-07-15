from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QPlainTextEdit, QMessageBox, QLabel
)

from chemauto.core.vde_ade import calculate_three_file_vde_ade
from chemauto.core.gaussian_parser import parse_gaussian_log
from chemauto.gui.widgets import DropPathLineEdit


class VDEADEDialog(QDialog):
    def __init__(self, parent=None, initial_files: list[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Calculate VDE / ADE (N−1 and N+1)")
        self.resize(1120, 720); self.setMinimumSize(980, 650); self.setAcceptDrops(True)
        self.setStyleSheet("QLineEdit { min-height: 30px; font-size: 12pt; } QLabel { font-size: 11pt; } QTableWidget { font-size: 11pt; }")
        self._history: list[list[str]] = []
        root = QVBoxLayout(self); form = QFormLayout(); self.edits = []
        ordered = self._classify_initial_files(initial_files or [])
        labels = ["Anion optimized log:", "Neutral N−1 log:", "Neutral N+1 log:"]
        for i, label in enumerate(labels):
            edit = DropPathLineEdit(ordered[i] if i < len(ordered) else "", suffixes={".log", ".out"}, allow_directory=False)
            b = QPushButton("Browse…"); b.clicked.connect(lambda checked=False, e=edit: self._pick(e))
            row = QHBoxLayout(); row.addWidget(edit, 1); row.addWidget(b); form.addRow(label, row); self.edits.append(edit)
        root.addLayout(form)
        controls = QHBoxLayout(); classify = QPushButton("Classify Current Files"); clear = QPushButton("Clear")
        classify.clicked.connect(self._classify_current); clear.clicked.connect(self._clear)
        controls.addWidget(classify); controls.addWidget(clear); controls.addStretch(1); root.addLayout(controls)
        note = QLabel("Drop a .log/.out file directly onto any input box, or drop three files anywhere in this window. ChemAuto classifies the anion and N−1/N+1 channels from charge and multiplicity. Ctrl+Z restores the previous selection.")
        note.setWordWrap(True); root.addWidget(note)

        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Channel", "Multiplicity", "VDE (eV)", "ADE (eV)", "Warnings"])
        root.addWidget(self.table, 1)
        self.details = QPlainTextEdit(); self.details.setReadOnly(True); self.details.setMaximumHeight(150); root.addWidget(self.details)
        row = QHBoxLayout(); calc = QPushButton("Calculate"); export = QPushButton("Export TXT…"); close = QPushButton("Close")
        calc.clicked.connect(self.calculate); export.clicked.connect(self.export_txt); close.clicked.connect(self.close)
        row.addStretch(1); row.addWidget(calc); row.addWidget(export); row.addWidget(close); root.addLayout(row)
        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self); self._undo_shortcut.activated.connect(self._undo)

    @staticmethod
    def _classify_initial_files(files: list[str]) -> list[str]:
        if len(files) != 3: return list(files)
        try:
            parsed = [(f, parse_gaussian_log(f)) for f in files]
            charges = [s.charge for _, s in parsed]; valid = [q for q in charges if q is not None]
            if len(valid) != 3: return list(files)
            anion_index = charges.index(min(valid)); anion_file, anion = parsed[anion_index]
            neutrals = [(f, s) for i, (f, s) in enumerate(parsed) if i != anion_index]
            if anion.multiplicity is None or any(s.multiplicity is None for _, s in neutrals): return [anion_file] + [f for f, _ in neutrals]
            target_minus, target_plus = anion.multiplicity - 1, anion.multiplicity + 1
            minus = next((f for f, s in neutrals if s.multiplicity == target_minus), neutrals[0][0])
            plus = next((f for f, s in neutrals if s.multiplicity == target_plus and f != minus), next(f for f, _ in neutrals if f != minus))
            return [anion_file, minus, plus]
        except Exception: return list(files)

    def _remember(self):
        state = [e.text() for e in self.edits]
        if not self._history or self._history[-1] != state: self._history.append(state)

    def _undo(self):
        if not self._history: return
        state = self._history.pop()
        for edit, value in zip(self.edits, state): edit.setText(value)

    def _pick(self, edit):
        p, _ = QFileDialog.getOpenFileName(self, "Select Gaussian log", edit.text(), "Gaussian log (*.log *.out)")
        if p: self._remember(); edit.setText(p)

    def dragEnterEvent(self, event):
        if any(Path(u.toLocalFile()).suffix.lower() in {'.log', '.out'} for u in event.mimeData().urls()): event.acceptProposedAction()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls() if Path(u.toLocalFile()).suffix.lower() in {'.log', '.out'}]
        if files:
            self._remember(); current = [e.text().strip() for e in self.edits if e.text().strip()]
            merged = (current + files)[:3]
            if len(merged) == 3: merged = self._classify_initial_files(merged)
            for i, edit in enumerate(self.edits): edit.setText(merged[i] if i < len(merged) else "")
            event.acceptProposedAction()

    def _classify_current(self):
        files = [e.text().strip() for e in self.edits]
        if not all(Path(p).is_file() for p in files): QMessageBox.warning(self, "VDE/ADE", "Select all three log files first."); return
        self._remember(); ordered = self._classify_initial_files(files)
        for e, value in zip(self.edits, ordered): e.setText(value)

    def _clear(self):
        self._remember()
        for e in self.edits: e.clear()
        self.table.setRowCount(0); self.details.clear()

    def calculate(self):
        paths = [e.text().strip() for e in self.edits]
        if not all(Path(p).is_file() for p in paths): QMessageBox.warning(self, "VDE/ADE", "Select all three log files."); return
        try: anion, results, global_warnings = calculate_three_file_vde_ade(*paths)
        except Exception as exc: QMessageBox.critical(self, "VDE/ADE", str(exc)); return
        self.table.setRowCount(0)
        for result in results:
            r = self.table.rowCount(); self.table.insertRow(r)
            vals = [result.label, result.multiplicity, result.vde_ev, result.ade_ev, "; ".join(result.warnings)]
            for c, v in enumerate(vals):
                text = f"{v:.8f}" if isinstance(v, float) else "" if v is None else str(v)
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()
        lines = [f"Anion: {Path(anion.path).name}; charge={anion.charge}; multiplicity={anion.multiplicity}"] + global_warnings
        lines.append("ADE never falls back to pure HF when ZPE/Etot is missing.")
        self.details.setPlainText("\n".join(lines))

    def export_txt(self):
        if self.table.rowCount() == 0: return
        first = Path(self.edits[0].text().strip())
        default = first.parent / f"{first.stem}_VDE_ADE.txt" if first.is_file() else Path("VDE_ADE.txt")
        p, _ = QFileDialog.getSaveFileName(self, "Export VDE/ADE result", str(default), "Text (*.txt)")
        if not p: return
        lines = ["Channel\tMultiplicity\tVDE(eV)\tADE(eV)\tWarnings"]
        for r in range(self.table.rowCount()): lines.append("\t".join(self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount())))
        Path(p).write_text("\n".join(lines) + "\n", encoding="utf-8")
