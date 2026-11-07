@echo off
rem One launcher for everything after Node.js and Python are installed: installs
rem dependencies on the very first run, then starts the app every time.
rem Double-click this file, or run it from PowerShell/Command Prompt.
cd /d "%~dp0"

if not exist node_modules (
    echo First run detected - installing dependencies, this can take a few minutes...
    call npm run setup
    if errorlevel 1 (
        echo Setup failed - see the error above.
        pause
        exit /b 1
    )
)

call npm start
pause
