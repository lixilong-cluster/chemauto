#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve files related to one Gaussian log by an exact shared stem.

The resolver is intentionally conservative: ``sample.log`` is associated with
``sample.gjf``, ``sample.chk`` and suffix variants such as
``sample-check.chk`` / ``sample-stable.chk``.  It does not fuzzy-match other
isomers whose names merely look similar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass
class RelatedFiles:
    log: Optional[Path] = None
    gjf: Optional[Path] = None
    com: Optional[Path] = None
    chk: Optional[Path] = None
    fchk: Optional[Path] = None
    fch: Optional[Path] = None
    xyz: Optional[Path] = None
    check_chk: Optional[Path] = None
    stable_chk: Optional[Path] = None
    extras: Dict[str, Path] = field(default_factory=dict)

    def existing(self) -> Dict[str, Path]:
        out: Dict[str, Path] = {}
        for name in (
            "log", "gjf", "com", "chk", "fchk", "fch", "xyz",
            "check_chk", "stable_chk",
        ):
            value = getattr(self, name)
            if value is not None and value.exists():
                out[name] = value
        out.update({k: v for k, v in self.extras.items() if v.exists()})
        return out

    @property
    def input_file(self) -> Optional[Path]:
        return self.gjf or self.com

    @property
    def formatted_checkpoint(self) -> Optional[Path]:
        return self.fchk or self.fch


def _casefold_index(directory: Path) -> Dict[str, Path]:
    try:
        return {p.name.casefold(): p for p in directory.iterdir() if p.is_file()}
    except OSError:
        return {}


def resolve_related_files(log_path: str | Path) -> RelatedFiles:
    log = Path(log_path).resolve()
    directory = log.parent
    stem = log.stem
    idx = _casefold_index(directory)

    def find(name: str) -> Optional[Path]:
        return idx.get(name.casefold())

    result = RelatedFiles(
        log=log if log.exists() else find(log.name),
        gjf=find(f"{stem}.gjf"),
        com=find(f"{stem}.com"),
        chk=find(f"{stem}.chk"),
        fchk=find(f"{stem}.fchk"),
        fch=find(f"{stem}.fch"),
        xyz=find(f"{stem}.xyz"),
        check_chk=find(f"{stem}-check.chk"),
        stable_chk=find(f"{stem}-stable.chk"),
    )
    return result


def resolve_many(log_paths: Iterable[str | Path]) -> Dict[str, RelatedFiles]:
    return {str(Path(p).resolve()): resolve_related_files(p) for p in log_paths}
