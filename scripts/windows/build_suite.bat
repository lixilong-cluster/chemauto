@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
set "CHEMAUTO_BATCH=1"
call "%ROOT%\scripts\windows\build_chemauto_portable.bat"
if errorlevel 1 goto :error
call "%ROOT%\scripts\windows\build_reference_explorer_portable.bat"
if errorlevel 1 goto :error

if exist dist\ChemAuto_Suite rmdir /s /q dist\ChemAuto_Suite
if exist release\ChemAuto_Suite_7.1.2.zip del /q release\ChemAuto_Suite_7.1.2.zip
mkdir dist\ChemAuto_Suite
xcopy /e /i /y dist\ChemAuto_Portable\* dist\ChemAuto_Suite\ >nul
if errorlevel 1 goto :error
mkdir dist\ChemAuto_Suite\ReferenceExplorer
xcopy /e /i /y dist\ReferenceExplorer_Portable\* dist\ChemAuto_Suite\ReferenceExplorer\ >nul
if errorlevel 1 goto :error
(
  echo @echo off
  echo start "" "%%~dp0ReferenceExplorer\ReferenceExplorer.exe"
) > dist\ChemAuto_Suite\ReferenceExplorer.cmd
copy /y README_CN.md dist\ChemAuto_Suite\README_CN.md >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -LiteralPath 'dist\ChemAuto_Suite' -DestinationPath 'release\ChemAuto_Suite_7.1.2.zip' -Force"
if errorlevel 1 goto :error

echo.
echo ALL PORTABLE BUILDS COMPLETED SUCCESSFULLY
echo Release ZIPs: %ROOT%\release
if not defined CHEMAUTO_BATCH pause
exit /b 0
:error
echo.
echo ChemAuto Suite build failed.
if not defined CHEMAUTO_BATCH pause
exit /b 1
