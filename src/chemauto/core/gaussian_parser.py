#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robust, UI-independent Gaussian log parser for ChemAuto.

The parser is intentionally independent from PyQt so it can be regression-tested
without starting the GUI.  It preserves the useful archive-entry patterns from
ChemAuto while selecting values from the correct printed Gaussian calculation
step and preferring ``SCF Done`` over wrapped archive HF values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HARTREE_TO_EV = 27.211386245988

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[DEde][+-]?\d+)?"
RE_SCF = re.compile(rf"SCF\s+Done:\s+E\([^)]*\)\s*=\s*({NUMBER})", re.I)
RE_ZPE = re.compile(rf"Zero-point\s+correction\s*=\s*({NUMBER})", re.I)
RE_ETOT = re.compile(rf"Sum\s+of\s+electronic\s+and\s+zero-point\s+Energies\s*=\s*({NUMBER})", re.I)
RE_CHARGE_MULT = re.compile(r"Charge\s*=\s*([+-]?\d+)\s+Multiplicity\s*=\s*(\d+)", re.I)
RE_ERROR = re.compile(r"Error termination .*?\bl(\d+)\.exe", re.I)
RE_NORMAL = re.compile(r"Normal termination", re.I)
RE_NIMAG_ARCHIVE = re.compile(r"N\s*I\s*m\s*a\s*g\s*=\s*([^=\\]*)\\", re.I | re.M)
RE_FREQ_LINE = re.compile(r"Frequencies\s+--\s+(.+)$", re.I | re.M)
RE_ROUTE = re.compile(r"^\s*#", re.I)
RE_DASH = re.compile(r"^\s*-{5,}\s*$")

RE_TABLE = re.compile(r"^\s*Item\s+Value\s+Threshold\s+Converged\?\s*$", re.I)
RE_ROW = re.compile(
    r"^\s*(Maximum Force|RMS\s+Force|Maximum Displacement|RMS\s+Displacement)\s+"
    r"([-0-9.DEdE+]+)\s+([-0-9.DEdE+]+)\s+(YES|NO)\s*$",
    re.I,
)
RE_OPT_DONE_1 = re.compile(r"^\s*Optimization completed\.\s*$", re.I)
RE_OPT_DONE_2 = re.compile(r"^\s*--\s*Stationary point found\.\s*$", re.I)

STABLE_PHRASE = "The wavefunction is stable under the perturbations considered"
UNSTABLE_PHRASES = (
    "The wavefunction has an internal instability",
    "The wavefunction has an RHF - UHF instability",
)

SO_START = re.compile(r"^\s*Standard orientation:\s*$", re.I)
SO_DASH = re.compile(r"^\s*-{10,}\s*$")

Z2SYM: Dict[int, str] = {
    1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O",
    9: "F", 10: "Ne", 11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P",
    16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca", 21: "Sc", 22: "Ti",
    23: "V", 24: "Cr", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni", 29: "Cu",
    30: "Zn", 31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr",
    37: "Rb", 38: "Sr", 39: "Y", 40: "Zr", 41: "Nb", 42: "Mo", 43: "Tc",
    44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
    51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La",
    58: "Ce", 59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd",
    65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb", 71: "Lu",
    72: "Hf", 73: "Ta", 74: "W", 75: "Re", 76: "Os", 77: "Ir", 78: "Pt",
    79: "Au", 80: "Hg", 81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At",
    86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th", 91: "Pa", 92: "U",
    93: "Np", 94: "Pu", 95: "Am", 96: "Cm", 97: "Bk", 98: "Cf", 99: "Es",
    100: "Fm", 101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db",
    106: "Sg", 107: "Bh", 108: "Hs", 109: "Mt", 110: "Ds", 111: "Rg",
    112: "Cn", 113: "Nh", 114: "Fl", 115: "Mc", 116: "Lv", 117: "Ts", 118: "Og",
}

