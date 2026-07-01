@echo off
REM ============================================================================
REM Script simple pour tester le refactoring de constantes C++ avec Visual Studio
REM Version Batch - Wrapper qui appelle le script PowerShell
REM ============================================================================

setlocal enabledelayedexpansion

REM Vérifier si PowerShell est disponible
where powershell >nul 2>nul
if errorlevel 1 (
    echo.
    echo ╔════════════════════════════════════════════════════════════════════╗
    echo ║  ERREUR: PowerShell n'est pas disponible                          ║
    echo ╚════════════════════════════════════════════════════════════════════╝
    echo.
    echo PowerShell est requis pour ce script.
    echo Sur Windows 7+, PowerShell devrait etre preinstalle.
    echo.
    pause
    exit /b 1
)

REM Afficher le message de bienvenue
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║  C++ Constants Refactoring - Launcher Batch                       ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier si des arguments ont été passés
if "%~1"=="" (
    echo Lancement avec les parametres par defaut...
    echo.
    powershell -ExecutionPolicy Bypass -File ".\run_simple.ps1"
) else if "%~1"=="-h" (
    powershell -ExecutionPolicy Bypass -File ".\run_simple.ps1" -Help
) else if "%~1"=="--help" (
    powershell -ExecutionPolicy Bypass -File ".\run_simple.ps1" -Help
) else if "%~1"=="/?" (
    powershell -ExecutionPolicy Bypass -File ".\run_simple.ps1" -Help
) else (
    echo.
    echo ╔════════════════════════════════════════════════════════════════════╗
    echo ║                         MODE AVANCE                                ║
    echo ╚════════════════════════════════════════════════════════════════════╝
    echo.
    echo Pour utiliser avec vos propres fichiers, utilisez directement
    echo le script PowerShell:
    echo.
    echo   powershell -ExecutionPolicy Bypass -File ".\run_simple.ps1" ^
    echo       -ConstantsFile "path\to\constants.h" ^
    echo       -ProjectRoot "path\to\project"
    echo.
    echo Exemples:
    echo   run_simple.bat                     # Test avec fichiers de demo
    echo   run_simple.bat -h                  # Afficher l'aide
    echo.
    echo Pour le mode avance, editez ce fichier .bat ou utilisez PowerShell.
    echo.
    pause
    exit /b 0
)

REM Capturer le code de sortie du script PowerShell
set exitcode=!errorlevel!

REM Pause pour voir les résultats
echo.
pause

exit /b !exitcode!
