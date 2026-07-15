@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
call "%ROOT%\scripts\windows\verify_build_inputs.bat"
if errorlevel 1 goto :error
set "PYTHONPATH=%ROOT%\src"
echo.
echo Testing the bundled ChemAuto 5.3 PyMOL renderer before packaging...
".venv\Scripts\python.exe" tests\build_checks\verify_pymol_renderer.py
if errorlevel 1 goto :error
echo [OK] Source PyMOL rendering test passed.
exit /b 0
:error
echo.
echo [ERROR] PyMOL source rendering test failed. ChemAuto was not packaged.
exit /b 1