SYMMAP = {
    "C1": "C1", "C01": "C1", "CS": "Cs", "CI": "Ci",
    "C2": "C2", "C02": "C2", "C2V": "C2v", "C02V": "C2v",
    "C2H": "C2h", "C02H": "C2h", "C3": "C3", "C03": "C3",
    "C3V": "C3v", "C03V": "C3v", "C3H": "C3h", "C03H": "C3h",
    "C4": "C4", "C04": "C4", "C4V": "C4v", "C04V": "C4v",
    "C4H": "C4h", "C04H": "C4h", "D2": "D2", "D02": "D2",
    "D2H": "D2h", "D02H": "D2h", "D2D": "D2d", "D02D": "D2d",
    "D3": "D3", "D03": "D3", "D3H": "D3h", "D03H": "D3h",
    "D3D": "D3d", "D03D": "D3d", "D4": "D4", "D04": "D4",
    "D4H": "D4h", "D04H": "D4h", "D4D": "D4d", "D04D": "D4d",
    "C*V": "Cinfv", "C*H": "Cinfh", "D*H": "Dinfh",
    "TD": "Td", "TH": "Th", "OH": "Oh", "IH": "Ih",
}


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
class GaussianStep:
    index: int
    start: int
    end: int
    route: str
    text: str
    input_step: int = 0
    input_route: str = ""
    charge: Optional[int] = None
    multiplicity: Optional[int] = None
    state: Optional[str] = None
    sym: Optional[str] = None
    scf_energies: List[float] = field(default_factory=list)
    archive_hfs: List[float] = field(default_factory=list)
    zpe: Optional[float] = None
    etot: Optional[float] = None
    stability_events: List[str] = field(default_factory=list)
    is_geom_opt: bool = False
    is_freq: bool = False
    is_stable: bool = False
    is_stable_opt: bool = False
    error_link: Optional[str] = None
    normal_termination: bool = False


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
    scf_energies: List[float] = field(default_factory=list)
    frames: Optional[List[str]] = None
    error_link: Optional[str] = None
    normal_termination: Optional[bool] = None
    charge: Optional[int] = None
    multiplicity: Optional[int] = None
    steps: List[GaussianStep] = field(default_factory=list)
    field_sources: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def _to_float(value: str) -> float:
    compact = re.sub(r"\s+", "", value)
    return float(compact.replace("D", "E").replace("d", "e"))


def _last_match(pattern: str, text: str, flags: int = 0) -> Optional[re.Match[str]]:
    matches = list(re.finditer(pattern, text, flags))
    return matches[-1] if matches else None


def _parse_charge_mult(text: str) -> Tuple[Optional[int], Optional[int]]:
    matches = list(RE_CHARGE_MULT.finditer(text))
    if not matches:
        return None, None
    m = matches[-1]
    return int(m.group(1)), int(m.group(2))


def _parse_scf(text: str) -> List[float]:
    out: List[float] = []
    for raw in RE_SCF.findall(text):
        try:
            out.append(_to_float(raw))
        except ValueError:
            continue
    return out


def _parse_archive_hfs(text: str) -> List[float]:
    # Handles Gaussian wrapping such as ``HF=-\n 3942.7280719`` and
    # ``HF=-4056.8\n 784896`` by stripping all inter-token whitespace.
    out: List[float] = []
    for raw in re.findall(r"\bHF\s*=\s*([+-]?[0-9.\sDEde]+)", text, flags=re.I):
        try:
            out.append(_to_float(raw))
        except ValueError:
            continue
    return out


def _clean_archive_token(raw: str) -> str:
    return re.sub(r"\s+", "", raw or "")


def _parse_state(text: str) -> Optional[str]:
    # Delimit on archive backslash, not newline: state labels are sometimes
    # wrapped as ``State=10-B\n U\`` or ``State=8\n -A\``.
    values = re.findall(r"\bState\s*=\s*([^=\\]*)\s*\\", text, flags=re.I | re.M)
    if values:
        val = _clean_archive_token(values[-1])
        return val or None
    m = _last_match(
        r"The\s+electronic\s+state(?:\s+of\s+the\s+initial\s+guess)?\s+is\s+([^\n\r.]+)",
        text,
        flags=re.I,
    )
    return _clean_archive_token(m.group(1)) if m else None


