import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

# Add the script's directory to the Python path to allow importing the script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from constants_refactor import (
    ConfigurationManager,
    ConfigurationError,
    CMakeAnalyzer,
    CMakeError,
    MalformedInputError,
    ConstantsParser,
    UsageAnalyzer,
    Constant,
    UsageCategory,
    Logger,
    FilePermissionError
)

class TestConfigurationManager(unittest.TestCase):

    def setUp(self):
        self.logger = Logger("test_logger", "ERROR")

    def _create_mock_args(self, **kwargs):
        """Helper to create a mock argparse.Namespace object."""
        args = argparse.Namespace()
        defaults = {
            'constants_file': None,
            'project_root': '.',
            'build_dir': 'build',
            'mode': 'sandbox',
            'sandbox': True,
            'source_dirs': ['src/', 'include/'],
            'exclude_dirs': None,
            'config': None,
            'output_format': 'text',
            'output_file': None,
            'verbose': False,
            'log_file': None,
            'log_level': 'INFO'
        }
        for key, value in defaults.items():
            setattr(args, key, kwargs.get(key, value))
        return args

    def test_get_constants_file_path_from_args(self):
        """Test that constants_file is correctly retrieved from command-line arguments."""
        args = self._create_mock_args(constants_file="path/from/args.h")
        config_manager = ConfigurationManager(args, self.logger)
        self.assertEqual(config_manager.get_constants_file_path(), "path/from/args.h")

    def test_get_constants_file_path_from_config(self):
        """Test that constants_file is correctly retrieved from the config file."""
        args = self._create_mock_args()
        config_manager = ConfigurationManager(args, self.logger)
        config_manager.config_data = {'constants_file': 'path/from/config.h'}
        self.assertEqual(config_manager.get_constants_file_path(), 'path/from/config.h')

    def test_get_constants_file_path_prefers_args(self):
        """Test that command-line arguments take precedence over the config file."""
        args = self._create_mock_args(constants_file="path/from/args.h")
        config_manager = ConfigurationManager(args, self.logger)
        config_manager.config_data = {'constants_file': 'path/from/config.h'}
        self.assertEqual(config_manager.get_constants_file_path(), "path/from/args.h")

    def test_get_constants_file_path_missing(self):
        """Test that a ConfigurationError is raised when the constants_file is not specified."""
        args = self._create_mock_args()
        config_manager = ConfigurationManager(args, self.logger)
        with self.assertRaises(ConfigurationError):
            config_manager.get_constants_file_path()

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_config_file(self, mock_exists, mock_file):
        """Test loading a valid JSON configuration file."""
        args = self._create_mock_args(config="config.json")
        config_manager = ConfigurationManager(args, self.logger)
        self.assertEqual(config_manager.config_data, {"key": "value"})

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_config_file_not_found(self, mock_exists):
        """Test that a ConfigurationError is raised for a non-existent config file."""
        args = self._create_mock_args(config="nonexistent.json")
        with self.assertRaises(ConfigurationError):
            ConfigurationManager(args, self.logger)

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_config_file_invalid_json(self, mock_exists, mock_file):
        """Test that a ConfigurationError is raised for an invalid JSON config file."""
        args = self._create_mock_args(config="invalid.json")
        with self.assertRaises(ConfigurationError):
            ConfigurationManager(args, self.logger)

    def test_get_project_root_default(self):
        """Test that the default project_root is returned when not specified."""
        args = self._create_mock_args()
        config_manager = ConfigurationManager(args, self.logger)
        self.assertEqual(config_manager.get_project_root(), ".")

    def test_get_source_directories(self):
        """Test retrieval of source directories from arguments."""
        args = self._create_mock_args(source_dirs=["custom_src/"])
        config_manager = ConfigurationManager(args, self.logger)
        self.assertEqual(config_manager.get_source_directories(), ["custom_src/"])

    def test_get_exclude_patterns(self):
        """Test that exclude patterns are correctly combined from args, config, and defaults."""
        args = self._create_mock_args(exclude_dirs="from_args/")
        config_manager = ConfigurationManager(args, self.logger)
        config_manager.config_data = {'exclude_patterns': ['from_config/']}
        
        patterns = config_manager.get_exclude_patterns()
        
        self.assertIn("from_args/", patterns)
        self.assertIn("from_config/", patterns)
        self.assertTrue(any("build/" in p for p in patterns)) # Check for defaults

    def test_get_execution_mode(self):
        """Test retrieval of execution mode."""
        args = self._create_mock_args(mode="direct")
        config_manager = ConfigurationManager(args, self.logger)
        self.assertEqual(config_manager.get_execution_mode(), "direct")

    @patch("pathlib.Path.exists", return_value=True)
    def test_validate_configuration_success(self, mock_exists):
        """Test successful validation of a correct configuration."""
        args = self._create_mock_args(constants_file="constants.h")
        config_manager = ConfigurationManager(args, self.logger)
        self.assertTrue(config_manager.validate_configuration())

    @patch("pathlib.Path.exists", return_value=False)
    def test_validate_configuration_missing_constants_file(self, mock_exists):
        """Test that validation fails if the constants file does not exist."""
        args = self._create_mock_args(constants_file="nonexistent.h")
        config_manager = ConfigurationManager(args, self.logger)
        with self.assertRaises(ConfigurationError):
            config_manager.validate_configuration()

class TestCMakeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.logger = Logger("test_cmake_analyzer", "ERROR")
        self.analyzer = CMakeAnalyzer(self.logger)

    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_generate_compile_commands_success(self, mock_exists, mock_mkdir, mock_run):
        """Test successful generation of compile_commands.json."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = self.analyzer.generate_compile_commands("build", ".")
        self.assertTrue(result)
        mock_run.assert_called_once()
        self.assertIn("cmake", mock_run.call_args[0][0])

    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    def test_generate_compile_commands_failure(self, mock_mkdir, mock_run):
        """Test failed generation of compile_commands.json."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="CMake error")
        result = self.analyzer.generate_compile_commands("build", ".")
        self.assertFalse(result)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="cmake", timeout=1))
    @patch("pathlib.Path.mkdir")
    def test_generate_compile_commands_timeout(self, mock_mkdir, mock_run):
        """Test that a timeout during CMake execution is handled."""
        result = self.analyzer.generate_compile_commands("build", ".")
        self.assertFalse(result)

    def test_parse_compile_commands_success(self):
        """Test successful parsing of a valid compile_commands.json file."""
        json_data = json.dumps([
            {
                "directory": "/project/build",
                "command": "g++ -o CMakeFiles/mod1.dir/src/file1.cpp.o -c src/file1.cpp",
                "file": "src/file1.cpp"
            },
            {
                "directory": "/project/build",
                "command": "g++ -o CMakeFiles/mod2.dir/src/file2.cpp.o -c src/file2.cpp",
                "file": "src/file2.cpp"
            }
        ])
        m = mock_open(read_data=json_data)
        with patch("builtins.open", m):
            result = self.analyzer.parse_compile_commands("dummy_path.json")
            self.assertEqual(len(result), 2)
            self.assertEqual(result["src/file1.cpp"], "mod1")
            self.assertEqual(result["src/file2.cpp"], "mod2")

    def test_parse_compile_commands_invalid_json(self):
        """Test that an error is raised when parsing an invalid JSON file."""
        m = mock_open(read_data="invalid json")
        with patch("builtins.open", m):
            with self.assertRaises(MalformedInputError):
                self.analyzer.parse_compile_commands("dummy_path.json")

    def test_map_files_to_modules(self):
        """Test the mapping of files to modules based on target names."""
        file_target_map = {
            "src/file1.cpp": "mod1",
            "src/file2.cpp": "mod2_lib",
            "src/file3.cpp": "another_target"
        }
        module_mapping = {
            "ModuleA": ["mod1"],
            "ModuleB": ["mod2_"]
        }
        result = self.analyzer.map_files_to_modules(file_target_map, module_mapping)
        self.assertEqual(result["src/file1.cpp"], "ModuleA")
        self.assertEqual(result["src/file2.cpp"], "ModuleB")
        self.assertEqual(result["src/file3.cpp"], "another_target") # Falls back to target name

    @patch("pathlib.Path.rglob")
    def test_fallback_cmake_parse(self, mock_rglob):
        """Test the fallback mechanism of parsing CMakeLists.txt files."""
        # Mock the file system structure and content
        mock_cmakelists_path = MagicMock()
        mock_cmakelists_path.parent = Path("/project/src/mod1")
        mock_rglob.return_value = [mock_cmakelists_path]

        cmakelists_content = "add_library(mod1 src/file1.cpp)"
        m = mock_open(read_data=cmakelists_content)
        
        # Mock the open call within the analyzer's methods
        with patch("builtins.open", m):
             # Mock exists for the source file
            with patch("pathlib.Path.exists", return_value=True):
                # We need to mock resolve as well
                with patch("pathlib.Path.resolve", return_value=Path("/project/src/mod1/src/file1.cpp")):
                    result = self.analyzer.fallback_cmake_parse("/project")
                    # The key should be the resolved path as a string
                    self.assertIn(str(Path("/project/src/mod1/src/file1.cpp")), result)
                    self.assertEqual(result[str(Path("/project/src/mod1/src/file1.cpp"))], "mod1")

