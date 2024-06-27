# CHANGELOG OF ChemAuto



## [5.3] - 2024-06-27

### Added
    - Function 6: Convert .gjf to .xyz or extract sturc from .log and save as .xyz.
    - Support for:
        -- convert gjf to xyz
        -- extract opted structures from log files and save as gjf, xyz or both gjf and xyz.
    
### Fixed
    Use module lazy loading to speed up program load time 


## [5.3] - 2024-06-25

### Added
    - Function 7: generation of atomic term symbols for single and mixed configurations.
    - Support for single configurations (e.g., p3, d2) and mixed configurations (e.g., s1p3, p5d4).
### Fixed



## [5.2] - 2024-04-05

### Added
    - Support for exporting as opju files.
    - Added CHANGELOG.md log.
### Fixed
    - Optimized the PES data export logic and code.
    - Optimized DOS spectra plotting code.
        - using methods in originpro
        - batch plotting only exit origin for the last time 
    - Added long and short names for DOS spectra workbook, worksheet, and layers.


## [5.1] - 2024-04-02

### Fixed
    - Fixed the export error of overlaid PES line data.


## [5.0] - 2024-04-01

### Added
    - Analyze Gaussian opt and sp tasks, export HF, ZPE, Etot, State, Sym., Nimag information to Excel or txt.
    - Extract the initial and optimized final structures of computed clusters to Excel.
    - Batch modify gjf files, changing computational methods and basis sets.
    - Export PES simulation spectra plotting data:
        1. Batch export PES data.
        2. Export Single PES Data.
        3. Export Overlay Spectra Data.
    - Plot DOS spectra:
        1. Batch plot DOS.
        2. Plot single DOS.


## [1.0]-[4.0]

    From August 2023 to January 2024

