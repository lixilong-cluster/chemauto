from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget, QPlainTextEdit, QScrollArea,
)

from chemauto.core.gjf_document import GJFDocument, GJFLink, split_route
from chemauto.core.external_open import open_external


# Gaussian route keywords rather than literature aliases. In particular,
# Gaussian's PBE0 keyword is PBE1PBE (and UPBE1PBE for unrestricted jobs).
METHODS = [
    "ub3lyp", "b3lyp", "upbe1pbe", "pbe1pbe", "upbepbe", "pbepbe",
    "utpssh", "tpssh", "utpss", "tpss", "ubpw91", "bpw91",
    "ubp86", "bp86", "ur2scan", "r2scan", "uwb97xd", "wb97xd",
    "ucam-b3lyp", "cam-b3lyp", "um062x", "m062x", "uhf", "rhf",
    "ump2", "mp2", "uccsd", "ccsd", "uccsd(t)", "ccsd(t)",
]
BASES = [
    "def2svp", "def2tzvp", "def2tzvpd", "def2qzvp", "def2qzvpp",
    "6-31g(d)", "6-311+g(d)", "6-311+g(2df)",
    "aug-cc-pvdz", "aug-cc-pvtz", "aug-cc-pvqz",
    "gen", "genecp", "chkbasis",
]
JOBS = ["sp", "opt", "freq", "opt freq", "stable", "stable=opt", "force", "irc", "scan"]
OPT_OPTIONS = [
    "", "opt", "opt=calcfc", "opt=calcall", "opt=readfc",
    "opt=(calcfc,maxcycle=200)", "opt=(calcall,maxcycle=200)",
    "opt=(readfc,maxcycle=200)", "opt=tight", "opt=verytight",
    "opt=(tight,calcfc,maxcycle=200)",
]
FREQ_OPTIONS = ["", "freq", "freq=noraman", "freq=readfc", "freq=(noraman,readfc)"]
SCF_OPTIONS = [
    "", "scf=xqc", "scf=(xqc,maxcycle=512)", "scf=qc",
    "scf=maxcycle=512", "scf=conver=8",
    "scf=(xqc,conver=8,maxcycle=512)", "scf=(yqc,maxcycle=512)",
]
INT_OPTIONS = ["", "int=ultrafine", "int=superfine", "integral=ultrafine", "integral=superfine"]
GEOM_OPTIONS = ["", "geom=check", "geom=allcheck", "geom=connectivity", "geom=modredundant", "geom=nocrowd"]
GUESS_OPTIONS = ["", "guess=read", "guess=mix", "guess=always", "guess=(read,mix)", "guess=cards"]


def _editable_combo(items: list[str], current: str = "") -> QComboBox:
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(items)
    combo.setCurrentText(current)
    combo.setMinimumWidth(190)
    combo.setMinimumHeight(30)
    combo.setFont(QFont("Segoe UI", 11))
    return combo


def _field_widget(label: str, widget: QWidget, tooltip: str = "") -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    text = QLabel(label)
    text.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
    if tooltip:
        text.setToolTip(tooltip)
        widget.setToolTip(tooltip)
    layout.addWidget(text)
    layout.addWidget(widget)
    return box


