# Batch Files for C++ Constants Refactoring Tool

This directory contains several batch files and PowerShell scripts to help you quickly get started with the C++ Constants Refactoring Tool.

## Available Scripts

### 🚀 Quick Start

**`quick_start.bat`** - The fastest way to see the tool in action (Windows CMD)
- Runs a basic analysis on sample data
- Uses safe sandbox mode (won't modify your files)
- Perfect for first-time users
- Shows next steps and guidance

**`quick_start.ps1`** - PowerShell version of quick start
- Same functionality as quick_start.bat
- Better formatting and colors in PowerShell
- Cross-platform compatible

**Usage:**
```cmd
quick_start.bat
```
or
```powershell
.\quick_start.ps1
```

### 📚 Comprehensive Examples

**`run_examples.bat`** - Interactive menu with all example scenarios
- 12 different usage examples
- Interactive menu system
- Demonstrates all major features
- Includes cleanup options
- Windows CMD compatible

**Usage:**
```cmd
run_examples.bat
```

## Example Scenarios Included

1. **Help and Version Information** - Basic tool information
2. **Dependency Check** - Verify required tools are installed
3. **Generate Sample Configuration** - Create template config files
4. **Usage Tips** - Show best practices and workflows
5. **Basic Analysis** - Safe sandbox mode analysis
6. **Verbose Analysis** - Detailed logging and debugging
7. **JSON Report Generation** - Machine-readable output
8. **Dry Run Analysis** - Preview changes without applying them
9. **Directory Exclusions** - Focus analysis on specific areas
10. **Custom Build Directory** - Use non-standard build locations
11. **Documentation Generation** - Create comprehensive docs
12. **Run All Examples** - Execute all scenarios automatically

## Prerequisites

- **Python 3.7+** installed and available in PATH
- **constants_refactor.py** in the current directory
- **Test data files** (included in `test_data/` directory)

## Getting Started

1. **First time users**: Run `quick_start.bat`
2. **Explore features**: Run `run_examples.bat` and try different options
3. **For your project**: Use the examples as templates for your own constants files

## Example Commands for Your Project

After trying the examples, use these patterns for your own projects:

### Basic Analysis (Safe)
```cmd
python constants_refactor.py --constants-file src/your_constants.h --project-root .
```

### Generate Configuration File
```cmd
python constants_refactor.py --create-config my_project_config.json
```

### Verbose Analysis with Logging
```cmd
python constants_refactor.py --constants-file src/your_constants.h --verbose --log-file analysis.log
```

### JSON Report for CI/CD
```cmd
python constants_refactor.py --constants-file src/your_constants.h --output-format json --output-file report.json
```

### Direct Mode (Modifies Files - Use with Caution)
```cmd
python constants_refactor.py --constants-file src/your_constants.h --mode direct
```

## Safety Notes

- ✅ **Sandbox mode** (default) is always safe - it never modifies your original files
- ⚠️ **Direct mode** modifies your codebase - ensure you have backups or version control
- 🧪 **Dry run mode** shows what would be changed without making modifications
- 📝 Always review the analysis results before applying changes

## Troubleshooting

### Common Issues

1. **"Python is not available"**
   - Install Python 3.7+ from https://python.org
   - Ensure Python is added to your PATH

2. **"constants_refactor.py not found"**
   - Run the batch files from the same directory as constants_refactor.py
   - Ensure the main script file is present

3. **"Missing dependencies"**
   - Run `python constants_refactor.py --check-deps` to see what's missing
   - Install required packages: `pip install pygccxml`

4. **PowerShell execution policy errors**
   - Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`
   - Or use the batch file version instead

### Getting Help

- Run `python constants_refactor.py --help` for complete documentation
- Run `python constants_refactor.py --tips` for usage guidance
- Check the generated log files for detailed error information

## File Cleanup

The example scripts generate various output files for demonstration:
- Configuration files (`.json`)
- Log files (`.log`) 
- Report files (`.json`)
- Documentation files (`.md`)

Both batch files offer cleanup options when you exit, or you can manually delete these files when no longer needed.

## Next Steps

1. Try the quick start example
2. Explore the comprehensive examples
3. Create a configuration file for your project
4. Run analysis on your own constants files
5. Review the results and apply changes as needed

For more detailed information, see the main README.md file or run the tool with `--help`.