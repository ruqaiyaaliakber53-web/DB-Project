@echo off
REM Double-click this file. First run installs the packages, then starts the app.
cd /d "%~dp0"
py -m pip install -r requirements.txt
cd app
py check_setup.py
echo.
echo Starting HamQadam...
py main.py
pause
