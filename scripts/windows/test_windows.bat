@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
call "%ROOT%\scripts\windows\verify_build_inputs.bat"
if errorlevel 1 goto :error
set "PYTHONPATH=%ROOT%\src"
echo.
echo Running ChemAuto automated regression tests...
".venv\Scripts\python.exe" -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\verify_pymol_renderer.bat"
if errorlevel 1 goto :error
echo.
echo [OK] Regression tests and bundled PyMOL rendering test passed.
pause
exit /b 0
:error
echo.
echo [ERROR] Tests failed. No release should be distributed.
pause
exit /b 1
