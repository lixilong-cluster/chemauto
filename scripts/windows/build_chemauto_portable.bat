@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
call "%ROOT%\scripts\windows\verify_build_inputs.bat"
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\verify_pymol_renderer.bat"
if errorlevel 1 goto :error

set "CHEMAUTO_PROJECT_ROOT=%ROOT%"
set "PYTHONPATH=%ROOT%\src"
if not exist release mkdir release
if exist build\ChemAuto_Portable rmdir /s /q build\ChemAuto_Portable
if exist dist\ChemAuto_Portable rmdir /s /q dist\ChemAuto_Portable
if exist release\ChemAuto_7.1.2_Portable.zip del /q release\ChemAuto_7.1.2_Portable.zip

echo.
echo Building ChemAuto portable folder...
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm ^
  --workpath "%ROOT%\build\ChemAuto_Portable" ^
  --distpath "%ROOT%\dist" ^
  "%ROOT%\ChemAuto_Portable.spec"
if errorlevel 1 goto :error

if not exist "dist\ChemAuto_Portable\ChemAuto.exe" (
  echo [ERROR] Expected executable was not created.
  goto :error
)
copy /y README_CN.md dist\ChemAuto_Portable\README_CN.md >nul

set "SMOKE_PNG=%TEMP%\ChemAuto_7.1.2_PyMOL_PostBuild.png"
if exist "%SMOKE_PNG%" del /q "%SMOKE_PNG%"
echo.
echo Running the packaged PyMOL rendering smoke test...
"dist\ChemAuto_Portable\ChemAuto.exe" --pymol-self-test "%SMOKE_PNG%"
if errorlevel 1 goto :pymol_error
if not exist "%SMOKE_PNG%" goto :pymol_error
for %%S in ("%SMOKE_PNG%") do if %%~zS LSS 512 goto :pymol_error
del /q "%SMOKE_PNG%" >nul 2>&1

echo [OK] Packaged PyMOL renderer produced a valid PNG.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -LiteralPath 'dist\ChemAuto_Portable' -DestinationPath 'release\ChemAuto_7.1.2_Portable.zip' -Force"
if errorlevel 1 goto :error

echo.
echo ChemAuto portable build completed and PyMOL-tested.
echo EXE : %ROOT%\dist\ChemAuto_Portable\ChemAuto.exe
echo ZIP : %ROOT%\release\ChemAuto_7.1.2_Portable.zip
if not defined CHEMAUTO_BATCH pause
exit /b 0

:pymol_error
echo [ERROR] Packaged ChemAuto could not render the PyMOL smoke-test PNG.
goto :error
:error
echo.
echo ChemAuto portable build failed. Source files were not modified.
if not defined CHEMAUTO_BATCH pause
exit /b 1
