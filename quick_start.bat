@echo off
REM ============================================================================
REM C++ Constants Refactoring Tool - Quick Start Example
REM ============================================================================
REM This is a simple batch file to quickly demonstrate the tool with safe defaults
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   C++ Constants Refactoring Tool - Quick Start              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not available. Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

REM Check if the script exists
if not exist "constants_refactor.py" (
    echo ❌ constants_refactor.py not found in current directory.
    pause
    exit /b 1
)

echo ✅ Running quick start example...
echo.
echo 🔍 This will analyze the sample constants file in SAFE sandbox mode
echo    (your original files will NOT be modified)
echo.

REM Run basic analysis on sample data
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data

echo.
echo ============================================================================
echo                              NEXT STEPS
echo ============================================================================
echo.
echo 🎉 Quick start complete! Here's what you can do next:
echo.
echo 1. Run 'run_examples.bat' to see more detailed examples
echo 2. Use 'python constants_refactor.py --help' for all options
echo 3. Try 'python constants_refactor.py --tips' for usage guidance
echo 4. Create a config file: 'python constants_refactor.py --create-config'
echo.
echo For your own project, use:
echo   python constants_refactor.py --constants-file YOUR_CONSTANTS.h --project-root YOUR_PROJECT_DIR
echo.
pause