class LinkEditor(QWidget):
    def __init__(self, link: GJFLink, index: int, parent=None):
        super().__init__(parent)
        self.link = link
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(10)

        # Four compact Link0 cards in one row.
        link0_box = QGroupBox(f"Link {index} — Link0 and resources")
        g = QGridLayout(link0_box)
        g.setHorizontalSpacing(12)
        self.nproc = QLineEdit(link.get_link0("nprocshared") or link.get_link0("nproc"))
        self.mem = QLineEdit(link.get_link0("mem"))
        self.chk = QLineEdit(link.get_link0("chk"))
        self.oldchk = QLineEdit(link.get_link0("oldchk"))
        for edit in (self.nproc, self.mem, self.chk, self.oldchk):
            edit.setMinimumHeight(30)
            edit.setFont(QFont("Segoe UI", 11))
        link0_fields = [
            ("%nprocshared", self.nproc), ("%mem", self.mem),
            ("%chk", self.chk), ("%oldchk", self.oldchk),
        ]
        for col, (label, widget) in enumerate(link0_fields):
            g.addWidget(_field_widget(label, widget), 0, col)
            g.setColumnStretch(col, 1)
        layout.addWidget(link0_box)

        # Three-column route layout. Every combo is editable, so uncommon valid
        # Gaussian keywords can still be typed even when not in the presets.
        route_box = QGroupBox("Route section")
        rg = QGridLayout(route_box)
        rg.setHorizontalSpacing(12)
        rg.setVerticalSpacing(8)
        c = link.components
        self.prefix = _editable_combo(["#p", "#", "#n", "#t"], c.prefix)
        self.job = _editable_combo(JOBS, c.job)
        self.method = _editable_combo(METHODS, c.method)
        self.basis = _editable_combo(BASES, c.basis)
        self.opt = _editable_combo(OPT_OPTIONS, c.opt)
        self.freq = _editable_combo(FREQ_OPTIONS, c.freq)
        self.scf = _editable_combo(SCF_OPTIONS, c.scf)
        self.integral = _editable_combo(INT_OPTIONS, c.integral)
        self.geom = _editable_combo(GEOM_OPTIONS, c.geom)
        self.guess = _editable_combo(GUESS_OPTIONS, c.guess)
        self.extra = QLineEdit(" ".join(c.extra_tokens))
        self.extra.setMinimumHeight(32)
        self.extra.setFont(QFont("Consolas", 11))

        fields = [
            ("Route prefix", self.prefix, "Gaussian route prefix."),
            ("Job type", self.job, "SP, Opt, Freq, Stable and other Gaussian job keywords."),
            ("Method / functional", self.method, "Use Gaussian keywords; PBE0 is written as PBE1PBE."),
            ("Basis set", self.basis, "Select or type a Gaussian basis keyword."),
            ("Opt options", self.opt, "Optimization keyword and options."),
            ("Freq options", self.freq, "Frequency keyword and options."),
            ("SCF options", self.scf, "SCF convergence algorithm and cycle options."),
            ("Integral options", self.integral, "Numerical integration grid."),
            ("Geom", self.geom, "Geometry source or connectivity options."),
        ]
        for i, (label, widget, tip) in enumerate(fields):
            row, col = divmod(i, 3)
            rg.addWidget(_field_widget(label, widget, tip), row, col)
            rg.setColumnStretch(col, 1)
        rg.addWidget(_field_widget("Guess", self.guess), 3, 0)
        rg.addWidget(_field_widget("Other route keywords", self.extra), 3, 1, 1, 2)
        layout.addWidget(route_box)

        mol_box = QGroupBox("Title and molecular specification")
        mg = QGridLayout(mol_box)
        self.title = QLineEdit(" ".join(link.title_lines))
        self.title.setMinimumHeight(31)
        self.title.setFont(QFont("Segoe UI", 11))
        self.charge = QSpinBox()
        self.charge.setRange(-99, 99)
        self.charge.setValue(link.charge)
        self.mult = QSpinBox()
        self.mult.setRange(1, 99)
        self.mult.setValue(link.multiplicity)
        self.charge.setMinimumHeight(31)
        self.mult.setMinimumHeight(31)
        mg.addWidget(QLabel("Title"), 0, 0)
        mg.addWidget(self.title, 0, 1, 1, 7)
        mg.addWidget(QLabel("Charge"), 1, 0)
        mg.addWidget(self.charge, 1, 1)
        mg.addWidget(QLabel("Multiplicity"), 1, 2)
        mg.addWidget(self.mult, 1, 3)
        mg.addWidget(QLabel(f"Coordinates: {len(link.coordinate_lines)} line(s)"), 1, 4, 1, 2)
        mg.addWidget(QLabel(f"Tail: {len([x for x in link.tail_lines if x.strip()])} non-empty line(s)"), 1, 6, 1, 2)
        layout.addWidget(mol_box)

        # Coordinates and tail are side by side, leaving enough vertical room
        # for Gen/GenECP basis blocks and multi-line ModRedundant directives.
        preview_box = QGroupBox("Molecular coordinates and tail section")
        pv = QGridLayout(preview_box)
        self.coordinates = QPlainTextEdit("\n".join(link.coordinate_lines))
        self.coordinates.setPlaceholderText("Coordinates may be blank for geom=check/allcheck inputs.")
        self.tail = QPlainTextEdit("\n".join(link.tail_lines))
        self.tail.setPlaceholderText("Custom Gen/GenECP basis, ECP, NBO directives, ModRedundant data, etc.")
        for edit in (self.coordinates, self.tail):
            edit.setMinimumHeight(220)
            edit.setFont(QFont("Consolas", 10))
        pv.addWidget(QLabel("Coordinates"), 0, 0)
        pv.addWidget(QLabel("Tail section / custom basis"), 0, 1)
        pv.addWidget(self.coordinates, 1, 0)
        pv.addWidget(self.tail, 1, 1)
        pv.setColumnStretch(0, 1)
        pv.setColumnStretch(1, 1)
        layout.addWidget(preview_box)

        raw_box = QGroupBox("Route preview")
        rv = QHBoxLayout(raw_box)
        self.route_preview = QLineEdit(link.components.build())
        self.route_preview.setReadOnly(True)
        self.route_preview.setFont(QFont("Consolas", 10))
        refresh = QPushButton("Refresh preview")
        refresh.clicked.connect(self.refresh_preview)
        rv.addWidget(self.route_preview, 1)
        rv.addWidget(refresh)
        layout.addWidget(raw_box)
        layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

    def refresh_preview(self):
        self._apply_components()
        self.route_preview.setText(self.link.components.build())

    def _apply_components(self):
        c = self.link.components
        c.prefix = self.prefix.currentText().strip() or "#p"
        c.job = self.job.currentText().strip() or "sp"
        c.method = self.method.currentText().strip()
        c.basis = self.basis.currentText().strip()
        c.opt = self.opt.currentText().strip()
        c.freq = self.freq.currentText().strip()
        c.scf = self.scf.currentText().strip()
        c.integral = self.integral.currentText().strip()
        c.geom = self.geom.currentText().strip()
        c.guess = self.guess.currentText().strip()
        c.extra_tokens = split_route(self.extra.text())

    def commit(self):
        self.link.set_link0("nprocshared", self.nproc.text())
        self.link.set_link0("nproc", "")
        self.link.set_link0("mem", self.mem.text())
        self.link.set_link0("chk", self.chk.text())
        self.link.set_link0("oldchk", self.oldchk.text())
        self._apply_components()
        self.link.title_lines = [self.title.text().strip() or "ChemAuto job"]
        self.link.charge = self.charge.value()
        self.link.multiplicity = self.mult.value()
        self.link.coordinate_lines = [x.rstrip() for x in self.coordinates.toPlainText().splitlines() if x.strip()]
        self.link.tail_lines = self.tail.toPlainText().splitlines()
        if self.link.components.basis.lower() in {"gen", "genecp"} and not self.link.has_custom_basis_tail():
            raise ValueError("Gen/GenECP is selected, but the custom basis section is missing or has no '****' separator.")


class GJFEditorDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.document = GJFDocument.from_file(self.path)
        self.setWindowTitle(f"Modify .gjf/.com — {self.path.name}")
        self.resize(1320, 900)
        self.setMinimumSize(1040, 720)
        self.setFont(QFont("Segoe UI", 10))
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        file_label = QLabel(f"File: {self.path}")
        top.addWidget(file_label, 1)
        open_btn = QPushButton("Open in default editor")
        open_btn.clicked.connect(lambda: open_external(self.path))
        top.addWidget(open_btn)
        root.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11))
        self.editors: list[LinkEditor] = []
        for i, link in enumerate(self.document.links, 1):
            editor = LinkEditor(link, i, self)
            self.editors.append(editor)
            self.tabs.addTab(editor, f"Link {i}")
        root.addWidget(self.tabs, 1)

        note = QLabel(
            "Every combo box is editable. Presets use Gaussian input keywords (for example, PBE0 = PBE1PBE). "
            "Unknown route keywords are preserved in Other route keywords. Save As is recommended to protect the original file."
        )
        note.setWordWrap(True)
        root.addWidget(note)
        buttons = QHBoxLayout()
        save_as = QPushButton("Save As…")
        overwrite = QPushButton("Overwrite original")
        close = QPushButton("Close")
        save_as.clicked.connect(self.save_as)
        overwrite.clicked.connect(self.overwrite)
        close.clicked.connect(self.close)
        buttons.addStretch(1)
        buttons.addWidget(save_as)
        buttons.addWidget(overwrite)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _commit_all(self) -> bool:
        try:
            for editor in self.editors:
                editor.commit()
            return True
        except Exception as exc:
            QMessageBox.warning(self, ".gjf validation", str(exc))
            return False

    def save_as(self):
        if not self._commit_all():
            return
        default = self.path.with_name(self.path.stem + "-modified" + self.path.suffix)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save modified Gaussian input", str(default), "Gaussian input (*.gjf *.com)"
        )
        if not path:
            return
        out = self.document.write(path)
        QMessageBox.information(self, ".gjf saved", f"Saved:\n{out}")

    def overwrite(self):
        if not self._commit_all():
            return
        answer = QMessageBox.question(
            self,
            "Overwrite original",
            f"Overwrite the original file?\n\n{self.path}\n\nNo backup is created.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.document.write(self.path)
        QMessageBox.information(self, ".gjf saved", f"Updated:\n{self.path}")