def _normalize_sym(raw: str) -> Optional[str]:
    key = _clean_archive_token(raw).upper()
    if not key:
        return None
    return SYMMAP.get(key, key)


def _parse_sym(text: str) -> Optional[str]:
    values = re.findall(r"\bPG\s*=\s*([^\\\[]+)", text, flags=re.I)
    if values:
        return _normalize_sym(values[-1])
    m = _last_match(r"Full\s+point\s+group\s+([A-Za-z0-9*]+)", text, flags=re.I)
    return _normalize_sym(m.group(1)) if m else None


def _parse_zpe(text: str) -> Optional[float]:
    values = RE_ZPE.findall(text)
    return _to_float(values[-1]) if values else None


def _parse_etot(text: str) -> Optional[float]:
    values = RE_ETOT.findall(text)
    return _to_float(values[-1]) if values else None


def _stability_events(text: str) -> List[str]:
    events: List[Tuple[int, str]] = []
    for m in re.finditer(re.escape(STABLE_PHRASE), text, flags=re.I):
        events.append((m.start(), "stable"))
    for phrase in UNSTABLE_PHRASES:
        for m in re.finditer(re.escape(phrase), text, flags=re.I):
            events.append((m.start(), "unstable"))
    events.sort(key=lambda x: x[0])
    out: List[str] = []
    for _, label in events:
        if not out or out[-1] != label:
            out.append(label)
    return out


def _previous_nonempty(lines: List[str], index: int) -> str:
    for j in range(index - 1, -1, -1):
        if lines[j].strip():
            return lines[j]
    return ""


def _collect_route(lines: List[str], start: int) -> str:
    parts: List[str] = []
    for j in range(start, min(start + 50, len(lines))):
        line = lines[j].strip()
        if j > start and (not line or RE_DASH.match(line)):
            break
        if line:
            parts.append(line)
    return " ".join(parts)


def _find_route_starts(text: str) -> List[Tuple[int, str]]:
    lines_keep = text.splitlines(keepends=True)
    stripped = [line.rstrip("\r\n") for line in lines_keep]
    starts: List[Tuple[int, str]] = []
    offset = 0
    for i, line in enumerate(lines_keep):
        if line.lstrip().startswith("#"):
            prev = _previous_nonempty(stripped, i)
            if RE_DASH.match(prev):
                route = _collect_route(stripped, i)
                # Archive entries also contain a literal # route; a backslash
                # identifies those fake starts.
                if "\\" not in route:
                    starts.append((offset, route))
        offset += len(line)
    return starts


def _classify_route(route: str) -> Tuple[bool, bool, bool, bool]:
    r = route.lower()
    is_stable = re.search(r"(^|[^a-z])stable([^a-z]|$|=|\()", r) is not None
    is_stable_opt = re.search(r"stable\s*=\s*opt|stable\s*\(\s*opt", r) is not None
    without_stable_opt = re.sub(r"stable\s*=\s*opt|stable\s*\(\s*opt\s*\)", "stable", r)
    is_geom_opt = re.search(r"(^|[^a-z])opt([^a-z]|$|=|\()", without_stable_opt) is not None and not is_stable
    is_freq = re.search(r"(^|[^a-z])freq([^a-z]|$|=|\()", r) is not None
    return is_geom_opt, is_freq, is_stable, is_stable_opt


def _is_auto_freq(route: str) -> bool:
    r = re.sub(r"\s+", " ", route.lower())
    return "freq" in r and "geom=allcheck" in r and "guess=tcheck" in r and "genchk" in r and "stable" not in r


def _assign_input_steps(steps: List[GaussianStep]) -> None:
    input_index = 0
    current_route = ""
    for step in steps:
        if input_index == 0:
            input_index = 1
            current_route = step.route
        elif _is_auto_freq(step.route):
            pass
        else:
            input_index += 1
            current_route = step.route
        step.input_step = input_index
        step.input_route = current_route


