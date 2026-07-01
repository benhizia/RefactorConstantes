@echo off
REM ============================================================================
REM C++ Constants Refactoring Tool - Example Usage Batch File
REM ============================================================================
REM This batch file demonstrates various ways to use the constants refactor tool
REM with different options and configurations.
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                     C++ Constants Refactoring Tool Examples                 ║
echo ║                                                                              ║
echo ║  This batch file demonstrates various usage patterns and options            ║
echo ║  for the constants refactoring tool.                                        ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not available in PATH. Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

REM Check if the constants_refactor.py script exists
if not exist "constants_refactor.py" (
    echo ❌ constants_refactor.py not found in current directory.
    echo    Please run this batch file from the directory containing constants_refactor.py
    pause
    exit /b 1
)

echo ✅ Python found and constants_refactor.py is available
echo.

:MENU
echo ============================================================================
echo                           EXAMPLE MENU
echo ============================================================================
echo.
echo Choose an example to run:
echo.
echo  1. Show Help and Version Information
echo  2. Check Dependencies
echo  3. Generate Sample Configuration File
echo  4. Show Usage Tips
echo  5. Basic Analysis (Sandbox Mode - Safe)
echo  6. Verbose Analysis with Logging
echo  7. Generate JSON Report
echo  8. Dry Run Analysis
echo  9. Analysis with Directory Exclusions
echo 10. Custom Build Directory Example
echo 11. Generate Documentation
echo 12. Run All Examples (Non-Interactive)
echo.
echo  0. Exit
echo.
set /p choice="Enter your choice (0-12): "

if "%choice%"=="0" goto EXIT
if "%choice%"=="1" goto HELP_VERSION
if "%choice%"=="2" goto CHECK_DEPS
if "%choice%"=="3" goto GENERATE_CONFIG
if "%choice%"=="4" goto USAGE_TIPS
if "%choice%"=="5" goto BASIC_ANALYSIS
if "%choice%"=="6" goto VERBOSE_ANALYSIS
if "%choice%"=="7" goto JSON_REPORT
if "%choice%"=="8" goto DRY_RUN
if "%choice%"=="9" goto EXCLUDE_DIRS
if "%choice%"=="10" goto CUSTOM_BUILD
if "%choice%"=="11" goto GENERATE_DOCS
if "%choice%"=="12" goto RUN_ALL

echo Invalid choice. Please try again.
echo.
goto MENU

:HELP_VERSION
echo.
echo ============================================================================
echo                        HELP AND VERSION INFORMATION
echo ============================================================================
echo.
echo 📖 Showing tool version:
python constants_refactor.py --version
echo.
echo 📖 Showing comprehensive help:
python constants_refactor.py --help
echo.
pause
goto MENU

:CHECK_DEPS
echo.
echo ============================================================================
echo                           DEPENDENCY CHECK
echo ============================================================================
echo.
echo 🔍 Checking for required dependencies:
python constants_refactor.py --check-deps
echo.
pause
goto MENU

:GENERATE_CONFIG
echo.
echo ============================================================================
echo                      GENERATE SAMPLE CONFIGURATION
echo ============================================================================
echo.
echo 📝 Creating sample configuration file:
python constants_refactor.py --create-config example_config.json
echo.
if exist "example_config.json" (
    echo 📄 Generated configuration file contents:
    type example_config.json
)
echo.
pause
goto MENU

:USAGE_TIPS
echo.
echo ============================================================================
echo                             USAGE TIPS
echo ============================================================================
echo.
echo 💡 Showing usage tips and workflows:
python constants_refactor.py --tips
echo.
pause
goto MENU

:BASIC_ANALYSIS
echo.
echo ============================================================================
echo                      BASIC ANALYSIS (SANDBOX MODE)
echo ============================================================================
echo.
echo 🔍 Running basic analysis on sample constants file:
echo    This is SAFE - it won't modify your original files
echo.
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data
echo.
pause
goto MENU

:VERBOSE_ANALYSIS
echo.
echo ============================================================================
echo                     VERBOSE ANALYSIS WITH LOGGING
echo ============================================================================
echo.
echo 🔍 Running verbose analysis with detailed logging:
python constants_refactor.py --constants-file test_data/large_constants.h --project-root test_data --verbose --log-file analysis_debug.log
echo.
if exist "analysis_debug.log" (
    echo 📄 Log file created: analysis_debug.log
    echo    First few lines of the log:
    more +1 analysis_debug.log | head -10
)
echo.
pause
goto MENU

:JSON_REPORT
echo.
echo ============================================================================
echo                          GENERATE JSON REPORT
echo ============================================================================
echo.
echo 📊 Generating JSON report for machine processing:
python constants_refactor.py --constants-file test_data/edge_cases_constants.h --project-root test_data --output-format json --output-file analysis_report.json
echo.
if exist "analysis_report.json" (
    echo 📄 JSON report created: analysis_report.json
    echo    Report structure preview:
    python -m json.tool analysis_report.json 2>nul | head -20
)
echo.
pause
goto MENU

