from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DOSPair:
    key: str
    curve: Path | None = None
    line: Path | None = None

    @property
    def complete(self) -> bool:
        return self.curve is not None and self.line is not None


def identify_dos_pairs(paths: Iterable[str | Path]) -> list[DOSPair]:
    """Strictly pair selected ``*_curve.txt`` and ``*_line.txt`` files.

    Pairing never crosses directories: both files must share the same parent
    folder and the same prefix before ``_curve`` / ``_line``.
    """
    found: dict[tuple[Path, str], dict[str, Path]] = {}
    for raw in paths:
        p = Path(raw)
        name = p.name
        if name.endswith("_curve.txt"):
            key = name[: -len("_curve.txt")]
            found.setdefault((p.parent, key), {})["curve"] = p
        elif name.endswith("_line.txt"):
            key = name[: -len("_line.txt")]
            found.setdefault((p.parent, key), {})["line"] = p
    out: list[DOSPair] = []
    for (parent, stem), vals in sorted(found.items(), key=lambda item: (str(item[0][0]).lower(), item[0][1].lower())):
        out.append(DOSPair(key=stem, curve=vals.get("curve"), line=vals.get("line")))
    return out


def scan_dos_pairs(folder: str | Path, recursive: bool = True) -> list[DOSPair]:
    root = Path(folder)
    if not root.is_dir():
        raise NotADirectoryError(root)
    files = root.rglob("*.txt") if recursive else root.glob("*.txt")
    # Preserve folder in the pairing key to avoid pairing same-named files from
    # different subfolders. The public key is then shown relative to root.
    found: dict[tuple[Path, str], dict[str, Path]] = {}
    for p in files:
        name = p.name
        if name.endswith("_curve.txt"):
            stem = name[: -len("_curve.txt")]
            found.setdefault((p.parent, stem), {})["curve"] = p
        elif name.endswith("_line.txt"):
            stem = name[: -len("_line.txt")]
            found.setdefault((p.parent, stem), {})["line"] = p
    out: list[DOSPair] = []
    for (parent, stem), vals in sorted(found.items(), key=lambda x: (str(x[0][0]).lower(), x[0][1].lower())):
        rel_parent = parent.relative_to(root)
        key = str(rel_parent / stem) if str(rel_parent) != "." else stem
        out.append(DOSPair(key=key, curve=vals.get("curve"), line=vals.get("line")))
    return out
