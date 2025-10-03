# chemauto
 An Automated Analysis Software for Cluster Chemistry.
Core Functions
1.Modify Input Files
 Automatically updates route section, functional/basis set, and spin multiplicity across multiple .gjf input files.
2.Analyze Optimization and Single-Point Results
 Parses Gaussian/ORCA output files to check convergence, common errors (e.g., L502, 1999), and wavefunction stability.
3.Extract Stable Isomers
 Extracts low-energy optimized structures and ranks isomers by relative energy for further analysis.
4.Export DOS Spectrum Data
 Collects molecular orbital eigenvalues and transforms them into Gaussian-broadened density-of-states (DOS) data.
5.Plot Spectrum
 Simulates PES-like spectra using calculated vertical detachment energies (VDEs) and visualizes DOS curves.
6.Generate Log Files
 Automatically creates structured log summaries of all calculations for tracking and reproducibility.
7.Generate Atomic Term Symbols
 Derives electronic term symbols and branching rules for fine-structure transitions based on electron configurations.
