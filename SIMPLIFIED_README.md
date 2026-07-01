# Simplified C++ Constants Refactor

Ultra-simple version of the constants refactoring tool. No dependencies, no CMake, no CastXML.

## What it does

1. Reads constants from a header file (#define, const, constexpr)
2. Finds modules in your project (directories with 3-5 letter names)
3. Searches where each constant is used
4. Reports which constants belong to which module

## Usage

```bash
# Analysis only (no file generation)
python simplified_cst_refactor.py <constants_file> <project_root>

# Analysis + Generate refactored files
python simplified_cst_refactor.py <constants_file> <project_root> --generate

# Specify custom output directory
python simplified_cst_refactor.py <constants_file> <project_root> -g -o output_dir
```

### Examples

```bash
# Test with sample data (analysis only)
python simplified_cst_refactor.py test_data/sample_constants.h test_data

# Generate refactored files
python simplified_cst_refactor.py test_data/sample_constants.h test_data --generate

# Your project - analysis only
python simplified_cst_refactor.py src/constants.h /path/to/project

# Your project - generate files in custom directory
python simplified_cst_refactor.py src/constants.h /path/to/project -g -o my_refactored_files
```

## Module Detection

The script looks for directories with **3, 4, or 5 letter names** in your project root:

```
project/
├── core/      ← Module (4 letters)
├── net/       ← Module (3 letters)
├── ui/        ← Module (2 letters - ignored)
├── utils/     ← Module (5 letters)
└── documentation/  ← Not a module (too long)
```

## Output

### Analysis Mode (default)

The script prints a report categorizing constants as:

- **Unused**: Not found in any source file
- **Module-specific**: Used only in one module
- **Shared**: Used by multiple modules

### Generation Mode (--generate)

Creates header files in the output directory:

```
refactored_constants/
├── core_constants.h          # Constants used only in 'core' module
├── net_constants.h           # Constants used only in 'net' module  
├── ui_constants.h            # Constants used only in 'ui' module
├── shared_constants.h        # Constants used by multiple modules
└── unused_constants.h        # Unused constants (for reference)
```

Each generated file:
- Has proper header guards
- Contains only relevant constants
- Includes comments about usage
- Ready to `#include` in your modules

## Requirements

- Python 3.7+
- No external dependencies!

## Testing

```bash
python test_simplified.py
```

Simple test suite (3 tests, not 10k like the original).

## Differences from Original

**Original (`constants_refactor.py`):**
- 4500+ lines
- Requires CastXML, pygccxml, CMake
- Complex configuration
- Extensive test suite
- Multiple output formats
- Sandbox mode, file generation, etc.

**Simplified (`simplified_cst_refactor.py`):**
- ~400 lines
- No dependencies
- Simple command line
- Basic test (3 tests)
- Text report + optional file generation
- Simple header files (module_constants.h, shared_constants.h, unused_constants.h)

Use the simplified version for quick refactoring. Use the original for complex projects with CMake integration.

## How it works

1. **Parse constants file** - Regex matching for #define, const, constexpr
2. **Find modules** - List directories matching 3-5 letter pattern
3. **Search usage** - Walk each module, grep for constant names in .cpp/.h files
4. **Categorize** - Count which modules use each constant
5. **Report** - Print simple text report

Fast, simple, no magic.