class TestConstantsParser(unittest.TestCase):

    def setUp(self):
        self.logger = Logger("test_parser", "ERROR")
        # Mock the pygccxml and CastXML dependencies
        self.mock_pygccxml = patch('constants_refactor.PYGCCXML_AVAILABLE', True).start()
        self.mock_find_xml_generator = patch('pygccxml.utils.find_xml_generator').start()
        self.mock_find_xml_generator.return_value = ('/path/to/castxml', 'castxml')
        self.mock_find_compiler = patch('constants_refactor.ConstantsParser._find_compiler').start()
        self.mock_find_compiler.return_value = 'g++'
        
        self.parser = ConstantsParser(logger=self.logger)

    def tearDown(self):
        patch.stopall()

    @patch('constants_refactor.ConstantsParser.parse_with_castxml')
    @patch('constants_refactor.ConstantsParser.handle_preprocessor_defines')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('constants_refactor.ErrorHandler.handle_malformed_input_error', return_value=True)
    def test_parse_constants_file_success(self, mock_validate, mock_exists, mock_defines, mock_castxml):
        """Test successful parsing of a constants file."""
        mock_castxml.return_value = MagicMock() # Dummy AST
        self.parser.extract_constants_from_ast = MagicMock(return_value=[
            Constant('MY_CONST', '123', 'const', [], 10, None)
        ])
        mock_defines.return_value = [
            Constant('MY_DEFINE', '456', 'define', [], 5, None)
        ]

        constants = self.parser.parse_constants_file("constants.h")
        
        self.assertEqual(len(constants), 2)
        self.assertEqual(constants[0].name, 'MY_CONST')
        self.assertEqual(constants[1].name, 'MY_DEFINE')
        mock_castxml.assert_called_once_with("constants.h")
        mock_defines.assert_called_once_with("constants.h")

    @patch('pathlib.Path.exists', return_value=False)
    def test_parse_constants_file_not_found(self, mock_exists):
        """Test that an error is raised if the constants file does not exist."""
        with self.assertRaises(FilePermissionError):
            self.parser.parse_constants_file("nonexistent.h")

    def test_parse_define_line_simple(self):
        """Test parsing a simple #define line."""
        line = "#define MAX_CONNECTIONS 100"
        constant = self.parser._parse_define_line(line, 1, "file.h")
        self.assertIsNotNone(constant)
        self.assertEqual(constant.name, "MAX_CONNECTIONS")
        self.assertEqual(constant.value, "100")
        self.assertEqual(constant.type, "define")

    def test_parse_define_line_with_comment(self):
        """Test parsing a #define line that has a comment."""
        line = "#define TIMEOUT 5000 // in milliseconds"
        constant = self.parser._parse_define_line(line, 1, "file.h")
        self.assertEqual(constant.name, "TIMEOUT")
        self.assertEqual(constant.value, "5000 // in milliseconds") # Comment is part of the value

    def test_parse_define_line_function_macro(self):
        """Test that function-like macros are ignored."""
        line = "#define ADD(a, b) ((a) + (b))"
        constant = self.parser._parse_define_line(line, 1, "file.h")
        self.assertIsNone(constant)

    def test_parse_const_variable_line_simple(self):
        """Test parsing a simple const variable line."""
        line = "const int MAX_USERS = 100;"
        constant = self.parser._parse_const_variable_line(line, 1)
        self.assertIsNotNone(constant)
        self.assertEqual(constant.name, "MAX_USERS")
        self.assertEqual(constant.value, "100")
        self.assertEqual(constant.type, "const")

    def test_parse_const_variable_line_constexpr(self):
        """Test parsing a constexpr variable line."""
        line = "constexpr double PI = 3.14159;"
        constant = self.parser._parse_const_variable_line(line, 1)
        self.assertIsNotNone(constant)
        self.assertEqual(constant.name, "PI")
        self.assertEqual(constant.value, "3.14159")
        self.assertEqual(constant.type, "constexpr")

    def test_parse_const_variable_line_pointer(self):
        """Test parsing a const pointer variable."""
        line = "const char* const GREETING = \"Hello\";"
        constant = self.parser._parse_const_variable_line(line, 1)
        self.assertIsNotNone(constant)
        self.assertEqual(constant.name, "GREETING")
        self.assertEqual(constant.value, "\"Hello\"")
        self.assertEqual(constant.type, "const")

