from __future__ import annotations

from pathlib import Path


def parse_xyz_frames(path: str | Path) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    frames: list[str] = []
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break
        try:
            n_atoms = int(lines[i].strip())
        except ValueError as exc:
            raise ValueError(f"Invalid XYZ atom count at line {i + 1}: {lines[i]!r}") from exc
        comment = lines[i + 1] if i + 1 < len(lines) else ""
        atom_lines = lines[i + 2:i + 2 + n_atoms]
        if len(atom_lines) != n_atoms:
            raise ValueError(f"Incomplete XYZ frame beginning at line {i + 1}.")
        frames.append("\n".join([str(n_atoms), comment, *atom_lines]) + "\n")
        i += 2 + n_atoms
    if not frames:
        raise ValueError("No XYZ frames were found.")
    return frames
