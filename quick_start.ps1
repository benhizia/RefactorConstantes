# C++ Constants Refactoring Tool - Quick Start PowerShell Script

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                   C++ Constants Refactoring Tool - Quick Start              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not available. Please install Python 3.7+ and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if the script exists
if (-not (Test-Path "constants_refactor.py")) {
    Write-Host "❌ constants_refactor.py not found in current directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Running quick start example..." -ForegroundColor Green
Write-Host ""
Write-Host "🔍 This will analyze the sample constants file in SAFE sandbox mode" -ForegroundColor White
Write-Host "   (your original files will NOT be modified)" -ForegroundColor White
Write-Host ""

# Run basic analysis on sample data
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "                              NEXT STEPS" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Quick start complete! Here's what you can do next:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Run 'run_examples.bat' to see more detailed examples" -ForegroundColor Cyan
Write-Host "2. Use 'python constants_refactor.py --help' for all options" -ForegroundColor Cyan
Write-Host "3. Try 'python constants_refactor.py --tips' for usage guidance" -ForegroundColor Cyan
Write-Host "4. Create a config file: 'python constants_refactor.py --create-config'" -ForegroundColor Cyan
Write-Host ""
Write-Host "For your own project, use:" -ForegroundColor White
Write-Host "  python constants_refactor.py --constants-file YOUR_CONSTANTS.h --project-root YOUR_PROJECT_DIR" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"