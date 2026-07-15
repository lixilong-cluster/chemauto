#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI for non-sensitive remote CHK -> FCHK connection profiles."""
from __future__ import annotations

from typing import Dict, Optional

try:
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
        QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
        QSpinBox, QVBoxLayout, QWidget,
    )
except Exception:
    from PyQt5.QtWidgets import (
        QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
        QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
        QSpinBox, QVBoxLayout, QWidget,
    )

from chemauto.core.remote_formchk import (
    RemoteFormchkProfile, get_active_profile_name, load_profiles, save_profiles,
)


class PathEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit = QLineEdit()
        self.button = QPushButton("Browse…")
        self.button.clicked.connect(self._browse)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.button)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select executable")
        if path:
            self.edit.setText(path)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, text: str) -> None:
        self.edit.setText(text or "")


class RemoteProfilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remote .chk → .fchk Profiles")
        self.resize(650, 520)
        self.profiles: Dict[str, RemoteFormchkProfile] = load_profiles()
        self.active_name = get_active_profile_name()

        self.combo = QComboBox()
        self.btn_new = QPushButton("New")
        self.btn_delete = QPushButton("Delete")
        top = QHBoxLayout()
        top.addWidget(self.combo, 1)
        top.addWidget(self.btn_new)
        top.addWidget(self.btn_delete)

        self.name = QLineEdit()
        self.user = QLineEdit()
        self.host = QLineEdit()
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(22)
        self.workdir = QLineEdit()
        self.exec_node = QLineEdit()
        self.command = QLineEdit()
        self.clean = QCheckBox("Delete the uploaded .chk and generated .fchk after a successful download")
        self.clean.setChecked(True)
        self.overwrite = QCheckBox("Overwrite an existing local .fchk")
        self.scp_legacy = QCheckBox("Force legacy SCP protocol (-O)")
        self.ssh_exe = PathEdit()
        self.scp_exe = PathEdit()

        form = QFormLayout()
        form.addRow("Profile name:", self.name)
        form.addRow("Remote user:", self.user)
        form.addRow("Remote host:", self.host)
        form.addRow("SSH port:", self.port)
        form.addRow("Remote work directory:", self.workdir)
        form.addRow("Execution node:", self.exec_node)
        form.addRow("Conversion command:", self.command)
        form.addRow("SSH executable (optional):", self.ssh_exe)
        form.addRow("SCP executable (optional):", self.scp_exe)
        form.addRow("", self.clean)
        form.addRow("", self.overwrite)
        form.addRow("", self.scp_legacy)

        note = QLineEdit()
        note.setReadOnly(True)
        note.setText("Passwords are never stored. OpenSSH/PowerShell asks for them in the conversion console.")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save profile")
        buttons.accepted.connect(self._save_current)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

        self.combo.currentTextChanged.connect(self._load_selected)
        self.btn_new.clicked.connect(self._new)
        self.btn_delete.clicked.connect(self._delete)
        self._refresh_combo()

    def _refresh_combo(self):
        current = self.active_name if self.active_name in self.profiles else ""
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(sorted(self.profiles))
        self.combo.blockSignals(False)
        if current:
            self.combo.setCurrentText(current)
            self._load_selected(current)
        elif self.profiles:
            self.combo.setCurrentIndex(0)
            self._load_selected(self.combo.currentText())
        else:
            self._new()

    def _new(self):
        self.combo.setCurrentIndex(-1)
        self.name.setText("New profile")
        self.user.clear(); self.host.clear(); self.port.setValue(22)
        self.workdir.setText("/home/user/fchk")
        self.exec_node.clear(); self.command.setText("/home/user/bin/c2f")
        self.clean.setChecked(True); self.overwrite.setChecked(False); self.scp_legacy.setChecked(False)
        self.ssh_exe.setText(""); self.scp_exe.setText("")
        self.name.setFocus()
        self.name.selectAll()

    def _profile_from_form(self) -> RemoteFormchkProfile:
        return RemoteFormchkProfile(
            name=self.name.text().strip(),
            remote_user=self.user.text().strip(),
            remote_host=self.host.text().strip(),
            remote_port=int(self.port.value()),
            remote_workdir=self.workdir.text().strip(),
            remote_exec_node=self.exec_node.text().strip(),
            remote_command=self.command.text().strip(),
            clean_remote_files=self.clean.isChecked(),
            overwrite_local_fchk=self.overwrite.isChecked(),
            scp_force_legacy=self.scp_legacy.isChecked(),
            ssh_exe=self.ssh_exe.text(),
            scp_exe=self.scp_exe.text(),
        )

    def _load_selected(self, name: str):
        p = self.profiles.get(name)
        if p is None:
            return
        self.name.setText(p.name); self.user.setText(p.remote_user); self.host.setText(p.remote_host)
        self.port.setValue(int(p.remote_port)); self.workdir.setText(p.remote_workdir)
        self.exec_node.setText(p.remote_exec_node); self.command.setText(p.remote_command)
        self.clean.setChecked(p.clean_remote_files); self.overwrite.setChecked(p.overwrite_local_fchk)
        self.scp_legacy.setChecked(p.scp_force_legacy); self.ssh_exe.setText(p.ssh_exe); self.scp_exe.setText(p.scp_exe)

    def _save_current(self):
        p = self._profile_from_form()
        missing = p.validate()
        if missing:
            QMessageBox.warning(self, "Incomplete profile", "Please fill in: " + ", ".join(missing))
            return
        old = self.combo.currentText()
        if old and old != p.name:
            self.profiles.pop(old, None)
        self.profiles[p.name] = p
        self.active_name = p.name
        save_profiles(self.profiles, active=p.name)
        self._refresh_combo()
        self.combo.setCurrentText(p.name)
        QMessageBox.information(self, "Saved", f"Profile '{p.name}' was saved. No password was stored.")

    def _delete(self):
        name = self.combo.currentText()
        if not name or name not in self.profiles:
            return
        if QMessageBox.question(self, "Delete profile", f"Delete profile '{name}'?") != QMessageBox.StandardButton.Yes:
            return
        self.profiles.pop(name, None)
        self.active_name = ""
        save_profiles(self.profiles, active="")
        self._refresh_combo()

    def selected_profile(self) -> Optional[RemoteFormchkProfile]:
        name = self.combo.currentText() or self.active_name
        return self.profiles.get(name)
