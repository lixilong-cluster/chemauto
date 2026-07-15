@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
set "FAILED=0"

echo ============================================================
echo ChemAuto 7.1.2 - Build input verification
echo ============================================================
call :check "build_cli.py"
call :check "ChemAuto_Portable.spec"
call :check "ReferenceExplorer_Portable.spec"
call :check "src\chemauto\__init__.py"
call :check "src\chemauto\cli.py"
call :check "src\chemauto\resources\DOS-default.otpu"
call :check "src\pymol\__init__.py"
call :check "src\pymol\cmd.py"
call :check "src\pymol\_cmd.cp311-win_amd64.pyd"
call :check "src\pymol\VCOMP140.DLL"
call :check "src\pymol\pymol_path\LICENSE"
call :check "assets\icons\chemauto.ico"
call :check "tools\reference_explorer\ReferenceExplorer.py"
call :check "tools\reference_explorer\search.ico"
call :check "requirements\requirements-suite.txt"
call :check "tests\build_checks\verify_pymol_renderer.py"
if "%FAILED%"=="1" goto :missing

if not exist ".venv\Scripts\python.exe" (
  echo [MISSING] .venv\Scripts\python.exe
  echo Run BUILD_FROM_SCRATCH.bat or scripts\windows\setup_environment.bat first.
  exit /b 1
)

for /f "tokens=2" %%V in ('".venv\Scripts\python.exe" --version 2^>^&1') do set "PYVER=%%V"
echo %PYVER% | findstr /b "3.11." >nul
if errorlevel 1 (
  echo [ERROR] Python 3.11 is required. Found %PYVER%.
  exit /b 1
)
".venv\Scripts\python.exe" -c "import struct; raise SystemExit(0 if struct.calcsize('P')*8==64 else 1)"
if errorlevel 1 (
  echo [ERROR] A 64-bit Python environment is required.
  exit /b 1
)

echo.
echo [OK] All required source, PyMOL, icon, and build files are present.
echo [OK] Python %PYVER% 64-bit.
exit /b 0

:missing
echo.
echo [ERROR] Required files are missing. Re-extract the complete repository archive.
exit /b 1

:check
if exist %~1 (
  echo [OK] %~1
) else (
  echo [MISSING] %~1
  set "FAILED=1"
)
exit /b 0
