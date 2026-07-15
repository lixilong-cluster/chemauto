"""Filesystem path helpers.

ChemAuto deals with three different "anchors" depending on the situation:

* **User data directory** — ``~/.chemauto/``. All writable runtime state
  (log file, user config) lives here. Stable regardless of how ChemAuto
  is launched.
* **Bundled resources** — files shipped *inside* the package
  (``src/chemauto/resources/``), such as the OriginLab DOS template.
  Located via :func:`get_resource_path` so the same call works in a
  source checkout, after ``pip install``, and when frozen by PyInstaller.
* **Project root** — the source-checkout directory that contains
  ``pyproject.toml``. Useful only during development; not meaningful
  after install. Provided here for completeness.
"""

import sys
from importlib import resources
from pathlib import Path


def is_frozen() -> bool:
    """Return ``True`` when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_user_data_dir() -> Path:
    """Return ``~/.chemauto/``, creating it if it does not yet exist.

    All writable runtime files (log, user config) live here. Using the
    user's home directory means the location is stable across
    development, ``pip install`` and PyInstaller bundles, and never
    requires write access to system directories.
    """
    d = Path.home() / ".chemauto"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root() -> Path:
    """Return the source-checkout root (the directory holding ``pyproject.toml``).

    Only meaningful during development. After ``pip install`` the package
    lives inside ``site-packages`` and there is no real "project root";
    in that case this function returns the parent of the installed
    ``src/`` location, which is *not* guaranteed to be writable. Most
    callers should prefer :func:`get_user_data_dir` (writable state) or
    :func:`get_resource_path` (read-only assets) instead.
    """
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # __file__ -> .../src/chemauto/infra/paths.py
    # parents[0]=infra, parents[1]=chemauto, parents[2]=src, parents[3]=root
    return Path(__file__).resolve().parents[3]


def get_resource_path(relative: str) -> Path:
    """Return the absolute path to a packaged resource.

    Resources are shipped under ``src/chemauto/resources/`` and accessed
    via :mod:`importlib.resources`, which works in source checkouts,
    after ``pip install``, and (with the PyInstaller branch below) when
    frozen into a single-file executable.

    Parameters
    ----------
    relative : str
        Resource name relative to the ``chemauto.resources`` package,
        e.g. ``"DOS-default.otpu"``.

    Returns
    -------
    Path
        Absolute filesystem path. The caller is responsible for checking
        existence — this function does not guarantee the file is there.
    """
    if is_frozen():
        # PyInstaller extracts data files into ``sys._MEIPASS`` mirroring
        # the package layout, so ``chemauto/resources/<relative>`` lives
        # under that root.
        return Path(sys._MEIPASS) / "chemauto" / "resources" / relative  # type: ignore[attr-defined]

    traversable = resources.files("chemauto.resources").joinpath(relative)
    return Path(str(traversable))
