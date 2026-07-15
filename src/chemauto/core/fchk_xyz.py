#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_fchk_to_xyz.py

Convert Gaussian formatted checkpoint files (.fchk/.fch) to .xyz.

Usage:
    python convert_fchk_to_xyz.py file1.fchk [file2.fchk ...]
    python convert_fchk_to_xyz.py --out-dir output_folder file1.fchk file2.fchk
    python convert_fchk_to_xyz.py --overwrite file1.fchk

The XYZ comment line is the original fchk/fch file name.
Coordinates are read from "Current cartesian coordinates" in the fchk file.
Gaussian fchk coordinates are in Bohr, so this script converts them to Angstrom.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List


BOHR_TO_ANGSTROM = 0.529177210903


PERIODIC_SYMBOLS = {
    1: "H", 2: "He",
    3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
    11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
    19: "K", 20: "Ca", 21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe",
    27: "Co", 28: "Ni", 29: "Cu", 30: "Zn", 31: "Ga", 32: "Ge", 33: "As", 34: "Se",
    35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y", 40: "Zr", 41: "Nb", 42: "Mo",
    43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
    51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La", 58: "Ce",
    59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy",
    67: "Ho", 68: "Er", 69: "Tm", 70: "Yb", 71: "Lu", 72: "Hf", 73: "Ta", 74: "W",
    75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg", 81: "Tl", 82: "Pb",
    83: "Bi", 84: "Po", 85: "At", 86: "Rn",
}


def read_text_lossless(path: Path) -> List[str]:
    """Read text while tolerating encoding oddities."""
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def parse_fchk_array(lines: List[str], key: str) -> List[str]:
    """
    Parse an array block in a Gaussian fchk file.

    Typical form:
        Atomic numbers                          I   N=           9
           27           6           6 ...
        Current cartesian coordinates           R   N=          27
          3.106699870460E+00 -3.710596812972E-01 ...
    """
    for i, line in enumerate(lines):
        if line.startswith(key):
            m = re.search(r"\bN=\s*(\d+)", line)
            if not m:
                raise ValueError(f'Found "{key}", but cannot find N= count.')
            n = int(m.group(1))
            values: List[str] = []
            j = i + 1
            while j < len(lines) and len(values) < n:
                values.extend(lines[j].split())
                j += 1
            if len(values) < n:
                raise ValueError(f'"{key}" expects {n} values, but only {len(values)} were read.')
            return values[:n]
    raise ValueError(f'Cannot find "{key}" in this fchk file.')


def parse_fchk_geometry(fchk_path: Path):
    lines = read_text_lossless(fchk_path)

    atomic_numbers_raw = parse_fchk_array(lines, "Atomic numbers")
    coordinates_raw = parse_fchk_array(lines, "Current cartesian coordinates")

    atomic_numbers = [int(x) for x in atomic_numbers_raw]
    coordinates_bohr = [float(x.replace("D", "E").replace("d", "e")) for x in coordinates_raw]

    if len(coordinates_bohr) != 3 * len(atomic_numbers):
        raise ValueError(
            f"Coordinate count mismatch: {len(coordinates_bohr)} coordinate values "
            f"for {len(atomic_numbers)} atoms."
        )

    atoms = []
    for i, atomic_number in enumerate(atomic_numbers):
        symbol = PERIODIC_SYMBOLS.get(atomic_number, f"X{atomic_number}")
        x_bohr, y_bohr, z_bohr = coordinates_bohr[3 * i: 3 * i + 3]
        atoms.append((
            symbol,
            x_bohr * BOHR_TO_ANGSTROM,
            y_bohr * BOHR_TO_ANGSTROM,
            z_bohr * BOHR_TO_ANGSTROM,
        ))
    return atoms


def unique_output_path(path: Path) -> Path:
    """Avoid overwriting unless requested."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for i in range(1, 10000):
        candidate = parent / f"{stem}_{i:03d}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Cannot create unique output path for {path}")


def write_xyz(atoms, xyz_path: Path, comment: str) -> None:
    with xyz_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{comment}\n")
        for symbol, x, y, z in atoms:
            f.write(f"{symbol:<2s} {x:16.8f} {y:16.8f} {z:16.8f}\n")


def convert_one(fchk_path: Path, out_dir: Path | None = None, overwrite: bool = False) -> Path:
    fchk_path = fchk_path.expanduser().resolve()

    if not fchk_path.exists():
        raise FileNotFoundError(f"File not found: {fchk_path}")

    if fchk_path.suffix.lower() not in {".fchk", ".fch"}:
        raise ValueError(f"Not a .fchk/.fch file: {fchk_path}")

    atoms = parse_fchk_geometry(fchk_path)

    target_dir = out_dir.expanduser().resolve() if out_dir else fchk_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    xyz_path = target_dir / f"{fchk_path.stem}.xyz"
    if not overwrite:
        xyz_path = unique_output_path(xyz_path)

    write_xyz(atoms, xyz_path, comment=fchk_path.name)
    return xyz_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Gaussian .fchk/.fch current Cartesian coordinates to .xyz."
    )
    parser.add_argument("files", nargs="+", help="Input .fchk/.fch file(s)")
    parser.add_argument("--out-dir", default=None, help="Optional output directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .xyz file")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir) if args.out_dir else None

    ok = 0
    failed = 0
    for file_name in args.files:
        try:
            xyz_path = convert_one(Path(file_name), out_dir=out_dir, overwrite=args.overwrite)
            print(f"[OK] {file_name} -> {xyz_path}")
            ok += 1
        except Exception as exc:
            print(f"[ERROR] {file_name}: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"Done with errors: {ok} converted, {failed} failed.", file=sys.stderr)
        return 1

    print(f"Done: {ok} file(s) converted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
