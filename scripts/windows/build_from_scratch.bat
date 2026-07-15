@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
set "CHEMAUTO_BATCH=1"

echo ============================================================
echo ChemAuto Suite 7.1.2 - COMPLETE FROM-SCRATCH BUILD
echo ============================================================
if exist .venv (
  echo An existing .venv is present.
  choice /c YN /m "Delete it and rebuild the environment from scratch"
  if errorlevel 2 goto :keepvenv
  rmdir /s /q .venv
)
:keepvenv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release

call "%ROOT%\scripts\windows\setup_environment.bat"
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\verify_build_inputs.bat"
if errorlevel 1 goto :error
set "PYTHONPATH=%ROOT%\src"
".venv\Scripts\python.exe" -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\verify_pymol_renderer.bat"
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\build_suite.bat"
if errorlevel 1 goto :error

echo.
echo FROM-SCRATCH BUILD FINISHED SUCCESSFULLY.
echo Use ZIP files under: %ROOT%\release
pause
exit /b 0
:error
echo.
echo FROM-SCRATCH BUILD FAILED. Read the first [ERROR] above.
pause
exit /b 1
