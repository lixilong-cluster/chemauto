from __future__ import annotations

import contextlib
import io

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QPlainTextEdit, QMessageBox, QFileDialog
)

from chemauto.features.term_gen import AtomicTermSymbolGenerator


class AtomicTermDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atomic Term Symbol Generator")
        self.resize(720, 520)
        root = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("Electronic configuration:"))
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("p2, d3, s2p2, p2d1 …")
        calc = QPushButton("Calculate")
        calc.clicked.connect(self.calculate)
        self.input_edit.returnPressed.connect(self.calculate)
        row.addWidget(self.input_edit, 1)
        row.addWidget(calc)
        root.addLayout(row)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        root.addWidget(self.output, 1)

        bottom = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        save_btn = QPushButton("Save TXT…")
        clear_btn = QPushButton("Clear")
        close_btn = QPushButton("Close")
        copy_btn.clicked.connect(lambda: self.output.selectAll() or self.output.copy())
        save_btn.clicked.connect(self.save_txt)
        clear_btn.clicked.connect(self.output.clear)
        close_btn.clicked.connect(self.close)
        bottom.addWidget(copy_btn); bottom.addWidget(save_btn); bottom.addWidget(clear_btn)
        bottom.addStretch(1); bottom.addWidget(close_btn)
        root.addLayout(bottom)

    def calculate(self):
        config = self.input_edit.text().strip().lower().replace(" ", "")
        if not config:
            return
        gen = AtomicTermSymbolGenerator()
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                n_e, orb = gen.handle_input(config)
                if n_e is not None and orb is not None:
                    print(f"Single configuration: {config}\n")
                    table = gen.generate_ml_ms_table(n_e, orb)
                    gen.display_ml_ms_table(table)
                    terms = gen.generate_term_symbols(table)
                    gen.print_term_symbols(terms, n_e, orb)
                else:
                    inputs = gen.handle_mixed_input(config)
                    if inputs is None or len(inputs) < 2:
                        raise ValueError("Invalid configuration. Examples: p2, d3, s2p2, p2d1")
                    print(f"Mixed configuration: {config}\n")
                    dictionaries = [gen.generate_L_S(ne, ob) for ob, ne in inputs]
                    # Preserve the verified legacy mixed-configuration scope: two open subshells.
                    combined = gen.generate_mutil_term_symbols(dictionaries[0], dictionaries[1])
                    gen.print_ground_state(combined)
            self.output.setPlainText(buffer.getvalue().strip())
        except Exception as exc:
            QMessageBox.warning(self, "Atomic Terms", str(exc))

    def save_txt(self):
        if not self.output.toPlainText().strip():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save term-symbol result", "atomic_terms.txt", "Text (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output.toPlainText() + "\n")