def _parse_steps(text: str) -> List[GaussianStep]:
    starts = _find_route_starts(text)
    if not starts:
        starts = [(0, "# unknown")]
    steps: List[GaussianStep] = []
    global_charge, global_mult = _parse_charge_mult(text)
    for idx, (start, route) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(text)
        segment = text[start:end]
        charge, mult = _parse_charge_mult(segment)
        geom_opt, freq, stable, stable_opt = _classify_route(route)
        err = RE_ERROR.search(segment)
        step = GaussianStep(
            index=idx + 1,
            start=start,
            end=end,
            route=route,
            text=segment,
            charge=charge if charge is not None else global_charge,
            multiplicity=mult if mult is not None else global_mult,
            state=_parse_state(segment),
            sym=_parse_sym(segment),
            scf_energies=_parse_scf(segment),
            archive_hfs=_parse_archive_hfs(segment),
            zpe=_parse_zpe(segment),
            etot=_parse_etot(segment),
            stability_events=_stability_events(segment),
            is_geom_opt=geom_opt,
            is_freq=freq,
            is_stable=stable,
            is_stable_opt=stable_opt,
            error_link=f"L{err.group(1)}" if err else None,
            normal_termination=bool(RE_NORMAL.search(segment)),
        )
        steps.append(step)
    _assign_input_steps(steps)
    return steps


def _select_energy_step(steps: List[GaussianStep]) -> GaussianStep:
    nonstable = [step for step in steps if not step.is_stable]
    pool = nonstable or steps
    with_thermo = [step for step in pool if step.etot is not None or step.zpe is not None]
    if with_thermo:
        return with_thermo[-1]
    with_task = [step for step in pool if step.is_geom_opt or step.is_freq]
    if with_task:
        return with_task[-1]
    return pool[-1]


def _select_trajectory_step(steps: List[GaussianStep], primary: GaussianStep) -> GaussianStep:
    candidates = [
        step for step in steps
        if step.input_step == primary.input_step and step.is_geom_opt and not step.is_stable
    ]
    if candidates:
        return candidates[-1]
    return primary


def _parse_conv_table(lines: List[str], start_i: int) -> ConvergenceTable:
    got: Dict[str, str] = {}
    i = start_i + 1
    while i < len(lines) and len(got) < 4:
        m = RE_ROW.match(lines[i])
        if m:
            label = re.sub(r"\s+", " ", m.group(1)).strip().lower()
            value = m.group(4).upper()
            if label == "maximum force":
                got["max_force"] = value
            elif label == "rms force":
                got["rms_force"] = value
            elif label == "maximum displacement":
                got["max_disp"] = value
            elif label == "rms displacement":
                got["rms_disp"] = value
        i += 1
    table = ConvergenceTable(
        max_force=got.get("max_force"),
        rms_force=got.get("rms_force"),
        max_disp=got.get("max_disp"),
        rms_disp=got.get("rms_disp"),
    )
    values = (table.max_force, table.rms_force, table.max_disp, table.rms_disp)
    if None not in values:
        table.all_yes = all(value == "YES" for value in values)
    return table


def _parse_convergence(steps: List[GaussianStep]) -> Tuple[Optional[ConvergenceTable], Optional[ConvergenceTable]]:
    opt_conv: Optional[ConvergenceTable] = None
    freq_conv: Optional[ConvergenceTable] = None
    for step in steps:
        lines = step.text.splitlines()
        tables: List[ConvergenceTable] = []
        for i, line in enumerate(lines):
            if RE_TABLE.match(line):
                tables.append(_parse_conv_table(lines, i))
        if not tables:
            continue
        if step.is_geom_opt:
            opt_conv = tables[-1]
        elif step.is_freq and not step.is_geom_opt:
            freq_conv = tables[-1]
    return opt_conv, freq_conv


def _count_imag(text: str) -> Optional[int]:
    archive = list(RE_NIMAG_ARCHIVE.finditer(text))
    if archive:
        raw = re.sub(r"\s+", "", archive[-1].group(1))
        try:
            return int(float(raw))
        except ValueError:
            pass
    freq_values: List[float] = []
    for raw_line in RE_FREQ_LINE.findall(text):
        for raw in re.findall(NUMBER, raw_line):
            try:
                freq_values.append(_to_float(raw))
            except ValueError:
                continue
    if not freq_values:
        return None
    return sum(value < 0.0 for value in freq_values)