:DRY_RUN
echo.
echo ============================================================================
echo                            DRY RUN ANALYSIS
echo ============================================================================
echo.
echo 🧪 Running dry-run analysis (shows what would be done without changes):
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data --dry-run --summary-only
echo.
pause
goto MENU

:EXCLUDE_DIRS
echo.
echo ============================================================================
echo                     ANALYSIS WITH DIRECTORY EXCLUSIONS
echo ============================================================================
echo.
echo 🔍 Running analysis while excluding specific directories:
python constants_refactor.py --constants-file test_data/large_constants.h --project-root test_data --exclude-dirs "build/,third_party/,tests/" --summary-only
echo.
pause
goto MENU

:CUSTOM_BUILD
echo.
echo ============================================================================
echo                       CUSTOM BUILD DIRECTORY EXAMPLE
echo ============================================================================
echo.
echo 🔧 Running analysis with custom build directory:
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data --build-dir cmake-build-debug --summary-only
echo.
pause
goto MENU

:GENERATE_DOCS
echo.
echo ============================================================================
echo                         GENERATE DOCUMENTATION
echo ============================================================================
echo.
echo 📚 Generating comprehensive documentation:
python constants_refactor.py --generate-docs tool_documentation.md
echo.
if exist "tool_documentation.md" (
    echo 📄 Documentation created: tool_documentation.md
    echo    First few lines:
    head -15 tool_documentation.md 2>nul || more +1 tool_documentation.md | head -15
)
echo.
pause
goto MENU

:RUN_ALL
echo.
echo ============================================================================
echo                          RUNNING ALL EXAMPLES
echo ============================================================================
echo.
echo 🚀 Running all examples in sequence (non-interactive mode)
echo.

echo 1/8 - Checking dependencies...
python constants_refactor.py --check-deps

echo.
echo 2/8 - Generating sample configuration...
python constants_refactor.py --create-config batch_example_config.json

echo.
echo 3/8 - Basic sandbox analysis...
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data --summary-only

echo.
echo 4/8 - Verbose analysis with logging...
python constants_refactor.py --constants-file test_data/large_constants.h --project-root test_data --verbose --log-file batch_analysis.log --summary-only

echo.
echo 5/8 - JSON report generation...
python constants_refactor.py --constants-file test_data/edge_cases_constants.h --project-root test_data --output-format json --output-file batch_report.json --summary-only

echo.
echo 6/8 - Dry run analysis...
python constants_refactor.py --constants-file test_data/sample_constants.h --project-root test_data --dry-run --summary-only

echo.
echo 7/8 - Analysis with exclusions...
python constants_refactor.py --constants-file test_data/large_constants.h --project-root test_data --exclude-dirs "build/,tests/" --summary-only

echo.
echo 8/8 - Generating documentation...
python constants_refactor.py --generate-docs batch_documentation.md

echo.
echo ✅ All examples completed!
echo.
echo Generated files:
if exist "batch_example_config.json" echo    - batch_example_config.json (sample configuration)
if exist "batch_analysis.log" echo    - batch_analysis.log (detailed analysis log)
if exist "batch_report.json" echo    - batch_report.json (JSON analysis report)
if exist "batch_documentation.md" echo    - batch_documentation.md (comprehensive documentation)
echo.
pause
goto MENU

:EXIT
echo.
echo ============================================================================
echo                               CLEANUP
echo ============================================================================
echo.
set /p cleanup="Do you want to clean up generated example files? (y/N): "
if /i "%cleanup%"=="y" (
    echo 🧹 Cleaning up generated files...
    if exist "example_config.json" del "example_config.json" && echo    Deleted: example_config.json
    if exist "analysis_debug.log" del "analysis_debug.log" && echo    Deleted: analysis_debug.log
    if exist "analysis_report.json" del "analysis_report.json" && echo    Deleted: analysis_report.json
    if exist "tool_documentation.md" del "tool_documentation.md" && echo    Deleted: tool_documentation.md
    if exist "batch_example_config.json" del "batch_example_config.json" && echo    Deleted: batch_example_config.json
    if exist "batch_analysis.log" del "batch_analysis.log" && echo    Deleted: batch_analysis.log
    if exist "batch_report.json" del "batch_report.json" && echo    Deleted: batch_report.json
    if exist "batch_documentation.md" del "batch_documentation.md" && echo    Deleted: batch_documentation.md
    echo    ✅ Cleanup completed!
) else (
    echo    Generated files preserved for your review.
)
echo.
echo 👋 Thank you for trying the C++ Constants Refactoring Tool!
echo    For more information, run: python constants_refactor.py --help
echo.
pause
exit /b 0