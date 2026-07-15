from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from chemauto.core.gjf_document import (
    GJFDocument, coordinates_from_xyz_text, select_primary_gjf, split_route, token_key
)
from chemauto.core.gaussian_parser import parse_gaussian_log

DEFAULT_NPROC = "64"
DEFAULT_MEM = "64GB"


@dataclass
class GeneratedJob:
    job_type: str
    multiplicity: int
    directory: Path
    gjf: Path
    copied_oldchk: Optional[Path]
    source_mode: str = "checkpoint"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_gjf(input_path: str | Path) -> Path:
    return select_primary_gjf(input_path)


def get_link0_value(link0_lines, key: str) -> Optional[str]:
    pat = re.compile(rf"^\s*%{re.escape(key)}\s*=\s*(.+?)\s*$", re.I)
    for line in link0_lines:
        m = pat.match(line)
        if m:
            return m.group(1).strip().strip('"')
    return None


def remove_job_geometry_tokens(tokens: list[str], remove_scf: bool = False) -> list[str]:
    remove_keys = {"opt", "freq", "geom", "guess", "stable", "irc", "scan", "sp"}
    if remove_scf:
        remove_keys.add("scf")
    out = []
    for token in tokens:
        if token.startswith("#") or token_key(token) not in remove_keys:
            out.append(token)
    return out


def convert_basis_to_chkbasis(tokens: list[str]) -> list[str]:
    out: list[str] = []
    basis_seen = False
    for token in tokens:
        low = token.lower()
        if low in {"gen", "genecp"}:
            out.append("chkbasis")
            basis_seen = True
        elif "/" in token and "=" not in token and not low.startswith("iop("):
            method = token.split("/", 1)[0]
            out.append(f"{method}/chkbasis")
            basis_seen = True
        elif low == "chkbasis":
            out.append(token)
            basis_seen = True
        else:
            out.append(token)
    if not basis_seen:
        # Preserve the original route prefix in position zero.
        insert = 1 if out and out[0].startswith("#") else 0
        out.insert(insert + 1, "chkbasis")
    return out


def _ensure_superfine(tokens: list[str]) -> list[str]:
    if not any(t.lower().replace(" ", "") in {"int=superfine", "integral=superfine"} for t in tokens):
        tokens.append("int=superfine")
    return tokens


def build_checkpoint_route(original_route: str, job_type: str) -> str:
    # Exact legacy behaviour: SCF is removed, basis becomes ChkBasis, geometry
    # and guess are read from the copied checkpoint.
    tokens = split_route(original_route)
    tokens = remove_job_geometry_tokens(tokens, remove_scf=True)
    tokens = convert_basis_to_chkbasis(tokens)
    _ensure_superfine(tokens)
    if job_type.upper() == "ADE":
        tokens.extend(["opt=(calcfc,maxcycle=200)", "freq"])
    else:
        tokens.append("sp")
    tokens.extend(["geom=check", "guess=read"])
    return " ".join(tokens)


def build_coordinate_route(original_route: str, job_type: str) -> str:
    # No checkpoint: retain method/basis, SCF and other useful keywords, but
    # remove geometry/guess/job keywords that require a checkpoint.
    tokens = remove_job_geometry_tokens(split_route(original_route), remove_scf=False)
    _ensure_superfine(tokens)
    if job_type.upper() == "ADE":
        tokens.extend(["opt=(calcfc,maxcycle=200)", "freq"])
    else:
        tokens.append("sp")
    return " ".join(tokens)


def _resolve_log(input_path: str | Path, gjf: Path) -> Path:
    p = Path(input_path).resolve()
    if p.is_file() and p.suffix.lower() in {".log", ".out"}:
        return p
    directory = gjf.parent
    for suffix in (".log", ".out"):
        same = gjf.with_suffix(suffix)
        if same.is_file():
            return same
    for suffix in (".log", ".out"):
        direct = directory / f"{directory.name}{suffix}"
        if direct.is_file():
            return direct
    logs = sorted(directory.glob("*.log")) + sorted(directory.glob("*.out"))
    if len(logs) == 1:
        return logs[0]
    names = ", ".join(x.name for x in logs) or "none"
    raise ValueError(f"No unique Gaussian log was found for coordinate fallback. Candidates: {names}")


def _make_checkpoint_gjf(nproc: str, mem: str, oldchk: str, newchk: str, route: str,
                         title: str, charge: int, mult: int) -> str:
    return (
        f"%nprocshared={nproc}\n%mem={mem}\n%oldchk={oldchk}\n%chk={newchk}\n"
        f"{route}\n\n{title}\n\n{charge} {mult}\n\n\n\n"
    )


