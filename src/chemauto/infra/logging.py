"""Application-wide logging utilities.

This module preserves the public interface of the legacy ``logcreator``
module — :func:`logged_input`, :func:`logged_print`, :func:`setup_logging`,
:func:`clean_logs`, :func:`global_exception_handler` — so feature modules
can import them with no behavioural change. The only difference: the log
file is now anchored at ``~/.chemauto/chemauto.log`` (via
:func:`chemauto.infra.paths.get_user_data_dir`) rather than the current
working directory, so the location is stable regardless of how ChemAuto
is launched.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from chemauto.infra.paths import get_user_data_dir

RETENTION_DAYS = 3
LOG_FILE: Path = get_user_data_dir() / "chemauto.log"


def setup_logging() -> None:
    """Initialise the root logger to write to :data:`LOG_FILE`.

    The parent directory is guaranteed to exist by
    :func:`chemauto.infra.paths.get_user_data_dir`, which runs at import
    time as part of computing :data:`LOG_FILE` — so we don't recreate it
    here. ``paths.get_user_data_dir`` is the single source of truth for
    creating ``~/.chemauto/``.
    """
    if not LOG_FILE.exists():
        LOG_FILE.touch()
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def clean_logs() -> None:
    """Trim :data:`LOG_FILE` to the last :data:`RETENTION_DAYS` days of entries.

    Behaviour matches the legacy implementation: scan from the top, drop
    entries whose timestamp is older than the cutoff *up to* the first
    line that is recent enough; from that point on, keep everything,
    including unparseable continuation lines (multi-line tracebacks).
    """
    if not LOG_FILE.exists():
        return

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    keep: list[str] = []
    started = False
    try:
        with LOG_FILE.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return
    
    for line in lines:
        if not started:
            try:
                ts_str = line.split(" - ", 1)[0]
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if ts >= cutoff:
                started = True
            else:
                continue
        keep.append(line)

    try:
        with LOG_FILE.open("w", encoding="utf-8") as f:
            f.writelines(keep)
    except OSError:
        return


def logged_input(prompt: str) -> str:
    """Drop-in replacement for :func:`input` that mirrors prompt + answer to the log."""
    user_input = input(prompt)
    logging.info(f"Input: {prompt}{user_input}")
    return user_input


def logged_print(*args: Any, **kwargs: Any) -> None:
    """Drop-in replacement for :func:`print` that also writes the message to the log."""
    message = " ".join(map(str, args))
    logging.info(message)
    print(*args, **kwargs)


def global_exception_handler(exctype, value, traceback) -> None:
    """``sys.excepthook`` that records uncaught exceptions and exits non-zero."""
    logging.exception(
        "Unhandled exception occurred", exc_info=(exctype, value, traceback)
    )
    sys.exit(1)
