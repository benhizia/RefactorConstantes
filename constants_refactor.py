#!/usr/bin/env python3
"""
C++ Constants Refactoring Tool

A script to analyze a large C++ constants file and automatically categorize 
constants based on their usage across modules in a CMake-based project.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import os
import re
import shutil
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

try:
    import pygccxml
    from pygccxml import parser, declarations, utils
    PYGCCXML_AVAILABLE = True
except ImportError:
    PYGCCXML_AVAILABLE = False
    print("Warning: pygccxml not available. Install with: pip install pygccxml")

try:
    import xml.etree.ElementTree as ET
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False


@dataclass
class Constant:
    """Represents a parsed constant from C++ code."""
    name: str
    value: str
    type: str  # 'define', 'const', 'constexpr'
    comments: List[str]
    line_number: int
    preprocessor_context: Optional[str] = None


class UsageCategory(Enum):
    """Categories for constant usage patterns."""
    PRIVATE = "private"      # Used only within one module
    SHARED = "shared"        # Used across multiple modules
    UNUSED = "unused"        # Not found in any files
    AMBIGUOUS = "ambiguous"  # Needs manual review


class ConstantsRefactorError(Exception):
    """Base exception class for constants refactor tool errors."""
    pass


class CastXMLError(ConstantsRefactorError):
    """Exception raised when CastXML operations fail."""
    pass


class CMakeError(ConstantsRefactorError):
    """Exception raised when CMake operations fail."""
    pass


class FilePermissionError(ConstantsRefactorError):
    """Exception raised when file permission issues occur."""
    pass


class MalformedInputError(ConstantsRefactorError):
    """Exception raised when input files are malformed or invalid."""
    pass


class ConfigurationError(ConstantsRefactorError):
    """Exception raised when configuration is invalid."""
    pass


class Logger:
    """Enhanced logging system with different verbosity levels."""
    
    def __init__(self, name: str = "constants_refactor", level: str = "INFO"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # Track error counts for reporting
        self.error_count = 0
        self.warning_count = 0
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.warning_count += 1
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details."""
        self.error_count += 1
        if exception:
            self.logger.error(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(f"Exception details: {traceback.format_exc()}")
        else:
            self.logger.error(message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception details."""
        self.error_count += 1
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(f"Exception details: {traceback.format_exc()}")
        else:
            self.logger.critical(message, **kwargs)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors and warnings encountered."""
        return {
            "errors": self.error_count,
            "warnings": self.warning_count
        }
    
    def add_file_handler(self, log_file: str, level: str = "DEBUG"):
        """
        Add file handler for logging to file.
        
        Args:
            log_file: Path to log file
            level: Logging level for file handler
        """
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.info(f"File logging enabled: {log_file}")
            
        except Exception as e:
            self.error(f"Failed to add file handler for {log_file}", e)


class ErrorHandler:
    """Centralized error handling with graceful fallback mechanisms."""
    
    def __init__(self, logger: Logger):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance for error reporting
        """
        self.logger = logger
        self.recovery_strategies = {}
    
    def handle_castxml_error(self, error: Exception, file_path: str) -> List[Constant]:
        """
        Handle CastXML parsing errors with fallback strategies.
        
        Args:
            error: The exception that occurred
            file_path: Path to the file being parsed
            
        Returns:
            List of constants parsed using fallback methods
        """
        self.logger.error(f"CastXML parsing failed for {file_path}", error)
        
        # Try fallback parsing strategies
        fallback_constants = []
        
        try:
            self.logger.info(f"Attempting manual parsing fallback for {file_path}")
            parser = ConstantsParser()
            fallback_constants = parser._parse_defines_manually(file_path)
            fallback_constants.extend(parser._parse_const_variables_manually(file_path))
            
            self.logger.info(f"Fallback parsing recovered {len(fallback_constants)} constants")
            
        except Exception as fallback_error:
            self.logger.error(f"Fallback parsing also failed for {file_path}", fallback_error)
            raise CastXMLError(f"Both CastXML and fallback parsing failed for {file_path}") from error
        
        return fallback_constants
    
    def handle_cmake_error(self, error: Exception, build_dir: str, project_root: str) -> Dict[str, str]:
        """
        Handle CMake errors with fallback strategies.
        
        Args:
            error: The exception that occurred
            build_dir: CMake build directory
            project_root: Project root directory
            
        Returns:
            File-to-module mapping using fallback methods
        """
        self.logger.error(f"CMake analysis failed for build directory {build_dir}", error)
        
        try:
            self.logger.info("Attempting CMakeLists.txt parsing fallback")
            analyzer = CMakeAnalyzer()
            fallback_mapping = analyzer.fallback_cmake_parse(project_root)
            
            if fallback_mapping:
                self.logger.info(f"CMakeLists.txt fallback recovered {len(fallback_mapping)} file mappings")
                return fallback_mapping
            else:
                self.logger.warning("CMakeLists.txt fallback found no mappings")
                
        except Exception as fallback_error:
            self.logger.error("CMakeLists.txt parsing fallback failed", fallback_error)
        
        try:
            self.logger.info("Attempting directory-based module detection fallback")
            fallback_mapping = self._directory_based_fallback(project_root)
            self.logger.info(f"Directory-based fallback created {len(fallback_mapping)} mappings")
            return fallback_mapping
            
        except Exception as dir_error:
            self.logger.error("Directory-based fallback failed", dir_error)
            raise CMakeError(f"All CMake fallback strategies failed for {project_root}") from error
    
    def handle_file_permission_error(self, error: Exception, file_path: str, operation: str) -> bool:
        """
        Handle file permission errors with recovery strategies.
        
        Args:
            error: The exception that occurred
            file_path: Path to the file with permission issues
            operation: Operation being attempted (read, write, etc.)
            
        Returns:
            True if recovery was successful, False otherwise
        """
        self.logger.error(f"File permission error during {operation} on {file_path}", error)
        
        # Check if file exists and is accessible
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            self.logger.error(f"File does not exist: {file_path}")
            return False
        
        # Try to provide helpful information about the permission issue
        try:
            stat_info = path_obj.stat()
            self.logger.info(f"File permissions: {oct(stat_info.st_mode)[-3:]}")
            self.logger.info(f"File owner: {stat_info.st_uid}")
            self.logger.info(f"Current user: {os.getuid() if hasattr(os, 'getuid') else 'unknown'}")
            
        except Exception as stat_error:
            self.logger.error("Could not get file stat information", stat_error)
        
        # For read operations, try alternative approaches
        if operation == "read":
            try:
                # Try reading with different encoding
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self.logger.info(f"Successfully read file with error handling: {file_path}")
                return True
                
            except Exception as read_error:
                self.logger.error(f"Alternative read strategy failed for {file_path}", read_error)
        
        return False
    
    def handle_malformed_input_error(self, error: Exception, file_path: str, line_number: Optional[int] = None) -> bool:
        """
        Handle malformed input errors with recovery strategies.
        
        Args:
            error: The exception that occurred
            file_path: Path to the malformed file
            line_number: Line number where error occurred (if known)
            
        Returns:
            True if recovery was successful, False otherwise
        """
        location = f" at line {line_number}" if line_number else ""
        self.logger.error(f"Malformed input in {file_path}{location}", error)
        
        try:
            # Try to validate and clean the input
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Basic validation
            if not lines:
                self.logger.error(f"File is empty: {file_path}")
                return False
            
            # Check for common issues
            issues_found = []
            
            # Check encoding issues
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                issues_found.append("encoding issues")
            
            # Check for extremely long lines that might cause issues
            max_line_length = max(len(line) for line in lines)
            if max_line_length > 10000:
                issues_found.append(f"very long lines (max: {max_line_length} chars)")
            
            # Check for binary content
            if any(b'\x00' in line.encode('utf-8', errors='ignore') for line in lines[:10]):
                issues_found.append("possible binary content")
            
            if issues_found:
                self.logger.warning(f"Input validation found issues in {file_path}: {', '.join(issues_found)}")
            else:
                self.logger.info(f"Input validation passed for {file_path}")
            
            return True
            
        except Exception as validation_error:
            self.logger.error(f"Input validation failed for {file_path}", validation_error)
            return False
    
    def _directory_based_fallback(self, project_root: str) -> Dict[str, str]:
        """
        Create file-to-module mapping based on directory structure.
        
        Args:
            project_root: Project root directory
            
        Returns:
            Dictionary mapping file paths to module names
        """
        mapping = {}
        project_path = Path(project_root)
        
        # Common source directories
        source_dirs = ['src', 'source', 'lib', 'libs', 'modules', 'components']
        
        for source_dir_name in source_dirs:
            source_dir = project_path / source_dir_name
            if source_dir.exists() and source_dir.is_dir():
                self._map_directory_to_modules(source_dir, mapping, source_dir_name)
        
        return mapping
    
    def _map_directory_to_modules(self, directory: Path, mapping: Dict[str, str], base_module: str):
        """
        Recursively map directory contents to modules.
        
        Args:
            directory: Directory to map
            mapping: Dictionary to populate with mappings
            base_module: Base module name for this directory
        """
        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in {'.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx'}:
                    # Map file to current module
                    mapping[str(item)] = base_module
                elif item.is_dir() and not item.name.startswith('.'):
                    # Recursively map subdirectories
                    sub_module = item.name
                    self._map_directory_to_modules(item, mapping, sub_module)
                    
        except PermissionError as e:
            self.logger.warning(f"Permission denied accessing directory {directory}: {e}")
        except Exception as e:
            self.logger.error(f"Error mapping directory {directory}", e)
    
    def with_error_handling(self, operation_name: str):
        """
        Decorator for adding comprehensive error handling to methods.
        
        Args:
            operation_name: Name of the operation for logging
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except ConstantsRefactorError:
                    # Re-raise our custom exceptions
                    raise
                except FileNotFoundError as e:
                    self.logger.error(f"File not found during {operation_name}", e)
                    raise FilePermissionError(f"File not found: {e}") from e
                except PermissionError as e:
                    self.logger.error(f"Permission denied during {operation_name}", e)
                    raise FilePermissionError(f"Permission denied: {e}") from e
                except subprocess.TimeoutExpired as e:
                    self.logger.error(f"Timeout during {operation_name}", e)
                    raise ConstantsRefactorError(f"Operation timed out: {operation_name}") from e
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Process failed during {operation_name}", e)
                    raise ConstantsRefactorError(f"Process failed: {operation_name}") from e
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing failed during {operation_name}", e)
                    raise MalformedInputError(f"Invalid JSON: {e}") from e
                except Exception as e:
                    self.logger.error(f"Unexpected error during {operation_name}", e)
                    raise ConstantsRefactorError(f"Unexpected error in {operation_name}: {e}") from e
            
            return wrapper
        return decorator


@dataclass
class UsageInfo:
    """Information about how a constant is used across the codebase."""
    constant: Constant
    usage_files: Dict[str, List[int]]  # file_path -> line_numbers
    modules_using: Set[str]
    category: UsageCategory
    target_file_type: str  # 'const' or 'export_const'


class CMakeAnalyzer:
    """Analyzer for CMake projects to determine file-to-module mappings."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the CMake analyzer."""
        self.logger = logger or Logger("CMakeAnalyzer")
        self.error_handler = ErrorHandler(self.logger)
    
    def generate_compile_commands(self, build_dir: str, project_root: str) -> bool:
        """
        Generate compile_commands.json using CMake.
        
        Args:
            build_dir: CMake build directory
            project_root: Project root directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            build_path = Path(build_dir)
            project_path = Path(project_root)
            
            # Create build directory if it doesn't exist
            build_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Generating compile commands in {build_dir}")
            
            # Run CMake to generate compile commands
            cmd = [
                'cmake',
                '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                str(project_path.absolute())
            ]
            
            result = subprocess.run(
                cmd,
                cwd=build_path,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"CMake generation failed: {result.stderr}")
                return False
            
            # Check if compile_commands.json was created
            compile_commands_path = build_path / "compile_commands.json"
            if not compile_commands_path.exists():
                self.logger.error("compile_commands.json was not generated")
                return False
            
            self.logger.info(f"Successfully generated compile_commands.json")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("CMake generation timed out")
            return False
        except Exception as e:
            self.logger.error("CMake generation failed", e)
            return False
    
    def parse_compile_commands(self, json_path: str) -> Dict[str, str]:
        """
        Parse compile_commands.json to get file-to-target mappings.
        
        Args:
            json_path: Path to compile_commands.json
            
        Returns:
            Dictionary mapping file paths to target names
        """
        try:
            self.logger.info(f"Parsing compile commands from {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                compile_commands = json.load(f)
            
            file_target_map = {}
            
            for entry in compile_commands:
                if 'file' in entry and 'command' in entry:
                    file_path = entry['file']
                    command = entry['command']
                    
                    # Extract target name from compile command
                    target = self._extract_target_from_command(command)
                    if target:
                        file_target_map[file_path] = target
            
            self.logger.info(f"Parsed {len(file_target_map)} file-to-target mappings")
            return file_target_map
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in compile commands file", e)
            raise MalformedInputError(f"Invalid compile_commands.json: {e}") from e
        except Exception as e:
            self.logger.error(f"Failed to parse compile commands", e)
            raise CMakeError(f"Failed to parse compile_commands.json: {e}") from e
    
    def _extract_target_from_command(self, command: str) -> Optional[str]:
        """
        Extract target name from compile command.
        
        Args:
            command: Compile command string
            
        Returns:
            Target name or None if not found
        """
        # Look for CMake target patterns in the command
        # This is a heuristic approach as compile commands don't directly contain target names
        
        # Try to find CMakeFiles/target.dir pattern
        import re
        target_pattern = r'CMakeFiles/([^/]+)\.dir'
        match = re.search(target_pattern, command)
        if match:
            return match.group(1)
        
        # Fallback: try to extract from output file path
        output_pattern = r'-o\s+([^\s]+)'
        match = re.search(output_pattern, command)
        if match:
            output_path = Path(match.group(1))
            # Extract directory name as potential target
            if 'CMakeFiles' in output_path.parts:
                for i, part in enumerate(output_path.parts):
                    if part == 'CMakeFiles' and i + 1 < len(output_path.parts):
                        next_part = output_path.parts[i + 1]
                        if next_part.endswith('.dir'):
                            return next_part[:-4]  # Remove .dir suffix
        
        return None
    
    def fallback_cmake_parse(self, project_root: str) -> Dict[str, str]:
        """
        Fallback method to parse CMakeLists.txt files for target definitions.
        
        Args:
            project_root: Project root directory
            
        Returns:
            Dictionary mapping file paths to module names
        """
        try:
            self.logger.info(f"Parsing CMakeLists.txt files in {project_root}")
            
            project_path = Path(project_root)
            file_module_map = {}
            
            # Find all CMakeLists.txt files
            cmake_files = list(project_path.rglob("CMakeLists.txt"))
            self.logger.info(f"Found {len(cmake_files)} CMakeLists.txt files")
            
            for cmake_file in cmake_files:
                try:
                    mappings = self._parse_cmake_file(cmake_file)
                    file_module_map.update(mappings)
                except Exception as e:
                    self.logger.warning(f"Failed to parse {cmake_file}", e)
                    continue
            
            self.logger.info(f"CMakeLists.txt parsing found {len(file_module_map)} file mappings")
            return file_module_map
            
        except Exception as e:
            self.logger.error("CMakeLists.txt fallback parsing failed", e)
            raise CMakeError(f"CMakeLists.txt parsing failed: {e}") from e
    
    def _parse_cmake_file(self, cmake_file: Path) -> Dict[str, str]:
        """
        Parse a single CMakeLists.txt file for target definitions.
        
        Args:
            cmake_file: Path to CMakeLists.txt file
            
        Returns:
            Dictionary mapping file paths to target names
        """
        mappings = {}
        
        try:
            with open(cmake_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for add_executable and add_library commands
            import re
            
            # Pattern to match add_executable/add_library commands
            target_patterns = [
                r'add_executable\s*\(\s*(\w+)\s+([^)]+)\)',
                r'add_library\s*\(\s*(\w+)\s+[^)]*?([^)]+)\)'
            ]
            
            cmake_dir = cmake_file.parent
            
            for pattern in target_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    target_name = match.group(1)
                    sources_str = match.group(2)
                    
                    # Extract source files from the sources string
                    source_files = self._extract_source_files(sources_str, cmake_dir)
                    
                    # Map each source file to this target
                    for source_file in source_files:
                        mappings[str(source_file)] = target_name
            
        except Exception as e:
            self.logger.warning(f"Error parsing CMake file {cmake_file}", e)
        
        return mappings
    
    def _extract_source_files(self, sources_str: str, cmake_dir: Path) -> List[Path]:
        """
        Extract source file paths from CMake sources string.
        
        Args:
            sources_str: String containing source file references
            cmake_dir: Directory containing the CMakeLists.txt file
            
        Returns:
            List of resolved source file paths
        """
        source_files = []
        
        # Split by whitespace and filter out CMake keywords
        cmake_keywords = {'PUBLIC', 'PRIVATE', 'INTERFACE', 'STATIC', 'SHARED', 'MODULE'}
        
        tokens = sources_str.split()
        
        for token in tokens:
            token = token.strip()
            
            # Skip empty tokens and CMake keywords
            if not token or token in cmake_keywords:
                continue
            
            # Skip variable references for now (would need full CMake parsing)
            if token.startswith('${') or token.startswith('$<'):
                continue
            
            # Check if it looks like a source file
            if any(token.endswith(ext) for ext in ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx']):
                # Resolve relative to CMake file directory
                source_path = cmake_dir / token
                if source_path.exists():
                    source_files.append(source_path.resolve())
                else:
                    # Try relative to project root
                    # This is a simplification - real CMake parsing would be more complex
                    pass
        
        return source_files
    
    def map_files_to_modules(self, file_target_map: Dict[str, str], 
                           module_mapping: Optional[Dict[str, List[str]]] = None) -> Dict[str, str]:
        """
        Map files to modules using target information and optional module mapping.
        
        Args:
            file_target_map: Dictionary mapping file paths to target names
            module_mapping: Optional mapping of module names to target patterns
            
        Returns:
            Dictionary mapping file paths to module names
        """
        try:
            self.logger.info("Mapping files to modules")
            
            file_module_map = {}
            
            for file_path, target in file_target_map.items():
                module = self._determine_module_for_target(target, module_mapping)
                if module:
                    file_module_map[file_path] = module
            
            self.logger.info(f"Mapped {len(file_module_map)} files to modules")
            return file_module_map
            
        except Exception as e:
            self.logger.error("File-to-module mapping failed", e)
            raise CMakeError(f"File-to-module mapping failed: {e}") from e
    
    def _determine_module_for_target(self, target: str, 
                                   module_mapping: Optional[Dict[str, List[str]]] = None) -> Optional[str]:
        """
        Determine module name for a given target.
        
        Args:
            target: Target name
            module_mapping: Optional mapping of module names to target patterns
            
        Returns:
            Module name or None if not determined
        """
        if module_mapping:
            # Check if target matches any module mapping patterns
            for module, patterns in module_mapping.items():
                for pattern in patterns:
                    if target.startswith(pattern):
                        return module
        
        # Default: use target name as module name
        return target


class UsageAnalyzer:
    """Analyzer for finding constant usage patterns across the codebase."""
    
    def __init__(self, file_module_map: Dict[str, str], exclude_file: str, logger: Optional[Logger] = None):
        """
        Initialize the usage analyzer.
        
        Args:
            file_module_map: Mapping of file paths to module names
            exclude_file: Path to the constants file to exclude from search
            logger: Logger instance for error reporting
        """
        self.file_module_map = file_module_map
        self.exclude_file = os.path.abspath(exclude_file)
        self.logger = logger or Logger("UsageAnalyzer")
        self.error_handler = ErrorHandler(self.logger)
        self.ripgrep_available = self._check_ripgrep_available()
        
    def _check_ripgrep_available(self) -> bool:
        """Check if ripgrep is available for fast text search."""
        try:
            result = subprocess.run(['rg', '--version'], capture_output=True, text=True, timeout=5)
            available = result.returncode == 0
            if available:
                self.logger.info("ripgrep is available for fast text search")
            else:
                self.logger.info("ripgrep not available, will use Python fallback")
            return available
        except subprocess.TimeoutExpired:
            self.logger.warning("ripgrep version check timed out")
            return False
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            self.logger.debug(f"ripgrep not available: {e}")
            return False
    
    def find_constant_usage(self, constant: Constant, source_directories: List[str]) -> Dict[str, List[int]]:
        """
        Find all usage locations of a constant across the codebase.
        
        Args:
            constant: The constant to search for
            source_directories: List of directories to search in
            
        Returns:
            Dictionary mapping file paths to lists of line numbers where the constant is used
        """
        usage_map = {}
        
        if self.ripgrep_available:
            usage_map = self._search_with_ripgrep(constant.name, source_directories)
        else:
            usage_map = self._search_with_python(constant.name, source_directories)
        
        # Filter out the original constants file
        filtered_usage = {}
        for file_path, line_numbers in usage_map.items():
            abs_file_path = os.path.abspath(file_path)
            if abs_file_path != self.exclude_file:
                filtered_usage[abs_file_path] = line_numbers
        
        return filtered_usage
    
    def _search_with_ripgrep(self, constant_name: str, source_directories: List[str]) -> Dict[str, List[int]]:
        """
        Use ripgrep for fast text search across the codebase.
        
        Args:
            constant_name: Name of the constant to search for
            source_directories: Directories to search in
            
        Returns:
            Dictionary mapping file paths to line numbers
        """
        usage_map = {}
        
        try:
            self.logger.debug(f"Searching for '{constant_name}' using ripgrep")
            
            # Build ripgrep command
            # Use word boundary search to avoid partial matches
            cmd = [
                'rg',
                '--line-number',
                '--no-heading',
                '--with-filename',
                '--type', 'cpp',
                '--type', 'c',
                '--type', 'h',
                f'\b{constant_name}\b'  # Word boundary search
            ]
            
            # Add source directories
            cmd.extend(source_directories)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse ripgrep output: filename:line_number:content
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 2:
                            file_path = os.path.abspath(parts[0])
                            try:
                                line_number = int(parts[1])
                                if file_path not in usage_map:
                                    usage_map[file_path] = []
                                usage_map[file_path].append(line_number)
                            except ValueError:
                                self.logger.debug(f"Invalid line number in ripgrep output: {parts[1]}")
                                continue
                
                self.logger.debug(f"ripgrep found {len(usage_map)} files with '{constant_name}'")
            elif result.returncode == 1:
                # No matches found (normal case)
                self.logger.debug(f"ripgrep found no matches for '{constant_name}'")
            else:
                # Error occurred
                self.logger.warning(f"ripgrep returned error code {result.returncode}: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"ripgrep search for '{constant_name}' timed out")
            # Fallback to Python search
            return self._search_with_python(constant_name, source_directories)
        except Exception as e:
            self.logger.warning(f"ripgrep search failed for '{constant_name}': {e}")
            # Fallback to Python search
            return self._search_with_python(constant_name, source_directories)
        
        return usage_map
    
    def _search_with_python(self, constant_name: str, source_directories: List[str]) -> Dict[str, List[int]]:
        """
        Fallback Python-based text search.
        
        Args:
            constant_name: Name of the constant to search for
            source_directories: Directories to search in
            
        Returns:
            Dictionary mapping file paths to line numbers
        """
        usage_map = {}
        
        # File extensions to search
        extensions = {'.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx'}
        
        for source_dir in source_directories:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue
                
            # Recursively find all C++ files
            for file_path in source_path.rglob('*'):
                if file_path.suffix.lower() in extensions and file_path.is_file():
                    line_numbers = self.search_in_file(str(file_path), constant_name)
                    if line_numbers:
                        abs_path = os.path.abspath(file_path)
                        usage_map[abs_path] = line_numbers
        
        return usage_map
    
    def search_in_file(self, file_path: str, constant_name: str) -> List[int]:
        """
        Search for a constant name in a specific file.
        
        Args:
            file_path: Path to the file to search
            constant_name: Name of the constant to search for
            
        Returns:
            List of line numbers where the constant is found
        """
        line_numbers = []
        
        try:
            # Check if file is accessible
            if not os.path.exists(file_path):
                self.logger.debug(f"File does not exist: {file_path}")
                return line_numbers
            
            # Check file size to avoid processing extremely large files
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                self.logger.warning(f"Skipping large file ({file_size} bytes): {file_path}")
                return line_numbers
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Use word boundary matching to avoid partial matches
                    import re
                    pattern = r'\b' + re.escape(constant_name) + r'\b'
                    if re.search(pattern, line):
                        line_numbers.append(line_num)
                        
        except PermissionError as e:
            self.logger.debug(f"Permission denied accessing file {file_path}: {e}")
        except UnicodeDecodeError as e:
            self.logger.debug(f"Unicode decode error in file {file_path}: {e}")
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        import re
                        pattern = r'\b' + re.escape(constant_name) + r'\b'
                        if re.search(pattern, line):
                            line_numbers.append(line_num)
            except Exception as fallback_e:
                self.logger.debug(f"Fallback encoding also failed for {file_path}: {fallback_e}")
        except Exception as e:
            self.logger.warning(f"Failed to search in file {file_path}: {e}")
        
        return line_numbers
    
    def categorize_usage(self, usage_map: Dict[str, List[int]]) -> UsageCategory:
        """
        Categorize constant usage based on which modules use it.
        
        Args:
            usage_map: Dictionary mapping file paths to line numbers
            
        Returns:
            UsageCategory indicating how the constant should be categorized
        """
        if not usage_map:
            return UsageCategory.UNUSED
        
        # Determine which modules use this constant
        modules_using = set()
        ambiguous_files = []
        test_files = []
        header_files = []
        
        for file_path in usage_map.keys():
            # Categorize file types for better analysis
            if self._is_test_file(file_path):
                test_files.append(file_path)
            elif self._is_header_file(file_path):
                header_files.append(file_path)
            
            module = self._get_module_for_file(file_path)
            if module:
                modules_using.add(module)
            else:
                ambiguous_files.append(file_path)
        
        # Handle edge cases and ambiguous patterns
        category = self._determine_category_with_edge_cases(
            modules_using, ambiguous_files, test_files, header_files, usage_map
        )
        
        return category
    
    def _determine_category_with_edge_cases(
        self, 
        modules_using: Set[str], 
        ambiguous_files: List[str],
        test_files: List[str],
        header_files: List[str],
        usage_map: Dict[str, List[int]]
    ) -> UsageCategory:
        """
        Determine category with enhanced edge case handling.
        
        Args:
            modules_using: Set of modules that use the constant
            ambiguous_files: Files that couldn't be mapped to modules
            test_files: Files identified as test files
            header_files: Files identified as header files
            usage_map: Original usage mapping
            
        Returns:
            UsageCategory with enhanced edge case handling
        """
        # If we have files that can't be mapped to modules, check if they're special cases
        if ambiguous_files:
            # Filter out common non-module files that shouldn't affect categorization
            significant_ambiguous = []
            for file_path in ambiguous_files:
                if not self._is_ignorable_file(file_path):
                    significant_ambiguous.append(file_path)
            
            # If we still have significant ambiguous files, mark as ambiguous
            if significant_ambiguous:
                print(f"Warning: Files without clear module mapping: {significant_ambiguous}")
                return UsageCategory.AMBIGUOUS
        
        # Handle test files specially - they don't usually affect module categorization
        if test_files and not modules_using:
            # If only used in test files, check if tests belong to a specific module
            test_modules = set()
            for test_file in test_files:
                test_module = self._infer_module_from_test_file(test_file)
                if test_module:
                    test_modules.add(test_module)
            
            if len(test_modules) == 1:
                return UsageCategory.PRIVATE
            elif len(test_modules) > 1:
                return UsageCategory.SHARED
        
        # Handle header files - they might indicate shared usage
        if header_files:
            # Check if header files are in include directories (likely shared)
            shared_headers = [f for f in header_files if self._is_shared_header(f)]
            if shared_headers and len(modules_using) >= 1:
                return UsageCategory.SHARED
        
        # Standard categorization based on number of modules
        if len(modules_using) == 0:
            return UsageCategory.UNUSED
        elif len(modules_using) == 1:
            return UsageCategory.PRIVATE
        else:
            return UsageCategory.SHARED
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file."""
        file_path_lower = file_path.lower()
        test_indicators = ['test', 'tests', 'unittest', 'gtest', '_test.', 'test_']
        return any(indicator in file_path_lower for indicator in test_indicators)
    
    def _is_header_file(self, file_path: str) -> bool:
        """Check if a file is a header file."""
        return Path(file_path).suffix.lower() in {'.h', '.hpp', '.hxx'}
    
    def _is_ignorable_file(self, file_path: str) -> bool:
        """Check if a file should be ignored for module categorization."""
        file_path_lower = file_path.lower()
        ignorable_patterns = [
            'build/', 'cmake', 'third_party/', 'external/', 'vendor/',
            'generated/', 'temp/', 'tmp/', '.git/', 'node_modules/'
        ]
        return any(pattern in file_path_lower for pattern in ignorable_patterns)
    
    def _is_shared_header(self, file_path: str) -> bool:
        """Check if a header file is likely to be shared across modules."""
        file_path_lower = file_path.lower()
        shared_indicators = ['include/', 'public/', 'api/', 'common/', 'shared/']
        return any(indicator in file_path_lower for indicator in shared_indicators)
    
    def _infer_module_from_test_file(self, test_file_path: str) -> Optional[str]:
        """Try to infer which module a test file belongs to."""
        # Look for patterns like: tests/module_name/, module_name/tests/, module_name_test.cpp
        path_parts = Path(test_file_path).parts
        
        # Check if any part of the path matches known modules
        for part in path_parts:
            # Remove test-related suffixes to find potential module name
            clean_part = part.lower()
            for suffix in ['_test', '_tests', 'test_', 'tests_']:
                if clean_part.endswith(suffix):
                    clean_part = clean_part[:-len(suffix)]
                elif clean_part.startswith(suffix):
                    clean_part = clean_part[len(suffix):]
            
            # Check if this matches any known module
            if clean_part in [module.lower() for module in self.file_module_map.values()]:
                return clean_part
        
        return None
    
    def _get_module_for_file(self, file_path: str) -> Optional[str]:
        """
        Get the module name for a given file path with enhanced matching.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Module name or None if not found
        """
        # Normalize the file path
        normalized_path = os.path.normpath(file_path)
        
        # Try exact match first
        if normalized_path in self.file_module_map:
            return self.file_module_map[normalized_path]
        
        # Try to find a match by checking if any key is a substring
        for mapped_path, module in self.file_module_map.items():
            mapped_normalized = os.path.normpath(mapped_path)
            if (normalized_path.endswith(mapped_normalized) or 
                mapped_normalized.endswith(normalized_path) or
                self._paths_match_fuzzy(normalized_path, mapped_normalized)):
                return module
        
        # Try directory-based matching as fallback
        return self._infer_module_from_directory_structure(normalized_path)
    
    def _paths_match_fuzzy(self, path1: str, path2: str) -> bool:
        """
        Check if two paths match using fuzzy logic.
        
        Args:
            path1: First path to compare
            path2: Second path to compare
            
        Returns:
            True if paths likely refer to the same file/directory
        """
        # Convert to Path objects for easier manipulation
        p1 = Path(path1)
        p2 = Path(path2)
        
        # Check if the file names match
        if p1.name == p2.name:
            # Check if they share common directory components
            p1_parts = set(p1.parts)
            p2_parts = set(p2.parts)
            common_parts = p1_parts.intersection(p2_parts)
            
            # If they share more than half of their path components, consider it a match
            min_parts = min(len(p1_parts), len(p2_parts))
            if min_parts > 0 and len(common_parts) / min_parts > 0.5:
                return True
        
        return False
    
    def _infer_module_from_directory_structure(self, file_path: str) -> Optional[str]:
        """
        Try to infer module name from directory structure as fallback.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Inferred module name or None
        """
        path_obj = Path(file_path)
        
        # Look for common module directory patterns
        for part in path_obj.parts:
            part_lower = part.lower()
            
            # Skip common non-module directories
            if part_lower in {'src', 'include', 'lib', 'libs', 'source', 'sources', 
                             'headers', 'inc', 'public', 'private', 'impl', 'implementation'}:
                continue
            
            # Skip build and system directories
            if part_lower in {'build', 'cmake', 'third_party', 'external', 'vendor',
                             'generated', 'temp', 'tmp', 'bin', 'obj', 'debug', 'release'}:
                continue
            
            # If we have a reasonable directory name, use it as module name
            if len(part) > 1 and part.isalnum():
                return part
        
        return None
    
    def analyze_constant_usage(self, constant: Constant, source_directories: List[str]) -> UsageInfo:
        """
        Perform complete usage analysis for a single constant.
        
        Args:
            constant: The constant to analyze
            source_directories: Directories to search in
            
        Returns:
            UsageInfo object with complete analysis results
        """
        # Find usage locations
        usage_files = self.find_constant_usage(constant, source_directories)
        
        # Determine modules using this constant
        modules_using = set()
        for file_path in usage_files.keys():
            module = self._get_module_for_file(file_path)
            if module:
                modules_using.add(module)
        
        # Categorize the usage
        category = self.categorize_usage(usage_files)
        
        # Determine target file type
        target_file_type = 'export_const' if category == UsageCategory.SHARED else 'const'
        
        return UsageInfo(
            constant=constant,
            usage_files=usage_files,
            modules_using=modules_using,
            category=category,
            target_file_type=target_file_type
        )


class ConstantsParser:
    """Parser for C++ constants using CastXML and pygccxml."""
    
    def __init__(self, castxml_path: Optional[str] = None, logger: Optional[Logger] = None):
        """
        Initialize the constants parser.
        
        Args:
            castxml_path: Path to CastXML executable. If None, will search in PATH.
            logger: Logger instance for error reporting
        """
        self.logger = logger or Logger("ConstantsParser")
        self.error_handler = ErrorHandler(self.logger)
        
        if not PYGCCXML_AVAILABLE:
            raise ConfigurationError("pygccxml not available. Install with: pip install pygccxml")
        
        # Find CastXML using pygccxml utils
        try:
            self.generator_path, self.generator_name = utils.find_xml_generator()
            self.logger.info(f"Found XML generator: {self.generator_name} at {self.generator_path}")
        except Exception as e:
            self.logger.error("CastXML not found", e)
            raise ConfigurationError(f"CastXML not found: {e}") from e
        
        # Set a basic compiler path - try gcc first, then fallback
        try:
            self.compiler_path = self._find_compiler()
            self.logger.info(f"Using compiler: {self.compiler_path}")
        except Exception as e:
            self.logger.error("Failed to find suitable compiler", e)
            raise ConfigurationError(f"No suitable compiler found: {e}") from e
    

    

    
    def parse_constants_file(self, file_path: str) -> List[Constant]:
        """
        Parse constants from a C++ file using CastXML and pygccxml.
        
        Args:
            file_path: Path to the C++ constants file
            
        Returns:
            List of parsed Constant objects
            
        Raises:
            FilePermissionError: If the constants file doesn't exist or can't be accessed
            CastXMLError: If CastXML execution fails and fallback also fails
            MalformedInputError: If the input file is malformed
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            self.logger.error(f"Constants file not found: {file_path}")
            raise FilePermissionError(f"Constants file not found: {file_path}")
        
        # Validate input file
        if not self.error_handler.handle_malformed_input_error(Exception("validation"), str(file_path)):
            raise MalformedInputError(f"Input file validation failed: {file_path}")
        
        self.logger.info(f"Parsing constants file: {file_path}")
        
        constants = []
        
        # Parse with CastXML for const/constexpr variables
        try:
            ast_declarations = self.parse_with_castxml(str(file_path))
            ast_constants = self.extract_constants_from_ast(ast_declarations)
            constants.extend(ast_constants)
            self.logger.info(f"CastXML parsing found {len(ast_constants)} const/constexpr constants")
            
        except Exception as e:
            self.logger.warning(f"CastXML parsing failed, attempting fallback: {e}")
            try:
                fallback_constants = self.error_handler.handle_castxml_error(e, str(file_path))
                constants.extend(fallback_constants)
            except CastXMLError:
                # If fallback also fails, continue with manual parsing only
                self.logger.error("Both CastXML and fallback parsing failed, continuing with manual parsing only")
        
        # Handle preprocessor defines (always use manual parsing for better reliability)
        try:
            define_constants = self.handle_preprocessor_defines(str(file_path))
            constants.extend(define_constants)
            self.logger.info(f"Manual parsing found {len(define_constants)} #define constants")
            
        except Exception as e:
            self.logger.error(f"Manual parsing of defines failed for {file_path}", e)
            # Continue without defines rather than failing completely
        
        self.logger.info(f"Found {len(constants)} total constants")
        
        if not constants:
            self.logger.warning(f"No constants found in {file_path} - this might indicate a parsing issue")
        
        return constants
    
    def parse_with_castxml(self, file_path: str) -> declarations.namespace_t:
        """
        Parse C++ file using CastXML and return pygccxml declarations.
        
        Args:
            file_path: Path to the C++ file
            
        Returns:
            pygccxml declarations namespace
            
        Raises:
            CastXMLError: If CastXML execution fails
        """
        try:
            self.logger.debug(f"Configuring CastXML for {file_path}")
            
            # Configure with basic compiler settings
            xml_generator_config = parser.xml_generator_configuration_t(
                xml_generator_path=self.generator_path,
                xml_generator=self.generator_name,
                compiler_path=self.compiler_path,
                cflags="-std=c++17"
            )
            
            # Parse the C++ file
            file_full_path = os.path.abspath(file_path)
            self.logger.debug(f"Running CastXML on {file_full_path}")
            
            decls = parser.parse([file_full_path], xml_generator_config)
            
            # Get the global namespace
            global_ns = declarations.get_global_namespace(decls)
            
            self.logger.debug(f"CastXML parsing completed successfully for {file_path}")
            return global_ns
            
        except Exception as e:
            self.logger.error(f"CastXML parsing failed for {file_path}", e)
            raise CastXMLError(f"CastXML parsing failed for {file_path}: {e}") from e
    
    def _find_compiler(self) -> str:
        """Find a suitable compiler for CastXML."""
        # Try common compilers
        compilers = ['gcc', 'g++', 'clang', 'clang++']
        
        for compiler in compilers:
            try:
                self.logger.debug(f"Checking compiler: {compiler}")
                result = subprocess.run([compiler, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.debug(f"Found working compiler: {compiler}")
                    return compiler
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Compiler check timed out for {compiler}")
                continue
            except (FileNotFoundError, subprocess.SubprocessError) as e:
                self.logger.debug(f"Compiler {compiler} not available: {e}")
                continue
        
        # Fallback to gcc (CastXML might find it in PATH)
        self.logger.warning("No compiler found through version check, falling back to 'gcc'")
        return 'gcc'
    
    def extract_constants_from_ast(self, declarations_ns: declarations.namespace_t) -> List[Constant]:
        """
        Extract const and constexpr constants from pygccxml AST.
        
        Args:
            declarations_ns: pygccxml declarations namespace
            
        Returns:
            List of Constant objects
        """
        constants = []
        
        # Find all variable declarations
        variables = declarations_ns.variables()
        
        for var in variables:
            # Check if it's a const or constexpr variable
            if self._is_constant_variable(var):
                constant = self._create_constant_from_variable(var)
                if constant:
                    constants.append(constant)
        
        return constants
    
    def _is_constant_variable(self, var: declarations.variable_t) -> bool:
        """Check if a variable declaration represents a constant."""
        # Check if the type is const_t (const qualified)
        if hasattr(var, 'decl_type') and type(var.decl_type).__name__ == 'const_t':
            return True
        
        # Check for constexpr (this might be in different attributes depending on pygccxml version)
        if hasattr(var, 'is_constexpr') and var.is_constexpr:
            return True
            
        return False
    
    def _create_constant_from_variable(self, var: declarations.variable_t) -> Optional[Constant]:
        """Create a Constant object from a pygccxml variable declaration."""
        try:
            name = var.name
            
            # Get the value if available
            value = ''
            if hasattr(var, 'value') and var.value:
                value = str(var.value)
            
            # Determine type (const vs constexpr)
            const_type = 'constexpr' if (hasattr(var, 'is_constexpr') and var.is_constexpr) else 'const'
            
            # Get line number
            line_number = getattr(var.location, 'line', 0) if hasattr(var, 'location') else 0
            
            # Extract comments (if available)
            comments = []
            if hasattr(var, 'documentation') and var.documentation:
                comments = [var.documentation]
            
            return Constant(
                name=name,
                value=value,
                type=const_type,
                comments=comments,
                line_number=line_number
            )
            
        except Exception as e:
            print(f"Warning: Failed to create constant from variable {getattr(var, 'name', 'unknown')}: {e}")
            return None
    
    def handle_preprocessor_defines(self, file_path: str) -> List[Constant]:
        """
        Handle preprocessor #define macros using CastXML preprocessor support.
        
        Args:
            file_path: Path to the C++ file
            
        Returns:
            List of Constant objects representing #define macros
        """
        constants = []
        
        try:
            # Use CastXML with preprocessor output to capture #define macros
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
                temp_xml_path = temp_file.name
            
            try:
                # Use manual parsing for #define macros as it's more reliable
                # CastXML preprocessor output is complex to parse correctly
                constants.extend(self._parse_defines_manually(file_path))
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_xml_path):
                    os.unlink(temp_xml_path)
                    
        except subprocess.TimeoutExpired:
            print("Warning: CastXML preprocessor timed out, falling back to manual parsing")
            constants.extend(self._parse_defines_manually(file_path))
        except Exception as e:
            print(f"Warning: Failed to run CastXML preprocessor: {e}")
            # Fallback to manual parsing
            constants.extend(self._parse_defines_manually(file_path))
        
        return constants
    
    def _parse_preprocessor_output(self, preprocessor_output: str, file_path: str) -> List[Constant]:
        """Parse CastXML preprocessor output to extract #define macros."""
        constants = []
        
        for line_num, line in enumerate(preprocessor_output.split('\n'), 1):
            line = line.strip()
            if line.startswith('#define '):
                constant = self._parse_define_line(line, line_num, file_path)
                if constant:
                    constants.append(constant)
        
        return constants
    
    def _parse_defines_manually(self, file_path: str) -> List[Constant]:
        """Fallback method to manually parse #define statements from the file."""
        constants = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_comments = []
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                
                # Collect comments
                if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                    current_comments.append(stripped_line)
                    continue
                elif stripped_line.startswith('*/'):
                    current_comments.append(stripped_line)
                    continue
                elif not stripped_line:
                    # Empty line resets comment collection
                    current_comments = []
                    continue
                
                # Parse #define statements
                if stripped_line.startswith('#define '):
                    constant = self._parse_define_line(stripped_line, line_num, file_path, current_comments.copy())
                    if constant:
                        constants.append(constant)
                    current_comments = []  # Reset after processing
                elif not stripped_line.startswith('#'):
                    # Non-preprocessor line resets comment collection
                    current_comments = []
                    
        except Exception as e:
            print(f"Warning: Failed to manually parse defines from {file_path}: {e}")
        
        return constants
    
    def _parse_define_line(self, line: str, line_num: int, file_path: str, comments: Optional[List[str]] = None) -> Optional[Constant]:
        """Parse a single #define line into a Constant object."""
        try:
            # Remove #define prefix
            define_content = line[8:].strip()  # len('#define ') = 8
            
            if not define_content:
                return None
            
            # Split into name and value
            parts = define_content.split(None, 1)  # Split on first whitespace
            if not parts:
                return None
            
            name = parts[0]
            value = parts[1] if len(parts) > 1 else ''
            
            # Skip function-like macros (contain parentheses immediately after name)
            if '(' in name:
                return None
            
            # Clean up the value
            value = value.strip()
            
            # Handle multi-line macros (ending with backslash)
            if value.endswith('\\'):
                # For now, just note it's a multi-line macro
                value = value[:-1].strip() + ' /* multi-line macro */'
            
            return Constant(
                name=name,
                value=value,
                type='define',
                comments=comments or [],
                line_number=line_num
            )
            
        except Exception as e:
            print(f"Warning: Failed to parse define line '{line}': {e}")
            return None
    
    def _parse_const_variables_manually(self, file_path: str) -> List[Constant]:
        """
        Fallback method to manually parse const and constexpr variables from the file.
        
        Args:
            file_path: Path to the C++ file
            
        Returns:
            List of Constant objects representing const/constexpr variables
        """
        constants = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_comments = []
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                
                # Collect comments
                if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                    current_comments.append(stripped_line)
                    continue
                elif stripped_line.startswith('*/'):
                    current_comments.append(stripped_line)
                    continue
                elif not stripped_line:
                    # Empty line resets comment collection
                    current_comments = []
                    continue
                
                # Parse const and constexpr variables
                if self._is_const_variable_line(stripped_line):
                    constant = self._parse_const_variable_line(stripped_line, line_num, current_comments.copy())
                    if constant:
                        constants.append(constant)
                    current_comments = []  # Reset after processing
                elif not stripped_line.startswith('#') and not stripped_line.startswith('//'):
                    # Non-preprocessor, non-comment line resets comment collection
                    current_comments = []
                    
        except Exception as e:
            print(f"Warning: Failed to manually parse const variables from {file_path}: {e}")
        
        return constants
    
    def _is_const_variable_line(self, line: str) -> bool:
        """Check if a line contains a const or constexpr variable declaration."""
        # Simple heuristic: look for const or constexpr keywords followed by variable patterns
        line = line.strip()
        
        # Skip preprocessor directives, function declarations, etc.
        if (line.startswith('#') or 
            line.startswith('//') or 
            line.startswith('/*') or
            '(' in line and ')' in line and not '=' in line):  # Likely function declaration
            return False
        
        # Look for const or constexpr variable patterns
        return (line.startswith('const ') or 
                line.startswith('constexpr ') or
                ' const ' in line and '=' in line)
    
    def _parse_const_variable_line(self, line: str, line_num: int, comments: Optional[List[str]] = None) -> Optional[Constant]:
        """Parse a single const/constexpr variable line into a Constant object."""
        try:
            # Remove semicolon if present
            line = line.rstrip(';').strip()
            
            # Determine if it's const or constexpr
            const_type = 'constexpr' if line.startswith('constexpr') or 'constexpr' in line else 'const'
            
            # Find the assignment operator
            if '=' not in line:
                return None
            
            # Split on assignment
            left_part, right_part = line.split('=', 1)
            left_part = left_part.strip()
            right_part = right_part.strip()
            
            # Extract variable name from left part
            # Handle patterns like: "const int VAR", "constexpr double PI", "const char* const HOST"
            tokens = left_part.split()
            if len(tokens) < 2:
                return None
            
            # The variable name is typically the last token
            var_name = tokens[-1]
            
            # Remove pointer/reference symbols
            var_name = var_name.lstrip('*&').strip()
            
            # Skip if it looks like a complex declaration
            if '(' in var_name or ')' in var_name or '[' in var_name:
                return None
            
            return Constant(
                name=var_name,
                value=right_part,
                type=const_type,
                comments=comments or [],
                line_number=line_num
            )
            
        except Exception as e:
            print(f"Warning: Failed to parse const variable line '{line}': {e}")
            return None


class ReportGenerator:
    """Generator for analysis reports in multiple formats."""
    
    def __init__(self, output_format: str = "text"):
        """
        Initialize the report generator.
        
        Args:
            output_format: Output format ('json', 'text', 'markdown', or 'csv')
        """
        self.output_format = output_format.lower()
        if self.output_format not in ['json', 'text', 'markdown', 'csv']:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def generate_report(self, usage_infos: List[UsageInfo], analysis_summary: Dict[str, Any]) -> str:
        """
        Generate a complete analysis report.
        
        Args:
            usage_infos: List of UsageInfo objects with analysis results
            analysis_summary: Summary statistics and metadata
            
        Returns:
            Formatted report string
        """
        if self.output_format == 'json':
            return self._generate_json_report(usage_infos, analysis_summary)
        elif self.output_format == 'markdown':
            return self.generate_markdown_report(usage_infos, analysis_summary)
        elif self.output_format == 'csv':
            return self.generate_csv_summary(usage_infos)
        else:
            return self._generate_text_report(usage_infos, analysis_summary)
    
    def _generate_json_report(self, usage_infos: List[UsageInfo], analysis_summary: Dict[str, Any]) -> str:
        """
        Generate JSON format report for programmatic processing.
        
        Args:
            usage_infos: List of UsageInfo objects
            analysis_summary: Summary statistics
            
        Returns:
            JSON formatted report string
        """
        report_data = {
            "analysis_summary": analysis_summary,
            "constants": []
        }
        
        for usage_info in usage_infos:
            constant_data = {
                "name": usage_info.constant.name,
                "value": usage_info.constant.value,
                "type": usage_info.constant.type,
                "line_number": usage_info.constant.line_number,
                "comments": usage_info.constant.comments,
                "category": usage_info.category.value,
                "target_file_type": usage_info.target_file_type,
                "modules_using": list(usage_info.modules_using),
                "usage_statistics": {
                    "total_files": len(usage_info.usage_files),
                    "total_usages": sum(len(lines) for lines in usage_info.usage_files.values()),
                    "files": [
                        {
                            "path": file_path,
                            "line_numbers": line_numbers,
                            "usage_count": len(line_numbers)
                        }
                        for file_path, line_numbers in usage_info.usage_files.items()
                    ]
                },
                "proposed_destination": self._get_proposed_destination(usage_info),
                "requires_manual_review": usage_info.category == UsageCategory.AMBIGUOUS
            }
            
            report_data["constants"].append(constant_data)
        
        return json.dumps(report_data, indent=2, sort_keys=True)
    
    def _generate_text_report(self, usage_infos: List[UsageInfo], analysis_summary: Dict[str, Any]) -> str:
        """
        Generate human-readable text format report.
        
        Args:
            usage_infos: List of UsageInfo objects
            analysis_summary: Summary statistics
            
        Returns:
            Human-readable formatted report string
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("C++ CONSTANTS REFACTORING ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary section
        lines.append("ANALYSIS SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total constants analyzed: {analysis_summary.get('total_constants', 0)}")
        lines.append(f"Constants file: {analysis_summary.get('constants_file', 'N/A')}")
        lines.append(f"Project root: {analysis_summary.get('project_root', 'N/A')}")
        lines.append(f"Analysis timestamp: {analysis_summary.get('timestamp', 'N/A')}")
        lines.append("")
        
        # Categorization summary
        lines.append("CATEGORIZATION SUMMARY")
        lines.append("-" * 40)
        category_counts = analysis_summary.get('category_counts', {})
        for category, count in category_counts.items():
            lines.append(f"{category.upper()}: {count}")
        lines.append("")
        
        # Highlight ambiguous cases
        ambiguous_constants = [ui for ui in usage_infos if ui.category == UsageCategory.AMBIGUOUS]
        if ambiguous_constants:
            lines.append("⚠️  CONSTANTS REQUIRING MANUAL REVIEW")
            lines.append("-" * 40)
            for usage_info in ambiguous_constants:
                lines.append(f"• {usage_info.constant.name}")
                lines.append(f"  Reason: Ambiguous usage pattern")
                lines.append(f"  Files: {len(usage_info.usage_files)}")
                lines.append(f"  Modules: {', '.join(usage_info.modules_using) if usage_info.modules_using else 'Unknown'}")
                lines.append("")
        
        # Detailed analysis by category
        categories = [UsageCategory.SHARED, UsageCategory.PRIVATE, UsageCategory.UNUSED, UsageCategory.AMBIGUOUS]
        
        for category in categories:
            category_constants = [ui for ui in usage_infos if ui.category == category]
            if not category_constants:
                continue
                
            lines.append(f"{category.value.upper()} CONSTANTS ({len(category_constants)})")
            lines.append("-" * 40)
            
            for usage_info in category_constants:
                lines.extend(self._format_constant_details(usage_info))
                lines.append("")
        
        # Footer with recommendations
        lines.append("NEXT STEPS")
        lines.append("-" * 40)
        lines.append("1. Review constants marked as 'AMBIGUOUS' and resolve manually")
        lines.append("2. For PRIVATE constants, they will be placed in module-specific MDL_const.h files")
        lines.append("3. For SHARED constants, they will be placed in MDL_export_const.h files")
        lines.append("4. Run the tool in direct mode to apply the refactoring")
        lines.append("")
        
        return "\n".join(lines)
    
    def _format_constant_details(self, usage_info: UsageInfo) -> List[str]:
        """
        Format detailed information for a single constant.
        
        Args:
            usage_info: UsageInfo object to format
            
        Returns:
            List of formatted lines
        """
        lines = []
        constant = usage_info.constant
        
        # Constant header
        lines.append(f"📌 {constant.name}")
        lines.append(f"   Type: {constant.type}")
        lines.append(f"   Value: {constant.value}")
        lines.append(f"   Line: {constant.line_number}")
        
        # Comments if available
        if constant.comments:
            lines.append(f"   Comments: {'; '.join(constant.comments)}")
        
        # Proposed destination
        destination = self._get_proposed_destination(usage_info)
        lines.append(f"   → Proposed destination: {destination}")
        
        # Usage statistics
        total_files = len(usage_info.usage_files)
        total_usages = sum(len(line_nums) for line_nums in usage_info.usage_files.values())
        lines.append(f"   Usage: {total_usages} occurrences in {total_files} files")
        
        # Modules using this constant
        if usage_info.modules_using:
            modules_str = ', '.join(sorted(usage_info.modules_using))
            lines.append(f"   Modules: {modules_str}")
        else:
            lines.append(f"   Modules: Unknown/Unmapped")
        
        # Detailed file usage (limit to top 5 files for readability)
        if usage_info.usage_files:
            lines.append("   Files:")
            sorted_files = sorted(usage_info.usage_files.items(), 
                                key=lambda x: len(x[1]), reverse=True)
            
            for i, (file_path, line_numbers) in enumerate(sorted_files[:5]):
                usage_count = len(line_numbers)
                # Truncate long file paths
                display_path = file_path if len(file_path) <= 60 else "..." + file_path[-57:]
                lines.append(f"     • {display_path} ({usage_count} uses)")
            
            if len(sorted_files) > 5:
                lines.append(f"     ... and {len(sorted_files) - 5} more files")
        
        return lines
    
    def _get_proposed_destination(self, usage_info: UsageInfo) -> str:
        """
        Get the proposed destination description for a constant.
        
        Args:
            usage_info: UsageInfo object
            
        Returns:
            Human-readable destination description
        """
        if usage_info.category == UsageCategory.UNUSED:
            return "Consider removing (unused)"
        elif usage_info.category == UsageCategory.AMBIGUOUS:
            return "Manual review required"
        elif usage_info.category == UsageCategory.SHARED:
            return "MDL_export_const.h (shared across modules)"
        elif usage_info.category == UsageCategory.PRIVATE:
            if usage_info.modules_using:
                module = next(iter(usage_info.modules_using))
                return f"{module}/MDL_const.h (module-private)"
            else:
                return "MDL_const.h (module-private, module TBD)"
        else:
            return "Unknown"
    
    def generate_summary_statistics(self, usage_infos: List[UsageInfo], 
                                  constants_file: str, project_root: str) -> Dict[str, Any]:
        """
        Generate summary statistics for the analysis.
        
        Args:
            usage_infos: List of UsageInfo objects
            constants_file: Path to the constants file
            project_root: Project root directory
            
        Returns:
            Dictionary with summary statistics
        """
        from datetime import datetime
        
        # Count constants by category
        category_counts = {}
        for category in UsageCategory:
            category_counts[category.value] = sum(1 for ui in usage_infos if ui.category == category)
        
        # Calculate additional statistics
        total_files_analyzed = len(set(
            file_path 
            for usage_info in usage_infos 
            for file_path in usage_info.usage_files.keys()
        ))
        
        total_modules = len(set(
            module
            for usage_info in usage_infos
            for module in usage_info.modules_using
        ))
        
        # Find most used constants
        most_used = sorted(usage_infos, 
                          key=lambda ui: sum(len(lines) for lines in ui.usage_files.values()),
                          reverse=True)[:5]
        
        return {
            "total_constants": len(usage_infos),
            "constants_file": constants_file,
            "project_root": project_root,
            "timestamp": datetime.now().isoformat(),
            "category_counts": category_counts,
            "total_files_analyzed": total_files_analyzed,
            "total_modules_detected": total_modules,
            "most_used_constants": [
                {
                    "name": ui.constant.name,
                    "usage_count": sum(len(lines) for lines in ui.usage_files.values()),
                    "file_count": len(ui.usage_files)
                }
                for ui in most_used
            ]
        }
    
    def save_report_to_file(self, report_content: str, output_path: str) -> None:
        """
        Save the generated report to a file.
        
        Args:
            report_content: The report content to save
            output_path: Path where to save the report
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"Report saved to: {output_path}")
        except Exception as e:
            print(f"Error saving report to {output_path}: {e}")
    
    def generate_csv_summary(self, usage_infos: List[UsageInfo]) -> str:
        """
        Generate a CSV summary for spreadsheet analysis.
        
        Args:
            usage_infos: List of UsageInfo objects
            
        Returns:
            CSV formatted string
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Constant Name', 'Type', 'Value', 'Line Number', 'Category',
            'Target File Type', 'Modules Using', 'Total Files', 'Total Usages',
            'Proposed Destination', 'Requires Manual Review'
        ])
        
        # Write data rows
        for usage_info in usage_infos:
            writer.writerow([
                usage_info.constant.name,
                usage_info.constant.type,
                usage_info.constant.value,
                usage_info.constant.line_number,
                usage_info.category.value,
                usage_info.target_file_type,
                '; '.join(sorted(usage_info.modules_using)) if usage_info.modules_using else '',
                len(usage_info.usage_files),
                sum(len(lines) for lines in usage_info.usage_files.values()),
                self._get_proposed_destination(usage_info),
                'Yes' if usage_info.category == UsageCategory.AMBIGUOUS else 'No'
            ])
        
        return output.getvalue()
    
    def generate_markdown_report(self, usage_infos: List[UsageInfo], analysis_summary: Dict[str, Any]) -> str:
        """
        Generate a Markdown format report for documentation.
        
        Args:
            usage_infos: List of UsageInfo objects
            analysis_summary: Summary statistics
            
        Returns:
            Markdown formatted report string
        """
        lines = []
        
        # Header
        lines.append("# C++ Constants Refactoring Analysis Report")
        lines.append("")
        
        # Summary section
        lines.append("## Analysis Summary")
        lines.append("")
        lines.append(f"- **Total constants analyzed:** {analysis_summary.get('total_constants', 0)}")
        lines.append(f"- **Constants file:** `{analysis_summary.get('constants_file', 'N/A')}`")
        lines.append(f"- **Project root:** `{analysis_summary.get('project_root', 'N/A')}`")
        lines.append(f"- **Analysis timestamp:** {analysis_summary.get('timestamp', 'N/A')}")
        lines.append("")
        
        # Categorization summary
        lines.append("## Categorization Summary")
        lines.append("")
        category_counts = analysis_summary.get('category_counts', {})
        for category, count in category_counts.items():
            lines.append(f"- **{category.upper()}:** {count}")
        lines.append("")
        
        # Highlight ambiguous cases
        ambiguous_constants = [ui for ui in usage_infos if ui.category == UsageCategory.AMBIGUOUS]
        if ambiguous_constants:
            lines.append("## ⚠️ Constants Requiring Manual Review")
            lines.append("")
            for usage_info in ambiguous_constants:
                lines.append(f"### `{usage_info.constant.name}`")
                lines.append(f"- **Reason:** Ambiguous usage pattern")
                lines.append(f"- **Files:** {len(usage_info.usage_files)}")
                lines.append(f"- **Modules:** {', '.join(usage_info.modules_using) if usage_info.modules_using else 'Unknown'}")
                lines.append("")
        
        # Detailed analysis by category
        categories = [UsageCategory.SHARED, UsageCategory.PRIVATE, UsageCategory.UNUSED, UsageCategory.AMBIGUOUS]
        
        for category in categories:
            category_constants = [ui for ui in usage_infos if ui.category == category]
            if not category_constants:
                continue
                
            lines.append(f"## {category.value.title()} Constants ({len(category_constants)})")
            lines.append("")
            
            for usage_info in category_constants:
                lines.extend(self._format_constant_details_markdown(usage_info))
                lines.append("")
        
        # Footer with recommendations
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. Review constants marked as 'AMBIGUOUS' and resolve manually")
        lines.append("2. For PRIVATE constants, they will be placed in module-specific `MDL_const.h` files")
        lines.append("3. For SHARED constants, they will be placed in `MDL_export_const.h` files")
        lines.append("4. Run the tool in direct mode to apply the refactoring")
        lines.append("")
        
        return "\n".join(lines)
    
    def _format_constant_details_markdown(self, usage_info: UsageInfo) -> List[str]:
        """
        Format detailed information for a single constant in Markdown.
        
        Args:
            usage_info: UsageInfo object to format
            
        Returns:
            List of formatted lines
        """
        lines = []
        constant = usage_info.constant
        
        # Constant header
        lines.append(f"### `{constant.name}`")
        lines.append("")
        lines.append(f"- **Type:** `{constant.type}`")
        lines.append(f"- **Value:** `{constant.value}`")
        lines.append(f"- **Line:** {constant.line_number}")
        
        # Comments if available
        if constant.comments:
            lines.append(f"- **Comments:** {'; '.join(constant.comments)}")
        
        # Proposed destination
        destination = self._get_proposed_destination(usage_info)
        lines.append(f"- **Proposed destination:** {destination}")
        
        # Usage statistics
        total_files = len(usage_info.usage_files)
        total_usages = sum(len(line_nums) for line_nums in usage_info.usage_files.values())
        lines.append(f"- **Usage:** {total_usages} occurrences in {total_files} files")
        
        # Modules using this constant
        if usage_info.modules_using:
            modules_str = ', '.join(sorted(usage_info.modules_using))
            lines.append(f"- **Modules:** {modules_str}")
        else:
            lines.append(f"- **Modules:** Unknown/Unmapped")
        
        # Detailed file usage (limit to top 5 files for readability)
        if usage_info.usage_files:
            lines.append("- **Files:**")
            sorted_files = sorted(usage_info.usage_files.items(), 
                                key=lambda x: len(x[1]), reverse=True)
            
            for i, (file_path, line_numbers) in enumerate(sorted_files[:5]):
                usage_count = len(line_numbers)
                lines.append(f"  - `{file_path}` ({usage_count} uses)")
            
            if len(sorted_files) > 5:
                lines.append(f"  - ... and {len(sorted_files) - 5} more files")
        
        return lines
    
    def get_file_extension(self) -> str:
        """
        Get the appropriate file extension for the current output format.
        
        Returns:
            File extension string (including the dot)
        """
        extensions = {
            'json': '.json',
            'text': '.txt',
            'markdown': '.md',
            'csv': '.csv'
        }
        return extensions.get(self.output_format, '.txt')
    
    def get_default_filename(self, constants_file: str) -> str:
        """
        Generate a default filename for the report based on the constants file.
        
        Args:
            constants_file: Path to the constants file being analyzed
            
        Returns:
            Default filename for the report
        """
        from datetime import datetime
        
        # Extract base name from constants file
        base_name = Path(constants_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self.get_file_extension()
        
        return f"{base_name}_analysis_{timestamp}{extension}"


class ExecutionMode:
    """Base class for execution modes."""
    
    def __init__(self, project_root: str):
        """
        Initialize execution mode.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
    
    def prepare_environment(self) -> str:
        """
        Prepare the execution environment.
        
        Returns:
            Path to the working directory
        """
        raise NotImplementedError("Subclasses must implement prepare_environment")
    
    def cleanup(self):
        """Clean up resources after execution."""
        pass


class SandboxExecutionMode(ExecutionMode):
    """Sandbox execution mode for safe testing without modifying the original codebase."""
    
    def __init__(self, project_root: str, sandbox_dir: Optional[str] = None, logger: Optional[Logger] = None):
        """
        Initialize sandbox execution mode.
        
        Args:
            project_root: Root directory of the project
            sandbox_dir: Custom sandbox directory path (optional)
            logger: Logger instance for error reporting
        """
        super().__init__(project_root)
        self.sandbox_dir = None
        self.custom_sandbox_dir = sandbox_dir
        self.logger = logger or Logger("SandboxExecutionMode")
        self.error_handler = ErrorHandler(self.logger)
        
    def prepare_environment(self) -> str:
        """
        Create sandbox directory with complete project structure replication.
        
        Returns:
            Path to the sandbox directory
        """
        # Create timestamped sandbox directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.custom_sandbox_dir:
            base_sandbox_name = Path(self.custom_sandbox_dir).name
            self.sandbox_dir = self.project_root / f"{base_sandbox_name}_{timestamp}"
        else:
            self.sandbox_dir = self.project_root / f"constants_refactor_sandbox_{timestamp}"
        
        # Handle existing sandbox directories
        if self.sandbox_dir.exists():
            self.logger.warning(f"Sandbox directory already exists: {self.sandbox_dir}")
            # Create new timestamped version
            counter = 1
            while self.sandbox_dir.exists():
                if self.custom_sandbox_dir:
                    base_sandbox_name = Path(self.custom_sandbox_dir).name
                    self.sandbox_dir = self.project_root / f"{base_sandbox_name}_{timestamp}_{counter}"
                else:
                    self.sandbox_dir = self.project_root / f"constants_refactor_sandbox_{timestamp}_{counter}"
                counter += 1
        
        self.logger.info(f"Creating sandbox environment: {self.sandbox_dir}")
        
        # Create sandbox directory
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Replicate project structure
        self._replicate_project_structure()
        
        self.logger.info(f"Sandbox environment ready: {self.sandbox_dir}")
        return str(self.sandbox_dir)
    
    def _replicate_project_structure(self):
        """
        Create complete project structure replication in sandbox environment.
        """
        # Define directories to replicate
        important_dirs = [
            "src",
            "include", 
            "lib",
            "libs",
            "modules",
            "components",
            "CMakeLists.txt"  # Will be handled as file
        ]
        
        # Define file patterns to copy
        important_file_patterns = [
            "*.h", "*.hpp", "*.hxx",
            "*.cpp", "*.cc", "*.cxx", "*.c",
            "CMakeLists.txt", "*.cmake",
            "*.json", "*.xml", "*.yaml", "*.yml"
        ]
        
        self.logger.info("Replicating project structure...")
        
        # Copy directory structure
        for item in self.project_root.iterdir():
            if item.is_dir() and not self._should_exclude_directory(item.name):
                self._copy_directory_structure(item, self.sandbox_dir / item.name)
        
        # Copy important files from root
        for pattern in important_file_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    target_path = self.sandbox_dir / file_path.name
                    try:
                        shutil.copy2(file_path, target_path)
                        self.logger.debug(f"  Copied: {file_path.name}")
                    except Exception as e:
                        self.logger.warning(f"  Failed to copy {file_path}: {e}")
        
        self.logger.info("Project structure replication complete")
    
    def _copy_directory_structure(self, source_dir: Path, target_dir: Path):
        """
        Recursively copy directory structure with selective file copying.
        
        Args:
            source_dir: Source directory to copy from
            target_dir: Target directory to copy to
        """
        if self._should_exclude_directory(source_dir.name):
            return
        
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file extensions to copy
        source_extensions = {'.h', '.hpp', '.hxx', '.cpp', '.cc', '.cxx', '.c'}
        build_files = {'CMakeLists.txt', '.cmake'}
        
        try:
            for item in source_dir.iterdir():
                target_item = target_dir / item.name
                
                if item.is_dir():
                    # Recursively copy subdirectories
                    self._copy_directory_structure(item, target_item)
                elif item.is_file():
                    # Copy source files and build files
                    if (item.suffix.lower() in source_extensions or 
                        item.name in build_files or
                        item.name.endswith('.cmake')):
                        try:
                            shutil.copy2(item, target_item)
                        except Exception as e:
                            self.logger.warning(f"    Failed to copy {item}: {e}")
                            
        except PermissionError as e:
            self.logger.warning(f"  Permission denied accessing {source_dir}: {e}")
        except Exception as e:
            self.logger.warning(f"  Error copying directory {source_dir}: {e}")
    
    def _should_exclude_directory(self, dir_name: str) -> bool:
        """
        Check if a directory should be excluded from sandbox replication.
        
        Args:
            dir_name: Name of the directory
            
        Returns:
            True if directory should be excluded
        """
        exclude_patterns = {
            'build', 'builds', 'cmake-build-debug', 'cmake-build-release',
            '.git', '.svn', '.hg',
            'node_modules', '__pycache__', '.pytest_cache',
            'third_party', 'external', 'vendor',
            'temp', 'tmp', 'temporary',
            '.vscode', '.idea', '.vs',
            'constants_refactor_sandbox'  # Exclude existing sandbox dirs
        }
        
        dir_name_lower = dir_name.lower()
        
        # Check exact matches
        if dir_name_lower in exclude_patterns:
            return True
        
        # Check if it starts with excluded patterns
        for pattern in exclude_patterns:
            if dir_name_lower.startswith(pattern):
                return True
        
        return False
    
    def cleanup(self):
        """Clean up sandbox resources."""
        # Note: We don't automatically delete sandbox directories
        # as users might want to inspect the results
        if self.sandbox_dir:
            self.logger.info(f"Sandbox directory preserved for inspection: {self.sandbox_dir}")


class DirectExecutionMode(ExecutionMode):
    """Direct execution mode that modifies the original codebase with safety checks."""
    
    def __init__(self, project_root: str, logger: Optional[Logger] = None):
        """
        Initialize direct execution mode.
        
        Args:
            project_root: Root directory of the project
            logger: Logger instance for error reporting
        """
        super().__init__(project_root)
        self.backup_files = []
        self.confirmed = False
        self.logger = logger or Logger("DirectExecutionMode")
        self.error_handler = ErrorHandler(self.logger)
    
    def prepare_environment(self) -> str:
        """
        Prepare direct modification environment with safety checks.
        
        Returns:
            Path to the project root (working directory)
        """
        if not self.confirmed:
            self._request_confirmation()
        
        self.logger.info("Direct modification mode: Working directly on codebase")
        self.logger.info("Safety features enabled: atomic file operations, backup creation")
        
        return str(self.project_root)
    
    def _request_confirmation(self):
        """Request user confirmation before making direct changes."""
        print("\n" + "="*60)
        print("WARNING: DIRECT MODIFICATION MODE")
        print("="*60)
        print("This mode will directly modify your codebase.")
        print("The following safety measures are in place:")
        print("- Atomic file operations to prevent partial updates")
        print("- Backup files will be created before modifications")
        print("- Changes can be reverted if needed")
        print("\nProject root:", self.project_root)
        print("="*60)
        
        while True:
            response = input("\nDo you want to proceed with direct modifications? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                self.confirmed = True
                self.logger.info("User confirmed direct modifications")
                break
            elif response in ['no', 'n']:
                self.logger.info("Operation cancelled by user")
                sys.exit(0)
            else:
                print("Please enter 'yes' or 'no'")
    
    def create_backup(self, file_path: str) -> str:
        """
        Create backup of a file before modification.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path_obj.with_suffix(f"{file_path_obj.suffix}.backup_{timestamp}")
        
        try:
            shutil.copy2(file_path, backup_path)
            self.backup_files.append(str(backup_path))
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")
            return ""
    
    def write_file_atomically(self, file_path: str, content: str) -> bool:
        """
        Write file content atomically to prevent partial updates.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        # Create backup before modification
        self.create_backup(file_path)
        
        try:
            file_path_obj = Path(file_path)
            
            # Create temporary file in the same directory
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                dir=file_path_obj.parent,
                delete=False,
                suffix='.tmp'
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Atomically move the temporary file to the target location
            shutil.move(temp_file_path, file_path)
            self.logger.info(f"Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing file atomically {file_path}: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
            return False
    
    def cleanup(self):
        """Clean up direct execution resources."""
        if self.backup_files:
            self.logger.info(f"\nBackup files created during execution:")
            for backup_file in self.backup_files:
                self.logger.info(f"  {backup_file}")
            self.logger.info("These backups can be used to revert changes if needed.")


class FileGenerator:
    """Generator for creating module-specific constant files."""
    
    def __init__(self, execution_mode: ExecutionMode, logger: Optional[Logger] = None):
        """
        Initialize the file generator with an execution mode.
        
        Args:
            execution_mode: Execution mode instance (sandbox or direct)
            logger: Logger instance for error reporting
        """
        self.execution_mode = execution_mode
        self.working_dir = None
        self.logger = logger or Logger("FileGenerator")
        self.error_handler = ErrorHandler(self.logger)
    
    def generate_module_const_file(self, module: str, constants: List[Constant], target_dir: Optional[str] = None) -> str:
        """
        Generate MDL_const.h file for module-private constants.
        
        Args:
            module: Module name
            constants: List of constants to include
            target_dir: Target directory for the file (optional)
            
        Returns:
            Path to the generated file
        """
        filename = f"{module}_const.h"
        return self._generate_const_file(module, constants, filename, "const", target_dir)
    
    def generate_export_const_file(self, module: str, constants: List[Constant], target_dir: Optional[str] = None) -> str:
        """
        Generate MDL_export_const.h file for shared constants.
        
        Args:
            module: Module name
            constants: List of constants to include
            target_dir: Target directory for the file (optional)
            
        Returns:
            Path to the generated file
        """
        filename = f"{module}_export_const.h"
        return self._generate_const_file(module, constants, filename, "export_const", target_dir)
    
    def _generate_const_file(self, module: str, constants: List[Constant], filename: str, file_type: str, target_dir: Optional[str] = None) -> str:
        """
        Generate a constants file with proper formatting and header guards.
        
        Args:
            module: Module name
            constants: List of constants to include
            filename: Name of the file to generate
            file_type: Type of file ('const' or 'export_const')
            target_dir: Target directory for the file (optional)
            
        Returns:
            Path to the generated file
        """
        # Prepare execution environment if not already done
        if self.working_dir is None:
            self.working_dir = self.execution_mode.prepare_environment()
        
        # Determine target directory
        if target_dir:
            base_dir = Path(target_dir)
        else:
            # Default to module directory structure
            base_dir = Path("src") / module
        
        # Construct file path based on execution mode
        file_path = Path(self.working_dir) / base_dir / filename
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate file content
        content = self._create_file_content(module, constants, file_type)
        
        # Write the file using execution mode's atomic write method
        if self._write_file_with_execution_mode(str(file_path), content):
            print(f"Generated {file_type} file: {file_path}")
            return str(file_path)
        else:
            raise RuntimeError(f"Failed to write {file_type} file: {file_path}")
    
    def _write_file_with_execution_mode(self, file_path: str, content: str) -> bool:
        """
        Write file using the appropriate method based on execution mode.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(self.execution_mode, DirectExecutionMode):
            return self.execution_mode.write_file_atomically(file_path, content)
        else:
            # For sandbox mode, use the standard atomic write
            return self.write_file_atomically(file_path, content)
    
    def _create_file_content(self, module: str, constants: List[Constant], file_type: str) -> str:
        """
        Create the content for a constants file.
        
        Args:
            module: Module name
            constants: List of constants to include
            file_type: Type of file ('const' or 'export_const')
            
        Returns:
            Complete file content as string
        """
        lines = []
        
        # File header comment
        lines.append(f"// {module}_{file_type}.h")
        lines.append(f"// Generated constants file for {module} module")
        lines.append(f"// File type: {'Module-private constants' if file_type == 'const' else 'Shared/exported constants'}")
        lines.append("// Auto-generated by constants_refactor.py")
        lines.append("")
        
        # Header guard
        header_guard = self.create_header_guards(module, file_type)
        lines.append(f"#ifndef {header_guard}")
        lines.append(f"#define {header_guard}")
        lines.append("")
        
        # Include necessary headers if needed
        if any(c.type in ['const', 'constexpr'] for c in constants):
            lines.append("// Standard includes")
            lines.append("#include <cstdint>")
            lines.append("")
        
        # Namespace opening (if applicable)
        namespace = self._get_module_namespace(module)
        if namespace:
            lines.append(f"namespace {namespace} {{")
            lines.append("")
        
        # Group constants by type
        defines = [c for c in constants if c.type == 'define']
        const_vars = [c for c in constants if c.type in ['const', 'constexpr']]
        
        # Add #define constants
        if defines:
            lines.append("// Preprocessor definitions")
            for constant in defines:
                lines.extend(self._format_constant(constant))
            lines.append("")
        
        # Add const/constexpr constants
        if const_vars:
            lines.append("// Constant variables")
            for constant in const_vars:
                lines.extend(self._format_constant(constant))
            lines.append("")
        
        # Namespace closing
        if namespace:
            lines.append(f"}} // namespace {namespace}")
            lines.append("")
        
        # Header guard closing
        lines.append(f"#endif // {header_guard}")
        lines.append("")
        
        return '\n'.join(lines)
    
    def create_header_guards(self, module_name: str, file_type: str) -> str:
        """
        Create header guard macro name.
        
        Args:
            module_name: Name of the module
            file_type: Type of file ('const' or 'export_const')
            
        Returns:
            Header guard macro name
        """
        # Convert to uppercase and replace special characters
        guard_base = f"{module_name}_{file_type}_h".upper()
        guard_base = re.sub(r'[^A-Z0-9_]', '_', guard_base)
        
        # Add project prefix if available
        prefix = "PROJECT_"  # Could be configurable
        return f"{prefix}{guard_base}"
    
    def _get_module_namespace(self, module: str) -> Optional[str]:
        """
        Get the namespace for a module.
        
        Args:
            module: Module name
            
        Returns:
            Namespace name or None if no namespace should be used
        """
        # For now, use the module name as namespace
        # This could be made configurable
        if module and module.isalnum():
            return module.lower()
        return None
    
    def append_to_existing_file(self, file_path: str, constants: List[Constant]) -> bool:
        """
        Append constants to an existing module file without overwriting.
        
        Args:
            file_path: Path to the existing file
            constants: List of constants to append
            
        Returns:
            True if successful, False otherwise
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            print(f"File does not exist: {file_path}")
            return False
        
        # Create backup before modifying
        if not self.sandbox_mode:
            backup_path = self._create_backup(file_path)
            if not backup_path:
                print(f"Failed to create backup for {file_path}")
                return False
            print(f"Created backup: {backup_path}")
        
        try:
            # Read existing file content
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Filter out duplicate constants
            unique_constants = self._filter_duplicate_constants(constants, existing_content)
            
            if not unique_constants:
                print(f"No new constants to add to {file_path}")
                return True
            
            # Find insertion point (before closing header guard)
            modified_content = self._insert_constants_into_existing_file(existing_content, unique_constants)
            
            # Write the modified content atomically
            if self.write_file_atomically(file_path, modified_content):
                print(f"Appended {len(unique_constants)} constants to {file_path}")
                return True
            else:
                print(f"Failed to write modified content to {file_path}")
                return False
            
        except Exception as e:
            print(f"Error appending to file {file_path}: {e}")
            return False
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of the file before modification.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file or None if failed
        """
        try:
            from datetime import datetime
            import shutil
            
            file_path_obj = Path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path_obj.with_suffix(f".backup_{timestamp}{file_path_obj.suffix}")
            
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
            
        except Exception as e:
            print(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _filter_duplicate_constants(self, constants: List[Constant], existing_content: str) -> List[Constant]:
        """
        Filter out constants that already exist in the file.
        
        Args:
            constants: List of constants to check
            existing_content: Content of the existing file
            
        Returns:
            List of constants that don't already exist in the file
        """
        unique_constants = []
        
        for constant in constants:
            if not self._constant_exists_in_content(constant, existing_content):
                unique_constants.append(constant)
            else:
                print(f"Skipping duplicate constant: {constant.name}")
        
        return unique_constants
    
    def _constant_exists_in_content(self, constant: Constant, content: str) -> bool:
        """
        Check if a constant already exists in the file content.
        
        Args:
            constant: Constant to check for
            content: File content to search in
            
        Returns:
            True if the constant already exists
        """
        # Create patterns to match different constant declarations
        patterns = []
        
        if constant.type == 'define':
            # Match #define patterns
            patterns.append(rf'#define\s+{re.escape(constant.name)}\b')
        elif constant.type in ['const', 'constexpr']:
            # Match const/constexpr variable declarations
            patterns.extend([
                rf'\bconst\s+.*\s+{re.escape(constant.name)}\s*[=;]',
                rf'\bconstexpr\s+.*\s+{re.escape(constant.name)}\s*[=;]',
                rf'\bconst\s+auto\s+{re.escape(constant.name)}\s*[=;]',
                rf'\bconstexpr\s+auto\s+{re.escape(constant.name)}\s*[=;]'
            ])
        
        # Check if any pattern matches
        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def _insert_constants_into_existing_file(self, existing_content: str, constants: List[Constant]) -> str:
        """
        Insert constants into existing file content at the appropriate location.
        
        Args:
            existing_content: Original file content
            constants: Constants to insert
            
        Returns:
            Modified file content
        """
        lines = existing_content.split('\n')
        
        # Find the insertion point (before closing header guard or namespace)
        insertion_index = self._find_insertion_point(lines)
        
        # Format the constants to insert
        constants_lines = []
        constants_lines.append("// Additional constants")
        for constant in constants:
            constants_lines.extend(self._format_constant(constant))
        
        # Insert the constants
        lines[insertion_index:insertion_index] = constants_lines
        
        return '\n'.join(lines)
    
    def _find_insertion_point(self, lines: List[str]) -> int:
        """
        Find the best insertion point for new constants in existing file.
        
        Args:
            lines: List of lines from the existing file
            
        Returns:
            Index where new constants should be inserted
        """
        # Look for common insertion points in reverse order
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            
            # Before closing header guard
            if line.startswith('#endif'):
                # Insert before the #endif, with some spacing
                return i
            
            # Before closing namespace
            if line.startswith('} // namespace') or line == '}':
                return i
        
        # If no specific insertion point found, insert near the end
        # but leave some space for the header guard
        return max(0, len(lines) - 2)
    
    def _format_constant(self, constant: Constant) -> List[str]:
        """
        Format a constant for output in the generated file.
        
        Args:
            constant: Constant to format
            
        Returns:
            List of lines representing the formatted constant
        """
        lines = []
        
        # Add comments if available
        if constant.comments:
            for comment in constant.comments:
                if not comment.startswith('//') and not comment.startswith('/*'):
                    lines.append(f"// {comment}")
                else:
                    lines.append(comment)
        
        # Format the constant declaration
        if constant.type == 'define':
            if constant.value:
                lines.append(f"#define {constant.name} {constant.value}")
            else:
                lines.append(f"#define {constant.name}")
        elif constant.type == 'const':
            if constant.value:
                lines.append(f"const auto {constant.name} = {constant.value};")
            else:
                lines.append(f"extern const auto {constant.name};")
        elif constant.type == 'constexpr':
            if constant.value:
                lines.append(f"constexpr auto {constant.name} = {constant.value};")
            else:
                lines.append(f"extern constexpr auto {constant.name};")
        
        # Add blank line after each constant
        lines.append("")
        
        return lines
    
    def write_file_atomically(self, file_path: str, content: str) -> bool:
        """
        Write file content atomically to prevent partial updates.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import tempfile
            import shutil
            
            file_path_obj = Path(file_path)
            
            # Create temporary file in the same directory
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                dir=file_path_obj.parent,
                delete=False,
                suffix='.tmp'
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Atomically move the temporary file to the target location
            shutil.move(temp_file_path, file_path)
            return True
            
        except Exception as e:
            print(f"Error writing file atomically {file_path}: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
            return False
    
    def get_existing_constants(self, file_path: str) -> Set[str]:
        """
        Get a set of constant names that already exist in a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Set of constant names found in the file
        """
        existing_constants = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find #define constants
            define_pattern = r'#define\s+([A-Za-z_][A-Za-z0-9_]*)'
            for match in re.finditer(define_pattern, content):
                existing_constants.add(match.group(1))
            
            # Find const/constexpr constants
            const_patterns = [
                r'\bconst\s+(?:auto\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[=;]',
                r'\bconstexpr\s+(?:auto\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[=;]'
            ]
            
            for pattern in const_patterns:
                for match in re.finditer(pattern, content):
                    existing_constants.add(match.group(1))
                    
        except Exception as e:
            print(f"Warning: Failed to read existing constants from {file_path}: {e}")
        
        return existing_constants
    
    def cleanup(self):
        """Clean up file generator resources."""
        if self.execution_mode:
            self.execution_mode.cleanup()





class ConfigurationManager:
    """Manager for handling configuration from command line arguments and config files."""
    
    def __init__(self, args: argparse.Namespace, logger: Optional[Logger] = None):
        """
        Initialize configuration manager.
        
        Args:
            args: Parsed command line arguments
            logger: Logger instance for error reporting
        """
        self.args = args
        self.logger = logger or Logger("ConfigurationManager")
        self.error_handler = ErrorHandler(self.logger)
        self.config_data = {}
        
        # Load configuration file if specified
        if hasattr(args, 'config') and args.config:
            self.load_config_file(args.config)
    
    def load_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration file is invalid
        """
        try:
            self.logger.info(f"Loading configuration from {config_path}")
            
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            self.logger.info(f"Successfully loaded configuration with {len(self.config_data)} settings")
            return self.config_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file {config_path}", e)
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}") from e
        except Exception as e:
            self.logger.error(f"Failed to load configuration file {config_path}", e)
            raise ConfigurationError(f"Failed to load configuration: {e}") from e
    
    def get_constants_file_path(self) -> str:
        """Get the constants file path from args or config."""
        if self.args.constants_file:
            return self.args.constants_file
        elif 'constants_file' in self.config_data:
            return self.config_data['constants_file']
        else:
            raise ConfigurationError("Constants file path not specified in arguments or configuration")
    
    def get_project_root(self) -> str:
        """Get the project root path from args or config."""
        if self.args.project_root:
            return self.args.project_root
        elif 'project_root' in self.config_data:
            return self.config_data['project_root']
        else:
            return "."  # Default to current directory
    
    def get_source_directories(self) -> List[str]:
        """Get source directories from args or config."""
        if hasattr(self.args, 'source_dirs') and self.args.source_dirs:
            return self.args.source_dirs
        elif 'source_directories' in self.config_data:
            return self.config_data['source_directories']
        else:
            return ["src/", "include/"]  # Default directories
    
    def get_exclude_patterns(self) -> List[str]:
        """Get exclude patterns from args or config."""
        patterns = []
        
        if hasattr(self.args, 'exclude_dirs') and self.args.exclude_dirs:
            patterns.extend(self.args.exclude_dirs.split(','))
        
        if 'exclude_patterns' in self.config_data:
            patterns.extend(self.config_data['exclude_patterns'])
        
        # Add default exclude patterns
        default_excludes = [
            "build/*", "cmake-build-*/*", ".git/*", "__pycache__/*",
            "third_party/*", "external/*", "vendor/*"
        ]
        patterns.extend(default_excludes)
        
        return list(set(patterns))  # Remove duplicates
    
    def get_execution_mode(self) -> str:
        """Get execution mode from args or config."""
        if hasattr(self.args, 'mode') and self.args.mode:
            return self.args.mode
        elif self.args.sandbox:
            return "sandbox"
        elif 'execution_mode' in self.config_data:
            return self.config_data['execution_mode']
        else:
            return "sandbox"  # Default to safe mode
    
    def get_build_directory(self) -> str:
        """Get build directory from args or config."""
        if hasattr(self.args, 'build_dir') and self.args.build_dir:
            return self.args.build_dir
        elif 'build_directory' in self.config_data:
            return self.config_data['build_directory']
        else:
            return "build"  # Default build directory
    
    def get_output_format(self) -> str:
        """Get output format from args or config."""
        if hasattr(self.args, 'output_format') and self.args.output_format:
            return self.args.output_format
        elif 'output_format' in self.config_data:
            return self.config_data['output_format']
        else:
            return "text"  # Default format
    
    def get_module_mapping(self) -> Optional[Dict[str, List[str]]]:
        """Get module mapping from config."""
        return self.config_data.get('module_mapping')
    
    def validate_configuration(self) -> bool:
        """
        Validate the complete configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Check required settings
            constants_file = self.get_constants_file_path()
            if not Path(constants_file).exists():
                raise ConfigurationError(f"Constants file does not exist: {constants_file}")
            
            project_root = self.get_project_root()
            if not Path(project_root).exists():
                raise ConfigurationError(f"Project root does not exist: {project_root}")
            
            # Validate source directories
            source_dirs = self.get_source_directories()
            project_path = Path(project_root)
            
            existing_source_dirs = []
            for source_dir in source_dirs:
                source_path = project_path / source_dir
                if source_path.exists():
                    existing_source_dirs.append(source_dir)
                else:
                    self.logger.warning(f"Source directory does not exist: {source_dir}")
            
            if not existing_source_dirs:
                self.logger.warning("No source directories found - this may affect analysis quality")
            
            # Validate execution mode
            mode = self.get_execution_mode()
            if mode not in ['sandbox', 'direct']:
                raise ConfigurationError(f"Invalid execution mode: {mode}")
            
            # Validate output format
            output_format = self.get_output_format()
            if output_format not in ['json', 'text', 'markdown', 'csv']:
                raise ConfigurationError(f"Invalid output format: {output_format}")
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error("Configuration validation failed", e)
            raise ConfigurationError(f"Configuration validation failed: {e}") from e


def create_execution_mode(mode: str, project_root: str, sandbox_dir: Optional[str] = None, 
                         logger: Optional[Logger] = None) -> ExecutionMode:
    """
    Factory function to create the appropriate execution mode.
    
    Args:
        mode: Execution mode ('sandbox' or 'direct')
        project_root: Root directory of the project
        sandbox_dir: Custom sandbox directory path (optional, for sandbox mode)
        logger: Logger instance for error reporting
        
    Returns:
        ExecutionMode instance
    """
    if mode == "direct":
        return DirectExecutionMode(project_root, logger)
    else:  # Default to sandbox
        return SandboxExecutionMode(project_root, sandbox_dir, logger)


def print_usage_tips():
    """Print helpful usage tips and common workflows."""
    tips = """
USAGE TIPS AND COMMON WORKFLOWS:

🚀 GETTING STARTED:
   1. Start with sandbox mode to safely explore your constants:
      constants_refactor --constants-file src/constants.h --project-root .
   
   2. Review the generated report and sandbox directory structure
   
   3. If satisfied, run in direct mode:
      constants_refactor --constants-file src/constants.h --mode direct

📊 ANALYSIS WORKFLOWS:
   • Generate detailed JSON report for further processing:
     constants_refactor --constants-file src/constants.h --output-format json --output-file analysis.json
   
   • Focus on specific modules by excluding irrelevant directories:
     constants_refactor --constants-file src/constants.h --exclude-dirs "tests/,third_party/,build/"
   
   • Get quick overview with summary statistics:
     constants_refactor --constants-file src/constants.h --summary-only

🔧 TROUBLESHOOTING:
   • Enable verbose logging for detailed analysis:
     constants_refactor --constants-file src/constants.h --verbose --log-file debug.log
   
   • If CMake fails, the tool will fallback to directory-based analysis
   
   • Use --dry-run to see what would be changed without making modifications

⚠️  SAFETY RECOMMENDATIONS:
   • Always use sandbox mode first to review proposed changes
   • Ensure your code is under version control before using direct mode
   • Review ambiguous constants manually before applying changes
   • Test your code after refactoring to ensure functionality is preserved

📁 TYPICAL PROJECT STRUCTURE AFTER REFACTORING:
   src/
   ├── module1/
   │   ├── MDL_const.h          # Module-private constants
   │   └── MDL_export_const.h   # Constants shared by this module
   ├── module2/
   │   ├── MDL_const.h
   │   └── MDL_export_const.h
   └── common/
       └── constants.h          # Original file (can be removed after refactoring)

For more detailed documentation, run: constants_refactor --help
    """
    print(tips)


def validate_arguments(args) -> bool:
    """
    Validate command line arguments and provide helpful error messages.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if arguments are valid, False otherwise
    """
    errors = []
    
    # Check required arguments
    if not args.constants_file and not args.config:
        errors.append("Either --constants-file or --config must be specified")
    
    # Check file existence
    if args.constants_file:
        constants_path = Path(args.constants_file)
        if not constants_path.exists():
            errors.append(f"Constants file not found: {args.constants_file}")
        elif not constants_path.is_file():
            errors.append(f"Constants file path is not a file: {args.constants_file}")
    
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            errors.append(f"Configuration file not found: {args.config}")
        elif not config_path.is_file():
            errors.append(f"Configuration file path is not a file: {args.config}")
    
    # Check project root
    if args.project_root:
        project_path = Path(args.project_root)
        if not project_path.exists():
            errors.append(f"Project root directory not found: {args.project_root}")
        elif not project_path.is_dir():
            errors.append(f"Project root path is not a directory: {args.project_root}")
    
    # Check mutually exclusive options
    if args.verbose and args.quiet:
        errors.append("Cannot specify both --verbose and --quiet")
    
    if args.dry_run and args.mode == "direct":
        print("Note: --dry-run implies sandbox mode, ignoring --mode direct")
        args.mode = "sandbox"
    
    # Validate output file path
    if args.output_file:
        output_path = Path(args.output_file)
        try:
            # Check if parent directory exists and is writable
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Try to create/touch the file to check write permissions
            output_path.touch(exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot write to output file {args.output_file}: {e}")
    
    # Validate log file path
    if args.log_file:
        log_path = Path(args.log_file)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot write to log file {args.log_file}: {e}")
    
    # Print errors if any
    if errors:
        print("❌ Argument validation errors:")
        for error in errors:
            print(f"   • {error}")
        print("\nRun 'constants_refactor --help' for usage information")
        return False
    
    return True


def print_welcome_banner():
    """Print a welcome banner with tool information."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     C++ Constants Refactoring Tool v1.0.0                   ║
║                                                                              ║
║  Automatically analyze and refactor large C++ constants files based on      ║
║  usage patterns across modules in CMake-based projects.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def generate_documentation(output_file: Optional[str] = None) -> str:
    """
    Generate comprehensive documentation for the tool.
    
    Args:
        output_file: Optional file path to save documentation
        
    Returns:
        Documentation string
    """
    doc = """
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
    """.strip()
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(doc)
            print(f"✅ Documentation saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save documentation: {e}")
    
    return doc


def create_sample_config(output_path: str = "constants_refactor_config.json") -> bool:
    """
    Create a sample configuration file with documentation.
    
    Args:
        output_path: Path where to create the sample config file
        
    Returns:
        True if successful, False otherwise
    """
    sample_config = {
        "_comment": "C++ Constants Refactoring Tool Configuration",
        "_description": "This file contains configuration options for the constants refactoring tool",
        
        "constants_file": "src/common/constants.h",
        "project_root": ".",
        "build_directory": "build",
        
        "source_directories": [
            "src/",
            "include/",
            "lib/"
        ],
        
        "exclude_patterns": [
            "*_test.cpp",
            "*_test.h",
            "*/third_party/*",
            "*/build/*",
            "*/cmake-build-*/*",
            "*.pb.h",
            "*.pb.cc"
        ],
        
        "module_mapping": {
            "_comment": "Map module names to directory patterns or CMake targets",
            "networking": ["net/", "network/", "protocol/"],
            "ui": ["gui/", "widgets/", "ui/"],
            "database": ["db/", "database/", "storage/"],
            "core": ["core/", "common/", "base/"],
            "utils": ["utils/", "utilities/", "tools/"]
        },
        
        "analysis_options": {
            "min_usage_threshold": 1,
            "ignore_test_files": True,
            "case_sensitive": False,
            "include_unused_constants": False,
            "highlight_ambiguous": True
        },
        
        "output_settings": {
            "header_guard_prefix": "PROJECT_",
            "include_comments": True,
            "sort_constants": True,
            "add_generation_timestamp": True,
            "preserve_original_formatting": False
        },
        
        "execution_settings": {
            "mode": "sandbox",
            "sandbox_directory": None,
            "backup_original_files": True,
            "atomic_file_operations": True
        },
        
        "logging": {
            "level": "INFO",
            "file": None,
            "include_timestamps": True,
            "include_function_names": False
        }
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sample configuration file created: {output_path}")
        print("   Edit this file to customize the tool behavior for your project.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample configuration file: {e}")
        return False


def check_dependencies() -> List[str]:
    """
    Check for required dependencies and return list of missing ones.
    
    Returns:
        List of missing dependencies
    """
    missing = []
    
    # Check for pygccxml
    if not PYGCCXML_AVAILABLE:
        missing.append("pygccxml (install with: pip install pygccxml)")
    
    # Check for CastXML
    try:
        result = subprocess.run(['castxml', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            missing.append("CastXML (install from: https://github.com/CastXML/CastXML)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing.append("CastXML (install from: https://github.com/CastXML/CastXML)")
    
    # Check for CMake
    try:
        result = subprocess.run(['cmake', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            missing.append("CMake (install from: https://cmake.org/)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing.append("CMake (install from: https://cmake.org/)")
    
    # Check for ripgrep (optional but recommended)
    try:
        result = subprocess.run(['rg', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            # Not critical, just note it
            pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # ripgrep is optional, don't add to missing
        pass
    
    return missing


def main():
    """Main entry point for the constants refactoring tool."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle special utility commands first
    if args.create_config:
        create_sample_config(args.create_config)
        return
    
    if args.check_deps:
        print("🔍 Checking dependencies...")
        missing_deps = check_dependencies()
        if missing_deps:
            print("❌ Missing dependencies:")
            for dep in missing_deps:
                print(f"   • {dep}")
            sys.exit(1)
        else:
            print("✅ All required dependencies are available")
            return
    
    if args.tips:
        print_usage_tips()
        return
    
    if args.generate_docs is not None:
        doc = generate_documentation(args.generate_docs)
        if args.generate_docs is None:
            print(doc)
        return
    
    # Handle special cases
    if len(sys.argv) == 1:
        # No arguments provided, show help and tips
        parser.print_help()
        print("\n" + "="*80)
        print_usage_tips()
        return
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    # Print welcome banner unless in quiet mode
    if not args.quiet:
        print_welcome_banner()
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("⚠️  Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\nSome features may not work correctly without these dependencies.")
        
        # Ask user if they want to continue
        if not args.force:
            try:
                response = input("\nContinue anyway? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Exiting. Please install missing dependencies and try again.")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(130)
    
    # Determine log level
    if args.verbose:
        log_level = "DEBUG"
    elif args.quiet:
        log_level = "ERROR"
    else:
        log_level = args.log_level
    
    # Initialize logging
    logger = Logger("constants_refactor", log_level)
    error_handler = ErrorHandler(logger)
    
    # Add file logging if requested
    if args.log_file:
        logger.add_file_handler(args.log_file)
    
    # Enable profiling if requested
    if args.profile:
        import time
        start_time = time.time()
        logger.info("Performance profiling enabled")
    
    try:
        # Initialize configuration manager
        config_manager = ConfigurationManager(args, logger)
        
        # Validate configuration
        config_manager.validate_configuration()
        
        # Get configuration values
        constants_file = config_manager.get_constants_file_path()
        project_root = config_manager.get_project_root()
        mode = "sandbox" if args.dry_run else config_manager.get_execution_mode()
        
        # Log configuration summary
        if not args.quiet:
            logger.info("🔍 Analysis Configuration:")
            logger.info(f"   Constants file: {constants_file}")
            logger.info(f"   Project root: {project_root}")
            logger.info(f"   Execution mode: {mode.capitalize()}")
            logger.info(f"   Build directory: {args.build_dir}")
            logger.info(f"   Source directories: {', '.join(args.source_dirs)}")
            if args.exclude_dirs:
                logger.info(f"   Excluded directories: {args.exclude_dirs}")
            logger.info(f"   Output format: {args.output_format}")
            if args.output_file:
                logger.info(f"   Output file: {args.output_file}")
            logger.info(f"   Log level: {log_level}")
            if args.dry_run:
                logger.info("   🧪 DRY RUN MODE - No changes will be made")
        
        # Confirmation prompt for direct mode
        if mode == "direct" and not args.force and not args.dry_run:
            logger.warning("⚠️  DIRECT MODE will modify your codebase!")
            logger.warning("   Ensure you have backups or version control before proceeding.")
            try:
                response = input("\nProceed with direct modifications? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    logger.info("Operation cancelled by user.")
                    return
            except KeyboardInterrupt:
                logger.info("Operation cancelled by user.")
                return
        
        # Create execution mode
        sandbox_dir = args.sandbox_dir if hasattr(args, 'sandbox_dir') else None
        execution_mode = create_execution_mode(mode, project_root, sandbox_dir, logger)
        
        # Initialize file generator with execution mode
        file_generator = FileGenerator(execution_mode, logger)
        
        try:
            # TODO: Implement main pipeline in subsequent tasks
            logger.info("📋 Main pipeline implementation pending - comprehensive error handling complete")
            logger.info("🎯 Ready for pipeline integration in subsequent tasks")
            
            # Show configuration summary for user
            if not args.quiet:
                print("\n" + "="*60)
                print("📊 ANALYSIS READY")
                print("="*60)
                print(f"Tool is configured and ready to analyze: {constants_file}")
                print(f"Mode: {mode.upper()}")
                if mode == "sandbox":
                    print("✅ Safe mode - original files will not be modified")
                else:
                    print("⚠️  Direct mode - original files will be modified")
                print("\nNext steps:")
                print("1. Pipeline integration will be completed in subsequent tasks")
                print("2. Full analysis and refactoring functionality will be available")
                print("3. Run with --help to see all available options")
            
            # Show error summary
            error_summary = logger.get_error_summary()
            if error_summary['errors'] > 0 or error_summary['warnings'] > 0:
                logger.info(f"Setup completed with {error_summary['errors']} errors and {error_summary['warnings']} warnings")
            else:
                logger.info("✅ Setup completed successfully with no errors or warnings")
            
            # Show profiling information if enabled
            if args.profile:
                elapsed_time = time.time() - start_time
                logger.info(f"⏱️  Total execution time: {elapsed_time:.2f} seconds")
            
        finally:
            # Always cleanup resources
            try:
                file_generator.cleanup()
            except Exception as cleanup_error:
                logger.error("Error during cleanup", cleanup_error)
        
    except ConstantsRefactorError as e:
        logger.critical(f"Tool error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", e)
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="constants_refactor",
        description="""
C++ Constants Refactoring Tool

Analyzes a large C++ constants file and automatically categorizes constants based on 
their usage across modules in a CMake-based project. The tool identifies whether 
constants are module-private (used only within one module) or shared (used across 
multiple modules), then suggests appropriate file locations for refactoring.

The tool supports both safe sandbox testing and direct codebase modification modes.
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:

Basic Analysis (Sandbox Mode - Safe):
  %(prog)s --constants-file src/constants.h --project-root .
  
  This will analyze constants.h and create a sandbox directory with proposed 
  refactoring structure without modifying your original codebase.

Direct Modification (Advanced):
  %(prog)s --constants-file src/constants.h --project-root . --mode direct
  
  This will directly modify your codebase. Use with caution and ensure you have 
  backups or version control.

Using Configuration File:
  %(prog)s --config config.json
  
  Load settings from a JSON configuration file. See documentation for format.

Custom Build Directory:
  %(prog)s --constants-file src/constants.h --build-dir cmake-build-debug
  
  Specify a custom CMake build directory for compile commands generation.

Exclude Directories:
  %(prog)s --constants-file src/constants.h --exclude-dirs "build/,third_party/,tests/"
  
  Exclude specific directories from analysis to focus on relevant code.

Generate JSON Report:
  %(prog)s --constants-file src/constants.h --output-format json --output-file report.json
  
  Generate a machine-readable JSON report for further processing.

Verbose Analysis with Logging:
  %(prog)s --constants-file src/constants.h --verbose --log-file analysis.log
  
  Enable detailed logging for troubleshooting and analysis review.

WORKFLOW:

1. ANALYSIS PHASE:
   - Parses the constants file using CastXML and pygccxml
   - Generates CMake compile commands database for accurate module detection
   - Searches for constant usage across all source files
   - Categorizes constants as module-private or shared

2. CLASSIFICATION PHASE:
   - Module-private constants → MDL_const.h files
   - Shared constants → MDL_export_const.h files
   - Ambiguous cases are flagged for manual review

3. EXECUTION PHASE:
   - Sandbox mode: Creates proposed structure in separate directory
   - Direct mode: Modifies original codebase (with confirmation prompt)

REQUIREMENTS:

- Python 3.7+
- pygccxml: pip install pygccxml
- CastXML: Available in PATH or specify with --castxml-path
- CMake: For compile commands generation
- ripgrep (optional): For faster text search

CONFIGURATION FILE FORMAT:

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

For more information and detailed documentation, visit:
https://github.com/your-repo/cpp-constants-refactor
        """
    )
    
    # Input/Output Arguments
    input_group = parser.add_argument_group('Input/Output', 'Specify input files and output options')
    
    input_group.add_argument(
        "--constants-file",
        type=str,
        metavar="PATH",
        help="Path to the C++ constants file to analyze (e.g., src/constants.h)"
    )
    
    input_group.add_argument(
        "--project-root",
        type=str,
        default=".",
        metavar="PATH",
        help="Root directory of the C++ project (default: current directory)"
    )
    
    input_group.add_argument(
        "--config",
        type=str,
        metavar="FILE",
        help="Path to JSON configuration file (overrides command line options)"
    )
    
    # Build Configuration
    build_group = parser.add_argument_group('Build Configuration', 'CMake and build system options')
    
    build_group.add_argument(
        "--build-dir",
        type=str,
        default="build",
        metavar="PATH",
        help="CMake build directory for compile commands generation (default: build)"
    )
    
    build_group.add_argument(
        "--source-dirs",
        nargs="+",
        default=["src/", "include/"],
        metavar="DIR",
        help="Source directories to scan for constant usage (default: src/ include/)"
    )
    
    build_group.add_argument(
        "--exclude-dirs",
        type=str,
        metavar="PATTERNS",
        help="Comma-separated list of directories to exclude (e.g., 'build/,third_party/,tests/')"
    )
    
    build_group.add_argument(
        "--castxml-path",
        type=str,
        metavar="PATH",
        help="Path to CastXML executable (default: search in PATH)"
    )
    
    # Execution Mode
    mode_group = parser.add_argument_group('Execution Mode', 'Control how changes are applied')
    
    mode_group.add_argument(
        "--mode",
        choices=["sandbox", "direct"],
        default="sandbox",
        help="Execution mode: 'sandbox' creates test directory, 'direct' modifies codebase (default: sandbox)"
    )
    
    mode_group.add_argument(
        "--sandbox-dir",
        type=str,
        metavar="PATH",
        help="Custom sandbox directory path (default: auto-generated with timestamp)"
    )
    
    mode_group.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts in direct mode (use with extreme caution)"
    )
    
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes (implies sandbox mode)"
    )
    
    # Output and Reporting
    output_group = parser.add_argument_group('Output and Reporting', 'Control analysis output and reports')
    
    output_group.add_argument(
        "--output-format",
        choices=["json", "text", "markdown", "csv"],
        default="text",
        help="Output format for analysis report (default: text)"
    )
    
    output_group.add_argument(
        "--output-file",
        type=str,
        metavar="FILE",
        help="Save analysis report to specified file instead of printing to stdout"
    )
    
    output_group.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary statistics, not detailed constant-by-constant analysis"
    )
    
    output_group.add_argument(
        "--show-unused",
        action="store_true",
        help="Include unused constants in the report"
    )
    
    output_group.add_argument(
        "--show-ambiguous",
        action="store_true",
        help="Highlight ambiguous cases that need manual review"
    )
    
    # Logging and Debugging
    debug_group = parser.add_argument_group('Logging and Debugging', 'Control logging and debug output')
    
    debug_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (equivalent to --log-level DEBUG)"
    )
    
    debug_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output (equivalent to --log-level ERROR)"
    )
    
    debug_group.add_argument(
        "--log-file",
        type=str,
        metavar="FILE",
        help="Save detailed logs to specified file (useful for troubleshooting)"
    )
    
    debug_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    debug_group.add_argument(
        "--profile",
        action="store_true",
        help="Enable performance profiling and timing information"
    )
    
    # Analysis Options
    analysis_group = parser.add_argument_group('Analysis Options', 'Fine-tune the analysis behavior')
    
    analysis_group.add_argument(
        "--min-usage-threshold",
        type=int,
        default=1,
        metavar="N",
        help="Minimum usage count to consider a constant (default: 1)"
    )
    
    analysis_group.add_argument(
        "--ignore-test-files",
        action="store_true",
        help="Ignore test files when analyzing constant usage"
    )
    
    analysis_group.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive constant name matching (default: case-insensitive)"
    )
    
    # Utility Commands
    utility_group = parser.add_argument_group('Utility Commands', 'Helper commands and utilities')
    
    utility_group.add_argument(
        "--create-config",
        type=str,
        nargs='?',
        const="constants_refactor_config.json",
        metavar="FILE",
        help="Create a sample configuration file (default: constants_refactor_config.json)"
    )
    
    utility_group.add_argument(
        "--check-deps",
        action="store_true",
        help="Check for required dependencies and exit"
    )
    
    utility_group.add_argument(
        "--tips",
        action="store_true",
        help="Show usage tips and common workflows"
    )
    
    utility_group.add_argument(
        "--generate-docs",
        type=str,
        nargs='?',
        const=None,
        metavar="FILE",
        help="Generate comprehensive documentation (optionally save to file)"
    )
    
    # Version and Help
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0 - C++ Constants Refactoring Tool"
    )
    
    return parser


if __name__ == "__main__":
    main()