def _make_coordinate_gjf(nproc: str, mem: str, newchk: str, route: str, title: str,
                         charge: int, mult: int, coordinates: list[str], tail: list[str]) -> str:
    parts = [
        f"%nprocshared={nproc}", f"%mem={mem}", f"%chk={newchk}", route, "", title, "",
        f"{charge} {mult}", *coordinates, "",
    ]
    parts.extend(tail)
    return "\n".join(parts).rstrip() + "\n"


def generate_vde_ade_jobs(
    input_path: str | Path,
    job_types: Iterable[str] = ("VDE", "ADE"),
    output_root: str | Path | None = None,
) -> list[GeneratedJob]:
    """Generate N−1/N+1 VDE/ADE Gaussian jobs.

    Preferred mode copies the original checkpoint and retains the verified
    ``%oldchk + ChkBasis + geom=check + guess=read`` workflow.  When the
    checkpoint is absent, ChemAuto deterministically selects the primary GJF,
    extracts the optimized coordinates from the corresponding log, preserves
    the original method/basis and custom Gen/GenECP tail, and writes explicit-
    coordinate inputs without ``%oldchk``, ``geom=check`` or ``guess=read``.
    """
    gjf = resolve_gjf(input_path)
    document = GJFDocument.from_file(gjf)
    source_link = document.links[0]
    calc_dir = gjf.parent
    parent_dir = Path(output_root).resolve() if output_root else calc_dir.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    stem = gjf.stem

    nproc = source_link.get_link0("nprocshared") or source_link.get_link0("nproc") or DEFAULT_NPROC
    mem = source_link.get_link0("mem") or DEFAULT_MEM
    chk_value = source_link.get_link0("chk")
    oldchk_path: Optional[Path] = None
    if chk_value:
        oldchk_path = Path(chk_value)
        if not oldchk_path.is_absolute():
            oldchk_path = calc_dir / oldchk_path
        if not oldchk_path.is_file():
            oldchk_path = None

    old_mult = source_link.multiplicity
    new_mults = [m for m in (old_mult - 1, old_mult + 1) if m >= 1]
    if not new_mults:
        raise ValueError(f"Cannot generate N−1/N+1 multiplicities from M={old_mult}.")

    coordinate_lines: list[str] = []
    tail_lines: list[str] = []
    source_mode = "checkpoint" if oldchk_path else "coordinates"
    if not oldchk_path:
        log_path = _resolve_log(input_path, gjf)
        summary = parse_gaussian_log(log_path)
        if not summary.opt_xyz:
            raise ValueError(f"No optimized structure could be extracted from {log_path.name}.")
        coordinate_lines = coordinates_from_xyz_text(summary.opt_xyz)
        tail_lines = list(source_link.tail_lines)
        basis = source_link.components.basis.lower()
        if basis in {"gen", "genecp"} and not source_link.has_custom_basis_tail():
            raise ValueError(
                f"{gjf.name} uses {source_link.components.basis}, but no complete custom basis section "
                "was found. Select the main GJF containing the Gen/GenECP basis block."
            )

    results: list[GeneratedJob] = []
    for raw_type in job_types:
        job_type = raw_type.upper()
        if job_type not in {"VDE", "ADE"}:
            raise ValueError(f"Unknown job type: {raw_type}")
        route = (
            build_checkpoint_route(source_link.route, job_type)
            if oldchk_path else build_coordinate_route(source_link.route, job_type)
        )
        for mult in new_mults:
            job_name = f"{stem}-{job_type}-M{mult}"
            job_dir = parent_dir / job_name
            job_dir.mkdir(exist_ok=True)
            new_gjf = job_dir / f"{job_name}.gjf"
            copied_chk: Optional[Path] = None
            title = (
                f"{stem} VDE M{mult} single point"
                if job_type == "VDE" else f"{stem} ADE M{mult} neutral opt freq"
            )
            if oldchk_path:
                copied_chk = job_dir / oldchk_path.name
                shutil.copy2(oldchk_path, copied_chk)
                content = _make_checkpoint_gjf(
                    nproc, mem, oldchk_path.name, f"{job_name}.chk", route, title, 0, mult
                )
            else:
                content = _make_coordinate_gjf(
                    nproc, mem, f"{job_name}.chk", route, title, 0, mult,
                    coordinate_lines, tail_lines,
                )
            write_text(new_gjf, content)
            results.append(GeneratedJob(job_type, mult, job_dir, new_gjf, copied_chk, source_mode))
    return results
