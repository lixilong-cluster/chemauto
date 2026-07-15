from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit


class DropPathLineEdit(QLineEdit):
    """A line edit that accepts a file or directory dropped directly onto it."""

    pathDropped = pyqtSignal(str)

    def __init__(self, *args, suffixes: Iterable[str] | None = None, allow_directory: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.suffixes = {s.lower() for s in (suffixes or [])}
        self.allow_directory = allow_directory

    def _accept_path(self, path: Path) -> bool:
        if path.is_dir():
            return self.allow_directory
        if not path.is_file():
            return False
        return not self.suffixes or path.suffix.lower() in self.suffixes

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(self._accept_path(Path(u.toLocalFile())) for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if self._accept_path(path):
                self.setText(str(path))
                self.pathDropped.emit(str(path))
                event.acceptProposedAction()
                return
        super().dropEvent(event)
