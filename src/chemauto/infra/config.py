"""Configuration management.

ChemAuto distinguishes two kinds of configuration:

1. **User config** — mutable, per-user numeric parameters such as
   ``PES_FWHM`` or the default DOS x-range. Stored as JSON at
   ``~/.chemauto/config.json`` and accessed via :func:`load_user_config`
   / :func:`save_user_config`.

2. **Bundled resources** — immutable assets that ship with the package,
   such as the OriginLab DOS template. Located via
   :func:`get_template_path`, which delegates to
   :func:`chemauto.infra.paths.get_resource_path` so the same call works
   in a source checkout, after ``pip install``, and inside a PyInstaller
   bundle.

Splitting these two avoids the legacy mistake of treating the template
filename as a writable user setting living next to the executable: the
template moves with the package, while user knobs live in the user's
home directory.
"""

import json
from pathlib import Path
from typing import Any

from chemauto.infra.paths import get_resource_path, get_user_data_dir

USER_CONFIG_FILE: Path = get_user_data_dir() / "config.json"

DEFAULT_USER_CONFIG: dict[str, Any] = {
    # PES exporter (legacy: chemauto_config.json)
    "PES_Xlow": 0.0,
    "PES_Xhigh": 5.0,
    "npoints": 5000,
    "PES_FWHM": 0.2,
    "PES_str": 1.0,
    "PES_scale": 5.0,
    "default_photon_energy": 3.493,
    # DOS plotter (legacy: chemauto_config.json)
    "default_x_range": [0, 3.3],
    "default_y_range": [-0.03, 6.5],
    "show_graph": False,
    # Name only — resolved to an absolute filesystem path via
    # `get_template_path()`. Feature modules must never interpret this
    # value as a path directly.
    "dos_template_name": "DOS-default.otpu",
    "dos_template_path": "",
    # GUI theme label persisted across sessions. Task 2.5 rolled back the
    # qt-material integration; today only "System Default" is wired up. The
    # field is preserved (rather than removed) so a future v6.1 theme pass
    # can re-enable additional labels without a config-format break.
    "ui_theme": "ChemAuto Light",
    # 3D viewer defaults
    "viewer_show_grid": False,
    "viewer_show_axis": False,
    # Parallel Gaussian log parsing. A modest value avoids saturating disks.
    "log_parse_workers": 4,
    # Optional Gaussian input template used by GUI structure export.
    "gjf_template_path": "",
    # Optional applications used by Related Files/Open actions. Blank means Windows default.
    "text_editor_path": "__WINDOWS_NOTEPAD__",
    "log_viewer_path": "__SYSTEM_DEFAULT__",
    "fchk_viewer_path": "__SYSTEM_DEFAULT__",
    "xyz_viewer_path": "__SYSTEM_DEFAULT__",
}


def load_user_config() -> dict[str, Any]:
    """Load the user config, filling missing keys from :data:`DEFAULT_USER_CONFIG`.

    The file is rewritten when keys were added so the user can inspect a
    complete settings file.
    """
    config: dict[str, Any] = {}
    if USER_CONFIG_FILE.exists():
        try:
            config = json.loads(USER_CONFIG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            config = {}

    needs_write = not USER_CONFIG_FILE.exists()
    for key, value in DEFAULT_USER_CONFIG.items():
        if key not in config:
            config[key] = value
            needs_write = True

    if needs_write:
        save_user_config(config)
    return config


def save_user_config(config: dict[str, Any]) -> None:
    """Persist the given mapping to :data:`USER_CONFIG_FILE`.

    The parent directory is created by
    :func:`chemauto.infra.paths.get_user_data_dir` at import time (when
    :data:`USER_CONFIG_FILE` is computed). ``paths`` owns directory
    creation; this function only writes.
    """
    USER_CONFIG_FILE.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def get_template_path(name: str | None = None) -> Path:
    """Resolve a template (e.g. an OriginLab ``.otpu``) shipped with the package.

    Parameters
    ----------
    name : str, optional
        Template filename relative to ``chemauto.resources`` (e.g.
        ``"DOS-default.otpu"``). When omitted, the name stored in the
        user config under ``dos_template_name`` is used.

    Returns
    -------
    Path
        Absolute path to the template on disk.

    Raises
    ------
    FileNotFoundError
        If the template is not present in the bundled resources directory.
    """
    cfg = load_user_config()
    custom = str(cfg.get("dos_template_path", "") or "").strip().strip('"')
    if custom:
        custom_path = Path(custom)
        if custom_path.is_file():
            return custom_path
    if name is None:
        name = cfg.get(
            "dos_template_name", DEFAULT_USER_CONFIG["dos_template_name"]
        )
    p = get_resource_path(name)
    if not p.exists():
        raise FileNotFoundError(
            f"Bundled template '{name}' not found at {p}. "
            "Place template files under 'src/chemauto/resources/'."
        )
    return p
