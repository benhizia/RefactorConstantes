# C++ Constants Refactoring Tool

## Overview

The C++ Constants Refactoring Tool is a Python-based utility that analyzes large C++ constants files and automatically redistributes constants to appropriate module-specific files based on usage patterns. The tool leverages CMake's compile commands database for accurate module boundary detection and supports both safe sandbox testing and direct codebase modification.

## Features

- **Intelligent Analysis**: Uses CastXML and pygccxml for robust C++ code parsing
- **Module Detection**: Leverages CMake compile commands for accurate module boundaries
- **Usage Pattern Analysis**: Searches entire codebase to determine constant usage
- **Safe Testing**: Sandbox mode allows testing changes without modifying original code
- **Multiple Output Formats**: JSON, text, markdown, and CSV report formats
- **Comprehensive Error Handling**: Graceful fallbacks and detailed error reporting
- **Flexible Configuration**: Command-line arguments and JSON configuration files

## Installation

### Prerequisites

1. **Python 3.7+**
2. **pygccxml**: `pip install pygccxml`
3. **CastXML**: Download from https://github.com/CastXML/CastXML
4. **CMake**: For compile commands generation
5. **ripgrep** (optional): For faster text search

### Quick Install

```bash
# Install Python dependencies
pip install pygccxml

# Install CastXML (example for Ubuntu)
sudo apt-get install castxml

# Or download from GitHub releases for other platforms
```

## Usage

### Basic Usage

```bash
# Analyze constants file in sandbox mode (safe)
constants_refactor --constants-file src/constants.h --project-root .

# Apply changes directly to codebase (use with caution)
constants_refactor --constants-file src/constants.h --mode direct
```

### Common Workflows

#### 1. Initial Analysis
```bash
# Start with sandbox mode to explore your constants
constants_refactor --constants-file src/constants.h --project-root . --verbose
```

#### 2. Generate Reports
```bash
# Create JSON report for further processing
constants_refactor --constants-file src/constants.h --output-format json --output-file analysis.json

# Generate summary statistics only
constants_refactor --constants-file src/constants.h --summary-only
```

#### 3. Focused Analysis
```bash
# Exclude test and third-party code
constants_refactor --constants-file src/constants.h --exclude-dirs "tests/,third_party/,build/"

# Analyze specific source directories only
constants_refactor --constants-file src/constants.h --source-dirs "src/core/,src/ui/"
```

#### 4. Production Refactoring
```bash
# Dry run to see what would be changed
constants_refactor --constants-file src/constants.h --dry-run

# Apply changes with confirmation
constants_refactor --constants-file src/constants.h --mode direct

# Apply changes without confirmation (use with extreme caution)
constants_refactor --constants-file src/constants.h --mode direct --force
```

## Configuration

### Command Line Options

Run `constants_refactor --help` for complete list of options.

### Configuration File

Create a configuration file for complex projects:

```bash
# Generate sample configuration
constants_refactor --create-config my_project_config.json

# Use configuration file
constants_refactor --config my_project_config.json
```

### Sample Configuration

```json
{
  "constants_file": "src/common/constants.h",
  "project_root": ".",
  "build_directory": "build",
  "source_directories": ["src/", "include/"],
  "exclude_patterns": ["*_test.cpp", "*/third_party/*"],
  "module_mapping": {
    "networking": ["net/", "protocol/"],
    "ui": ["gui/", "widgets/"]
  },
  "output_settings": {
    "header_guard_prefix": "PROJECT_",
    "include_comments": true,
    "sort_constants": true
  }
}
```

## How It Works

### 1. Analysis Phase
- Parses constants file using CastXML and pygccxml
- Extracts #define, const, and constexpr declarations
- Generates CMake compile commands database for module detection

### 2. Usage Detection
- Searches for constant usage across all source files
- Maps files to modules using CMake target information
- Categorizes constants as module-private or shared

### 3. Classification
- **Module-private constants** → `MDL_const.h` files
- **Shared constants** → `MDL_export_const.h` files
- **Ambiguous cases** → Flagged for manual review

### 4. File Generation
- **Sandbox mode**: Creates proposed structure in separate directory
- **Direct mode**: Modifies original codebase with safety checks

## Output Structure

After refactoring, your project will have a structure like:

```
src/
├── module1/
│   ├── MDL_const.h          # Module-private constants
│   └── MDL_export_const.h   # Constants shared by this module
├── module2/
│   ├── MDL_const.h
│   └── MDL_export_const.h
└── common/
    └── constants.h          # Original file (can be removed)
```

## Troubleshooting

### Common Issues

1. **CastXML not found**
   - Ensure CastXML is installed and in PATH
   - Use `--castxml-path` to specify custom location

2. **CMake generation fails**
   - Tool will fallback to directory-based analysis
   - Ensure CMakeLists.txt files are present and valid

3. **Permission errors**
   - Check file permissions
   - Use sandbox mode first to test

4. **Large codebases**
   - Use `--exclude-dirs` to focus analysis
   - Enable `--verbose` logging to monitor progress

### Getting Help

```bash
# Check dependencies
constants_refactor --check-deps

# Show usage tips
constants_refactor --tips

# Enable verbose logging
constants_refactor --constants-file src/constants.h --verbose --log-file debug.log
```

## Safety Recommendations

1. **Always use sandbox mode first** to review proposed changes
2. **Ensure code is under version control** before using direct mode
3. **Review ambiguous constants manually** before applying changes
4. **Test your code after refactoring** to ensure functionality is preserved
5. **Start with small constants files** to understand the tool behavior

## Contributing

This tool is designed to be extensible and maintainable. Key areas for contribution:

- Additional output formats
- Enhanced module detection algorithms
- Support for more C++ constructs
- Performance optimizations
- Additional safety checks

## License

[Add your license information here]

## Support

For issues, questions, or contributions, please visit:
[Add your repository URL here]