class TestUsageAnalyzer(unittest.TestCase):

    def setUp(self):
        self.logger = Logger("test_usage_analyzer", "ERROR")
        self.file_module_map = {
            os.path.abspath("src/moduleA/fileA1.cpp"): "ModuleA",
            os.path.abspath("src/moduleA/fileA2.h"): "ModuleA",
            os.path.abspath("src/moduleB/fileB1.cpp"): "ModuleB",
            os.path.abspath("include/shared.h"): "Shared",
        }
        self.exclude_file = os.path.abspath("constants.h")
        self.analyzer = UsageAnalyzer(self.file_module_map, self.exclude_file, self.logger)

    def test_search_in_file_found(self):
        """Test finding a constant in a file."""
        m = mock_open(read_data="line 1\nconst int x = MY_CONST;\nline 3")
        with patch("builtins.open", m):
            with patch("os.path.exists", return_value=True):
                 with patch("os.path.getsize", return_value=100):
                    lines = self.analyzer.search_in_file("dummy.cpp", "MY_CONST")
                    self.assertEqual(lines, [2])

    def test_search_in_file_not_found(self):
        """Test not finding a constant in a file."""
        m = mock_open(read_data="line 1\nconst int x = OTHER_CONST;\nline 3")
        with patch("builtins.open", m):
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getsize", return_value=100):
                    lines = self.analyzer.search_in_file("dummy.cpp", "MY_CONST")
                    self.assertEqual(lines, [])

    def test_search_in_file_word_boundary(self):
        """Test that search respects word boundaries."""
        m = mock_open(read_data="const int x = MY_CONST_EXTRA;")
        with patch("builtins.open", m):
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getsize", return_value=100):
                    lines = self.analyzer.search_in_file("dummy.cpp", "MY_CONST")
                    self.assertEqual(lines, [])

    @patch('constants_refactor.UsageAnalyzer._search_with_python')
    def test_find_constant_usage_python_fallback(self, mock_search_python):
        """Test the Python-based search fallback."""
        constant = Constant("MY_CONST", "1", "define", [], 1, None)
        source_dirs = ["src/"]
        
        # Mock the search result
        mock_search_python.return_value = {
            os.path.abspath("src/moduleA/fileA1.cpp"): [10],
            os.path.abspath("constants.h"): [5]
        }

        with patch.object(self.analyzer, 'ripgrep_available', False):
            usage_map = self.analyzer.find_constant_usage(constant, source_dirs)
            
            self.assertIn(os.path.abspath("src/moduleA/fileA1.cpp"), usage_map)
            self.assertNotIn(os.path.abspath("constants.h"), usage_map)
            mock_search_python.assert_called_once_with(constant.name, source_dirs)

    @patch('constants_refactor.UsageAnalyzer._search_with_ripgrep')
    def test_find_constant_usage_ripgrep(self, mock_search_rg):
        """Test the ripgrep-based search."""
        constant = Constant("MY_CONST", "1", "define", [], 1, None)
        source_dirs = ["src/"]
        
        # Mock the search result
        mock_search_rg.return_value = {
            os.path.abspath("src/moduleA/fileA1.cpp"): [10],
            os.path.abspath("constants.h"): [5]
        }

        with patch.object(self.analyzer, 'ripgrep_available', True):
            usage_map = self.analyzer.find_constant_usage(constant, source_dirs)

            self.assertIn(os.path.abspath("src/moduleA/fileA1.cpp"), usage_map)
            self.assertNotIn(os.path.abspath("constants.h"), usage_map) # Should be excluded
            mock_search_rg.assert_called_once_with(constant.name, source_dirs)

    def test_categorize_usage_unused(self):
        """Test categorization of an unused constant."""
        category = self.analyzer.categorize_usage({})
        self.assertEqual(category, UsageCategory.UNUSED)

    def test_categorize_usage_private(self):
        """Test categorization of a module-private constant."""
        usage_map = {os.path.abspath("src/moduleA/fileA1.cpp"): [10]}
        category = self.analyzer.categorize_usage(usage_map)
        self.assertEqual(category, UsageCategory.PRIVATE)

    def test_categorize_usage_shared(self):
        """Test categorization of a shared constant."""
        usage_map = {
            os.path.abspath("src/moduleA/fileA1.cpp"): [10],
            os.path.abspath("src/moduleB/fileB1.cpp"): [20]
        }
        category = self.analyzer.categorize_usage(usage_map)
        self.assertEqual(category, UsageCategory.SHARED)

    def test_categorize_usage_ambiguous(self):
        """Test categorization of a constant with ambiguous usage."""
        # This file is not in the file_module_map
        unmapped_file = os.path.abspath("src/unmapped/fileU1.cpp")
        usage_map = {unmapped_file: [15]}
        
        # Ensure the fallback mechanism does not infer a module for this test
        with patch.object(self.analyzer, '_infer_module_from_directory_structure', return_value=None):
            with patch.object(self.analyzer, '_is_ignorable_file', return_value=False):
                category = self.analyzer.categorize_usage(usage_map)
                self.assertEqual(category, UsageCategory.AMBIGUOUS)

    def test_get_module_for_file(self):
        """Test retrieving the module for a given file path."""
        path = os.path.abspath("src/moduleA/fileA1.cpp")
        module = self.analyzer._get_module_for_file(path)
        self.assertEqual(module, "ModuleA")

    def test_get_module_for_unmapped_file(self):
        """Test that an unmapped file returns None initially."""
        path = os.path.abspath("src/unmapped/fileU1.cpp")
        # The primary lookup should fail
        self.assertNotIn(path, self.analyzer.file_module_map)
        # Test the fallback mechanism
        with patch.object(self.analyzer, '_infer_module_from_directory_structure', return_value="unmapped"):
            module = self.analyzer._get_module_for_file(path)
            self.assertEqual(module, "unmapped")

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary C++ project structure for integration testing."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create project structure
        self.project_root = Path(self.test_dir)
        (self.project_root / "src" / "moduleA").mkdir(parents=True)
        (self.project_root / "src" / "moduleB").mkdir(parents=True)
        (self.project_root / "include").mkdir(parents=True)

        # Create CMakeLists.txt
        cmakelists_content = """
cmake_minimum_required(VERSION 3.10)
project(TestProject)

add_library(moduleA src/moduleA/fileA.cpp)
add_library(moduleB src/moduleB/fileB.cpp)
"""
        (self.project_root / "CMakeLists.txt").write_text(cmakelists_content)

        # Create constants file
        self.constants_file = self.project_root / "include" / "constants.h"
        constants_content = """
#pragma once

#// Private constant for Module A
#define MOD_A_PRIVATE 100

#// Private constant for Module B
const int MOD_B_PRIVATE = 200;

#// Shared constant used by A and B
constexpr double SHARED_CONST = 3.14;

#// Unused constant
#define UNUSED_CONST 999
""".strip()
        self.constants_file.write_text(constants_content)

        # Create source files
        (self.project_root / "src" / "moduleA" / "fileA.cpp").write_text(f"""
#include \"{self.constants_file.as_posix()}\"\nint a = MOD_A_PRIVATE;\ndouble s = SHARED_CONST;\n""".strip())
        (self.project_root / "src" / "moduleB" / "fileB.cpp").write_text(f"""
#include \"{self.constants_file.as_posix()}\"\nint b = MOD_B_PRIVATE;\ndouble s = SHARED_CONST;\n""".strip())

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_end_to_end_analysis(self):
        """
        Test the full analysis pipeline from command line to JSON report.
        This test requires a working C++ compiler (like g++) and CMake in the system's PATH.
        """
        # Path to the main script
        script_path = Path(__file__).parent / "constants_refactor.py"
        
        # Command to execute
        command = [
            sys.executable, str(script_path),
            "--project-root", str(self.project_root),
            "--constants-file", str(self.constants_file),
            "--output-format", "json",
            "--log-level", "ERROR" # Keep test output clean
        ]

        # Execute the script
        result = subprocess.run(command, capture_output=True, text=True)

        # Check for successful execution
        self.assertEqual(result.returncode, 0, f"Script failed to execute:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        # Parse the JSON output
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Script did not produce valid JSON output.\nOutput:\n{result.stdout}")

        # Verify the report contents
        self.assertIn("constants", report)
        
        categorized_constants = {c['name']: c['category'] for c in report['constants']}

        self.assertEqual(categorized_constants.get("MOD_A_PRIVATE"), "private")
        self.assertEqual(categorized_constants.get("MOD_B_PRIVATE"), "private")
        self.assertEqual(categorized_constants.get("SHARED_CONST"), "shared")
        self.assertEqual(categorized_constants.get("UNUSED_CONST"), "unused")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)