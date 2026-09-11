@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py scripts\project.py check
) else (
    python scripts\project.py check
)
set "PROJECT_EXIT=%errorlevel%"
if not "%PROJECT_EXIT%"=="0" echo Command failed. Read the message above.
pause
exit /b %PROJECT_EXIT%
