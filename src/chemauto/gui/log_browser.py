#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChemAuto 7.1 Gaussian Results Browser
Based on Gaussian Log Viewer v6.6, with ChemAuto v6 integration changes:
- Detail fields rearranged into 8-row hybrid grid (Path/File moved to right-click menu)
- Right-click context menu on the file table
- Per-viewer 💾 Export buttons
- QSplitter minimum sizes
- PyQt5/6 compat shims for QSizePolicy / Qt.Orientation / Qt.ContextMenuPolicy
"""

from __future__ import annotations
import os
import re
import csv
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Sequence, Tuple, Any

# -----------------------
# Qt compatibility layer
# -----------------------
QT_LIB = "PyQt5"
try:
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QObject, QThread, pyqtSlot, QRect
    from PyQt6.QtGui import QFont, QAction, QActionGroup, QColor, QIcon, QPalette
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
        QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QLineEdit, QFormLayout, QSplitter, QSlider,
        QAbstractItemView, QSizePolicy, QFrame, QDialog, QColorDialog,
        QHeaderView, QMenu, QTextBrowser, QProgressDialog, QGroupBox, QStyleFactory
    )
    USER_ROLE = Qt.ItemDataRole.UserRole
    ASC = Qt.SortOrder.AscendingOrder
    DESC = Qt.SortOrder.DescendingOrder
    QT_LIB = "PyQt6"
except Exception:
    from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QThread, pyqtSlot, QRect
    from PyQt5.QtGui import QFont, QColor, QIcon, QPalette
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
        QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QLineEdit, QFormLayout, QSplitter, QSlider,
        QAbstractItemView, QSizePolicy, QFrame, QDialog, QColorDialog,
        QHeaderView, QAction, QActionGroup, QMenu, QTextBrowser, QProgressDialog, QGroupBox, QStyleFactory
    )
    QT_LIB = "PyQt5"
    USER_ROLE = Qt.UserRole
    ASC = Qt.AscendingOrder
    DESC = Qt.DescendingOrder

# Qt enum compatibility shims (PyQt5/6)
try:
    SP_EXPANDING = QSizePolicy.Policy.Expanding  # PyQt6
    SP_FIXED = QSizePolicy.Policy.Fixed
    SP_MINIMUM = QSizePolicy.Policy.Minimum
    SP_PREFERRED = QSizePolicy.Policy.Preferred
    SP_IGNORED = QSizePolicy.Policy.Ignored
except AttributeError:
    SP_EXPANDING = QSizePolicy.Expanding  # PyQt5
    SP_FIXED = QSizePolicy.Fixed
    SP_MINIMUM = QSizePolicy.Minimum
    SP_PREFERRED = QSizePolicy.Preferred
    SP_IGNORED = QSizePolicy.Ignored

try:
    ORIENT_VERTICAL = Qt.Orientation.Vertical  # PyQt6
    ORIENT_HORIZONTAL = Qt.Orientation.Horizontal
except AttributeError:
    ORIENT_VERTICAL = Qt.Vertical  # PyQt5
    ORIENT_HORIZONTAL = Qt.Horizontal

try:
    CMP_CUSTOM = Qt.ContextMenuPolicy.CustomContextMenu  # PyQt6
except AttributeError:
    CMP_CUSTOM = Qt.CustomContextMenu  # PyQt5

try:
    HDR_RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents  # PyQt6
    HDR_INTERACTIVE = QHeaderView.ResizeMode.Interactive
except AttributeError:
    HDR_RESIZE_TO_CONTENTS = QHeaderView.ResizeToContents  # PyQt5
    HDR_INTERACTIVE = QHeaderView.Interactive

try:
    PEN_DASH = Qt.PenStyle.DashLine  # PyQt6
except AttributeError:
    PEN_DASH = Qt.DashLine  # PyQt5

# ChemAuto uses a small built-in QSS theme rather than an additional
# third-party theme package. This keeps startup and packaging predictable.
_THEME_LABELS = ["ChemAuto Light", "ChemAuto Dark", "System Default"]

_CHEMAUTO_LIGHT_QSS = r"""
QMainWindow, QDialog { background: #f5f7fa; }
QMenuBar { background: #ffffff; border-bottom: 1px solid #d9dee7; padding: 2px; }
QMenuBar::item { padding: 6px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: #e9f2ff; color: #0b5cad; }
QMenu { background: #ffffff; border: 1px solid #cfd6df; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 10px; border-radius: 4px; }
QMenu::item:selected { background: #e9f2ff; color: #0b5cad; }
QPushButton { background: #ffffff; border: 1px solid #c5ccd6; border-radius: 5px; padding: 5px 11px; min-height: 22px; }
QPushButton:hover { border-color: #3a82d4; background: #f2f7fd; }
QPushButton:pressed { background: #e5f0fb; }
QPushButton:disabled { color: #9aa2ad; background: #eceff3; border-color: #d8dde4; }
QLineEdit, QPlainTextEdit, QTextBrowser, QSpinBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #c9d0d9; border-radius: 4px; padding: 3px; selection-background-color: #2f7fd1; }
QTableWidget { background: #ffffff; alternate-background-color: #f7f9fc; gridline-color: #dfe4eb; border: 1px solid #cfd6df; }
QHeaderView::section { background: #eef2f7; border: 0; border-right: 1px solid #d8dee7; border-bottom: 1px solid #cfd6df; padding: 6px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #ccd3dc; background: #ffffff; }
QTabBar::tab { background: #e9edf3; padding: 7px 14px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; }
QTabBar::tab:selected { background: #ffffff; color: #0b5cad; }
QGroupBox { font-weight: 600; border: 1px solid #d1d7df; border-radius: 6px; margin-top: 10px; padding-top: 8px; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QGroupBox#sectionStructures { border: 2px solid #7fb3e6; background: #f7fbff; }
QGroupBox#sectionTrajectory { border: 2px solid #8dc8a4; background: #f7fcf9; }
QGroupBox#sectionDetails { border: 2px solid #d9b47c; background: #fffaf3; }
QGroupBox#sectionResults { border: 2px solid #9a9fd0; background: #fafaff; }
QGroupBox#sectionStructures::title { color: #185f9b; }
QGroupBox#sectionTrajectory::title { color: #247a46; }
QGroupBox#sectionDetails::title { color: #9a5e12; }
QGroupBox#sectionResults::title { color: #4e4f9c; }
QStatusBar { background: #ffffff; border-top: 1px solid #d9dee7; }
"""

_CHEMAUTO_DARK_QSS = r"""
QMainWindow, QDialog { background: #20242b; color: #e7eaf0; }
QMenuBar { background: #262b33; color: #e7eaf0; border-bottom: 1px solid #3a414c; padding: 2px; }
QMenuBar::item { padding: 6px 10px; border-radius: 4px; }
QMenuBar::item:selected { background: #34455c; color: #ffffff; }
QMenu { background: #282e37; color: #e7eaf0; border: 1px solid #49515d; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 10px; border-radius: 4px; }
QMenu::item:selected { background: #38577d; }
QPushButton { background: #303741; color: #f3f5f8; border: 1px solid #56606d; border-radius: 5px; padding: 5px 11px; min-height: 22px; }
QPushButton:hover { border-color: #68a7e8; background: #394451; }
QPushButton:pressed { background: #263a50; }
QPushButton:disabled { color: #7e8793; background: #282d34; border-color: #3c434d; }
QLineEdit, QPlainTextEdit, QTextBrowser, QSpinBox, QDoubleSpinBox, QComboBox { background: #171b20; color: #eef1f5; border: 1px solid #4a535f; border-radius: 4px; padding: 3px; selection-background-color: #2f7fd1; }
QTableWidget { background: #171b20; color: #eef1f5; alternate-background-color: #20262d; gridline-color: #3b434d; border: 1px solid #4a535f; }
QHeaderView::section { background: #2b3139; color: #f2f4f7; border: 0; border-right: 1px solid #414954; border-bottom: 1px solid #4a535f; padding: 6px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #4a535f; background: #20242b; }
QTabBar::tab { background: #303741; color: #d9dde3; padding: 7px 14px; margin-right: 2px; }
QTabBar::tab:selected { background: #20242b; color: #7eb8f0; }
QGroupBox { font-weight: 600; border: 1px solid #4a535f; border-radius: 6px; margin-top: 10px; padding-top: 8px; background: #242930; color: #eef1f5; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QGroupBox#sectionStructures { border: 2px solid #4778a8; background: #222a33; }
QGroupBox#sectionTrajectory { border: 2px solid #4f8866; background: #222b27; }
QGroupBox#sectionDetails { border: 2px solid #9b7544; background: #2b2822; }
QGroupBox#sectionResults { border: 2px solid #666ba1; background: #252631; }
QGroupBox#sectionStructures::title { color: #86bdf0; }
QGroupBox#sectionTrajectory::title { color: #82c99d; }
QGroupBox#sectionDetails::title { color: #dfb473; }
QGroupBox#sectionResults::title { color: #a9ace4; }
QLabel { color: #e7eaf0; }
QStatusBar { background: #262b33; border-top: 1px solid #3a414c; }
QToolTip { background: #111418; color: #ffffff; border: 1px solid #5c6673; }
"""

# -----------------------
# Optional: 3D viewer deps
# -----------------------
HAS_PG = False
try:
    import numpy as np
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    HAS_PG = True
except Exception:
    HAS_PG = False
    np = None
    pg = None
    gl = None

# -----------------------
# Parsing utilities
# -----------------------
PAT_SYM   = re.compile(r'P\s*G\s*=\s*([^=\[]*)\s*\[', re.M)
PAT_STATE = re.compile(r'S\s*t\s*a\s*t\s*e\s*=\s*([^=\\]*)\s*\\', re.M)
PAT_HF    = re.compile(r'H\s*F\s*=\s*([^=\\]*)\s*\\', re.M)
PAT_ZPE   = re.compile(r'Zero-point correction=\s*([^=\(]*)\s*\(', re.M)
PAT_ETOT  = re.compile(r'Sum of electronic and zero-point Energies=\s*([^=\s]*)\n', re.M)
PAT_SCF   = re.compile(r'SCF Done:\s+E\([^)]+\)\s*=\s*(-?\d+\.\d+)', re.M)
# Gaussian's "Error termination via ... lNNNN.exe" line — captures the link
# number (e.g. "9999") so the status panel can break errors down by Lcode.
PAT_ERROR = re.compile(r'Error termination .*\bl(\d+)\.exe', re.I)
PAT_NIMAG2 = re.compile(r'N\s*I\s*m\s*a\s*g\s*=\s*([^=\\]*)\\', re.M)

NUM_TOKEN = re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[DEde][-+]?\d+)?')

SYMMAP = {
    "C01": "C1", "CS": "Cs", "C02": "C2", "C02V": "C2v", "C02H": "C2h",
    "C03V": "C3v", "D02H": "D2h", "D03H": "D3h", "C04V": "C4v",
    "D02D": "D2d", "D*H": "Dinfh", "C*H": "Cinfh",
}

RE_TABLE = re.compile(r'^\s*Item\s+Value\s+Threshold\s+Converged\?\s*$', re.I)
RE_ROW = re.compile(
    r'^\s*(Maximum Force|RMS\s+Force|Maximum Displacement|RMS\s+Displacement)\s+'
    r'([-0-9.DEdE+]+)\s+([-0-9.DEdE+]+)\s+(YES|NO)\s*$',
    re.I
)
RE_OPT_DONE_1 = re.compile(r'^\s*Optimization completed\.\s*$', re.I)
RE_OPT_DONE_2 = re.compile(r'^\s*--\s*Stationary point found\.\s*$', re.I)
RE_ROUTE = re.compile(r'^\s*#', re.I)

STABLE_PHRASE = "The wavefunction is stable under the perturbations considered"
UNSTABLE_PHRASES = (
    "The wavefunction has an internal instability",
    "The wavefunction has an RHF - UHF instability",
)

SO_START = re.compile(r'^\s*Standard orientation:\s*$', re.I)
SO_DASH = re.compile(r'^\s*-{10,}\s*$')

Z2SYM = {
    1:"H",6:"C",7:"N",8:"O",9:"F",14:"Si",15:"P",16:"S",17:"Cl",
    26:"Fe",27:"Co",28:"Ni",29:"Cu",30:"Zn",35:"Br",51:"Sb",53:"I",
}

def last_match(pattern: re.Pattern, text: str) -> Optional[str]:
    ms = list(pattern.finditer(text))
    return ms[-1].group(1) if ms else None

def first_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    s2 = s.replace('D', 'E').replace('d', 'E')
    toks = NUM_TOKEN.findall(s2)
    if not toks:
        return None
    try:
        return float(toks[0].replace('D', 'E').replace('d', 'E'))
    except Exception:
        return None

def normalize_sym(sym_raw: str) -> str:
    key = sym_raw.replace(" ", "").replace("\n", "").replace("\r", "").upper()
    return SYMMAP.get(key, sym_raw.strip())

def count_imag_from_freq(lines: List[str]) -> int:
    neg = 0
    for l in lines:
        if "Frequencies --" in l:
            nums = re.findall(r'[-+]?\d+\.\d+', l)
            for x in nums:
                try:
                    if float(x) < 0:
                        neg += 1
                except Exception:
                    pass
    return neg

def extract_standard_orientation_xyz(text: str) -> Tuple[Optional[str], Optional[str]]:
    lines = text.splitlines()
    blocks: List[Tuple[List[str], List[Tuple[float,float,float]]]] = []

    i = 0
    while i < len(lines):
        if SO_START.match(lines[i].strip()):
            j = i + 1
            dash_count = 0
            while j < len(lines) and dash_count < 2:
                if SO_DASH.match(lines[j].strip()):
                    dash_count += 1
                j += 1
            if dash_count < 2:
                i += 1
                continue

            syms: List[str] = []
            coords: List[Tuple[float,float,float]] = []
            while j < len(lines):
                if SO_DASH.match(lines[j].strip()):
                    break
                parts = lines[j].split()
                if len(parts) >= 6:
                    try:
                        z = int(parts[1])
                        x = float(parts[3])
                        y = float(parts[4])
                        zz = float(parts[5])
                        syms.append(Z2SYM.get(z, str(z)))
                        coords.append((x,y,zz))
                    except Exception:
                        pass
                j += 1
            if syms and coords:
                blocks.append((syms, coords))
            i = j + 1
            continue
        i += 1

    if not blocks:
        return (None, None)

    def to_xyz(syms: List[str], coords: List[Tuple[float,float,float]], comment: str) -> str:
        out = [str(len(syms)), comment]
        for sym, (x,y,z) in zip(syms, coords):
            out.append(f"{sym:2s}  {x: .8f}  {y: .8f}  {z: .8f}")
        return "\n".join(out) + "\n"

    init_xyz = to_xyz(blocks[0][0], blocks[0][1], "init (first Standard orientation)")
    opt_xyz  = to_xyz(blocks[-1][0], blocks[-1][1], "opt (last Standard orientation)")
    return (init_xyz, opt_xyz)

@lru_cache(maxsize=32)
def parse_full_frames(path: str) -> List[str]:
    """Extract every Standard Orientation frame from a Gaussian .log.

    Returns one XYZ string per optimization step (empty list on failure).
    Lazy: callers should only invoke when the user actually wants the
    trajectory, not on bulk import. LRU-cached by path so revisiting a
    recently-clicked row hits memory instead of re-reading the file.

    NOTE: duplicates the per-frame parse loop in
    `extract_standard_orientation_xyz`; both should converge into a shared
    helper in a future cleanup (see MODERNIZATION-CANDIDATES.md).
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    lines = text.splitlines()
    frames: List[str] = []

    i = 0
    n = len(lines)
    while i < n:
        if not SO_START.match(lines[i].strip()):
            i += 1
            continue
        # Skip the two dash separators around the column-header block.
        j = i + 1
        dash_count = 0
        while j < n and dash_count < 2:
            if SO_DASH.match(lines[j].strip()):
                dash_count += 1
            j += 1
        if dash_count < 2:
            i += 1
            continue
        syms: List[str] = []
        coords: List[Tuple[float, float, float]] = []
        while j < n and not SO_DASH.match(lines[j].strip()):
            parts = lines[j].split()
            if len(parts) >= 6:
                try:
                    z = int(parts[1])
                    x = float(parts[3])
                    y = float(parts[4])
                    zz = float(parts[5])
                    syms.append(Z2SYM.get(z, str(z)))
                    coords.append((x, y, zz))
                except Exception:
                    pass
            j += 1
        if syms:
            out = [str(len(syms)), f"frame {len(frames) + 1}"]
            for sym, (x, y, z) in zip(syms, coords):
                out.append(f"{sym:2s}  {x: .8f}  {y: .8f}  {z: .8f}")
            frames.append("\n".join(out) + "\n")
        i = j + 1

    return frames

# -----------------------
# Visual settings (radii/colors)
# -----------------------
def _hex_to_rgba255(h: str, a255: int = 255) -> Tuple[int,int,int,int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c+c for c in h])
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (r,g,b,a255)

_VIS_R: Dict[str, float] = {
    "H":0.22, "C":0.30, "N":0.30, "O":0.30, "F":0.30,
    "P":0.36, "S":0.36, "Cl":0.38, "Si":0.40,
    "Fe":0.55, "Co":0.55, "Ni":0.55, "Cu":0.55, "Zn":0.55,
    "Br":0.45, "I":0.50, "Sb":0.55,
}
_COV_R: Dict[str, float] = {
    "H":0.31, "C":0.76, "N":0.71, "O":0.66, "F":0.57,
    "P":1.07, "S":1.05, "Cl":1.02, "Si":1.11,
    "Fe":1.24, "Co":1.18, "Ni":1.17, "Cu":1.22, "Zn":1.20,
    "Br":1.20, "I":1.39, "Sb":1.39,
}

# Default colors (RGBA 0-255)
DEFAULT_ELEM_COLOR_255: Dict[str, Tuple[int,int,int,int]] = {
    "H": _hex_to_rgba255("#FFFFFF"),
    "C": _hex_to_rgba255("#7A7A7A"),
    "N": _hex_to_rgba255("#3050F8"),
    "O": _hex_to_rgba255("#FF0D0D"),
    "F": _hex_to_rgba255("#90E050"),
    "P": _hex_to_rgba255("#FF8000"),
    "S": _hex_to_rgba255("#FFFF30"),
    "Cl": _hex_to_rgba255("#1FF01F"),
    "Si": _hex_to_rgba255("#F0C8A0"),
    "Fe": _hex_to_rgba255("#D94A3A"),
    "Co": _hex_to_rgba255("#FF66CC"),
    "Ni": _hex_to_rgba255("#50D050"),
    "Cu": _hex_to_rgba255("#C88033"),
    "Zn": _hex_to_rgba255("#7D80B0"),
    "Br": _hex_to_rgba255("#A62929"),
    "I": _hex_to_rgba255("#940094"),
    "Sb": _hex_to_rgba255("#7A68A6"),
}

# Current editable colors (start from default)
ELEM_COLOR_255: Dict[str, Tuple[int,int,int,int]] = dict(DEFAULT_ELEM_COLOR_255)

def _rgba255_to_f01(rgba255: Tuple[int,int,int,int]) -> Tuple[float,float,float,float]:
    r,g,b,a = rgba255
    return (r/255.0, g/255.0, b/255.0, a/255.0)

def _parse_xyz_text(xyz: str) -> Optional[Tuple[List[str], List[Tuple[float,float,float]]]]:
    try:
        ls = [l.strip() for l in xyz.splitlines() if l.strip() != ""]
        if len(ls) < 3:
            return None
        n = int(ls[0])
        body = ls[2:2+n]
        if len(body) < n:
            return None
        syms: List[str] = []
        coords: List[Tuple[float,float,float]] = []
        for line in body:
            p = line.split()
            if len(p) < 4:
                continue
            sym = p[0]
            x,y,z = float(p[1]), float(p[2]), float(p[3])
            syms.append(sym)
            coords.append((x,y,z))
        if len(syms) != n:
            return None
        return (syms, coords)
    except Exception:
        return None

# -----------------------
# Convergence data
# -----------------------
@dataclass
class ConvergenceTable:
    max_force: Optional[str] = None
    rms_force: Optional[str] = None
    max_disp: Optional[str] = None
    rms_disp: Optional[str] = None
    all_yes: Optional[bool] = None

    def to_compact(self) -> str:
        if None in (self.max_force, self.rms_force, self.max_disp, self.rms_disp):
            return ""
        return f"F({self.max_force}/{self.rms_force}) D({self.max_disp}/{self.rms_disp})"

@dataclass
class LogSummary:
    path: str
    file: str
    cluster: Optional[str] = None
    sym: Optional[str] = None
    state: Optional[str] = None
    hf: Optional[float] = None
    zpe: Optional[float] = None
    etot: Optional[float] = None
    nimag: Optional[int] = None
    freq_completed: Optional[bool] = None
    stable_1: Optional[str] = None
    stable_2: Optional[str] = None
    opt_conv: Optional[ConvergenceTable] = None
    freq_conv: Optional[ConvergenceTable] = None
    init_xyz: Optional[str] = None
    opt_xyz: Optional[str] = None
    # SCF energies harvested at parse time (one entry per "SCF Done:" line).
    # Cheap to compute, so kept on the eager path with the rest of the row.
    scf_energies: List[float] = field(default_factory=list)
    # Full optimization trajectory, populated lazily on first row selection
    # via `parse_full_frames(path)`. None == not yet attempted; an empty list
    # means we tried and found nothing (SP job or unparseable log).
    frames: Optional[List[str]] = None
    # Gaussian Lcode of the failing link if the run errored out (e.g.
    # "L9999"); None for normal terminations. Drives the status panel
    # error breakdown.
    error_link: Optional[str] = None

def parse_conv_table(lines: List[str], start_i: int) -> ConvergenceTable:
    got: Dict[str, str] = {}
    i = start_i + 1
    while i < len(lines) and len(got) < 4:
        m = RE_ROW.match(lines[i])
        if m:
            label = re.sub(r'\s+', ' ', m.group(1)).strip().title()
            if "Maximum Force" in label:
                got["Maximum Force"] = m.group(4).upper()
            elif "Rms" in label and "Force" in label:
                got["RMS Force"] = m.group(4).upper()
            elif "Maximum Displacement" in label:
                got["Maximum Displacement"] = m.group(4).upper()
            elif "Rms" in label and "Displacement" in label:
                got["RMS Displacement"] = m.group(4).upper()
        i += 1

    ct = ConvergenceTable(
        max_force=got.get("Maximum Force"),
        rms_force=got.get("RMS Force"),
        max_disp=got.get("Maximum Displacement"),
        rms_disp=got.get("RMS Displacement"),
    )
    if None not in (ct.max_force, ct.rms_force, ct.max_disp, ct.rms_disp):
        ct.all_yes = all(x == "YES" for x in (ct.max_force, ct.rms_force, ct.max_disp, ct.rms_disp))
    return ct

def parse_gaussian_log(path: str) -> LogSummary:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = p.read_text(errors="ignore")
    lines = text.splitlines()

    s = LogSummary(path=str(p), file=p.name)
    sto = re.findall(r'Stoichiometry\s+([A-Za-z0-9]+)', text)
    s.cluster = sto[-1] if sto else p.stem

    sym_raw = last_match(PAT_SYM, text)
    if sym_raw:
        s.sym = normalize_sym(sym_raw)

    st = last_match(PAT_STATE, text)
    s.state = st.replace(" ", "").replace("\n", "").replace("\r", "") if st else None

    s.hf = first_float(last_match(PAT_HF, text))
    s.zpe = first_float(last_match(PAT_ZPE, text))
    s.etot = first_float(last_match(PAT_ETOT, text))

    nim_raw = last_match(PAT_NIMAG2, text)
    if nim_raw is not None:
        try:
            s.nimag = int(float(nim_raw.strip()))
        except Exception:
            s.nimag = None
    else:
        s.nimag = count_imag_from_freq(lines)

    s.freq_completed = bool(re.search(r'^\s*Harmonic frequencies', text, re.M))

    results: List[str] = []
    for l in lines:
        if STABLE_PHRASE in l:
            results.append("stable")
        elif any(u in l for u in UNSTABLE_PHRASES):
            results.append("unstable")
    if len(results) >= 1:
        s.stable_1 = results[0]
    if len(results) >= 2:
        s.stable_2 = results[1]

    opt_conv: Optional[ConvergenceTable] = None
    freq_pending = False
    freq_conv: Optional[ConvergenceTable] = None

    for i, l in enumerate(lines):
        if RE_ROUTE.match(l):
            if re.search(r'\bFREQ\b', l, re.I) and not re.search(r'\bOPT\b', l, re.I):
                freq_pending = True

        if RE_TABLE.match(l):
            ct = parse_conv_table(lines, i)
            look = lines[i:min(i + 80, len(lines))]

            if freq_pending and freq_conv is None:
                freq_conv = ct
                freq_pending = False
                continue

            if any(RE_OPT_DONE_1.match(x) for x in look) or any(RE_OPT_DONE_2.match(x) for x in look):
                opt_conv = ct

    s.opt_conv = opt_conv
    s.freq_conv = freq_conv

    try:
        init_xyz, opt_xyz = extract_standard_orientation_xyz(text)
        s.init_xyz = init_xyz
        s.opt_xyz = opt_xyz
    except Exception:
        s.init_xyz = None
        s.opt_xyz = None

    try:
        s.scf_energies = [float(m) for m in PAT_SCF.findall(text)]
    except Exception:
        s.scf_energies = []

    m = PAT_ERROR.search(text)
    s.error_link = f"L{m.group(1)}" if m else None

    return s

# ---------------------------------------------------------------------------
# v6.1 core parser binding
# ---------------------------------------------------------------------------
# Keep the legacy parsing helpers above as a readable compatibility reference,
# but use the UI-independent, regression-tested parser for all real GUI work.
# This avoids importing PyQt in parser tests and gives CLI/GUI a shared data
# model without rewriting the viewer layer.
from chemauto.core.gaussian_parser import (
    ConvergenceTable as CoreConvergenceTable,
    LogSummary as CoreLogSummary,
    parse_gaussian_log as core_parse_gaussian_log,
    minimum_etot,
    delta_e_ev,
)
ConvergenceTable = CoreConvergenceTable
LogSummary = CoreLogSummary
parse_gaussian_log = core_parse_gaussian_log

from chemauto.core.record_sorting import sort_records
from chemauto.core.related_files import RelatedFiles, resolve_related_files
from chemauto.core.external_open import open_external, can_open_related
from chemauto.core.gjf_stability import ChemAutoGJFHandler, read_text_safely
from chemauto.core.fchk_xyz import convert_one as convert_fchk_to_xyz
from chemauto.core.remote_formchk import (
    get_active_profile_name, launch_remote_conversion, load_profiles,
)

# -----------------------
# Background log loading
# -----------------------
class LogLoadWorker(QObject):
    parsed = pyqtSignal(object)
    progress = pyqtSignal(int, int, str)
    failed = pyqtSignal(str, str)
    finished = pyqtSignal(int, int)

    def __init__(self, files: List[str]):
        super().__init__()
        self.files = files
        self._cancelled = False

    @pyqtSlot()
    def run(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        try:
            from chemauto.infra.config import load_user_config
            workers = int(load_user_config().get("log_parse_workers", 4))
        except Exception:
            workers = 4
        workers = max(1, min(workers, 16, len(self.files) or 1))
        total = len(self.files)
        good = bad = 0
        ordered: List[Optional[LogSummary]] = [None] * total
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="chemauto-log") as pool:
            futures = {pool.submit(parse_gaussian_log, fp): (idx, fp) for idx, fp in enumerate(self.files)}
            completed = 0
            for fut in as_completed(futures):
                idx, fp = futures[fut]
                if self._cancelled:
                    for pending in futures: pending.cancel()
                    break
                try:
                    ordered[idx] = fut.result()
                    good += 1
                except Exception as exc:
                    self.failed.emit(fp, str(exc))
                    bad += 1
                completed += 1
                self.progress.emit(completed, total, os.path.basename(fp))
        # Emit in the original load order, so parallel parsing never makes the
        # table order nondeterministic.
        for summary in ordered:
            if summary is not None:
                self.parsed.emit(summary)
        self.finished.emit(good, bad)

    @pyqtSlot()
    def cancel(self):
        self._cancelled = True

# -----------------------
# Sorting helpers
# -----------------------
class NumericItem(QTableWidgetItem):
    def __init__(self, text: str = "", value: Optional[float] = None):
        super().__init__(text)
        self._value = value

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            a, b = self._value, other._value
        else:
            a = self._value
            try:
                b = float(other.text())
            except Exception:
                b = None
        if a is None and b is None:
            return super().__lt__(other)
        if a is None:
            return False
        if b is None:
            return True
        return a < b

def open_in_file_manager(path: str):
    p = Path(path).resolve()
    folder = str(p.parent) if p.is_file() else str(p)
    try:
        system = platform.system().lower()
        if system.startswith("windows"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif system == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception:
        pass

# -----------------------
# Excel export
# -----------------------

def export_excel_xlsx(out_path: str, summaries: Sequence[LogSummary], base_etot: Optional[float] = None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    headers = [
        "", "Cluster", "Sym.", "State",
        "HF", "ZPE", "Etot", "ΔE",
        "NImag", "Freq Done",
        "Opt Conv.", "Freq Conv.",
        "Stable1", "Stable2"
    ]
    ws.append(headers)

    header_font = Font(name="Times New Roman", size=14, bold=True)
    body_font = Font(name="Times New Roman", size=12, bold=False)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    body_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.alignment = header_align

    if base_etot is None:
        base_etot = minimum_etot(list(summaries))

    for s in summaries:
        de = delta_e_ev(s, base_etot)
        ws.append([
            "",
            s.file, s.sym, s.state,
            s.hf, s.zpe, s.etot, de,
            s.nimag,
            s.freq_completed,
            s.opt_conv.to_compact() if s.opt_conv else "",
            s.freq_conv.to_compact() if s.freq_conv else "",
            s.stable_1, s.stable_2
        ])

    for r in range(2, ws.max_row + 1):
        for c in range(1, len(headers) + 1):
            ws.cell(r, c).font = body_font
            ws.cell(r, c).alignment = body_align

    # number formats — column indices reflect the 14-cell layout:
    # spacer=1, Cluster=2, Sym.=3, State=4, HF=5, ZPE=6, Etot=7, ΔE=8.
    for r in range(2, ws.max_row + 1):
        for c in (5, 6, 7):
            ws.cell(r, c).number_format = "0.00000000"
        ws.cell(r, 8).number_format = "0.000000"

    widths = [3, 28, 8, 10, 16, 12, 16, 12, 8, 10, 20, 20, 10, 10]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    wb.save(out_path)

# -----------------------
# 3D Viewer

# -----------------------
class ViewerSettings:
    def __init__(self):
        # Default WHITE background (always)
        self.bg_color = (255, 255, 255, 255)  # RGBA 0-255
        self.show_grid = False
        self.show_axis = False
        self.atom_scale = 1.0
        self.bond_width = 2.5
        self.bond_color = (50, 50, 50, 255)   # dark gray
        self.bond_scale = 1.25
        self.max_bond = 3.0

class StructureViewer(QWidget):
    def __init__(self, title: str, parent=None, xyz_kind: str = ""):
        super().__init__(parent)
        self._title = title
        self._xyz_kind = xyz_kind
        self._cluster_name: Optional[str] = None
        self._has_pg = HAS_PG
        self._xyz_cache: Optional[str] = None
        self.settings = ViewerSettings()

        lay = QVBoxLayout()
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        title_row = QHBoxLayout()
        # Static caption ("Init Struc" / "Opt Struc"). The dynamic frame
        # indicator now lives in `frame_label` below, so the title can stay
        # at its natural size — no width pin or shake-prevention tricks needed.
        self.title_label = QLabel(title)
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        self.title_label.setFont(f)
        self.title_label.setMinimumWidth(95)
        self.title_label.setMaximumWidth(95)
        self.title_label.setSizePolicy(SP_PREFERRED, SP_PREFERRED)
        title_row.addWidget(self.title_label)
        # Frame indicator slot. Init viewer leaves it empty; Opt viewer fills
        # it with "FINAL" / "N/M" while the trajectory slider moves so the
        # static title above can stay put across frame changes.
        self.frame_label = QLabel("")
        self.frame_label.setFont(f)
        self.frame_label.setMinimumWidth(64)
        self.frame_label.setMaximumWidth(64)
        self.frame_label.setSizePolicy(SP_PREFERRED, SP_PREFERRED)
        title_row.addWidget(self.frame_label)
        title_row.addStretch(1)
        # Plain text only. The old emoji icon rendered inconsistently and wasted space.
        self.btn_export = QPushButton("Export")
        self.btn_export.setFixedWidth(58)
        self.btn_export.setToolTip("Export XYZ")
        self.btn_export.clicked.connect(self._on_export)
        title_row.addWidget(self.btn_export)
        lay.addLayout(title_row)

        if not self._has_pg:
            ph = QLabel("3D viewer not available\nInstall: pyqtgraph PyOpenGL numpy")
            ph.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter if QT_LIB == "PyQt6" else Qt.AlignCenter)
            lay.addWidget(ph, 1)
            self.setLayout(lay)
            return

        pg.setConfigOptions(antialias=True)

        self.view = gl.GLViewWidget()
        self.view.setSizePolicy(SP_EXPANDING, SP_EXPANDING)
        # Orthographic-like projection: pyqtgraph 0.14 has no native ortho
        # mode, so we shrink fov to ~1° and scale camera distance ~60× to
        # match. Atom sizes then stay constant under rotation, matching the
        # convention of GaussView / VESTA / Avogadro / ChemCraft. See the
        # v6.0 经验记 entry in docs/MODERNIZATION-CANDIDATES.md.
        self.view.opts["fov"] = 1.0
        # Initial placeholder distance — overwritten by set_xyz() once a
        # molecule lands. 700 ≈ a typical small-cluster ortho distance.
        self.view.opts["distance"] = 700

        # Background: must use mkColor
        self._apply_bg()

        self._grid = gl.GLGridItem()
        self._grid.scale(2, 2, 1)
        self.view.addItem(self._grid)

        # Custom axis lines (so we can switch black/white depending on background)
        self._axis_items: List[Any] = []
        self._axis_size = 2.0
        self._build_axis()

        self._atom_items: List[Any] = []
        self._bond_item: Optional[Any] = None
        self._sphere_cache: Dict[float, Any] = {}

        lay.addWidget(self.view, 1)
        self.setLayout(lay)
        self.apply_settings()

    def _apply_bg(self):
        if not self._has_pg:
            return
        r, g, b, a = self.settings.bg_color
        try:
            self.view.setBackgroundColor(pg.mkColor(r, g, b, a))
        except Exception:
            # Fallback: some versions use opts["bgcolor"]
            try:
                self.view.opts["bgcolor"] = (r, g, b, a)
            except Exception:
                pass

    def _axis_rgba(self) -> Tuple[int,int,int,int]:
        # Kept for backwards-compatible callers. Individual X/Y/Z axes are
        # now rendered red/green/blue, the convention used by molecular viewers.
        return (0, 0, 0, 255)

    def _clear_axis(self):
        if not self._has_pg:
            return
        for it in getattr(self, "_axis_items", []):
            try:
                self.view.removeItem(it)
            except Exception:
                pass
        self._axis_items = []

    def _build_axis(self):
        if not self._has_pg:
            return
        self._clear_axis()
        s = float(getattr(self, "_axis_size", 2.0))
        # Conventional molecular-viewer colours: X red, Y green, Z blue.
        lines = [
            (np.array([[0,0,0],[s,0,0]], dtype=np.float32), (1.0, 0.15, 0.15, 1.0)),
            (np.array([[0,0,0],[0,s,0]], dtype=np.float32), (0.15, 0.75, 0.20, 1.0)),
            (np.array([[0,0,0],[0,0,s]], dtype=np.float32), (0.15, 0.35, 1.0, 1.0)),
        ]
        for seg, col in lines:
            it = gl.GLLinePlotItem(pos=seg, mode="lines", width=2.0, color=col, antialias=True)
            self.view.addItem(it)
            self._axis_items.append(it)

    def _update_axis_color(self):
        # simplest: rebuild axis lines when background changes
        try:
            self._build_axis()
        except Exception:
            pass

    def apply_settings(self):
        if not self._has_pg:
            return
        self._apply_bg()
        try:
            self._grid.setVisible(bool(self.settings.show_grid))
        except Exception:
            pass

        # axis visibility + color adapt to background
        self._update_axis_color()
        for it in getattr(self, "_axis_items", []):
            try:
                it.setVisible(bool(self.settings.show_axis))
            except Exception:
                pass

    def force_redraw(self):
        """Bypass xyz cache and redraw current structure."""
        if not self._has_pg:
            return
        xyz = self._xyz_cache
        self._xyz_cache = None
        self.set_xyz(xyz)

    def _get_sphere_mesh(self, radius: float):
        if radius in self._sphere_cache:
            return self._sphere_cache[radius]
        md = gl.MeshData.sphere(rows=18, cols=18, radius=radius)
        self._sphere_cache[radius] = md
        return md

    def clear(self):
        self._xyz_cache = None
        if not self._has_pg:
            return
        for it in self._atom_items:
            try:
                self.view.removeItem(it)
            except Exception:
                pass
        self._atom_items = []
        if self._bond_item is not None:
            try:
                self.view.removeItem(self._bond_item)
            except Exception:
                pass
            self._bond_item = None

    def _guess_bonds(self, syms: List[str], pts: "np.ndarray") -> List[Tuple[int, int]]:
        scale = float(self.settings.bond_scale)
        max_bond = float(self.settings.max_bond)
        n = len(syms)
        bonds: List[Tuple[int, int]] = []
        for i in range(n):
            ri = _COV_R.get(syms[i], 0.77)
            for j in range(i + 1, n):
                rj = _COV_R.get(syms[j], 0.77)
                thr = min(scale * (ri + rj), max_bond)
                d = float(np.linalg.norm(pts[i] - pts[j]))
                if d > 0.1 and d <= thr:
                    bonds.append((i, j))
        return bonds

    def set_xyz(self, xyz: Optional[str]):
        if not self._has_pg:
            # still cache the xyz so the export button can save it
            self._xyz_cache = xyz if (xyz and xyz.strip()) else None
            return
        if xyz is None or xyz.strip() == "":
            self.clear()
            return
        if xyz == self._xyz_cache:
            return
        self._xyz_cache = xyz

        parsed = _parse_xyz_text(xyz)
        if not parsed:
            self.clear()
            return

        syms, coords = parsed
        pts = np.array(coords, dtype=np.float32)
        center = pts.mean(axis=0)
        pts = pts - center

        # remove old
        for it in self._atom_items:
            try:
                self.view.removeItem(it)
            except Exception:
                pass
        self._atom_items = []
        if self._bond_item is not None:
            try:
                self.view.removeItem(self._bond_item)
            except Exception:
                pass
            self._bond_item = None

        # bonds
        bonds = self._guess_bonds(syms, pts)
        if bonds:
            seg = []
            for i, j in bonds:
                seg.append(pts[i])
                seg.append(pts[j])
            seg = np.array(seg, dtype=np.float32)
            br, bg, bb, ba = self.settings.bond_color
            self._bond_item = gl.GLLinePlotItem(
                pos=seg, mode="lines",
                width=float(self.settings.bond_width),
                color=(br/255.0, bg/255.0, bb/255.0, ba/255.0),
                antialias=True
            )
            self.view.addItem(self._bond_item)

        # atoms
        for sym, p in zip(syms, pts):
            rgba255 = ELEM_COLOR_255.get(sym, (200, 200, 200, 255))
            col = _rgba255_to_f01(rgba255)
            base_r = _VIS_R.get(sym, 0.35)
            rad = float(base_r) * float(self.settings.atom_scale)
            md = self._get_sphere_mesh(rad)
            item = gl.GLMeshItem(meshdata=md, smooth=True, color=col, shader="shaded", drawEdges=False)
            item.translate(float(p[0]), float(p[1]), float(p[2]))
            self.view.addItem(item)
            self._atom_items.append(item)

        r = float(np.max(np.linalg.norm(pts, axis=1))) if len(pts) else 10.0
        # Orthographic-like camera (fov=1° set in __init__). Distance
        # multiplier ~185 makes the molecule fill ~2/3 of the viewport.
        # All values are scaled ~60× from the equivalent perspective
        # formula because tan(30°)/tan(0.5°) ≈ 66.
        self.view.opts["distance"] = max(330.0, min(8000.0, r * 185.0))

    def set_cluster_name(self, name: Optional[str]):
        self._cluster_name = name

    def _on_export(self):
        xyz = self._xyz_cache
        if not xyz:
            QMessageBox.information(self, "Export", "No structure available to export.")
            return
        cluster = self._cluster_name or "cluster"
        suffix = self._xyz_kind or "structure"
        default_name = f"{cluster}_{suffix}.xyz"
        out, _ = QFileDialog.getSaveFileName(self, "Export XYZ", default_name, "XYZ (*.xyz)")
        if not out:
            return
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(xyz)
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Failed to save:\n{e}")
            return
        QMessageBox.information(self, "Exported", f"XYZ saved:\n{out}")

# -----------------------
# Colors dialog
# -----------------------
class ColorsDialog(QDialog):
    def __init__(self, parent=None, on_changed=None):
        super().__init__(parent)
        self.setWindowTitle("Element Colors")
        self.resize(420, 520)
        self.on_changed = on_changed

        lay = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Element", "Color", "Hex"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        try:
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        btn_row = QHBoxLayout()
        btn_pick = QPushButton("Pick Color…")
        btn_reset = QPushButton("Reset Defaults")
        btn_close = QPushButton("Close")
        btn_row.addWidget(btn_pick)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_close)

        btn_pick.clicked.connect(self.pick_color_for_selected)
        btn_reset.clicked.connect(self.reset_defaults)
        btn_close.clicked.connect(self.accept)

        lay.addWidget(QLabel("Select an element row, then click 'Pick Color…'"))
        lay.addWidget(self.table, 1)
        lay.addLayout(btn_row)
        self.setLayout(lay)

        self.reload()

    def reload(self):
        elems = sorted(ELEM_COLOR_255.keys())
        self.table.setRowCount(0)
        for e in elems:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(e))

            rgba = ELEM_COLOR_255[e]
            color_item = QTableWidgetItem("      ")
            color_item.setBackground(QColor(rgba[0], rgba[1], rgba[2], rgba[3]))
            self.table.setItem(r, 1, color_item)

            hexs = f"#{rgba[0]:02X}{rgba[1]:02X}{rgba[2]:02X}"
            self.table.setItem(r, 2, QTableWidgetItem(hexs))

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def selected_element(self) -> Optional[str]:
        idx = self.table.currentRow()
        if idx < 0:
            return None
        it = self.table.item(idx, 0)
        return it.text() if it else None

    def pick_color_for_selected(self):
        e = self.selected_element()
        if not e:
            return
        r,g,b,a = ELEM_COLOR_255.get(e, (200,200,200,255))
        init = QColor(r,g,b,a)
        c = QColorDialog.getColor(init, self, f"Pick color for {e}")
        if not c.isValid():
            return
        ELEM_COLOR_255[e] = (c.red(), c.green(), c.blue(), 255)
        self.reload()
        if callable(self.on_changed):
            self.on_changed()

    def reset_defaults(self):
        ELEM_COLOR_255.clear()
        ELEM_COLOR_255.update(DEFAULT_ELEM_COLOR_255)
        self.reload()
        if callable(self.on_changed):
            self.on_changed()

# -----------------------
# GUI
# -----------------------
class ClickableSlider(QSlider):
    """QSlider that seeks to the click location instead of page-stepping.

    Default Qt behaviour on a groove click is to advance by one page-step
    toward the click. For a frame scrubber the user expects a media-player
    convention: click anywhere on the groove to jump there. We compute the
    target value, set it, then defer to the base class so handle drag still
    works after the click.
    """
    def mousePressEvent(self, event):
        try:
            x = float(event.position().x())  # PyQt6
        except AttributeError:
            x = float(event.x())  # PyQt5
        if self.orientation() == ORIENT_HORIZONTAL and self.width() > 0:
            rng = self.maximum() - self.minimum()
            if rng > 0:
                new_val = self.minimum() + int(round(rng * x / self.width()))
                if new_val != self.value():
                    self.setValue(new_val)
        super().mousePressEvent(event)


class DropTable(QTableWidget):
    filesDropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp:
                paths.append(fp)
        if paths:
            self.filesDropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChemAuto 7.1.2")
        try:
            from chemauto.infra.paths import get_resource_path
            self.setWindowIcon(QIcon(str(get_resource_path("chemauto.ico"))))
        except Exception:
            pass
        self.resize(1280, 720)
        # Floor of 700px keeps the new 3-section left panel (viewers / SCF
        # plot+slider / detail fields) from collapsing when the user shrinks
        # the window vertically.
        self.setMinimumHeight(700)
        screen = QApplication.primaryScreen()
        if screen is not None:
            center = screen.availableGeometry().center()
            fg = self.frameGeometry()
            fg.moveCenter(center)
            self.move(fg.topLeft())

        self.summaries: List[LogSummary] = []
        self.last_io_dir: str = os.getcwd()
        self._load_thread = None
        self._load_worker = None
        self._load_progress = None
        self._load_results: List[LogSummary] = []
        self._load_failures: List[Tuple[str, str]] = []

        # v6.0 persisted GUI knobs: inner SCF plot theme + viewer background.
        # Read once at startup; saving happens inline whenever the user toggles
        # via menu (persist=True), so the file matches the current UI state.
        cfg = self._load_gui_config()

        self._scf_plot_theme = str(cfg.get("scf_plot_theme", "dark")).lower()
        if self._scf_plot_theme not in ("dark", "light"):
            self._scf_plot_theme = "dark"

        # Default 3D viewer background as a persisted RGBA tuple. The legacy
        # "viewer_bg" key (white/black string) is still honoured as a fallback
        # so older config files continue to work; new writes only ever go to
        # "viewer_bg_rgba".
        viewer_bg_rgba = cfg.get("viewer_bg_rgba", None)
        if isinstance(viewer_bg_rgba, (list, tuple)) and len(viewer_bg_rgba) >= 3:
            try:
                r = int(viewer_bg_rgba[0])
                g = int(viewer_bg_rgba[1])
                b = int(viewer_bg_rgba[2])
                a = int(viewer_bg_rgba[3]) if len(viewer_bg_rgba) >= 4 else 255
                self._viewer_bg_rgba = (
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)),
                    max(0, min(255, a)),
                )
            except Exception:
                self._viewer_bg_rgba = (255, 255, 255, 255)
        else:
            # Backward compatibility with older config key: viewer_bg = white/black.
            legacy_bg = str(cfg.get("viewer_bg", "white")).lower()
            if legacy_bg == "black":
                self._viewer_bg_rgba = (0, 0, 0, 255)
            else:
                self._viewer_bg_rgba = (255, 255, 255, 255)

        self._viewer_show_grid = bool(cfg.get("viewer_show_grid", False))
        self._viewer_show_axis = bool(cfg.get("viewer_show_axis", False))

        base_font = QFont()
        base_font.setPointSize(11)
        self.setFont(base_font)

        self._pending_view_row: Optional[int] = None
        self._sel_timer = QTimer(self)
        self._sel_timer.setSingleShot(True)
        self._sel_timer.timeout.connect(self._apply_pending_selection)

        self.viewer_init = StructureViewer("Init Struc", self, xyz_kind="init")
        self.viewer_opt  = StructureViewer("Opt Struc", self, xyz_kind="opt")
        for _viewer in (self.viewer_init, self.viewer_opt):
            _viewer.settings.show_grid = self._viewer_show_grid
            _viewer.settings.show_axis = self._viewer_show_axis
            _viewer.apply_settings()
        self.viewer_init.setMinimumHeight(200)
        self.viewer_opt.setMinimumHeight(200)

        viewers_box = QWidget()
        viewers_layout = QHBoxLayout()
        viewers_layout.setContentsMargins(0, 0, 0, 0)
        viewers_layout.setSpacing(8)
        viewers_layout.addWidget(self.viewer_init, 1)
        viewers_layout.addWidget(self.viewer_opt, 1)
        viewers_box.setLayout(viewers_layout)
        viewers_box.setMinimumHeight(220)
        viewers_section = QGroupBox("1. Structures")
        viewers_section.setObjectName("sectionStructures")
        viewers_section_layout = QVBoxLayout(viewers_section)
        viewers_section_layout.setContentsMargins(8, 10, 8, 8)
        viewers_section_layout.addWidget(viewers_box)

        # 8-row hybrid grid: Path/File moved to right-click menu.
        # Row 0 (tri): Cluster | Sym | State
        # Rows 1-4 (single, value spans 5 cols): HF / ZPE / Etot / ΔE
        # Rows 5-7 (dual): NImag/Freq completed | Opt/Freq conver. | Stable 1/2
        self.detail_fields: Dict[str, QLineEdit] = {}
        grid = QGridLayout()
        grid.setSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)

        def _make_le(key: str) -> QLineEdit:
            le = QLineEdit()
            le.setReadOnly(True)
            le.setMinimumHeight(24)
            self.detail_fields[key] = le
            return le

        # Row 0: dual-column (Cluster removed; Sym. + State use the same
        # 0|1-2 + 3|4-5 grid structure as the dual-pair rows below).
        grid.addWidget(QLabel("Sym."), 0, 0)
        grid.addWidget(_make_le("Sym."), 0, 1, 1, 2)
        grid.addWidget(QLabel("State"), 0, 3)
        grid.addWidget(_make_le("State"), 0, 4, 1, 2)

        # Rows 1-4: single-field. Only ΔE shows a unit tooltip ("eV") —
        # Hartree is the default assumption and needs no reminder.
        single_keys = ("HF", "ZPE", "Etot", "ΔE")
        for i, key in enumerate(single_keys, start=1):
            lbl = QLabel(key)
            if key == "ΔE":
                lbl.setToolTip("eV")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(_make_le(key), i, 1, 1, 5)

        # Rows 5-7: dual-column. Conv. labels carry tooltips explaining
        # the F/D compact format (Force/Displacement Maximum/RMS).
        dual_pairs = [
            ("NImag", "Freq Done"),
            ("Opt Conv.", "Freq Conv."),
            ("Stable1", "Stable2"),
        ]
        _CONV_TIPS = {
            "Opt Conv.": (
                "F = Force 受力收敛 (Maximum/RMS), "
                "D = Displacement 位移收敛 (Maximum/RMS)\n"
                "Gaussian 几何优化的 4 个收敛标准全部达标后才算收敛"
            ),
            "Freq Conv.": (
                "F = Force 受力收敛 (Maximum/RMS), "
                "D = Displacement 位移收敛 (Maximum/RMS)\n"
                "Gaussian 频率分析的几何收敛检查（多数情况下与 Opt Conv. 一致）"
            ),
        }
        for i, (k1, k2) in enumerate(dual_pairs):
            row = 5 + i
            lbl1 = QLabel(k1)
            lbl2 = QLabel(k2)
            if k1 in _CONV_TIPS:
                lbl1.setToolTip(_CONV_TIPS[k1])
            if k2 in _CONV_TIPS:
                lbl2.setToolTip(_CONV_TIPS[k2])
            grid.addWidget(lbl1, row, 0)
            grid.addWidget(_make_le(k1), row, 1, 1, 2)
            grid.addWidget(lbl2, row, 3)
            grid.addWidget(_make_le(k2), row, 4, 1, 2)

        detail_box = QWidget()
        detail_box.setLayout(grid)
        detail_box.setMinimumHeight(200)
        detail_section = QGroupBox("3. Calculation details")
        detail_section.setObjectName("sectionDetails")
        detail_section_layout = QVBoxLayout(detail_section)
        detail_section_layout.setContentsMargins(8, 10, 8, 8)
        detail_section_layout.addWidget(detail_box)

        # ----- SCF energy plot + trajectory slider (Task 2.5 B phase) -----
        # Polyline of "SCF Done" energies vs optimization step, with a red
        # dashed cursor showing which frame the slider is currently on.
        self.scf_plot = pg.PlotWidget()
        self.scf_plot.setLabel("bottom", "Step")
        self.scf_plot.setLabel("left", "Energy (Hartree)")
        self.scf_plot.showGrid(x=True, y=True, alpha=0.3)
        self.scf_plot.setMinimumHeight(120)
        # Close the plot frame. The intuitive showAxis('top')/showAxis('right')
        # approach is broken in pyqtgraph 0.14: axes with showValues=False
        # report thickness 0, the layout shoves them flush to the edge, and
        # PlotWidget's outer clip eats them at the pixel level. The reliable
        # workaround is to draw the rectangle on the ViewBox itself (which
        # is laid out independently of the axis stack) and just match the
        # left/bottom axis pens to its colour.
        self.scf_plot.hideAxis("top")
        self.scf_plot.hideAxis("right")
        # Origin-style two-tier background: outer PlotWidget transparent so it
        # blends with the surrounding light-grey UI (axis labels stay readable
        # on the host's palette), inner ViewBox painted black so the blue data
        # curve pops. The grey border pen still rims the data area.
        self.scf_plot.setBackground(None)
        self.scf_plot.getPlotItem().getViewBox().setBackgroundColor("k")
        _scf_border_pen = pg.mkPen(color=(150, 150, 150), width=1)
        self.scf_plot.getPlotItem().getViewBox().setBorder(_scf_border_pen)
        # Axis lines + tick text in black: the surrounding light background
        # makes the previous grey illegible.
        _scf_axis_pen = pg.mkPen(color="k", width=1)
        for _axis_name in ("left", "bottom"):
            _axis = self.scf_plot.getAxis(_axis_name)
            _axis.setPen(_scf_axis_pen)
            _axis.setTextPen("k")
        # Compact axis geometry: reduce useless outer blank while keeping label/tick readable.
        try:
            self.scf_plot.getAxis("left").setWidth(68)
            self.scf_plot.getAxis("bottom").setHeight(32)
            self.scf_plot.getAxis("left").setStyle(tickTextOffset=3)
            self.scf_plot.getAxis("bottom").setStyle(tickTextOffset=3)
        except Exception:
            pass
        # Breathing room is enforced by a QWidget shell wrapping the plot
        # below — pyqtgraph's internal margin APIs (PlotItem.setContentsMargins
        # / setDefaultPadding) are unreliable here because the inner GraphicsLayout
        # consumes them. ViewBox.setDefaultPadding stays as a small data-range
        # cushion so points never touch the rectangle.
        self.scf_plot.getPlotItem().getViewBox().setDefaultPadding(0.05)
        self.scf_curve = self.scf_plot.plot(
            [], [],
            pen=pg.mkPen("b", width=2),
            symbol="o", symbolSize=4, symbolBrush="b",
        )
        self.scf_cursor = pg.InfiniteLine(
            pos=0, angle=90,
            pen=pg.mkPen("r", width=1, style=PEN_DASH),
        )
        self.scf_cursor.setVisible(False)
        self.scf_plot.addItem(self.scf_cursor)
        # Apply persisted plot theme without rewriting the config (startup
        # path; the user toggles via menu later with persist=True).
        self._apply_scf_plot_theme(self._scf_plot_theme, persist=False)

        self.opt_slider = ClickableSlider(ORIENT_HORIZONTAL)
        self.opt_slider.setMinimum(0)
        self.opt_slider.setMaximum(0)
        self.opt_slider.setEnabled(False)
        self.opt_slider.valueChanged.connect(self._on_trajectory_frame_changed)

        # Step buttons for precise ±1 navigation when the slider is too
        # coarse — typical opt jobs have 30+ steps, dragging is imprecise.
        self.btn_prev_frame = QPushButton("◀")
        self.btn_prev_frame.setFixedWidth(28)
        self.btn_prev_frame.setToolTip("Previous frame")
        self.btn_prev_frame.setEnabled(False)
        self.btn_prev_frame.clicked.connect(
            lambda: self.opt_slider.setValue(self.opt_slider.value() - 1)
        )
        self.btn_next_frame = QPushButton("▶")
        self.btn_next_frame.setFixedWidth(28)
        self.btn_next_frame.setToolTip("Next frame")
        self.btn_next_frame.setEnabled(False)
        self.btn_next_frame.clicked.connect(
            lambda: self.opt_slider.setValue(self.opt_slider.value() + 1)
        )

        opt_slider_row = QWidget()
        slider_row_layout = QHBoxLayout(opt_slider_row)
        slider_row_layout.setContentsMargins(0, 0, 0, 0)
        slider_row_layout.setSpacing(2)
        slider_row_layout.addWidget(self.btn_prev_frame, 0)
        slider_row_layout.addWidget(self.opt_slider, 1)
        slider_row_layout.addWidget(self.btn_next_frame, 0)

        # QWidget shell that pads around the plot (the "squeeze" approach) —
        # pyqtgraph's own margin/padding APIs get swallowed by its internal
        # GraphicsLayout, so we wrap the PlotWidget in a plain Qt container
        # whose contentsMargins are enforced at the Qt layout level.
        # Left/top/right are now small safety margins only — the y-label and
        # tick numbers fit in the axis's own setWidth(68) / setHeight(32),
        # so the wrapper just keeps the data rectangle from touching the
        # outer frame. Bottom is 0 because the slider row sits flush below.
        scf_wrapper = QWidget()
        scf_wrapper_layout = QVBoxLayout(scf_wrapper)
        scf_wrapper_layout.setContentsMargins(4, 4, 4, 0)
        scf_wrapper_layout.setSpacing(0)
        scf_wrapper_layout.addWidget(self.scf_plot)

        scf_with_slider_box = QWidget()
        scf_layout = QVBoxLayout(scf_with_slider_box)
        scf_layout.setContentsMargins(0, 0, 0, 0)
        scf_layout.setSpacing(4)
        scf_layout.addWidget(scf_wrapper, 1)
        scf_layout.addWidget(opt_slider_row, 0)
        scf_with_slider_box.setMinimumHeight(140)
        scf_section = QGroupBox("2. SCF energy / optimization trajectory")
        scf_section.setObjectName("sectionTrajectory")
        scf_section_layout = QVBoxLayout(scf_section)
        scf_section_layout.setContentsMargins(8, 10, 8, 8)
        scf_section_layout.addWidget(scf_with_slider_box)

        # Nested splitters. The dynamic content (viewers + SCF) shares an
        # inner adjustable region above the more-or-less fixed-height detail
        # box. Outer left_splitter draws the boundary between dynamic-zone
        # and detail-zone; inner top_half splits viewers vs SCF (1:1 default).
        top_half = QSplitter()
        top_half.setOrientation(ORIENT_VERTICAL)
        top_half.addWidget(viewers_section)
        top_half.addWidget(scf_section)
        top_half.setChildrenCollapsible(False)
        top_half.setStretchFactor(0, 1)
        top_half.setStretchFactor(1, 1)
        top_half.setSizes([240, 240])

        left_splitter = QSplitter()
        left_splitter.setOrientation(ORIENT_VERTICAL)
        left_splitter.addWidget(top_half)
        left_splitter.addWidget(detail_section)
        left_splitter.setChildrenCollapsible(False)
        # Detail box has a fixed 8-row grid; only the top dynamic zone
        # should grow when the window is enlarged vertically. Drag handle
        # still works freely either way.
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 0)
        left_splitter.setSizes([480, 220])
        left_splitter.setMinimumWidth(460)

        self.table = DropTable(self)
        self.table.filesDropped.connect(self.add_files)
        self.table.currentCellChanged.connect(self.on_current_changed)
        self.table.setContextMenuPolicy(CMP_CUSTOM)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        headers = [
            "File", "Sym.", "State",
            "HF", "ZPE", "Etot", "ΔE",
            "NImag", "Freq Done",
            "Opt Conv.", "Freq Conv.",
            "Stable1", "Stable2"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setSortingEnabled(False)
        self._sort_order: Dict[int, int] = {}
        self._active_sort_text = "load order"
        # Sortable columns in the 13-col layout (Cluster removed):
        # 0=File, 1=Sym., 2=State, 3=HF, 4=ZPE (not sortable per legacy),
        # 5=Etot, 6=ΔE, 7=NImag, 8=Freq Done, 9=Opt Conv., 10=Freq Conv.,
        # 11=Stable1, 12=Stable2.
        self._sortable_cols = set(range(13))
        hdr = self.table.horizontalHeader()
        # Every column is user-draggable. Initial widths are header-text sized
        # via resizeColumnsToContents(); refresh_table re-fits exactly once
        # after the first data load and then leaves widths alone.
        for col in range(self.table.columnCount()):
            hdr.setSectionResizeMode(col, HDR_INTERACTIVE)
        self.table.resizeColumnsToContents()
        # File and Sym. defaults: keep them readable even before any data
        # lands. refresh_table later "grows-only" them based on content.
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 60)
        self._first_resize_done = False
        try:
            hdr.setSortIndicatorShown(True)
        except Exception:
            pass
        hdr.sectionClicked.connect(self.on_header_clicked)

        # High-frequency table actions stay visible. File import remains in the
        # File menu so the toolbar is compact but practical.
        btn_export_csv = QPushButton("Export CSV")
        btn_export_csv.clicked.connect(self.export_csv)
        btn_export_excel = QPushButton("Export Excel")
        btn_export_excel.clicked.connect(self.export_excel)
        btn_excel_struct = QPushButton("Excel + Structures")
        btn_excel_struct.clicked.connect(self.export_excel_with_structures)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_loaded_files)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self.delete_selected)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_all)
        btn_exit = QPushButton("Exit")
        btn_exit.clicked.connect(self.close)

        topbar = QHBoxLayout()
        for button in (btn_export_csv, btn_export_excel, btn_excel_struct, btn_refresh, btn_delete, btn_clear, btn_exit):
            topbar.addWidget(button)
        topbar.addStretch(1)
        hint = QLabel("Drag & drop .log files or folders — or use File → Open.")
        topbar.addWidget(hint)

        # Aggregate stats panel: Total / Normal / Errors-by-Lcode. Refreshed
        # by `_update_status_panel` whenever `self.summaries` changes.
        self.status_panel = QTextBrowser()
        self.status_panel.setMinimumHeight(50)
        self.status_panel.setMaximumHeight(80)

        right_box = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addLayout(topbar)
        right_layout.addWidget(self.table, 1)
        right_layout.addWidget(self.status_panel)
        right_box.setLayout(right_layout)
        right_box.setMinimumWidth(520)
        results_section = QGroupBox("4. Parsed Gaussian results")
        results_section.setObjectName("sectionResults")
        results_section_layout = QVBoxLayout(results_section)
        results_section_layout.setContentsMargins(8, 10, 8, 8)
        results_section_layout.addWidget(right_box)

        splitter = QSplitter()
        splitter.addWidget(left_splitter)
        splitter.addWidget(results_section)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([480, 800])

        root = QWidget()
        root_layout = QVBoxLayout()
        root_layout.addWidget(splitter)
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self._build_menu()

        # Apply persisted 3D viewer background preference on startup.
        self._apply_viewer_bg_color(self._viewer_bg_rgba, persist=False)
        self._update_status_panel()

    # -------------- menu --------------
    def _build_menu(self):
        menubar = self.menuBar()

        # ----- File menu (Task 2.5 C: keyboard shortcuts + central entry) -----
        menu_file = menubar.addMenu("File")
        act_open = QAction("Open...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.open_files)
        menu_file.addAction(act_open)
        act_open_folder = QAction("Open Folder...", self)
        act_open_folder.setShortcut("Ctrl+Shift+O")
        act_open_folder.triggered.connect(self.open_folder)
        menu_file.addAction(act_open_folder)
        act_open_xyz = QAction("Open XYZ / trajectory…", self)
        act_open_xyz.triggered.connect(lambda checked=False: self.open_xyz_viewer())
        menu_file.addAction(act_open_xyz)
        menu_file.addSeparator()
        act_export_interface = QAction("Export Interface Image…", self)
        act_export_interface.triggered.connect(self.export_interface_image)
        menu_file.addAction(act_export_interface)
        act_delayed_capture = QAction("Delayed Interface Capture…", self)
        act_delayed_capture.setShortcut("Ctrl+Shift+P")
        act_delayed_capture.triggered.connect(self.delayed_interface_capture)
        menu_file.addAction(act_delayed_capture)
        menu_file.addSeparator()
        act_export_csv_menu = QAction("Export CSV", self)
        act_export_csv_menu.triggered.connect(self.export_csv)
        menu_file.addAction(act_export_csv_menu)
        act_export_xlsx_menu = QAction("Export Excel", self)
        act_export_xlsx_menu.triggered.connect(self.export_excel)
        menu_file.addAction(act_export_xlsx_menu)
        act_export_txt_menu = QAction("Export TXT", self)
        act_export_txt_menu.triggered.connect(self.export_txt)
        menu_file.addAction(act_export_txt_menu)
        act_export_struct = QAction("Export Excel + Structures…", self)
        act_export_struct.triggered.connect(self.export_excel_with_structures)
        menu_file.addAction(act_export_struct)
        menu_file.addSeparator()
        act_refresh_shortcut = QAction(self)
        act_refresh_shortcut.setShortcut("F5")
        act_refresh_shortcut.triggered.connect(self.refresh_loaded_files)
        self.addAction(act_refresh_shortcut)

        act_exit = QAction("Exit", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        menu_view = menubar.addMenu("View")
        # Background submenu: White/Black/Custom only preview the current
        # selection on the live viewers. Persisting to config is opt-in via
        # "Set current background as default", or atomically reset via
        # "Reset default background to white".
        menu_bg = menu_view.addMenu("Background")
        act_bg_white = QAction("White", self)
        act_bg_black = QAction("Black", self)
        act_bg_custom = QAction("Custom color…", self)
        act_bg_set_default = QAction("Set current background as default", self)
        act_bg_reset_default = QAction("Reset default background to white", self)
        menu_bg.addAction(act_bg_white)
        menu_bg.addAction(act_bg_black)
        menu_bg.addAction(act_bg_custom)
        menu_bg.addSeparator()
        menu_bg.addAction(act_bg_set_default)
        menu_bg.addAction(act_bg_reset_default)

        act_toggle_grid = QAction("Show 3D grid", self, checkable=True)
        act_toggle_axis = QAction("Show XYZ axes", self, checkable=True)
        act_toggle_grid.setChecked(self.viewer_init.settings.show_grid)
        act_toggle_axis.setChecked(self.viewer_init.settings.show_axis)
        act_bigger = QAction("Atoms: Bigger", self)
        act_smaller = QAction("Atoms: Smaller", self)
        act_more_bonds = QAction("Bonds: More (looser)", self)
        act_less_bonds = QAction("Bonds: Less (tighter)", self)

        menu_view.addSeparator()
        menu_view.addAction(act_toggle_grid)
        menu_view.addAction(act_toggle_axis)
        menu_view.addSeparator()
        menu_view.addAction(act_bigger)
        menu_view.addAction(act_smaller)
        menu_view.addSeparator()
        menu_view.addAction(act_more_bonds)
        menu_view.addAction(act_less_bonds)

        act_bg_white.triggered.connect(lambda checked=False: self._set_bg_white())
        act_bg_black.triggered.connect(lambda checked=False: self._set_bg_black())
        act_bg_custom.triggered.connect(lambda checked=False: self._pick_viewer_bg_color())
        act_bg_set_default.triggered.connect(lambda checked=False: self._save_current_viewer_bg_as_default())
        act_bg_reset_default.triggered.connect(lambda checked=False: self._reset_default_viewer_bg_to_white())
        act_toggle_grid.triggered.connect(self._toggle_grid)
        act_toggle_axis.triggered.connect(self._toggle_axis)
        act_bigger.triggered.connect(lambda: self._scale_atoms(1.15))
        act_smaller.triggered.connect(lambda: self._scale_atoms(1/1.15))
        act_more_bonds.triggered.connect(lambda: self._scale_bonds(1.08))
        act_less_bonds.triggered.connect(lambda: self._scale_bonds(1/1.08))

        menu_colors = menubar.addMenu("Colors")
        act_edit = QAction("Edit element colors…", self)
        act_reset = QAction("Reset element colors to defaults", self)
        menu_colors.addAction(act_edit)
        menu_colors.addAction(act_reset)
        act_edit.triggered.connect(self._open_colors_dialog)
        act_reset.triggered.connect(self._reset_colors)

        # SCF plot inner-ViewBox theme. Exclusive group so the menu always
        # shows which theme is currently active; persist=True writes the
        # chosen value back to user config so it survives the next launch.
        menu_colors.addSeparator()
        menu_scf = menu_colors.addMenu("SCF plot background")
        self._scf_theme_group = QActionGroup(self)
        self._scf_theme_group.setExclusive(True)
        act_scf_dark = QAction("Dark", self, checkable=True)
        act_scf_light = QAction("Light", self, checkable=True)
        if self._scf_plot_theme == "light":
            act_scf_light.setChecked(True)
        else:
            act_scf_dark.setChecked(True)
        self._scf_theme_group.addAction(act_scf_dark)
        self._scf_theme_group.addAction(act_scf_light)
        menu_scf.addAction(act_scf_dark)
        menu_scf.addAction(act_scf_light)
        act_scf_dark.triggered.connect(lambda checked=False: self._apply_scf_plot_theme("dark", persist=True))
        act_scf_light.triggered.connect(lambda checked=False: self._apply_scf_plot_theme("light", persist=True))

        menu_gaussian = menubar.addMenu("Gaussian Input")
        act_modify_gjf = QAction("Modify .gjf/.com…", self)
        act_modify_gjf.triggered.connect(lambda checked=False: self.open_gjf_editor())
        menu_gaussian.addAction(act_modify_gjf)
        act_vde_ade_gen_menu = QAction("Generate VDE / ADE inputs…", self)
        act_vde_ade_gen_menu.triggered.connect(lambda checked=False: self.open_vde_ade_generator_dialog())
        menu_gaussian.addAction(act_vde_ade_gen_menu)

        menu_spectra = menubar.addMenu("Spectra")
        act_pes_gui = QAction("Generate PES Data…", self)
        act_dos_gui = QAction("Plot DOS with Origin…", self)
        act_pes_gui.triggered.connect(lambda checked=False: self.open_pes_dialog())
        act_dos_gui.triggered.connect(lambda checked=False: self.open_dos_dialog())
        menu_spectra.addAction(act_pes_gui)
        menu_spectra.addAction(act_dos_gui)

        menu_analysis = menubar.addMenu("Analysis")
        act_vde_ade_gen = QAction("Generate VDE / ADE Gaussian Inputs…", self)
        act_vde_ade = QAction("Calculate VDE / ADE…", self)
        act_terms = QAction("Atomic Term Symbols…", self)
        act_vde_ade_gen.triggered.connect(lambda checked=False: self.open_vde_ade_generator_dialog())
        act_vde_ade.triggered.connect(lambda checked=False: self.open_vde_ade_dialog())
        act_terms.triggered.connect(lambda checked=False: self.open_term_dialog())
        menu_analysis.addAction(act_vde_ade_gen)
        menu_analysis.addAction(act_vde_ade)
        menu_analysis.addSeparator()
        menu_analysis.addAction(act_terms)

        # ----- Settings → Theme -----
        menu_settings = menubar.addMenu("Settings")
        act_preferences = QAction("Preferences…", self)
        act_preferences.triggered.connect(lambda checked=False: self.open_preferences())
        menu_settings.addAction(act_preferences)
        act_remote_profiles = QAction("Remote .chk → .fchk Profiles…", self)
        act_remote_profiles.triggered.connect(self.open_remote_profiles)
        menu_settings.addAction(act_remote_profiles)
        menu_settings.addSeparator()
        menu_theme = menu_settings.addMenu("Theme")
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        try:
            from chemauto.infra.config import load_user_config
            current_theme = load_user_config().get("ui_theme", "ChemAuto Light")
        except Exception:
            current_theme = "ChemAuto Light"
        if current_theme not in _THEME_LABELS:
            current_theme = "ChemAuto Light"
        for label in _THEME_LABELS:
            act = QAction(label, self, checkable=True)
            if label == current_theme:
                act.setChecked(True)
            act.triggered.connect(
                lambda checked=False, l=label: self._apply_theme(l)
            )
            self._theme_group.addAction(act)
            menu_theme.addAction(act)

    def _apply_theme(self, label: str) -> None:
        app = QApplication.instance()
        if label in {"ChemAuto Light", "ChemAuto Dark"}:
            try:
                app.setStyle("Fusion")
            except Exception:
                pass
            app.setStyleSheet(_CHEMAUTO_LIGHT_QSS if label == "ChemAuto Light" else _CHEMAUTO_DARK_QSS)
        else:
            # Restore the native style and palette captured before any ChemAuto
            # stylesheet was applied. Clearing QSS alone leaves Fusion active,
            # which is why the old "System Default" did not match first launch.
            app.setStyleSheet("")
            native_name = getattr(app, "_chemauto_native_style_name", "")
            native_palette = getattr(app, "_chemauto_native_palette", None)
            try:
                if native_name:
                    native_style = QStyleFactory.create(native_name)
                    if native_style is not None:
                        app.setStyle(native_style)
                if native_palette is not None:
                    app.setPalette(QPalette(native_palette))
            except Exception:
                pass
        # Force already-created widgets to repolish immediately.
        for widget in QApplication.topLevelWidgets():
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except Exception:
                pass
        self._save_gui_config_value("ui_theme", label)

    def _load_gui_config(self) -> Dict[str, Any]:
        """Read the persisted user config (single source of truth for GUI knobs)."""
        try:
            from chemauto.infra.config import load_user_config
            return load_user_config()
        except Exception:
            return {}

    def _save_gui_config_value(self, key: str, value: Any) -> None:
        """Persist one config key without disturbing the rest of the file."""
        try:
            from chemauto.infra.config import load_user_config, save_user_config
            cfg = load_user_config()
            cfg[key] = value
            save_user_config(cfg)
        except Exception:
            pass

    def _apply_scf_plot_theme(self, theme: str, persist: bool = False) -> None:
        """Apply the SCF plot's inner ViewBox theme.

        The outer PlotWidget background stays transparent/None so the axis labels
        and tick text remain readable on the surrounding Qt palette. Only the
        inner ViewBox data area, border, grid alpha, curve, symbols, and cursor
        are themed.
        """
        if not HAS_PG:
            return

        theme = (theme or "dark").lower()
        if theme not in ("dark", "light"):
            theme = "dark"
        self._scf_plot_theme = theme

        if theme == "light":
            view_bg = (255, 255, 255)
            border = (80, 80, 80)
            curve = (0, 70, 220)
            cursor = (220, 0, 0)
            grid_alpha = 0.18
        else:
            view_bg = (0, 0, 0)
            border = (150, 150, 150)
            curve = (40, 90, 255)
            cursor = (255, 0, 0)
            grid_alpha = 0.30

        pi = self.scf_plot.getPlotItem()
        vb = pi.getViewBox()
        # Keep the outer PlotWidget transparent so it blends into the surrounding
        # Qt UI. Only the inner ViewBox receives the dark/light background.
        self.scf_plot.setBackground(None)
        vb.setBackgroundColor(pg.mkColor(*view_bg))
        vb.setBorder(pg.mkPen(color=border, width=1))

        # Axis labels and tick text remain black because they sit outside the
        # ViewBox on the surrounding light UI background.
        axis_pen = pg.mkPen(color="k", width=1)
        for axis_name in ("left", "bottom"):
            axis = self.scf_plot.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen("k")

        self.scf_plot.setLabel("bottom", "Step", color="k")
        self.scf_plot.setLabel("left", "Energy (Hartree)", color="k")
        self.scf_plot.showGrid(x=True, y=True, alpha=grid_alpha)

        # Re-theme the SCF polyline and point symbols.
        if hasattr(self, "scf_curve"):
            self.scf_curve.setPen(pg.mkPen(curve, width=2))
            try:
                self.scf_curve.setSymbolBrush(pg.mkBrush(curve))
                self.scf_curve.setSymbolPen(pg.mkPen(curve, width=1))
            except Exception:
                pass

        # Re-theme the trajectory cursor.
        if hasattr(self, "scf_cursor"):
            self.scf_cursor.setPen(pg.mkPen(cursor, width=1, style=PEN_DASH))

        if persist:
            self._save_gui_config_value("scf_plot_theme", theme)

    def _open_colors_dialog(self):
        dlg = ColorsDialog(self, on_changed=self._on_colors_changed)
        dlg.exec()

    def _on_colors_changed(self):
        # Redraw both viewers
        self.viewer_init.force_redraw()
        self.viewer_opt.force_redraw()

    def _reset_colors(self):
        ELEM_COLOR_255.clear()
        ELEM_COLOR_255.update(DEFAULT_ELEM_COLOR_255)
        self._on_colors_changed()

    # -------------- view actions --------------
    def _normalize_viewer_bg_rgba(self, rgba) -> Tuple[int, int, int, int]:
        try:
            r = int(rgba[0])
            g = int(rgba[1])
            b = int(rgba[2])
            a = int(rgba[3]) if len(rgba) >= 4 else 255
        except Exception:
            return (255, 255, 255, 255)
        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
            max(0, min(255, a)),
        )

    def _apply_viewer_bg_color(self, rgba, persist: bool = False) -> None:
        """Single entry point for changing both viewers' background.

        The Init/Opt viewers stay in lockstep, ``self._viewer_bg_rgba`` mirrors
        the live state, and the value is only written to user config when the
        caller asks (``persist=True``), so transient previews from White/Black/
        Custom color don't pollute the saved default.
        """
        rgba4 = self._normalize_viewer_bg_rgba(rgba)
        self._viewer_bg_rgba = rgba4
        for v in (self.viewer_init, self.viewer_opt):
            v.settings.bg_color = rgba4
            v.apply_settings()
        if persist:
            self._save_gui_config_value("viewer_bg_rgba", list(rgba4))

    def _set_bg_white(self):
        self._apply_viewer_bg_color((255, 255, 255, 255), persist=False)

    def _set_bg_black(self):
        self._apply_viewer_bg_color((0, 0, 0, 255), persist=False)

    def _pick_viewer_bg_color(self):
        rgba = getattr(self, "_viewer_bg_rgba", (255, 255, 255, 255))
        r, g, b, a = self._normalize_viewer_bg_rgba(rgba)
        init = QColor(r, g, b, a)
        color = QColorDialog.getColor(init, self, "Pick 3D viewer background color")
        if not color.isValid():
            return
        self._apply_viewer_bg_color(
            (color.red(), color.green(), color.blue(), 255),
            persist=False,
        )

    def _save_current_viewer_bg_as_default(self):
        rgba = getattr(self, "_viewer_bg_rgba", (255, 255, 255, 255))
        rgba4 = self._normalize_viewer_bg_rgba(rgba)
        self._viewer_bg_rgba = rgba4
        self._save_gui_config_value("viewer_bg_rgba", list(rgba4))
        QMessageBox.information(
            self,
            "Background default saved",
            f"Default 3D viewer background saved as RGBA {list(rgba4)}.",
        )

    def _reset_default_viewer_bg_to_white(self):
        rgba4 = (255, 255, 255, 255)
        self._apply_viewer_bg_color(rgba4, persist=True)
        QMessageBox.information(
            self,
            "Background default reset",
            "Default 3D viewer background reset to white.",
        )

    def _toggle_grid(self, checked=False):
        value = bool(checked)
        for v in (self.viewer_init, self.viewer_opt):
            v.settings.show_grid = value
            v.apply_settings()
        self._save_gui_config_value("viewer_show_grid", value)

    def _toggle_axis(self, checked=False):
        value = bool(checked)
        for v in (self.viewer_init, self.viewer_opt):
            v.settings.show_axis = value
            v.apply_settings()
        self._save_gui_config_value("viewer_show_axis", value)

    def _scale_atoms(self, factor: float):
        for v in (self.viewer_init, self.viewer_opt):
            v.settings.atom_scale = max(0.2, min(3.0, v.settings.atom_scale * factor))
            v.force_redraw()

    def _scale_bonds(self, factor: float):
        for v in (self.viewer_init, self.viewer_opt):
            v.settings.bond_scale = max(0.7, min(2.0, v.settings.bond_scale * factor))
            v.force_redraw()

    # -------------- sorting --------------
    def _etot_key(self, s: LogSummary) -> float:
        return float(s.etot) if isinstance(s.etot, (int, float)) else float("inf")

    def _stable_rank(self, v: Optional[str]) -> int:
        if v is None or str(v).strip() == "":
            return 3
        vv = str(v).strip().lower()
        if vv == "stable":
            return 0
        if vv == "unstable":
            return 1
        return 2

    def _yesno_rank(self, v: Any) -> int:
        # For "True/False" strings or booleans: YES/True first when ascending.
        if v is None:
            return 2
        if isinstance(v, bool):
            return 0 if v else 1
        vv = str(v).strip().lower()
        if vv in ("true", "yes", "y", "1"):
            return 0
        if vv in ("false", "no", "n", "0"):
            return 1
        return 2

    def _has_content_rank(self, v: Any) -> int:
        # Content first when ascending
        return 0 if (v is not None and str(v).strip() != "") else 1

    def _is_missing_for_col(self, col: int, s: LogSummary) -> bool:
        value_map = {
            0: s.file, 1: s.sym, 2: s.state, 3: s.hf, 4: s.zpe,
            5: s.etot, 6: s.etot, 7: s.nimag, 8: s.freq_completed,
            9: s.opt_conv.to_compact() if s.opt_conv else None,
            10: s.freq_conv.to_compact() if s.freq_conv else None,
            11: s.stable_1, 12: s.stable_2,
        }
        value = value_map.get(col)
        return value is None or (isinstance(value, str) and not value.strip())

    def _primary_key(self, col: int, s: LogSummary):
        # Complete 13-column mapping. Missing values are handled separately by
        # ``on_header_clicked`` so they remain at the bottom in both directions.
        if col == 0:
            return s.file.casefold()
        if col == 1:
            return (s.sym or "").casefold()
        if col == 2:
            return (s.state or "").casefold()
        if col == 3:
            return float(s.hf)
        if col == 4:
            return float(s.zpe)
        if col in (5, 6):
            return float(s.etot)
        if col == 7:
            return int(s.nimag)
        if col == 8:
            return self._yesno_rank(s.freq_completed)
        if col == 9:
            return (s.opt_conv.to_compact() if s.opt_conv else "").casefold()
        if col == 10:
            return (s.freq_conv.to_compact() if s.freq_conv else "").casefold()
        if col == 11:
            return self._stable_rank(s.stable_1)
        if col == 12:
            return self._stable_rank(s.stable_2)
        return s.file.casefold()

    def on_header_clicked(self, col: int):
        if col not in self._sortable_cols:
            return
        current = self._sort_order.get(col, ASC)
        new_order = DESC if current == ASC else ASC
        self._sort_order[col] = new_order
        try:
            self.table.horizontalHeader().setSortIndicator(col, new_order)
        except Exception:
            pass

        field_by_column = {
            0: "file", 1: "sym", 2: "state", 3: "hf", 4: "zpe",
            5: "etot", 6: "delta_e", 7: "nimag", 8: "freq_done",
            9: "opt_conv", 10: "freq_conv", 11: "stable1", 12: "stable2",
        }
        field = field_by_column[col]
        self.summaries[:] = sort_records(
            self.summaries, field, descending=(new_order == DESC)
        )
        direction = "descending" if new_order == DESC else "ascending"
        secondary = "Etot/HF ascending"
        self._active_sort_text = (
            f"{self.table.horizontalHeaderItem(col).text()} {direction}; "
            f"secondary: {secondary}"
        )
        self.refresh_table()

    # -------------- open files --------------
    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Gaussian .log files", self.last_io_dir,
            "Gaussian log (*.log);;All files (*)"
        )
        if files:
            self.add_files(files)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.last_io_dir)
        if folder:
            self.add_files([folder])

    def _expand_log_paths(self, paths: List[str]) -> List[str]:
        expanded: List[str] = []
        for raw in paths:
            value = (raw or "").strip().strip('"').strip("'")
            if not value:
                continue
            if os.path.isdir(value):
                for root, _, files in os.walk(value):
                    for fn in files:
                        if fn.lower().endswith(".log"):
                            expanded.append(os.path.join(root, fn))
            elif value.lower().endswith(".log") and os.path.exists(value):
                expanded.append(value)
        # Resolve + de-duplicate without changing discovery order.
        return list(dict.fromkeys(str(Path(x).resolve()) for x in expanded))

    def add_files(self, paths: List[str], replace: bool = False):
        # The active parser owns the import pipeline. A second drop/open request
        # is intentionally ignored rather than queued or run in parallel.
        if self._load_thread is not None:
            QMessageBox.information(
                self,
                "Please wait",
                "Gaussian log files are still being parsed. Please wait for the current import to finish before importing another batch. The new selection was ignored.",
            )
            return
        # Directly dropped XYZ files open in the trajectory viewer. This keeps
        # the main drop target useful for both Gaussian logs and XYZ trajectories.
        xyz_files = [
            str(Path(str(raw).strip().strip('"').strip("'")))
            for raw in paths
            if str(raw).strip().strip('"').strip("'").lower().endswith(".xyz")
            and Path(str(raw).strip().strip('"').strip("'")).is_file()
        ]
        if xyz_files:
            self.open_xyz_viewer(xyz_files[0])
            if len(xyz_files) > 1:
                QMessageBox.information(
                    self, "XYZ Viewer",
                    f"Opened the first of {len(xyz_files)} dropped XYZ files. "
                    "Additional XYZ files can be dragged into the viewer window."
                )

        expanded = self._expand_log_paths(paths)
        if not expanded:
            if xyz_files:
                return
            QMessageBox.information(self, "No logs", "No .log files found in the selection.")
            return
        try:
            self.last_io_dir = os.path.commonpath([str(Path(x).parent) for x in expanded])
        except Exception:
            self.last_io_dir = str(Path(expanded[0]).parent)

        if not replace:
            existing = {str(Path(x.path).resolve()).casefold() for x in self.summaries}
            expanded = [x for x in expanded if x.casefold() not in existing]
            if not expanded:
                QMessageBox.information(self, "Already loaded", "All selected log files are already loaded.")
                return

        self._load_results = []
        self._load_failures = []
        self._load_replace = replace
        self._load_thread = QThread(self)
        self._load_worker = LogLoadWorker(expanded)
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.parsed.connect(self._on_log_parsed)
        self._load_worker.failed.connect(self._on_log_failed)
        self._load_worker.progress.connect(self._on_load_progress)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_thread.finished.connect(self._cleanup_loader)

        self._load_progress = QProgressDialog("Preparing…", "Cancel", 0, len(expanded), self)
        self._load_progress.setWindowTitle("Loading Gaussian logs")
        self._load_progress.setMinimumDuration(200)
        self._load_progress.setAutoClose(False)
        self._load_progress.canceled.connect(self._load_worker.cancel)
        self._load_thread.start()

    def _on_log_parsed(self, summary):
        self._load_results.append(summary)

    def _on_log_failed(self, path: str, error: str):
        self._load_failures.append((path, error))

    def _on_load_progress(self, value: int, total: int, filename: str):
        if self._load_progress is not None:
            self._load_progress.setMaximum(total)
            self._load_progress.setValue(value)
            self._load_progress.setLabelText(f"Parsing {value}/{total}: {filename}")

    def _on_load_finished(self, good: int, bad: int):
        if getattr(self, "_load_replace", False):
            self.summaries[:] = self._load_results
        else:
            self.summaries.extend(self._load_results)
        self._active_sort_text = "load order"
        self.refresh_table()
        if self._load_progress is not None:
            self._load_progress.setValue(self._load_progress.maximum())
            self._load_progress.close()
        if bad:
            example = "\n".join(f"{Path(p).name}: {e}" for p, e in self._load_failures[:5])
            QMessageBox.warning(self, "Parse warning", f"{bad} file(s) failed to parse.\n\n{example}")

    def _cleanup_loader(self):
        if self._load_worker is not None:
            self._load_worker.deleteLater()
        if self._load_thread is not None:
            self._load_thread.deleteLater()
        self._load_worker = None
        self._load_thread = None
        self._load_progress = None

    def refresh_loaded_files(self):
        if not self.summaries:
            QMessageBox.information(self, "Refresh", "No files are currently loaded.")
            return
        self.add_files([s.path for s in self.summaries], replace=True)

    # -------------- table --------------
    def _summary_from_view_row(self, view_row: int) -> Optional[LogSummary]:
        it = self.table.item(view_row, 0)
        if it is None:
            return None
        idx = it.data(USER_ROLE)
        if idx is None:
            return None
        try:
            idx = int(idx)
        except Exception:
            return None
        if 0 <= idx < len(self.summaries):
            return self.summaries[idx]
        return None

    def _selected_summaries(self) -> List[LogSummary]:
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()})
        return [s for r in rows if (s := self._summary_from_view_row(r)) is not None]

    def _write_xyz(self, xyz: Optional[str], default_path: Path, title: str):
        if not xyz:
            QMessageBox.warning(self, title, "No structure was found in this log.")
            return
        out, _ = QFileDialog.getSaveFileName(self, title, str(default_path), "XYZ (*.xyz)")
        if out:
            Path(out).write_text(xyz, encoding="utf-8", newline="\n")
            QMessageBox.information(self, title, f"Saved:\n{out}")

    def _write_opt_gjf(self, s: LogSummary):
        if not s.opt_xyz:
            QMessageBox.warning(self, "Export .gjf", "No optimized structure was found.")
            return
        from chemauto.core.gjf_template import build_gjf_from_template_path
        from chemauto.infra.config import load_user_config
        lines = s.opt_xyz.splitlines()[2:]
        charge = s.charge if s.charge is not None else 0
        mult = s.multiplicity if s.multiplicity is not None else 1
        default = Path(s.path).with_suffix(".gjf")
        out, _ = QFileDialog.getSaveFileName(
            self, "Export optimized structure as .gjf", str(default),
            "Gaussian input (*.gjf *.com)"
        )
        if not out:
            return
        cfg = load_user_config()
        template = str(cfg.get("gjf_template_path", "")).strip()
        try:
            text, used_template = build_gjf_from_template_path(
                template, lines, charge, mult, Path(out).stem, s.file
            )
            Path(out).write_text(text, encoding="utf-8", newline="\n")
        except Exception as exc:
            QMessageBox.critical(self, "Export .gjf", f"Template processing failed:\n{exc}")
            return
        if used_template:
            message = f"Saved using the configured .gjf template:\n{out}"
        else:
            message = (
                f"Saved with the minimal fallback template:\n{out}\n\n"
                "Set a preferred template under Settings → Preferences for production inputs."
            )
        QMessageBox.information(self, "Export .gjf", message)

    def _append_stability(self, gjf: Path, mode: str):
        label = "Stable Check" if mode == "stable" else "Stable=Opt"
        reply = QMessageBox.warning(
            self, label,
            f"The verified V1.7.2 logic will append {label} and overwrite the original .gjf without a .bak file:\n\n{gjf}\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            content, enc = read_text_safely(str(gjf))
            handler = ChemAutoGJFHandler()
            handler.load_from_text(content, filename=gjf.stem)
            ok, message = handler.add_stability_check(mode=mode)
            if not ok:
                QMessageBox.warning(self, label, message)
                return
            out_enc = enc if enc != "latin-1" else "utf-8"
            gjf.write_text(handler.build_text(), encoding=out_enc, newline="\n")
            QMessageBox.information(self, label, message)
        except Exception as exc:
            QMessageBox.critical(self, label, str(exc))

    def open_preferences(self):
        from chemauto.gui.preferences_dialog import PreferencesDialog
        PreferencesDialog(self).exec()

    def open_term_dialog(self):
        from chemauto.gui.term_dialog import AtomicTermDialog
        AtomicTermDialog(self).exec()

    def open_gjf_editor(self, path: str = ""):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Modify Gaussian input", self.last_io_dir, "Gaussian input (*.gjf *.com)")
        if not path:
            return
        from chemauto.gui.gjf_editor_dialog import GJFEditorDialog
        GJFEditorDialog(path, self).exec()

    def open_xyz_viewer(self, path: str = ""):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open XYZ / trajectory", self.last_io_dir, "XYZ files (*.xyz);;All files (*)")
        if not path:
            return
        from chemauto.gui.xyz_viewer_dialog import XYZViewerDialog
        XYZViewerDialog(path, self).exec()

    def open_pes_dialog(self, initial_fchk: str = ""):
        from chemauto.gui.pes_dialog import PESDialog
        PESDialog(self, initial_fchk=initial_fchk).exec()

    def open_dos_dialog(self, initial_folder: str = ""):
        from chemauto.gui.dos_dialog import DOSDialog
        DOSDialog(self, initial_folder=initial_folder).exec()

    def open_vde_ade_dialog(self, initial_files: Optional[List[str]] = None):
        from chemauto.gui.vde_ade_dialog import VDEADEDialog
        VDEADEDialog(self, initial_files=initial_files).exec()

    def open_vde_ade_generator_dialog(self, initial_path: str = ""):
        from chemauto.gui.vde_ade_generator_dialog import VDEADEGeneratorDialog
        VDEADEGeneratorDialog(self, initial_path=initial_path).exec()

    def export_excel_with_structures(self):
        if not self.summaries:
            QMessageBox.information(self, "Excel + Structures", "No parsed logs to export.")
            return
        from chemauto.gui.excel_structures_dialog import ExcelStructuresDialog
        ExcelStructuresDialog(self._get_export_subset(), self).exec()

    def open_remote_profiles(self):
        from chemauto.gui.remote_formchk_dialog import RemoteProfilesDialog
        RemoteProfilesDialog(self).exec()

    def _remote_chk_to_fchk(self, chk: Path):
        profiles = load_profiles()
        active = get_active_profile_name()
        profile = profiles.get(active)
        if profile is None:
            QMessageBox.information(self, "Remote .chk → .fchk", "Create and save a remote profile first.")
            self.open_remote_profiles()
            profiles = load_profiles(); active = get_active_profile_name(); profile = profiles.get(active)
        if profile is None:
            return
        try:
            launch_remote_conversion(chk, profile)
            QMessageBox.information(self, "Remote .chk → .fchk", "The conversion console was opened. Enter passwords there if OpenSSH asks. ChemAuto stores no password.")
        except Exception as exc:
            QMessageBox.critical(self, "Remote .chk → .fchk", str(exc))

    def _on_table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item is None:
            return
        if not self.table.selectionModel().isRowSelected(item.row(), self.table.rootIndex()):
            self.table.selectRow(item.row())
        selected = self._selected_summaries()
        s = self._summary_from_view_row(item.row())
        if s is None:
            return
        rel = resolve_related_files(s.path)
        path = Path(s.path)

        menu = QMenu(self.table)
        act_open_file = menu.addAction("Open Log")
        act_open_folder = menu.addAction("Open Folder")
        act_copy_name = menu.addAction("Copy File Name")
        act_copy_path = menu.addAction("Copy Full Path")

        related_menu = menu.addMenu("Related Files")
        related_actions = {}
        for key, rp in rel.existing().items():
            action = related_menu.addAction(f"{key}: {rp.name}")
            action.setEnabled(can_open_related(rp))
            if not can_open_related(rp):
                action.setToolTip("Binary .chk files are not opened directly; use .chk → .fchk.")
            related_actions[action] = rp
        if not rel.existing():
            empty = related_menu.addAction("No related files found")
            empty.setEnabled(False)

        act_modify_gjf_ctx = menu.addAction("Modify .gjf/.com…")
        act_modify_gjf_ctx.setEnabled(rel.input_file is not None)

        menu.addSeparator()
        structure_menu = menu.addMenu("Structure")
        act_init_xyz = structure_menu.addAction("Export Initial Structure as XYZ")
        act_opt_xyz = structure_menu.addAction("Export Optimized Structure as XYZ")
        act_opt_gjf = structure_menu.addAction("Export Optimized Structure as .gjf (Template)")
        act_copy_coords = structure_menu.addAction("Copy Optimized Coordinates")
        act_init_xyz.setEnabled(bool(s.init_xyz))
        for act in (act_opt_xyz, act_opt_gjf, act_copy_coords):
            act.setEnabled(bool(s.opt_xyz))

        gjf_menu = menu.addMenu("Gaussian Input")
        act_open_gjf = gjf_menu.addAction("Open .gjf/.com")
        act_stable = gjf_menu.addAction("Add Stable Check")
        act_stable_opt = gjf_menu.addAction("Add Stable=Opt")
        act_vde_inputs = gjf_menu.addAction("Generate VDE / ADE Inputs…")
        act_nbo = gjf_menu.addAction("Generate NBO7 Input (reserved)")
        act_nbo.setEnabled(False)
        for act in (act_open_gjf, act_stable, act_stable_opt, act_vde_inputs):
            act.setEnabled(rel.input_file is not None)

        # Frequent one-step conversions stay at the root level. They are
        # always visible so users learn where the commands live; availability
        # is communicated by enabled/disabled state.
        act_remote = menu.addAction(".chk → .fchk (Remote)")
        act_remote.setEnabled(rel.chk is not None)
        act_fchk_xyz = menu.addAction(".fchk → XYZ")
        act_fchk_xyz.setEnabled(rel.formatted_checkpoint is not None)
        act_pes = menu.addAction(".fchk → PES Data…")
        act_pes.setEnabled(rel.formatted_checkpoint is not None)

        if len(selected) > 1:
            batch = menu.addMenu(f"Batch Operations ({len(selected)} records)")
            batch_xyz = batch.addAction("Export Optimized XYZ Files…")
            batch_vde = batch.addAction("Build VDE / ADE Task from 3 Selected Logs…")
            batch_vde.setEnabled(len(selected) == 3)
        else:
            batch_xyz = batch_vde = None

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        try:
            if chosen in related_actions:
                open_external(related_actions[chosen])
            elif chosen is act_open_folder:
                open_in_file_manager(str(path))
            elif chosen is act_open_file:
                open_external(path)
            elif chosen is act_copy_path:
                QApplication.clipboard().setText(str(path))
            elif chosen is act_copy_name:
                QApplication.clipboard().setText(path.name)
            elif chosen is act_init_xyz:
                self._write_xyz(s.init_xyz, path.with_name(path.stem + "_init.xyz"), "Export Initial XYZ")
            elif chosen is act_opt_xyz:
                self._write_xyz(s.opt_xyz, path.with_suffix(".xyz"), "Export Optimized XYZ")
            elif chosen is act_opt_gjf:
                self._write_opt_gjf(s)
            elif chosen is act_copy_coords:
                QApplication.clipboard().setText("\n".join((s.opt_xyz or "").splitlines()[2:]))
            elif chosen is act_open_gjf and rel.input_file:
                open_external(rel.input_file)
            elif chosen is act_modify_gjf_ctx and rel.input_file:
                self.open_gjf_editor(str(rel.input_file))
            elif chosen is act_stable and rel.input_file:
                self._append_stability(rel.input_file, "stable")
            elif chosen is act_stable_opt and rel.input_file:
                self._append_stability(rel.input_file, "stable=opt")
            elif chosen is act_vde_inputs and rel.input_file:
                self.open_vde_ade_generator_dialog(str(rel.input_file))
            elif chosen is act_remote and rel.chk:
                self._remote_chk_to_fchk(rel.chk)
            elif chosen is act_fchk_xyz and rel.formatted_checkpoint:
                out = convert_fchk_to_xyz(rel.formatted_checkpoint, overwrite=False)
                QMessageBox.information(self, ".fchk → XYZ", f"Created:\n{out}")
            elif chosen is act_pes and rel.formatted_checkpoint:
                self.open_pes_dialog(str(rel.formatted_checkpoint))
            elif batch_xyz is not None and chosen is batch_xyz:
                folder = QFileDialog.getExistingDirectory(self, "Select output folder", self.last_io_dir)
                if folder:
                    count = 0
                    for rec in selected:
                        if rec.opt_xyz:
                            Path(folder, Path(rec.path).stem + ".xyz").write_text(
                                rec.opt_xyz, encoding="utf-8", newline="\n"
                            )
                            count += 1
                    QMessageBox.information(self, "Batch XYZ", f"Exported {count} XYZ file(s).")
            elif batch_vde is not None and chosen is batch_vde:
                self.open_vde_ade_dialog([rec.path for rec in selected])
        except Exception as exc:
            QMessageBox.critical(self, "Operation failed", str(exc))

    def refresh_table(self):
        self.table.setRowCount(0)

        # All loaded records share one global Etot reference. Sorting never
        # changes this physical zero; the user decides which records are comparable.
        base_etot = minimum_etot(self.summaries)

        for idx, s in enumerate(self.summaries):
            r = self.table.rowCount()
            self.table.insertRow(r)

            def put_text(col: int, val):
                item = QTableWidgetItem("" if val is None else str(val))
                self.table.setItem(r, col, item)

            def put_sortable_num(col: int, val: Optional[float], fmt: str = "{:.8f}"):
                if isinstance(val, (int, float)):
                    item = NumericItem(fmt.format(float(val)), float(val))
                else:
                    item = NumericItem("", None)
                self.table.setItem(r, col, item)

            file_item = QTableWidgetItem(s.file)
            file_item.setData(USER_ROLE, idx)
            self.table.setItem(r, 0, file_item)

            put_text(1, s.sym)
            put_text(2, s.state)
            put_sortable_num(3, s.hf)
            put_sortable_num(4, s.zpe)  # ZPE numeric sorting
            put_sortable_num(5, s.etot)

            de = delta_e_ev(s, base_etot)
            if de is not None:
                put_sortable_num(6, de, fmt="{:.6f}")
            else:
                self.table.setItem(r, 6, NumericItem("", None))

            put_text(7, s.nimag)
            put_text(8, "" if s.freq_completed is None else ("True" if s.freq_completed else "False"))
            put_text(9, s.opt_conv.to_compact() if s.opt_conv else "")
            put_text(10, s.freq_conv.to_compact() if s.freq_conv else "")
            put_text(11, s.stable_1)
            put_text(12, s.stable_2)

        # One-shot fit-to-content the first time data lands. File and Sym.
        # use a "grow-only" rule (keep default if content is narrower) so the
        # narrowest possible dataset doesn't shrink them below readability.
        # Subsequent refreshes preserve any column widths the user dragged.
        if self.summaries and not self._first_resize_done:
            try:
                self.table.resizeColumnsToContents()
                self.table.setColumnWidth(0, max(200, self.table.columnWidth(0)))
                self.table.setColumnWidth(1, max(60, self.table.columnWidth(1)))
                self._first_resize_done = True
            except Exception:
                pass
        self._update_status_panel()

    # -------------- delete / clear / export --------------
    def delete_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectionModel().selectedRows()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Delete", "No rows selected.")
            return
        to_remove = []
        for vr in rows:
            it = self.table.item(vr, 0)
            if it is None:
                continue
            idx = it.data(USER_ROLE)
            if idx is None:
                continue
            to_remove.append(int(idx))
        for idx in sorted(set(to_remove), reverse=True):
            if 0 <= idx < len(self.summaries):
                self.summaries.pop(idx)
        self.refresh_table()

    def clear_all(self):
        self.summaries.clear()
        self.table.setRowCount(0)
        for le in self.detail_fields.values():
            le.setText("")
        self.viewer_init.set_xyz(None)
        self.viewer_opt.set_xyz(None)

    def _get_export_subset(self) -> List[LogSummary]:
        rows = sorted({idx.row() for idx in self.table.selectionModel().selectedRows()})
        if rows:
            out: List[LogSummary] = []
            for vr in rows:
                s = self._summary_from_view_row(vr)
                if s:
                    out.append(s)
            return out
        return list(self.summaries)

    def export_csv(self):
        if not self.summaries:
            QMessageBox.information(self, "Export", "No parsed logs to export.")
            return
        subset = self._get_export_subset()
        default_path = os.path.join(self.last_io_dir, "results.csv")
        out, _ = QFileDialog.getSaveFileName(self, "Export CSV", default_path, "CSV (*.csv)")
        if not out:
            return

        # Keep the same single global physical zero used in the GUI.
        base_etot = minimum_etot(self.summaries)

        headers = [
            "Cluster", "Sym.", "State",
            "HF", "ZPE", "Etot", "ΔE",
            "NImag", "Freq Done",
            "Opt Conv.", "Freq Conv.",
            "Stable1", "Stable2"
        ]
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for s in subset:
                de_value = delta_e_ev(s, base_etot)
                de = "" if de_value is None else de_value
                w.writerow([
                    s.file, s.sym, s.state,
                    s.hf, s.zpe, s.etot,
                    de,
                    s.nimag, s.freq_completed,
                    s.opt_conv.to_compact() if s.opt_conv else "",
                    s.freq_conv.to_compact() if s.freq_conv else "",
                    s.stable_1, s.stable_2,
                ])
        QMessageBox.information(self, "Exported", f"CSV saved:\n{out}")
        open_in_file_manager(out)

    def export_excel(self):
        if not self.summaries:
            QMessageBox.information(self, "Export", "No parsed logs to export.")
            return
        subset = self._get_export_subset()
        default_path = os.path.join(self.last_io_dir, "results.xlsx")
        out, _ = QFileDialog.getSaveFileName(self, "Export Excel", default_path, "Excel (*.xlsx)")
        if not out:
            return
        try:
            export_excel_xlsx(out, subset, base_etot=minimum_etot(self.summaries))
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Excel export failed:\n{e}")
            return
        QMessageBox.information(self, "Exported", f"Excel saved:\n{out}")
        open_in_file_manager(out)

    def export_txt(self):
        if not self.summaries:
            QMessageBox.information(self, "Export", "No parsed logs to export.")
            return
        subset = self._get_export_subset()
        default_path = os.path.join(self.last_io_dir, "results.txt")
        out, _ = QFileDialog.getSaveFileName(self, "Export TXT", default_path, "Text (*.txt)")
        if not out:
            return
        base_etot = minimum_etot(self.summaries)
        headers = ["File", "Sym.", "State", "HF", "ZPE", "Etot", "ΔE/eV", "NImag", "Freq Done", "Opt Conv.", "Freq Conv.", "Stable1", "Stable2"]
        rows = ["\t".join(headers)]
        for rec in subset:
            de = delta_e_ev(rec, base_etot)
            rows.append("\t".join(str(v) if v is not None else "" for v in (
                rec.file, rec.sym, rec.state, rec.hf, rec.zpe, rec.etot, de, rec.nimag, rec.freq_completed,
                rec.opt_conv.to_compact() if rec.opt_conv else "",
                rec.freq_conv.to_compact() if rec.freq_conv else "", rec.stable_1, rec.stable_2,
            )))
        Path(out).write_text("\n".join(rows) + "\n", encoding="utf-8")
        QMessageBox.information(self, "Exported", f"TXT saved:\n{out}")
        open_in_file_manager(out)

    # -------------- interface image export --------------
    def _default_capture_path(self) -> str:
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.last_io_dir, f"ChemAuto_GUI_{stamp}.png")

    def _capture_visible_application_windows(self, output_path: str) -> None:
        app = QApplication.instance()
        visible = [w for w in app.topLevelWidgets() if w.isVisible()]
        if not visible:
            raise RuntimeError("No visible ChemAuto window is available for capture.")
        rect = QRect()
        for widget in visible:
            try:
                frame = widget.frameGeometry()
                rect = QRect(frame) if rect.isNull() else rect.united(frame)
            except Exception:
                continue
        if rect.isNull():
            rect = self.frameGeometry()
        center = rect.center()
        screen = app.screenAt(center) if hasattr(app, "screenAt") else app.primaryScreen()
        if screen is None:
            screen = app.primaryScreen()
        screen_geometry = screen.geometry()
        local_x = rect.x() - screen_geometry.x()
        local_y = rect.y() - screen_geometry.y()
        pixmap = screen.grabWindow(0, local_x, local_y, rect.width(), rect.height())
        if pixmap.isNull() or not pixmap.save(output_path, "PNG"):
            raise RuntimeError("The interface image could not be saved.")

    def export_interface_image(self):
        default_path = self._default_capture_path()
        out, _ = QFileDialog.getSaveFileName(
            self, "Export Interface Image", default_path, "PNG image (*.png)"
        )
        if not out:
            return
        if not out.lower().endswith(".png"):
            out += ".png"
        try:
            QApplication.processEvents()
            self._capture_visible_application_windows(out)
        except Exception as exc:
            QMessageBox.critical(self, "Capture failed", str(exc))
            return
        QMessageBox.information(self, "Image exported", f"PNG saved:\n{out}")

    def delayed_interface_capture(self):
        default_path = self._default_capture_path()
        out, _ = QFileDialog.getSaveFileName(
            self, "Delayed Interface Capture", default_path, "PNG image (*.png)"
        )
        if not out:
            return
        if not out.lower().endswith(".png"):
            out += ".png"
        self.statusBar().showMessage(
            "Interface capture in 3 seconds — open the required menu or dialog now.", 3500
        )

        def do_capture():
            try:
                QApplication.processEvents()
                self._capture_visible_application_windows(out)
                self.statusBar().showMessage(f"Interface image saved: {out}", 5000)
            except Exception as exc:
                QMessageBox.critical(self, "Capture failed", str(exc))

        QTimer.singleShot(3000, do_capture)

    # -------------- selection (debounced) --------------
    def on_current_changed(self, currentRow, currentCol, prevRow, prevCol):
        if currentRow < 0:
            return
        self._pending_view_row = currentRow
        self._sel_timer.start(60)

    def _apply_pending_selection(self):
        if self._pending_view_row is None:
            return
        s = self._summary_from_view_row(self._pending_view_row)
        if s is None:
            return
        self._fill_detail_fields(s)
        self.viewer_init.set_cluster_name(s.cluster)
        self.viewer_opt.set_cluster_name(s.cluster)
        self.viewer_init.set_xyz(s.init_xyz)
        # SCF + trajectory: parse frames lazily on first selection of this
        # row, then drive the Opt viewer through the slider so the user can
        # scrub through the optimization path.
        self._update_scf_plot(s)
        self._setup_trajectory_slider(s)
        if s.frames:
            self._on_trajectory_frame_changed(self.opt_slider.value())
        else:
            # Frame extraction failed — fall back to the legacy single view.
            self.viewer_opt.set_xyz(s.opt_xyz)
            # Reset the export suffix so a stale "opt-25" from the previous
            # row's trajectory can't carry over into this single-frame view.
            self.viewer_opt._xyz_kind = "opt"
            # Static title stays put; clear any leftover frame indicator.
            self.viewer_opt.frame_label.setText("")
            self.viewer_opt.frame_label.setStyleSheet("")

    def _update_scf_plot(self, s: LogSummary) -> None:
        """Refresh the SCF energy polyline + cursor for the selected log."""
        energies = s.scf_energies
        if not energies:
            self.scf_curve.setData([], [])
            self.scf_cursor.setVisible(False)
            return
        xs = list(range(1, len(energies) + 1))
        self.scf_curve.setData(xs, energies)
        self.scf_cursor.setVisible(True)
        # Cursor lands on the FINAL step by default; the slider handler
        # moves it as the user scrubs through earlier frames.
        self.scf_cursor.setPos(len(energies))
        self.scf_plot.enableAutoRange()

    def _setup_trajectory_slider(self, s: LogSummary) -> None:
        """Lazily parse Standard-Orientation frames + configure the slider."""
        if s.frames is None:
            s.frames = parse_full_frames(s.path)
        n = len(s.frames)
        # Block signals while resetting so we don't fire premature changes
        # back at _on_trajectory_frame_changed mid-setup.
        self.opt_slider.blockSignals(True)
        if n <= 1:
            # Single-point or unparseable: slider is meaningless.
            self.opt_slider.setMinimum(0)
            self.opt_slider.setMaximum(0)
            self.opt_slider.setValue(0)
            self.opt_slider.setEnabled(False)
        else:
            self.opt_slider.setMinimum(0)
            self.opt_slider.setMaximum(n - 1)
            self.opt_slider.setValue(n - 1)  # Start at FINAL frame.
            self.opt_slider.setEnabled(True)
        self.opt_slider.blockSignals(False)
        # Step buttons follow the slider's enabled state.
        self.btn_prev_frame.setEnabled(n > 1)
        self.btn_next_frame.setEnabled(n > 1)

    def _update_status_panel(self) -> None:
        """Refresh totals, termination status, current sort and ΔE zero."""
        n = len(self.summaries)
        if n == 0:
            self.status_panel.setHtml(
                "<i>Drop .log files or folders to begin "
                "(or use <b>File → Open</b> / Ctrl+O).</i>"
            )
            return
        error_links: Dict[str, int] = {}
        normal_count = 0
        incomplete_count = 0
        warning_count = 0
        for s in self.summaries:
            warning_count += len(getattr(s, "warnings", []) or [])
            if s.error_link:
                error_links[s.error_link] = error_links.get(s.error_link, 0) + 1
            elif getattr(s, "normal_termination", None) is True:
                normal_count += 1
            else:
                incomplete_count += 1
        error_count = sum(error_links.values())
        base_etot = minimum_etot(self.summaries)
        base_text = f"global minimum Etot = {base_etot:.10f} Ha" if base_etot is not None else "—"
        line = (
            f"<b>Total:</b> {n}"
            f" &nbsp;|&nbsp; <b>Normal:</b> {normal_count}"
            f" &nbsp;|&nbsp; <b>Errors:</b> {error_count}"
            f" &nbsp;|&nbsp; <b>Incomplete:</b> {incomplete_count}"
        )
        if error_links:
            breakdown = ", ".join(
                f"{k}: {v}" for k, v in sorted(error_links.items())
            )
            line += f" ({breakdown})"
        line += (
            f"<br><b>Sort:</b> {getattr(self, '_active_sort_text', 'load order')}"
            f" &nbsp;|&nbsp; <b>ΔE zero:</b> {base_text}"
            f" &nbsp;|&nbsp; <b>Parser warnings:</b> {warning_count}"
        )
        self.status_panel.setHtml(line)

    def _on_trajectory_frame_changed(self, idx: int) -> None:
        """Slider moved → swap Opt viewer to that frame; cursor + title follow."""
        row = self.table.currentRow()
        if row < 0:
            return
        s = self._summary_from_view_row(row)
        if s is None or not s.frames:
            return
        idx = max(0, min(idx, len(s.frames) - 1))
        self.viewer_opt.set_xyz(s.frames[idx])
        # Tag the viewer with the 1-indexed frame number so the Export
        # default filename becomes e.g. "C6Fe4_opt-25.xyz" instead of
        # always "C6Fe4_opt.xyz".
        self.viewer_opt._xyz_kind = f"opt-{idx + 1}"
        # Cursor lives on the SCF plot (1-indexed visually); cap to its
        # length so a frame-vs-SCF count mismatch can't push it off the curve.
        if s.scf_energies:
            cursor_x = min(idx + 1, len(s.scf_energies))
        else:
            cursor_x = idx + 1
        self.scf_cursor.setPos(cursor_x)
        # Frame indicator on frame_label, leaving the static title alone.
        # Green "FINAL" for the last frame, red "N/M" for any intermediate
        # frame, blank for single-frame (SP / 1-step opt).
        if len(s.frames) <= 1:
            self.viewer_opt.frame_label.setText("")
            self.viewer_opt.frame_label.setStyleSheet("")
        elif idx == len(s.frames) - 1:
            self.viewer_opt.frame_label.setText("FINAL")
            self.viewer_opt.frame_label.setStyleSheet("color: green;")
        else:
            self.viewer_opt.frame_label.setText(
                f"{idx + 1}/{len(s.frames)}"
            )
            self.viewer_opt.frame_label.setStyleSheet("color: red;")

    def _fill_detail_fields(self, s: LogSummary):
        def setv(k, v):
            self.detail_fields[k].setText("" if v is None else str(v))
        setv("Sym.", s.sym)
        setv("State", s.state)
        setv("HF", f"{s.hf:.10f}" if isinstance(s.hf, float) else None)
        setv("ZPE", f"{s.zpe:.10f}" if isinstance(s.zpe, float) else None)
        setv("Etot", f"{s.etot:.10f}" if isinstance(s.etot, float) else None)
        base_etot = minimum_etot(self.summaries)
        de = delta_e_ev(s, base_etot)
        setv("ΔE", f"{de:.6f}" if de is not None else "")
        setv("NImag", s.nimag)
        setv("Freq Done", "" if s.freq_completed is None else s.freq_completed)
        setv("Opt Conv.", s.opt_conv.to_compact() if s.opt_conv else "")
        setv("Freq Conv.", s.freq_conv.to_compact() if s.freq_conv else "")
        setv("Stable1", s.stable_1)
        setv("Stable2", s.stable_2)

def main():
    ready_path = None
    qt_argv = list(sys.argv)
    if "--ready-file" in qt_argv:
        idx = qt_argv.index("--ready-file")
        if idx + 1 < len(qt_argv):
            ready_path = qt_argv[idx + 1]
            del qt_argv[idx:idx + 2]
    app = QApplication(qt_argv)
    app.setApplicationName("ChemAuto")
    app.setApplicationDisplayName("ChemAuto")
    # Capture the native Windows style before applying any ChemAuto theme so
    # Settings → Theme → System Default can restore the true first-launch look.
    try:
        app._chemauto_native_style_name = app.style().objectName()
        app._chemauto_native_palette = QPalette(app.palette())
    except Exception:
        pass
    try:
        from chemauto.infra.paths import get_resource_path
        app.setWindowIcon(QIcon(str(get_resource_path("chemauto.ico"))))
    except Exception:
        pass
    app.setFont(QFont("Segoe UI", 10))
    try:
        from chemauto.infra.config import load_user_config
        _theme = load_user_config().get("ui_theme", "ChemAuto Light")
        if _theme in {"ChemAuto Light", "ChemAuto Dark"}:
            app.setStyle("Fusion")
            app.setStyleSheet(_CHEMAUTO_LIGHT_QSS if _theme == "ChemAuto Light" else _CHEMAUTO_DARK_QSS)
    except Exception:
        pass
    w = MainWindow()
    w.show()
    app.processEvents()
    # Optional startup handshake used by the CMD launcher. The marker is only
    # written after the main window has been shown and processed once.
    try:
        if ready_path:
            Path(ready_path).write_text("ready", encoding="utf-8")
    except Exception:
        pass
    app.exec()

if __name__ == "__main__":
    main()
