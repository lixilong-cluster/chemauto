@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
call "%ROOT%\scripts\windows\verify_build_inputs.bat"
if errorlevel 1 goto :error
set "CHEMAUTO_PROJECT_ROOT=%ROOT%"
if not exist release mkdir release

set "PLAYWRIGHT_BROWSERS_PATH=%ROOT%\tools\reference_explorer\pw-browsers"
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" mkdir "%PLAYWRIGHT_BROWSERS_PATH%"
dir /b "%PLAYWRIGHT_BROWSERS_PATH%\chromium-*" >nul 2>&1
if errorlevel 1 (
  echo Installing the portable Playwright Chromium browser...
  ".venv\Scripts\python.exe" -m playwright install chromium
  if errorlevel 1 goto :error
)

if exist build\ReferenceExplorer_Portable rmdir /s /q build\ReferenceExplorer_Portable
if exist dist\ReferenceExplorer_Portable rmdir /s /q dist\ReferenceExplorer_Portable
if exist release\ReferenceExplorer_3.1_Portable.zip del /q release\ReferenceExplorer_3.1_Portable.zip

".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm ^
  --workpath "%ROOT%\build\ReferenceExplorer_Portable" ^
  --distpath "%ROOT%\dist" ^
  "%ROOT%\ReferenceExplorer_Portable.spec"
if errorlevel 1 goto :error
if not exist "dist\ReferenceExplorer_Portable\ReferenceExplorer.exe" goto :error

xcopy /e /i /y "%PLAYWRIGHT_BROWSERS_PATH%" "dist\ReferenceExplorer_Portable\pw-browsers" >nul
if errorlevel 1 goto :error
copy /y README_CN.md dist\ReferenceExplorer_Portable\README_CN.md >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -LiteralPath 'dist\ReferenceExplorer_Portable' -DestinationPath 'release\ReferenceExplorer_3.1_Portable.zip' -Force"
if errorlevel 1 goto :error

echo.
echo Reference Explorer portable build completed:
echo EXE : %ROOT%\dist\ReferenceExplorer_Portable\ReferenceExplorer.exe
echo ZIP : %ROOT%\release\ReferenceExplorer_3.1_Portable.zip
if not defined CHEMAUTO_BATCH pause
exit /b 0
:error
echo.
echo Reference Explorer portable build failed.
if not defined CHEMAUTO_BATCH pause
exit /b 1
