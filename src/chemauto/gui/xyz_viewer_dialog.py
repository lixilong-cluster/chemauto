from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QFileDialog, QMessageBox
)

from chemauto.core.xyz_frames import parse_xyz_frames


class XYZViewerDialog(QDialog):
    """View single-frame and multi-frame XYZ files.

    XYZ files can be selected with the Open button or dragged directly into
    this window. Dropping a new file replaces the current trajectory.
    """

    def __init__(self, path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("XYZ Viewer - ChemAuto")
        self.resize(760, 700)
        self.setAcceptDrops(True)
        self.frames: list[str] = []
        self.path = Path(path) if path else None

        from chemauto.gui.log_browser import StructureViewer
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.path_label = QLabel("Drag an .xyz file here, or click Open XYZ…")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        open_btn = QPushButton("Open XYZ…")
        open_btn.clicked.connect(self.pick_file)
        top.addWidget(self.path_label, 1)
        top.addWidget(open_btn)
        root.addLayout(top)

        self.viewer = StructureViewer("XYZ Structure", self, xyz_kind="xyz")
        root.addWidget(self.viewer, 1)

        bottom = QHBoxLayout()
        self.frame_label = QLabel("Frame 0/0")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.show_frame)
        prev_btn = QPushButton("◀")
        next_btn = QPushButton("▶")
        prev_btn.clicked.connect(lambda: self.slider.setValue(max(self.slider.minimum(), self.slider.value() - 1)))
        next_btn.clicked.connect(lambda: self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 1)))
        bottom.addWidget(prev_btn)
        bottom.addWidget(self.slider, 1)
        bottom.addWidget(next_btn)
        bottom.addWidget(self.frame_label)
        root.addLayout(bottom)

        if self.path:
            self.load_file(self.path)

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open XYZ trajectory",
            str(self.path.parent if self.path else ""),
            "XYZ files (*.xyz);;All files (*)",
        )
        if path:
            self.load_file(path)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() == ".xyz" for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        xyz_files = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.toLocalFile() and Path(url.toLocalFile()).suffix.lower() == ".xyz"
        ]
        if not xyz_files:
            event.ignore()
            return
        self.load_file(xyz_files[0])
        event.acceptProposedAction()
        if len(xyz_files) > 1:
            QMessageBox.information(
                self,
                "XYZ Viewer",
                f"Opened {xyz_files[0].name}. Drop the other XYZ files one at a time to view them.",
            )

    def load_file(self, path: str | Path):
        try:
            self.path = Path(path)
            self.frames = parse_xyz_frames(self.path)
        except Exception as exc:
            QMessageBox.warning(self, "XYZ Viewer", str(exc))
            return
        self.path_label.setText(str(self.path))
        self.slider.setRange(0, max(0, len(self.frames) - 1))
        self.slider.setEnabled(len(self.frames) > 1)
        self.slider.setValue(0)
        self.show_frame(0)

    def show_frame(self, index: int):
        if not self.frames:
            return
        index = max(0, min(index, len(self.frames) - 1))
        self.viewer.set_xyz(self.frames[index])
        self.frame_label.setText(f"Frame {index + 1}/{len(self.frames)}")
