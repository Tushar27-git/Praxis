@echo off
setlocal
cd /d "%~dp0"
powershell -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
