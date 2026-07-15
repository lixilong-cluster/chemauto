@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
echo This deletes only .venv, build, dist, and release.
choice /c YN /m "Continue with a completely fresh rebuild"
if errorlevel 2 exit /b 0
if exist .venv rmdir /s /q .venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release
echo Clean state restored. Run BUILD_FROM_SCRATCH.bat.
pause
