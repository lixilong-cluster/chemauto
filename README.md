# ChemAuto

**ChemAuto — An Automated Analysis Software for Cluster Chemistry**

ChemAuto is a Windows-oriented toolkit for batch processing, inspecting, and organizing quantum-chemistry calculations, with a focus on cluster research and Gaussian workflows. The project began as a collection of frequently used scripts and has evolved into an integrated command-line and graphical application.

Current archived version: **7.1.2**  
Release date: **2026-07-15**  
Developer: **Li Xilong**

[中文说明](README_CN.md) · [Changelog](CHANGELOG.md) · [Maintenance guide](docs/MAINTENANCE_GUIDE_CN.md)

## Main features

- Batch parsing of Gaussian log files, including energies, symmetry, electronic state, imaginary frequencies, optimization/frequency convergence, termination status, and wavefunction stability.
- Interactive GUI with initial/final structures, SCF energy trajectories, sorting, filtering, and CSV/Excel export.
- Global relative-energy ranking for all loaded records, with Etot/HF-aware secondary sorting.
- Structure extraction, multi-frame XYZ viewing, `.fchk → XYZ`, and editable multi-Link1 `.gjf/.com` files.
- Stable/Stable=Opt input generation with Gen/GenECP and ChkBasis handling.
- VDE/ADE input generation and two-channel result analysis.
- PES plotting-data generation and DOS plotting through Origin/OriginPro.
- Excel export with initial/optimized structure images using the validated legacy PyMOL renderer or the built-in renderer.
- Atomic term-symbol generation.
- Optional independent Reference Explorer for literature metadata and citation-file retrieval.

## Quick build on Windows

Requirements:

- Windows 10/11, 64-bit
- Python 3.11, 64-bit
- Internet access for the first dependency installation

Run:

```bat
BUILD_FROM_SCRATCH.bat
```

Advanced Windows helper scripts are organized under `scripts/windows/`.

The script creates a clean `.venv`, installs dependencies, runs regression tests and PyMOL smoke tests, builds portable folders, and writes release ZIP files to `release\`.

## Source layout

```text
src/chemauto/                 ChemAuto source code
src/pymol/                    Bundled legacy PyMOL rendering runtime
tools/reference_explorer/     Reference Explorer source
assets/                       Icons and resources
requirements/                 Python dependency lists
tests/                        Regression tests
test_data/                    Small test fixtures
tests/build_checks/           Pre/post-build PyMOL smoke tests
```

## Portable packages

The build workflow can generate:

- `ChemAuto_7.1.2_Portable.zip`
- `ReferenceExplorer_3.1_Portable.zip`
- `ChemAuto_Suite_7.1.2.zip`

These are **folder-portable** distributions. Copy or extract the complete folder; do not separate the EXE from its `_internal` directory.

## External software and services

Some features require external components:

- Origin/OriginPro for automated DOS plotting
- OpenSSH, network access, and a configured server account for remote `.chk → .fchk`
- GaussView or another configured viewer for formatted checkpoint files

Passwords and private-key passphrases are not stored by ChemAuto.

## Testing

The source archive includes automated regression tests covering Gaussian parsing, wrapped archive fields, multi-Link1 handling, global relative-energy ranking, Stable input generation, Gen/GenECP inheritance, DOS pairing, VDE/ADE workflows, multi-frame XYZ files, Excel export, and PyMOL rendering integration.

Run:

```bat
test_windows.bat
```

## License and third-party components

The repository retains its Apache-2.0 project license. Bundled third-party components retain their own upstream notices; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff).
