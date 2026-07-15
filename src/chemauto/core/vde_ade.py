from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from chemauto.core.gaussian_parser import LogSummary, parse_gaussian_log

HARTREE_TO_EV = 27.211386245988


@dataclass
class VDEADEResult:
    label: str
    multiplicity: int | None
    vde_ev: float | None
    ade_ev: float | None
    warnings: list[str]


def _composition_signature(summary: LogSummary) -> tuple[tuple[str, int], ...]:
    raw = (summary.cluster or "").strip()
    # Gaussian Stoichiometry commonly appends charge/multiplicity, e.g.
    # C3Fe4(1-,12) versus C3Fe4(1,11).  Those suffixes are not composition.
    formula = raw.split("(", 1)[0]
    parts = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    if not parts:
        return tuple()
    counts: dict[str, int] = {}
    for element, count in parts:
        counts[element] = counts.get(element, 0) + (int(count) if count else 1)
    return tuple(sorted(counts.items()))


def calculate_three_file_vde_ade(
    anion_log: str | Path,
    neutral_minus_log: str | Path,
    neutral_plus_log: str | Path,
) -> tuple[LogSummary, list[VDEADEResult], list[str]]:
    anion = parse_gaussian_log(str(anion_log))
    neutrals = [
        ("N−1", parse_gaussian_log(str(neutral_minus_log))),
        ("N+1", parse_gaussian_log(str(neutral_plus_log))),
    ]
    global_warnings: list[str] = []

    if anion.hf is None:
        global_warnings.append("Anion HF/electronic energy is missing; VDE cannot be calculated.")
    if anion.etot is None:
        global_warnings.append("Anion Etot (electronic + ZPE) is missing; ADE cannot be calculated.")

    sig = _composition_signature(anion)
    out: list[VDEADEResult] = []
    for label, neutral in neutrals:
        warnings: list[str] = []
        if sig and _composition_signature(neutral) and _composition_signature(neutral) != sig:
            warnings.append("Atomic composition differs from the anion reference.")
        vde = None
        ade = None
        if anion.hf is not None and neutral.hf is not None:
            vde = (neutral.hf - anion.hf) * HARTREE_TO_EV
        else:
            warnings.append("VDE unavailable because an HF/electronic energy is missing.")
        if anion.etot is not None and neutral.etot is not None:
            ade = (neutral.etot - anion.etot) * HARTREE_TO_EV
        else:
            warnings.append("ADE unavailable because Etot/ZPE is missing; no HF fallback was used.")
        out.append(
            VDEADEResult(
                label=label,
                multiplicity=neutral.multiplicity,
                vde_ev=vde,
                ade_ev=ade,
                warnings=warnings,
            )
        )
    return anion, out, global_warnings
