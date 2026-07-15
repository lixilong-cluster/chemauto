# Changelog of ChemAuto

All notable changes to ChemAuto are documented in this file.

## [7.1.2] - 2026-07-15

### Added
- Complete from-scratch Windows build workflow for ChemAuto Portable, Reference Explorer Portable, and ChemAuto Suite.
- Pre-build and post-build PyMOL rendering smoke tests.
- Lossless GUI PNG export and delayed capture for menus and dialogs.
- Multi-Link1 `.gjf/.com` editor, multi-frame XYZ viewer, expanded preferences, and independent Reference Explorer launcher.

### Changed
- Restored the validated ChemAuto 5.3 PyMOL ball-and-stick workflow as the default Excel structure renderer; the built-in renderer remains a fallback.
- Relative energies now use one global minimum Etot for all currently loaded records, without automatic grouping.
- Table-header sorting uses the selected field as the primary key and Etot/HF as the secondary energy key.
- Non-image Excel columns automatically fit the widest cell; structure-image columns keep fixed widths.
- A second import request during active parsing is ignored with a wait message.

### Fixed
- Robust parsing of wrapped Gaussian archive fields, including HF, state, and point group.
- Correct target-step selection for Opt/Freq/Stable/Stable=Opt and multi-Link1 outputs.
- Gen/GenECP and ChkBasis inheritance in Stable and VDE/ADE input generation.
- PyInstaller entry-path resolution and portable Reference Explorer discovery.
- Excluded optional PyMOL Tk plugin components while retaining the headless renderer.

## [7.1.0] - 2026-07-15
- Added GUI readiness handshake and independent-process launch from the CMD menu.
- Added structured GUI regions, Light/Dark/System themes, direct `.gjf/.com` modification, and Gaussian keyword presets.
- Added VDE/ADE generation and analysis, PES/DOS dialogs, `.fchk → XYZ`, remote `.chk → .fchk` profiles, and atomic term-symbol GUI.

## [6.0.0] - 2026-04-26
- Reorganized the project into a Python package.
- Added the Gaussian Log Browser GUI with structure previews, SCF trajectories, status inspection, sorting, and export.
- Retained the validated CMD functions as menu options.

## [5.3] - 2024-06-27
- Stable command-line integrated version with seven main functions: log analysis, structure extraction, GJF creation, PES data generation, DOS/Origin plotting, coordinate conversion, and atomic term-symbol generation.

## [5.2] - 2024-04-05
### Added
- OPJU project output.
- Initial changelog.

### Fixed
- Improved PES export and DOS/Origin batch plotting.
- Origin exits only after the final batch item.
- Added long/short names for workbooks, worksheets, and layers.

## [5.1] - 2024-04-02
### Fixed
- Fixed overlay PES line-data export.

## [5.0] - 2024-04-01
### Added
- Gaussian optimization and single-point result analysis.
- Excel/TXT export of HF, ZPE, Etot, state, symmetry, and imaginary frequencies.
- Initial/final structure extraction and Excel insertion.
- Batch GJF modification.
- Single, batch, and overlay PES plotting-data export.
- Single and batch DOS plotting.

## [1.0]-[4.0] - 2023-08 to 2024-01
- Early framework and foundational calculation-file processing functions.
