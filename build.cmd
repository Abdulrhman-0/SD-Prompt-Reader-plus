@echo off
rem Double-clickable wrapper around build.py.
rem Uses the project virtual environment when it exists, otherwise the
rem python on PATH. Any extra arguments are forwarded to build.py.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo [build] using %PYTHON%
"%PYTHON%" build.py %*

if errorlevel 1 (
    echo.
    echo [build] FAILED
) else (
    echo.
    echo [build] SUCCESS - see the dist folder
)

rem Keep the window open when launched by double-click.
echo.
pause
