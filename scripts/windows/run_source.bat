@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
  echo Run BUILD_FROM_SCRATCH.bat or scripts\windows\setup_environment.bat first.
  pause
  exit /b 1
)
set "PYTHONPATH=%ROOT%\src"
".venv\Scripts\python.exe" -m chemauto
pause
