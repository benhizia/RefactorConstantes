# Guide Rapide - Utilisation Simple

## 🚀 Démarrage Rapide (3 minutes)

### Test avec les fichiers de démonstration

```powershell
# Ouvrez PowerShell dans ce dossier et lancez:
.\run_simple.ps1
```

C'est tout ! Le script:
- ✅ Détecte automatiquement Visual Studio
- ✅ Crée le fichier de config automatiquement
- ✅ Utilise les fichiers de test comme exemple
- ✅ Mode SANDBOX (ne touche pas vos fichiers)

---

## 📂 Utiliser sur VOTRE projet

### Chemins: RELATIFS ou ABSOLUS ? 

**Les deux fonctionnent !** Mais les chemins **RELATIFS** sont recommandés pour la portabilité.

### Option 1: Chemins RELATIFS (recommandé)

Si votre structure est:
```
C:\MesProjets\
├── RefactorCSTS\          ← Vous êtes ici
│   └── run_simple.ps1
└── MonProjet\             ← Votre projet C++
    ├── src\
    │   └── constants.h    ← Votre fichier à analyser
    └── CMakeLists.txt
```

Commande:
```powershell
.\run_simple.ps1 -ConstantsFile '..\MonProjet\src\constants.h' -ProjectRoot '..\MonProjet'
```

### Option 2: Chemins ABSOLUS

```powershell
.\run_simple.ps1 -ConstantsFile 'C:\MesProjets\MonProjet\src\constants.h' -ProjectRoot 'C:\MesProjets\MonProjet'
```

---

## 🔧 Configuration des Chemins de Modules

### Question: "Quels chemins pour les modules dois-je mettre ?"

Le script auto-génère un fichier `auto_config.json` avec des defaults raisonnables:

```json
{
  "source_directories": [
    "src/",
    "include/"
  ],
  "exclude_patterns": [
    "*_test.cpp",
    "*_test.h",
    "*/third_party/*",
    "*/build/*"
  ]
}
```

### Pour personnaliser selon VOTRE projet:

Éditez `auto_config.json` **après** la première exécution:

```json
{
  "source_directories": [
    "src/core/",       ← Vos vrais chemins de modules
    "src/network/",
    "src/ui/",
    "include/"
  ],
  "module_mapping": {
    "core": ["src/core/", "core/"],
    "network": ["src/network/", "network/"],
    "ui": ["src/ui/", "ui/"]
  }
}
```

**Ces chemins sont RELATIFS à `project_root`** que vous avez spécifié.

---

## 🛠️ Visual Studio & CMake

### Le script détecte automatiquement:

1. **Visual Studio** via `vswhere.exe`
2. **Le générateur CMake approprié**:
   - VS 2022 → `Visual Studio 17 2022`
   - VS 2019 → `Visual Studio 16 2019`
   - VS 2017 → `Visual Studio 15 2017`

### Si la détection échoue:

Deux solutions:

#### Solution A: Developer Command Prompt

1. Ouvrez **"Developer Command Prompt for VS 2022"** (ou votre version)
2. Naviguez vers le dossier RefactorCSTS
3. Lancez: `.\run_simple.ps1`

#### Solution B: Spécifier manuellement

Éditez `auto_config.json` et ajoutez:

```json
{
  "cmake_generator": "Visual Studio 17 2022",
  "cmake_platform": "x64"
}
```

---

## 📋 Exemples Réels

### Exemple 1: Projet simple

```
MonProjet\
├── src\
│   ├── main.cpp
│   └── constants.h      ← Le fichier à refactorer
└── CMakeLists.txt
```

```powershell
.\run_simple.ps1 -ConstantsFile 'C:\MonProjet\src\constants.h' -ProjectRoot 'C:\MonProjet'
```

### Exemple 2: Projet multi-modules

```
GrosProjet\
├── modules\
│   ├── core\
│   ├── network\
│   └── ui\
├── common\
│   └── all_constants.h  ← Fichier de constantes géant à dispatcher
└── CMakeLists.txt
```

```powershell
.\run_simple.ps1 -ConstantsFile 'C:\GrosProjet\common\all_constants.h' -ProjectRoot 'C:\GrosProjet'
```

Puis éditez `auto_config.json`:

```json
{
  "constants_file": "common/all_constants.h",
  "project_root": "C:/GrosProjet",
  "source_directories": [
    "modules/core/",
    "modules/network/",
    "modules/ui/"
  ],
  "module_mapping": {
    "core": ["modules/core/"],
    "network": ["modules/network/"],
    "ui": ["modules/ui/"]
  }
}
```

---

## ❓ FAQ

### Q: Les chemins dans le JSON sont relatifs ou absolus ?

**R:** Dans `auto_config.json`:
- `project_root` peut être **absolu** ou **relatif** (au dossier où vous lancez le script)
- Tous les autres chemins (`source_directories`, `module_mapping`, etc.) sont **RELATIFS à `project_root`**

### Q: Je dois créer le build_directory manuellement ?

**R:** Non ! Le script le crée automatiquement. Par défaut c'est `build_temp/`.

### Q: Que fait vraiment le mode SANDBOX ?

**R:** Il crée une copie de votre structure dans un dossier `sandbox_output/` et fait tous les changements là-dedans. Vos fichiers originaux ne sont **jamais touchés**.

### Q: Comment appliquer les changements pour de vrai ?

**R:** Une fois que vous avez vérifié les résultats dans `sandbox_output/`:

1. Éditez `auto_config.json`:
   ```json
   "execution_settings": {
     "mode": "direct"    ← Changez de "sandbox" à "direct"
   }
   ```

2. Relancez le script

3. **IMPORTANT**: Faites un commit git AVANT !

### Q: Ça marche sans CMake ?

**R:** Le script essaie CMake en premier, mais si ça échoue, il fait une analyse basée sur la structure des dossiers. Moins précis mais fonctionnel.

---

## 🎯 Workflow Typique

1. **Premier test** (mode sandbox):
   ```powershell
   .\run_simple.ps1 -ConstantsFile 'path\to\constants.h' -ProjectRoot 'path\to\project'
   ```

2. **Vérifier** le résultat dans `sandbox_output/`

3. **Ajuster** `auto_config.json` si besoin (module_mapping, exclude_patterns, etc.)

4. **Relancer** pour affiner

5. **Appliquer** en changeant le mode à "direct" dans le config

---

## 💡 Astuces

- **Commencez petit**: Testez sur un petit fichier de constantes d'abord
- **Git commit**: Faites toujours un commit avant le mode "direct"
- **Logs**: Ajoutez `--log-file debug.log` pour déboguer
- **Dry-run**: Le script supporte aussi `--dry-run` en ligne de commande

---

## 🆘 Aide

```powershell
# Aide du wrapper
.\run_simple.ps1 -Help

# Aide du script Python
python constants_refactor.py --help

# Vérifier les dépendances
python constants_refactor.py --check-deps
```
