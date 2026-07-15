@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

echo ============================================================
echo ChemAuto 7.1.2 - Create a clean Python 3.11 environment
echo ============================================================

where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Windows Python launcher "py" was not found.
  echo Install 64-bit Python 3.11 from python.org and enable the launcher.
  if not defined CHEMAUTO_BATCH pause
  exit /b 1
)

py -3.11 -c "import sys,struct; assert sys.version_info[:2]==(3,11); assert struct.calcsize('P')*8==64; print(sys.version)"
if errorlevel 1 (
  echo [ERROR] 64-bit Python 3.11 is required by the bundled PyMOL cp311 runtime.
  if not defined CHEMAUTO_BATCH pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating .venv ...
  py -3.11 -m venv .venv
  if errorlevel 1 goto :error
) else (
  echo Existing .venv found. It will be reused.
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
python -m pip install -r requirements\requirements-suite.txt
if errorlevel 1 goto :error

echo.
echo Environment ready: %ROOT%\.venv
if not defined CHEMAUTO_BATCH pause
exit /b 0

:error
echo.
echo [ERROR] Environment setup failed.
if not defined CHEMAUTO_BATCH pause
exit /b 1
