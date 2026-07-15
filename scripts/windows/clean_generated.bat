@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release
for /d /r %%D in (__pycache__) do @if exist "%%D" rmdir /s /q "%%D"
for /r %%F in (*.pyc *.pyo) do @if exist "%%F" del /q "%%F"
echo Generated build, distribution, release, and Python cache files were removed.
pause
