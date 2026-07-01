# ============================================================================
# Script simple pour tester le refactoring de constantes C++ avec Visual Studio
# ============================================================================
# Ce script configure automatiquement tout ce dont vous avez besoin
# ============================================================================

param(
    [string]$ConstantsFile = "",
    [string]$ProjectRoot = "",
    [switch]$Help
)

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

if ($Help) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Script Simple - C++ Constants Refactoring avec Visual Studio    ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\run_simple.ps1                    # Utilise les fichiers de test par défaut"
    Write-Host "  .\run_simple.ps1 -Help              # Affiche cette aide"
    Write-Host ""
    Write-Host "  # Pour votre propre projet:"
    Write-Host "  .\run_simple.ps1 -ConstantsFile 'path\to\constants.h' -ProjectRoot 'path\to\project'"
    Write-Host ""
    Write-Host "EXEMPLES:" -ForegroundColor Yellow
    Write-Host "  .\run_simple.ps1"
    Write-Host "  .\run_simple.ps1 -ConstantsFile 'C:\MyProject\src\constants.h' -ProjectRoot 'C:\MyProject'"
    Write-Host ""
    Write-Host "NOTES:" -ForegroundColor Yellow
    Write-Host "  - Les chemins peuvent être RELATIFS ou ABSOLUS"
    Write-Host "  - Le script détecte automatiquement Visual Studio"
    Write-Host "  - Par défaut, mode SANDBOX (ne modifie pas vos fichiers)"
    Write-Host "  - Un fichier de config auto.config.json est créé automatiquement"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  C++ Constants Refactoring - Configuration Automatique VS        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Étape 1: Vérifier Python
# ============================================================================
Write-Host "[1/5] Vérification de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput Green "✅ Python trouvé: $pythonVersion"
} catch {
    Write-ColorOutput Red "❌ Python non trouvé. Installez Python 3.7+ et ajoutez-le au PATH"
    exit 1
}

# ============================================================================
# Étape 2: Détecter Visual Studio
# ============================================================================
Write-Host ""
Write-Host "[2/5] Détection de Visual Studio..." -ForegroundColor Yellow

# Chemins possibles pour vswhere.exe
$vswherePaths = @(
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\Installer\vswhere.exe"
)

$vswhere = $null
foreach ($path in $vswherePaths) {
    if (Test-Path $path) {
        $vswhere = $path
        break
    }
}

$vsPath = $null
$generator = "Ninja"  # Par défaut

if ($vswhere) {
    try {
        $vsInstallPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($vsInstallPath) {
            $vsPath = $vsInstallPath
            Write-ColorOutput Green "✅ Visual Studio trouvé: $vsPath"

            # Détecter la version pour le générateur CMake
            $vsVersion = & $vswhere -latest -property catalog_productLineVersion
            if ($vsVersion -eq "2022") {
                $generator = "Visual Studio 17 2022"
            } elseif ($vsVersion -eq "2019") {
                $generator = "Visual Studio 16 2019"
            } elseif ($vsVersion -eq "2017") {
                $generator = "Visual Studio 15 2017"
            }
            Write-ColorOutput Green "   Générateur CMake: $generator"
        }
    } catch {
        Write-ColorOutput Yellow "⚠️  vswhere trouvé mais échec de détection. On continue avec les defaults."
    }
}

# Si VS non détecté, chercher cl.exe dans PATH
if (-not $vsPath) {
    try {
        $clPath = (Get-Command cl.exe -ErrorAction SilentlyContinue).Source
        if ($clPath) {
            Write-ColorOutput Yellow "⚠️  Visual Studio non détecté via vswhere, mais cl.exe trouvé dans PATH"
            Write-ColorOutput Yellow "   Assurez-vous d'exécuter ce script depuis 'Developer Command Prompt for VS'"
        } else {
            Write-ColorOutput Yellow "⚠️  Visual Studio/MSVC non détecté"
            Write-ColorOutput Yellow "   Le script va essayer avec les outils disponibles"
        }
    } catch {
        Write-ColorOutput Yellow "⚠️  Compilateur MSVC non trouvé. CMake utilisera le compilateur par défaut."
    }
}

# ============================================================================
# Étape 3: Définir les chemins par défaut
# ============================================================================
Write-Host ""
Write-Host "[3/5] Configuration des chemins..." -ForegroundColor Yellow

