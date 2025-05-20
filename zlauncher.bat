@echo off
title Uta Yuki

REM Change to the directory where the batch file is located
cd /d "%~dp0"

REM Display the contents of ascii.txt
type ascii.txt

REM Activate the virtual environment
echo Activating virtual environment: venv...
call "%~dp0venv\Scripts\activate"

REM Check if the virtual environment was activated successfully
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment. Please ensure the environment exists.
    pause
    exit /b 1
)

REM Run the Python script using the Python interpreter from the virtual environment
echo Starting Uta Yuki...
python "%~dp0main.py"

REM Check if the Python script ran successfully
if %errorlevel% neq 0 (
    echo Failed to run Python script. Check the logs for more details.
    pause
    exit /b 1
)

REM Pause to keep the window open
pause
