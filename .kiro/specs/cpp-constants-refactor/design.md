# Design Document

## Overview

The C++ Constants Refactoring Tool is a Python-based script that analyzes a large constants file and redistributes constants to appropriate module-specific files based on usage patterns. The tool leverages CMake's compile commands database for accurate module boundary detection and supports both safe sandbox testing and direct codebase modification.

## Architecture

The system follows a pipeline architecture with distinct phases:

1. **Configuration Phase** - Parse command line arguments and configuration files
2. **Discovery Phase** - Generate CMake compile commands and parse constants file
3. **Analysis Phase** - Map file-to-module relationships and analyze constant usage
4. **Classification Phase** - Categorize constants as module-private or shared
5. **Generation Phase** - Create or update module-specific constant files
6. **Execution Phase** - Apply changes in sandbox or direct mode

## Components and Interfaces

### Core Components

#### 1. ConfigurationManager
```python
class ConfigurationManager:
    def __init__(self, args: argparse.Namespace)
    def load_config_file(self, path: str) -> Dict
    def get_constants_file_path(self) -> str
    def get_source_directories(self) -> List[str]
    def get_exclude_patterns(self) -> List[str]
    def is_sandbox_mode(self) -> bool
```

#### 2. CMakeAnalyzer
```python
class CMakeAnalyzer:
    def generate_compile_commands(self, build_dir: str) -> bool
    def parse_compile_commands(self, json_path: str) -> Dict[str, str]
    def fallback_cmake_parse(self, project_root: str) -> Dict[str, str]
    def map_files_to_modules(self, file_target_map: Dict) -> Dict[str, str]
```

#### 3. ConstantsParser
```python
class ConstantsParser:
    def __init__(self, castxml_path: str = None)
    def parse_constants_file(self, file_path: str) -> List[Constant]
    def parse_with_castxml(self, file_path: str) -> pygccxml.declarations_t
    def extract_constants_from_ast(self, declarations) -> List[Constant]
    def handle_preprocessor_defines(self, file_path: str) -> List[Constant]
```

#### 4. UsageAnalyzer
```python
class UsageAnalyzer:
    def __init__(self, file_module_map: Dict[str, str], exclude_file: str)
    def find_constant_usage(self, constant: Constant) -> Dict[str, List[str]]
    def search_in_file(self, file_path: str, constant_name: str) -> List[int]
    def categorize_usage(self, usage_map: Dict) -> UsageCategory
```

#### 5. FileGenerator
```python
class FileGenerator:
    def __init__(self, sandbox_mode: bool, project_root: str)
    def generate_module_const_file(self, module: str, constants: List[Constant])
    def generate_export_const_file(self, module: str, constants: List[Constant])
    def append_to_existing_file(self, file_path: str, constants: List[Constant])
    def create_header_guards(self, module_name: str, file_type: str) -> str
```

### Data Models

#### Constant
```python
@dataclass
class Constant:
    name: str
    value: str
    type: str  # 'define', 'const', 'constexpr'
    comments: List[str]
    line_number: int
    preprocessor_context: Optional[str]
```

#### UsageInfo
```python
@dataclass
class UsageInfo:
    constant: Constant
    usage_files: Dict[str, List[int]]  # file_path -> line_numbers
    modules_using: Set[str]
    category: UsageCategory  # PRIVATE, SHARED
    target_file_type: str  # 'const' or 'export_const'
```

#### UsageCategory
```python
class UsageCategory(Enum):
    PRIVATE = "private"  # Used only within one module
    SHARED = "shared"    # Used across multiple modules
    UNUSED = "unused"    # Not found in any files
    AMBIGUOUS = "ambiguous"  # Needs manual review
```

## Error Handling

### CMake Integration Errors
- **Compile Commands Generation Failure**: Fall back to CMakeLists.txt parsing
- **Missing CMake Files**: Use directory-based module detection
- **Invalid JSON Format**: Log error and use fallback methods

### File Processing Errors
- **Constants File Not Found**: Exit with clear error message
- **Permission Errors**: Handle gracefully with informative messages
- **Malformed Constants**: Log warnings and continue processing

### Usage Analysis Errors
- **Binary Files**: Skip non-text files during search
- **Large Files**: Implement streaming for memory efficiency
- **Encoding Issues**: Handle different text encodings gracefully

## Testing Strategy

### Unit Tests
- **ConstantsParser**: Test CastXML integration and pygccxml AST processing for various C++ constructs
- **UsageAnalyzer**: Test constant search accuracy and module categorization
- **CMakeAnalyzer**: Test compile commands parsing and fallback mechanisms
- **FileGenerator**: Test header file generation and append functionality

### Integration Tests
- **End-to-End Pipeline**: Test complete workflow with sample C++ project
- **CMake Integration**: Test with real CMake projects of varying complexity
- **File System Operations**: Test sandbox and direct modification modes

### Test Data
- **Sample Constants File**: Create 100+ line test file with various constant types, templates, and namespaces
- **Mock C++ Project**: Multi-module project with known usage patterns
- **CMake Test Cases**: Projects with different CMake configurations
- **CastXML Test Cases**: Verify parsing of complex C++ constructs and edge cases

## Implementation Details

### Constants Parsing Strategy
The parser will use CastXML and pygccxml for robust C++ code analysis:
- **CastXML Integration**: Generate XML AST representation of the constants file
- **pygccxml Processing**: Parse the AST to extract const/constexpr variables and their metadata
- **Preprocessor Handling**: Use CastXML's preprocessor support to handle #define macros
- **Type Information**: Leverage AST to get accurate type information and scope resolution
- **Complex Constructs**: Handle templates, namespaces, and conditional compilation correctly

### Module Detection Algorithm
1. **Primary**: Use compile_commands.json to map files to CMake targets
2. **Secondary**: Parse CMakeLists.txt files for target definitions
3. **Fallback**: Use directory structure to infer module boundaries

### Usage Search Optimization
- Use ripgrep or similar fast text search tools when available
- Implement parallel processing for large codebases
- Cache search results to avoid redundant file scanning

### File Generation Strategy
- Generate temporary files first, then atomic moves for safety
- Maintain consistent formatting and header guard conventions
- Support incremental updates without duplicating existing constants

## Configuration Format

### Command Line Interface
```bash
python constants_refactor.py \
    --constants-file path/to/constants.h \
    --project-root /path/to/project \
    --build-dir build/ \
    --mode [sandbox|direct] \
    --exclude-dirs "build/,third_party/" \
    --config config.json
```

### Configuration File (JSON)
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