def _extract_standard_orientation_xyz(text: str) -> Tuple[Optional[str], Optional[str]]:
    lines = text.splitlines()
    blocks: List[Tuple[List[str], List[Tuple[float, float, float]]]] = []
    i = 0
    while i < len(lines):
        if SO_START.match(lines[i]):
            j = i + 1
            dash_count = 0
            while j < len(lines) and dash_count < 2:
                if SO_DASH.match(lines[j]):
                    dash_count += 1
                j += 1
            if dash_count < 2:
                i += 1
                continue
            symbols: List[str] = []
            coords: List[Tuple[float, float, float]] = []
            while j < len(lines) and not SO_DASH.match(lines[j]):
                parts = lines[j].split()
                if len(parts) >= 6:
                    try:
                        atomic_number = int(parts[1])
                        symbols.append(Z2SYM.get(atomic_number, str(atomic_number)))
                        coords.append((float(parts[3]), float(parts[4]), float(parts[5])))
                    except (ValueError, IndexError):
                        pass
                j += 1
            if symbols and len(symbols) == len(coords):
                blocks.append((symbols, coords))
            i = j + 1
            continue
        i += 1
    if not blocks:
        return None, None

    def make_xyz(block: Tuple[List[str], List[Tuple[float, float, float]]], comment: str) -> str:
        symbols, coords = block
        rows = [str(len(symbols)), comment]
        for symbol, (x, y, z) in zip(symbols, coords):
            rows.append(f"{symbol:2s}  {x: .8f}  {y: .8f}  {z: .8f}")
        return "\n".join(rows) + "\n"

    return make_xyz(blocks[0], "init (first Standard orientation)"), make_xyz(blocks[-1], "opt (last Standard orientation)")


def _select_stability(steps: List[GaussianStep]) -> Tuple[Optional[str], Optional[str]]:
    stable_steps = [step for step in steps if step.is_stable or step.stability_events]
    if not stable_steps:
        return None, None
    first: Optional[str] = None
    second: Optional[str] = None
    collected: List[str] = []
    for step in stable_steps:
        events = step.stability_events
        if not events:
            continue
        if step.is_stable_opt:
            # For Stable=Opt, expose the checked input state and final optimized
            # state separately whenever both were printed.
            if first is None:
                first = events[0]
            if len(events) > 1:
                second = events[-1]
            elif len(stable_steps) > 1:
                collected.append(events[-1])
        else:
            collected.append(events[-1])
    for status in collected:
        if first is None:
            first = status
        elif second is None:
            second = status
    return first, second


