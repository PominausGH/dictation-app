@echo off
REM Double-click wrapper for setup.ps1. -ExecutionPolicy Bypass is scoped to
REM this one process only — it does not change your system's persistent
REM PowerShell execution policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
pause