# Si pas de paramètres, utiliser les fichiers de test
if (-not $ConstantsFile) {
    $ConstantsFile = "test_data\sample_constants.h"
    Write-ColorOutput Cyan "   Fichier de constantes: $ConstantsFile (par défaut - fichier de test)"
} else {
    Write-ColorOutput Cyan "   Fichier de constantes: $ConstantsFile"
}

if (-not $ProjectRoot) {
    $ProjectRoot = "test_data"
    Write-ColorOutput Cyan "   Racine du projet: $ProjectRoot (par défaut - dossier de test)"
} else {
    Write-ColorOutput Cyan "   Racine du projet: $ProjectRoot"
}

# Vérifier que le fichier de constantes existe
if (-not (Test-Path $ConstantsFile)) {
    Write-ColorOutput Red "❌ Fichier de constantes introuvable: $ConstantsFile"
    exit 1
}

# ============================================================================
# Étape 4: Créer un fichier de configuration automatique
# ============================================================================
Write-Host ""
Write-Host "[4/5] Création du fichier de configuration automatique..." -ForegroundColor Yellow

$configFile = "auto_config.json"
$configContent = @{
    "_comment" = "Configuration générée automatiquement par run_simple.ps1"
    "constants_file" = $ConstantsFile
    "project_root" = $ProjectRoot
    "build_directory" = "build_temp"
    "source_directories" = @("src/", "include/")
    "exclude_patterns" = @(
        "*_test.cpp",
        "*_test.h",
        "*/third_party/*",
        "*/build/*",
        "*/cmake-build-*/*"
    )
    "analysis_options" = @{
        "min_usage_threshold" = 1
        "ignore_test_files" = $true
        "case_sensitive" = $false
    }
    "output_settings" = @{
        "include_comments" = $true
        "sort_constants" = $true
    }
    "execution_settings" = @{
        "mode" = "sandbox"
        "backup_original_files" = $true
    }
    "logging" = @{
        "level" = "INFO"
    }
} | ConvertTo-Json -Depth 10

$configContent | Out-File -FilePath $configFile -Encoding UTF8
Write-ColorOutput Green "✅ Configuration créée: $configFile"

# ============================================================================
# Étape 5: Lancer l'analyse
# ============================================================================
Write-Host ""
Write-Host "[5/5] Lancement de l'analyse..." -ForegroundColor Yellow
Write-Host ""
Write-Host "┌─────────────────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "│  Mode: SANDBOX (vos fichiers originaux ne seront PAS modifiés) │" -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────────────┘" -ForegroundColor White
Write-Host ""

# Construire la commande
$pythonArgs = @(
    "constants_refactor.py",
    "--config", $configFile,
    "--verbose"
)

# Si Visual Studio détecté, définir la variable d'environnement pour CMake
if ($vsPath) {
    $env:CMAKE_GENERATOR = $generator
}

# Lancer le script Python
Write-ColorOutput Cyan "Commande: python $($pythonArgs -join ' ')"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray

& python @pythonArgs

$exitCode = $LASTEXITCODE

Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Résumé final
# ============================================================================
if ($exitCode -eq 0) {
    Write-ColorOutput Green "✅ Analyse terminée avec succès!"
} else {
    Write-ColorOutput Red "❌ L'analyse a échoué avec le code d'erreur: $exitCode"
}

Write-Host ""
Write-Host "┌─────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│                      PROCHAINES ÉTAPES                          │" -ForegroundColor Cyan
Write-Host "└─────────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Fichiers générés:" -ForegroundColor Yellow
Write-Host "   - $configFile (configuration utilisée)"
if (Test-Path "build_temp") {
    Write-Host "   - build_temp\ (répertoire de build temporaire)"
}
if (Test-Path "sandbox_output") {
    Write-Host "   - sandbox_output\ (résultats de l'analyse)"
}
Write-Host ""
Write-Host "📖 Pour utiliser sur VOTRE projet:" -ForegroundColor Yellow
Write-Host "   .\run_simple.ps1 -ConstantsFile 'VOTRE_FICHIER.h' -ProjectRoot 'VOTRE_PROJET'"
Write-Host ""
Write-Host "   Exemples de chemins:" -ForegroundColor White
Write-Host "     RELATIFS: -ConstantsFile '..\OtherProject\src\const.h'"
Write-Host "     ABSOLUS:  -ConstantsFile 'C:\Projects\MyApp\include\constants.h'"
Write-Host ""
Write-Host "💡 Conseil: Les chemins RELATIFS sont plus portables!" -ForegroundColor Cyan
Write-Host ""