def parse_gaussian_log(path: str | Path) -> LogSummary:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    steps = _parse_steps(text)
    primary = _select_energy_step(steps)
    trajectory = _select_trajectory_step(steps, primary)

    summary = LogSummary(path=str(file_path), file=file_path.name, steps=steps)
    sto = re.findall(r"Stoichiometry\s+([^\s]+)", text)
    summary.cluster = sto[-1] if sto else file_path.stem
    summary.charge = primary.charge
    summary.multiplicity = primary.multiplicity

    # Field values and explicit provenance.
    summary.sym = primary.sym or next((step.sym for step in reversed(steps) if step.sym), None)
    summary.state = primary.state or next((step.state for step in reversed(steps) if step.state), None)
    if summary.sym:
        summary.field_sources["sym"] = f"Step {primary.input_step} archive PG"
    if summary.state:
        summary.field_sources["state"] = f"Step {primary.input_step} archive State"

    if primary.etot is not None and primary.zpe is not None:
        summary.hf = primary.etot - primary.zpe
        summary.field_sources["hf"] = f"Step {primary.input_step}: Etot - ZPE"
    elif primary.scf_energies:
        summary.hf = primary.scf_energies[-1]
        summary.field_sources["hf"] = f"Step {primary.input_step}: final SCF Done"
    elif primary.archive_hfs:
        summary.hf = primary.archive_hfs[-1]
        summary.field_sources["hf"] = f"Step {primary.input_step}: archive HF fallback"

    summary.zpe = primary.zpe
    summary.etot = primary.etot
    if summary.zpe is not None:
        summary.field_sources["zpe"] = f"Step {primary.input_step}: Zero-point correction"
    if summary.etot is not None:
        summary.field_sources["etot"] = f"Step {primary.input_step}: electronic + ZPE"

    summary.scf_energies = list(trajectory.scf_energies)
    summary.field_sources["scf_curve"] = f"Step {trajectory.input_step}: {trajectory.route}"

    summary.nimag = _count_imag(primary.text)
    if summary.nimag is None:
        summary.nimag = _count_imag(text)
    if summary.nimag is not None:
        summary.field_sources["nimag"] = f"Step {primary.input_step}: frequency/archive data"

    freq_requested = any(step.is_freq for step in steps if step.input_step == primary.input_step)
    freq_output = bool(re.search(r"Harmonic frequencies|Frequencies\s+--", primary.text, flags=re.I))
    if not freq_output:
        same_input_text = "\n".join(step.text for step in steps if step.input_step == primary.input_step)
        freq_output = bool(re.search(r"Harmonic frequencies|Frequencies\s+--", same_input_text, flags=re.I))
    summary.freq_completed = freq_output if freq_requested else None

    summary.stable_1, summary.stable_2 = _select_stability(steps)
    summary.opt_conv, summary.freq_conv = _parse_convergence(steps)
    summary.init_xyz, summary.opt_xyz = _extract_standard_orientation_xyz(text)

    errors = [step.error_link for step in steps if step.error_link]
    summary.error_link = errors[-1] if errors else None
    summary.normal_termination = summary.error_link is None and bool(RE_NORMAL.search(text))

    # Consistency diagnostics; warnings are displayed later by the GUI/log.
    if primary.scf_energies and primary.archive_hfs:
        diff = abs(primary.scf_energies[-1] - primary.archive_hfs[-1])
        if diff > 5e-6:
            summary.warnings.append(
                f"SCF/archive HF differ by {diff:.3e} Ha; SCF Done was selected."
            )
    if summary.hf is not None and summary.etot is not None and summary.zpe is not None:
        diff = abs((summary.hf + summary.zpe) - summary.etot)
        if diff > 5e-7:
            summary.warnings.append(f"HF + ZPE differs from Etot by {diff:.3e} Ha.")
    if not summary.state:
        summary.warnings.append("Electronic state was not found.")
    if not summary.sym:
        summary.warnings.append("Point group was not found.")
    return summary


def minimum_etot(summaries: List[LogSummary]) -> Optional[float]:
    values = [float(summary.etot) for summary in summaries if isinstance(summary.etot, (int, float))]
    return min(values) if values else None


def delta_e_ev(summary: LogSummary, base_etot: Optional[float]) -> Optional[float]:
    if base_etot is None or not isinstance(summary.etot, (int, float)):
        return None
    return (float(summary.etot) - base_etot) * HARTREE_TO_EV


# Compatibility key retained for callers from older ChemAuto releases.
# ChemAuto 7.1.2 deliberately uses ONE global relative-energy zero for every
# record currently loaded by the user.  No automatic grouping by composition,
# charge, multiplicity, directory or filename is performed.
_GLOBAL_ENERGY_KEY: tuple[str, int | None] = ("__global__", None)


def comparison_group_key(summary: LogSummary) -> tuple[str, int | None]:
    """Return the single global comparison key used by ChemAuto 7.1.2.

    The function name is kept only for source compatibility with older modules.
    """
    return _GLOBAL_ENERGY_KEY


def minimum_etot_by_group(summaries: List[LogSummary]) -> Dict[tuple[str, int | None], float]:
    """Compatibility wrapper returning at most one global Etot reference."""
    base = minimum_etot(summaries)
    return {} if base is None else {_GLOBAL_ENERGY_KEY: base}


def grouped_delta_e_ev(summary: LogSummary, bases: Dict[tuple[str, int | None], float]) -> Optional[float]:
    """Compatibility wrapper calculating ΔE from the single global minimum."""
    if not isinstance(summary.etot, (int, float)):
        return None
    base = bases.get(_GLOBAL_ENERGY_KEY)
    return delta_e_ev(summary, base)
