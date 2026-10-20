@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Project virtual environment was not found.
    echo Please create the virtual environment first.
    pause
    exit /b 1
)

echo Checking Firebase Admin SDK...

"venv\Scripts\python.exe" -c "import firebase_admin" >nul 2>&1

if errorlevel 1 (
    echo Firebase Admin SDK is missing. Installing project dependencies...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt

    if errorlevel 1 (
        echo ERROR: Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Starting CampusConnect...
"venv\Scripts\python.exe" run.py

if errorlevel 1 (
    echo.
    echo CampusConnect stopped because an error occurred.
    pause
)