from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton,
    QFileDialog, QDoubleSpinBox, QPlainTextEdit, QMessageBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QLabel
)

from chemauto.core.dos_pairs import DOSPair, identify_dos_pairs, scan_dos_pairs
from chemauto.infra.config import load_user_config


class _DOSWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, pairs: list[DOSPair], xlim: tuple[float, float], ylim: tuple[float, float]):
        super().__init__(); self.pairs = pairs; self.xlim = xlim; self.ylim = ylim

    @pyqtSlot()
    def run(self):
        try:
            from chemauto.features.dos_plotter import AutoDOS, op
            plotter = AutoDOS(); done = 0
            try:
                for pair in self.pairs:
                    if not pair.complete: continue
                    self.progress.emit(f"Plotting {pair.key} …")
                    plotter.process_file(
                        str(pair.curve), str(pair.line),
                        xlim_values=self.xlim, ylim_values=self.ylim,
                        exit_origin=False,
                    )
                    done += 1
            finally:
                try: op.exit()
                except Exception: pass
            self.finished.emit(f"Completed {done} DOS plot(s).")
        except Exception as exc:
            self.failed.emit(str(exc))


class DOSDialog(QDialog):
    """Plot existing ``_curve/_line`` data, with or without a prior PES step."""

    def __init__(self, parent=None, initial_folder: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Plot DOS with Origin")
        self.resize(1000, 660)
        self.setAcceptDrops(True)
        self.pairs: list[DOSPair] = []
        self._paths: list[Path] = []
        self._history: list[list[Path]] = []
        self._thread = None; self._worker = None
        cfg = load_user_config(); xr = cfg.get("default_x_range", [0, 3.3]); yr = cfg.get("default_y_range", [-0.03, 6.5])

        root = QVBoxLayout(self)
        controls = QHBoxLayout()
        add_files = QPushButton("Add Curve/Line Files…")
        add_folder = QPushButton("Add Folder…")
        remove = QPushButton("Remove Selected")
        clear = QPushButton("Clear")
        add_files.clicked.connect(self._pick_files); add_folder.clicked.connect(self._pick_folder)
        remove.clicked.connect(self._remove_selected); clear.clicked.connect(self._clear)
        controls.addWidget(add_files); controls.addWidget(add_folder); controls.addWidget(remove); controls.addWidget(clear); controls.addStretch(1)
        root.addLayout(controls)
        note = QLabel(
            "This window can plot existing local DOS data directly; generating PES first is optional. "
            "Drop _curve.txt/_line.txt files or a folder here. Files are paired strictly by exact suffix and never across folders. "
            "Ctrl+Z restores the previous input list."
        )
        note.setWordWrap(True); root.addWidget(note)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Use", "Dataset", "Curve", "Line", "Folder"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        root.addWidget(self.table, 1)

        form = QFormLayout()
        xr_row = QHBoxLayout(); self.xmin = QDoubleSpinBox(); self.xmax = QDoubleSpinBox()
        yr_row = QHBoxLayout(); self.ymin = QDoubleSpinBox(); self.ymax = QDoubleSpinBox()
        for w in (self.xmin, self.xmax, self.ymin, self.ymax): w.setRange(-100000, 100000); w.setDecimals(6)
        self.xmin.setValue(float(xr[0])); self.xmax.setValue(float(xr[1])); self.ymin.setValue(float(yr[0])); self.ymax.setValue(float(yr[1]))
        xr_row.addWidget(self.xmin); xr_row.addWidget(QLabel("to")); xr_row.addWidget(self.xmax)
        yr_row.addWidget(self.ymin); yr_row.addWidget(QLabel("to")); yr_row.addWidget(self.ymax)
        form.addRow("X range:", xr_row); form.addRow("Y range:", yr_row); root.addLayout(form)

        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(120); root.addWidget(self.log)
        buttons = QHBoxLayout(); self.run_btn = QPushButton("Plot Selected"); open_btn = QPushButton("Open Output Folder"); close = QPushButton("Close")
        self.run_btn.clicked.connect(self.run_job); open_btn.clicked.connect(self._open_folder); close.clicked.connect(self.close)
        buttons.addStretch(1); buttons.addWidget(self.run_btn); buttons.addWidget(open_btn); buttons.addWidget(close); root.addLayout(buttons)

        self._undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self); self._undo_shortcut.activated.connect(self._undo)
        if initial_folder and Path(initial_folder).is_dir(): self._add_folder(Path(initial_folder))

    def _remember(self):
        state = list(self._paths)
        if not self._history or self._history[-1] != state: self._history.append(state)
        if len(self._history) > 20: self._history.pop(0)

    def _undo(self):
        if not self._history: return
        self._paths = self._history.pop(); self._rebuild_pairs()

    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select curve and line data", "",
            "DOS data (*_curve.txt *_line.txt);;Text files (*.txt);;All files (*)"
        )
        if files: self._add_paths([Path(f) for f in files])

    def _pick_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Select DOS data folder", "")
        if p: self._add_folder(Path(p))

    def _add_folder(self, folder: Path):
        if not folder.is_dir(): return
        self._remember()
        for p in folder.rglob("*.txt"):
            if p.name.endswith("_curve.txt") or p.name.endswith("_line.txt"):
                if p not in self._paths: self._paths.append(p)
        self._rebuild_pairs()

    def _add_paths(self, paths: list[Path]):
        self._remember()
        for p in paths:
            if p.is_dir():
                for f in p.rglob("*.txt"):
                    if f.name.endswith("_curve.txt") or f.name.endswith("_line.txt"):
                        if f not in self._paths: self._paths.append(f)
            elif p.is_file() and (p.name.endswith("_curve.txt") or p.name.endswith("_line.txt")):
                if p not in self._paths: self._paths.append(p)
        self._rebuild_pairs()

    def _rebuild_pairs(self):
        self.pairs = identify_dos_pairs(self._paths)
        self.table.setRowCount(0)
        for pair in self.pairs:
            r = self.table.rowCount(); self.table.insertRow(r)
            use = QTableWidgetItem("✓" if pair.complete else "")
            self.table.setItem(r, 0, use); self.table.setItem(r, 1, QTableWidgetItem(pair.key))
            self.table.setItem(r, 2, QTableWidgetItem(pair.curve.name if pair.curve else "Missing"))
            self.table.setItem(r, 3, QTableWidgetItem(pair.line.name if pair.line else "Missing"))
            parent = pair.curve.parent if pair.curve else pair.line.parent if pair.line else Path()
            self.table.setItem(r, 4, QTableWidgetItem(str(parent)))
        self.table.resizeColumnsToContents()
        complete = sum(p.complete for p in self.pairs)
        self.log.setPlainText(f"Found {complete} complete pair(s), {len(self.pairs)-complete} incomplete dataset(s).")

    def _remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()}, reverse=True)
        if not rows: return
        self._remember(); remove_paths: set[Path] = set()
        for r in rows:
            pair = self.pairs[r]
            if pair.curve: remove_paths.add(pair.curve)
            if pair.line: remove_paths.add(pair.line)
        self._paths = [p for p in self._paths if p not in remove_paths]; self._rebuild_pairs()

    def _clear(self):
        if not self._paths: return
        self._remember(); self._paths = []; self._rebuild_pairs()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        self._add_paths([Path(u.toLocalFile()) for u in event.mimeData().urls()]); event.acceptProposedAction()

    def _open_folder(self):
        selected = self._selected_pairs()
        pair = selected[0] if selected else next((p for p in self.pairs if p.complete), None)
        p = pair.curve.parent if pair and pair.curve else pair.line.parent if pair and pair.line else None
        if p and p.is_dir():
            import os; os.startfile(str(p))

    def _selected_pairs(self):
        rows = {i.row() for i in self.table.selectionModel().selectedRows()}
        return [self.pairs[r] for r in sorted(rows) if 0 <= r < len(self.pairs) and self.pairs[r].complete]

    def run_job(self):
        if self.xmin.value() >= self.xmax.value(): QMessageBox.warning(self, "DOS", "X minimum must be smaller than X maximum."); return
        if self.ymin.value() >= self.ymax.value(): QMessageBox.warning(self, "DOS", "Y minimum must be smaller than Y maximum."); return
        selected = self._selected_pairs() or [p for p in self.pairs if p.complete]
        if not selected: QMessageBox.warning(self, "DOS", "Add a complete _curve/_line pair first."); return
        self.run_btn.setEnabled(False); self.log.setPlainText("Starting Origin…")
        self._thread = QThread(self); self._worker = _DOSWorker(
            selected, (self.xmin.value(), self.xmax.value()), (self.ymin.value(), self.ymax.value())
        )
        self._worker.moveToThread(self._thread); self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.log.appendPlainText); self._worker.finished.connect(self._done); self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._thread.quit); self._worker.failed.connect(self._thread.quit); self._thread.start()

    def _done(self, msg): self.log.appendPlainText(msg); self.run_btn.setEnabled(True)
    def _failed(self, msg): self.log.appendPlainText("ERROR: " + msg); self.run_btn.setEnabled(True)
