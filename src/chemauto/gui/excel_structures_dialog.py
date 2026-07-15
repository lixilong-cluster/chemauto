from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, QLabel,
    QPushButton, QFileDialog, QProgressDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from chemauto.core.excel_structures import export_excel_with_structures, pymol_available


class ExcelStructuresDialog(QDialog):
    def __init__(self, summaries, parent=None):
        super().__init__(parent); self.summaries=summaries
        self.setWindowTitle("Export Excel with Structures"); self.resize(560,230)
        root=QVBoxLayout(self)
        root.addWidget(QLabel("Choose the structure columns. Data columns are shifted automatically so images never overwrite Sym./State/energy fields."))
        self.init_cb=QCheckBox("Initial structure"); self.opt_cb=QCheckBox("Optimized structure")
        self.init_cb.setChecked(True); self.opt_cb.setChecked(True)
        row=QHBoxLayout(); row.addWidget(self.init_cb); row.addWidget(self.opt_cb); row.addStretch(1); root.addLayout(row)
        renderer_row=QHBoxLayout(); renderer_row.addWidget(QLabel("Renderer:")); self.renderer=QComboBox()
        self.renderer.addItem("PyMOL (ChemAuto 5.3 legacy renderer)", "pymol")
        self.renderer.addItem("ChemAuto built-in renderer", "built-in")
        if not pymol_available():
            model_item = self.renderer.model().item(0)
            if model_item is not None:
                model_item.setEnabled(False)
                model_item.setToolTip("PyMOL is unavailable in this environment.")
            self.renderer.setCurrentIndex(1)
        renderer_row.addWidget(self.renderer,1); root.addLayout(renderer_row)
        buttons=QHBoxLayout(); run=QPushButton("Export…"); close=QPushButton("Close"); run.clicked.connect(self.export); close.clicked.connect(self.close)
        buttons.addStretch(1); buttons.addWidget(run); buttons.addWidget(close); root.addLayout(buttons)
    def export(self):
        if not self.init_cb.isChecked() and not self.opt_cb.isChecked(): QMessageBox.warning(self,"Excel + Structures","Select at least one structure type."); return
        if self.renderer.currentData() == "pymol" and not pymol_available():
            QMessageBox.warning(
                self,
                "Excel + Structures",
                "The PyMOL renderer is unavailable. ChemAuto will use the built-in renderer instead.",
            )
            self.renderer.setCurrentIndex(1)
        out,_=QFileDialog.getSaveFileName(self,"Export Excel with structures","ChemAuto_structures.xlsx","Excel (*.xlsx)")
        if not out: return
        progress=QProgressDialog("Rendering structures…","Cancel",0,len(self.summaries),self); progress.setWindowModality(Qt.WindowModality.WindowModal); progress.show()
        def cb(i,total,name): progress.setValue(i); progress.setLabelText(f"Rendering {name} ({i}/{total})")
        try:
            export_excel_with_structures(out,self.summaries,self.init_cb.isChecked(),self.opt_cb.isChecked(),self.renderer.currentData(),cb)
            progress.setValue(len(self.summaries)); QMessageBox.information(self,"Excel + Structures",f"Saved:\n{out}")
        except Exception as exc:
            progress.close()
            if self.renderer.currentData() == "pymol":
                answer = QMessageBox.question(
                    self,
                    "PyMOL rendering failed",
                    f"The legacy PyMOL renderer could not complete the export:\n\n{exc}\n\n"
                    "Retry the same export with the ChemAuto built-in renderer?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self.renderer.setCurrentIndex(1)
                    progress = QProgressDialog("Rendering structures with the built-in renderer…", "Cancel", 0, len(self.summaries), self)
                    progress.setWindowModality(Qt.WindowModality.WindowModal); progress.show()
                    try:
                        export_excel_with_structures(out,self.summaries,self.init_cb.isChecked(),self.opt_cb.isChecked(),"built-in",cb)
                        progress.setValue(len(self.summaries)); QMessageBox.information(self,"Excel + Structures",f"Saved with the built-in renderer:\n{out}")
                        return
                    except Exception as fallback_exc:
                        progress.close(); QMessageBox.critical(self,"Excel + Structures",str(fallback_exc)); return
            QMessageBox.critical(self,"Excel + Structures",str(exc))
