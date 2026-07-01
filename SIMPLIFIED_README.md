# Simplified C++ Constants Refactor

Ultra-simple version of the constants refactoring tool. No dependencies, no CMake, no CastXML.

## What it does

1. Reads constants from a header file (#define, const, constexpr)
2. Finds modules in your project (directories with 3-5 letter names)
3. Searches where each constant is used
4. Reports which constants belong to which module

## Usage

```bash
python simplified_cst_refactor.py <constants_file> <project_root>
```

### Examples

```bash
# Test with sample data
python simplified_cst_refactor.py test_data/sample_constants.h test_data

# Your project
python simplified_cst_refactor.py src/constants.h /path/to/project
python simplified_cst_refactor.py include/common/defs.h .
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

The script categorizes constants as:

- **Unused**: Not found in any source file
- **Module-specific**: Used only in one module → should go in `module/constants.h`
- **Shared**: Used by multiple modules → should stay in shared header

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
- ~350 lines
- No dependencies
- Simple command line
- Basic test (3 tests)
- Text output only
- Analysis only (no file generation)

Use the simplified version for quick analysis. Use the original for production refactoring.

## How it works

1. **Parse constants file** - Regex matching for #define, const, constexpr
2. **Find modules** - List directories matching 3-5 letter pattern
3. **Search usage** - Walk each module, grep for constant names in .cpp/.h files
4. **Categorize** - Count which modules use each constant
5. **Report** - Print simple text report

Fast, simple, no magic.
