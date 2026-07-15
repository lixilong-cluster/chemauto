"""Stable sorting rules for ChemAuto result records.

The selected table column is the primary key.  Within equal primary values,
records are ordered by Etot; HF is used only when Etot is unavailable.  Missing
primary values are always placed after valid values.
"""
from __future__ import annotations

from math import inf
from typing import Any, Iterable, List, Sequence

from chemauto.core.gaussian_parser import LogSummary


def energy_secondary_key(record: LogSummary) -> tuple[int, float, str]:
    """Return one comparable energy key: Etot when present, otherwise HF."""
    if isinstance(record.etot, (int, float)):
        return (0, float(record.etot), record.file.casefold())
    if isinstance(record.hf, (int, float)):
        return (0, float(record.hf), record.file.casefold())
    return (1, inf, record.file.casefold())


def _state_key(record: LogSummary) -> int:
    """Use spin multiplicity as the State-column primary key."""
    multiplicity = record.multiplicity
    if not isinstance(multiplicity, int):
        text = (record.state or "").strip()
        try:
            multiplicity = int(text.split("-", 1)[0])
        except Exception:
            multiplicity = 10**9
    return multiplicity


def primary_value(record: LogSummary, field: str) -> Any:
    if field == "file":
        return record.file.casefold()
    if field == "sym":
        return (record.sym or "").casefold()
    if field == "state":
        return _state_key(record)
    if field == "hf":
        return float(record.hf)
    if field == "zpe":
        return float(record.zpe)
    if field in {"etot", "delta_e"}:
        return energy_secondary_key(record)[:2]
    if field == "nimag":
        return int(record.nimag)
    if field == "freq_done":
        return 0 if record.freq_completed is True else 1
    if field == "opt_conv":
        return (record.opt_conv.to_compact() if record.opt_conv else "").casefold()
    if field == "freq_conv":
        return (record.freq_conv.to_compact() if record.freq_conv else "").casefold()
    if field == "stable1":
        return _stable_rank(record.stable_1)
    if field == "stable2":
        return _stable_rank(record.stable_2)
    return record.file.casefold()


def _stable_rank(value: Any) -> int:
    text = "" if value is None else str(value).strip().lower()
    if text == "stable":
        return 0
    if text == "unstable":
        return 1
    if text:
        return 2
    return 3


def primary_missing(record: LogSummary, field: str) -> bool:
    if field == "file":
        return not bool(record.file.strip())
    if field == "sym":
        return not bool((record.sym or "").strip())
    if field == "state":
        return record.multiplicity is None and not bool((record.state or "").strip())
    if field == "hf":
        return not isinstance(record.hf, (int, float))
    if field == "zpe":
        return not isinstance(record.zpe, (int, float))
    if field in {"etot", "delta_e"}:
        # HF-only single-point records remain sortable after Etot records.
        return not isinstance(record.etot, (int, float)) and not isinstance(record.hf, (int, float))
    if field == "nimag":
        return not isinstance(record.nimag, int)
    if field == "freq_done":
        return record.freq_completed is None
    if field == "opt_conv":
        return record.opt_conv is None
    if field == "freq_conv":
        return record.freq_conv is None
    if field == "stable1":
        return not bool((record.stable_1 or "").strip())
    if field == "stable2":
        return not bool((record.stable_2 or "").strip())
    return False


def sort_records(records: Sequence[LogSummary], field: str, descending: bool = False) -> List[LogSummary]:
    """Sort by selected primary field with Etot/HF as the ascending secondary."""
    valid = [record for record in records if not primary_missing(record, field)]
    missing = [record for record in records if primary_missing(record, field)]

    # Stable sorting makes the secondary key independent of primary direction.
    valid.sort(key=energy_secondary_key)
    valid.sort(key=lambda record: primary_value(record, field), reverse=descending)
    missing.sort(key=energy_secondary_key)
    return valid + missing
