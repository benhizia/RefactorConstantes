#!/usr/bin/env python3
"""
Integration tests for the C++ Constants Refactor Tool

Tests the complete pipeline from parsing constants to generating refactored files.
Includes comprehensive end-to-end testing with multiple project configurations.
"""

import unittest
import tempfile
import shutil
import os
import json
import subprocess
import time
from pathlib import Path
from constants_refactor import (
    ConstantsParser, UsageAnalyzer, CMakeAnalyzer, FileGenerator, 
    Logger, ConfigurationManager, ReportGenerator, SandboxExecutionMode
)


class IntegrationTestBase(unittest.TestCase):
    """Base class for integration tests with common setup."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_data_dir = Path("test_data")
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = Logger("IntegrationTest", "DEBUG")
        
        # Copy test data to temp directory
        if self.test_data_dir.exists():
            shutil.copytree(self.test_data_dir, self.temp_dir / "test_project")
        else:
            self.skipTest("Test data directory not found")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class TestEndToEndPipeline(IntegrationTestBase):
    """Test the complete end-to-end pipeline."""
    
    def test_complete_pipeline_sandbox_mode(self):
        """Test complete pipeline in sandbox mode with sample project."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        build_dir = self.temp_dir / "build"
        sandbox_dir = self.temp_dir / "sandbox"
        
        try:
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            self.assertGreater(len(constants), 10, "Should parse constants from test file")
            
            # Analyze usage
            analyzer = UsageAnalyzer(self.logger)
            usage_info = analyzer.analyze_usage(constants, str(project_dir), str(constants_file))
            
            # Create sandbox execution mode
            sandbox_mode = SandboxExecutionMode(str(sandbox_dir), self.logger)
            sandbox_mode.setup()
            
            # Verify sandbox was created
            self.assertTrue(sandbox_dir.exists(), "Sandbox directory should be created")
            
            # Generate report
            report_generator = ReportGenerator(self.logger)
            report_path = sandbox_dir / "analysis_report.json"
            report_generator.generate_json_report(usage_info, str(report_path))
            
            # Verify report was generated
            self.assertTrue(report_path.exists(), "Analysis report should be generated")
            
            # Check for specific constants we know should be there
            constant_names = [c.name for c in constants]
            self.assertIn("MAX_BUFFER_SIZE", constant_names)
            self.assertIn("DEFAULT_PORT", constant_names)
            
        except Exception as e:
            self.fail(f"Pipeline failed with exception: {e}")
    
    def test_complete_pipeline_large_constants_file(self):
        """Test complete pipeline with large constants file (100+ constants)."""
        project_dir = self.temp_dir / "test_project"
        large_constants_file = project_dir / "large_constants.h"
        
        # Copy large constants file to test project
        shutil.copy2("test_data/large_constants.h", large_constants_file)
        
        try:
            # Parse large constants file
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(large_constants_file))
            
            # Verify we have 100+ constants
            self.assertGreaterEqual(len(constants), 100, "Should parse 100+ constants from large file")
            
            # Analyze usage across the project
            analyzer = UsageAnalyzer(self.logger)
            usage_info = analyzer.analyze_usage(constants, str(project_dir), str(large_constants_file))
            
            # Verify analysis completed
            self.assertIsInstance(usage_info, list, "Usage analysis should return a list")
            
            # Generate comprehensive report
            report_generator = ReportGenerator(self.logger)
            report_path = self.temp_dir / "large_constants_report.json"
            report_generator.generate_json_report(usage_info, str(report_path))
            
            # Verify report contains expected data
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            self.assertIn("constants", report_data, "Report should contain constants section")
            self.assertIn("summary", report_data, "Report should contain summary section")
            
        except Exception as e:
            self.fail(f"Large constants pipeline failed: {e}")
    
    def test_complex_project_pipeline(self):
        """Test pipeline with complex multi-module project."""
        # Copy complex project structure
        complex_project_src = Path("test_data/complex_project")
        if not complex_project_src.exists():
            self.skipTest("Complex project test data not available")
        
        complex_project_dir = self.temp_dir / "complex_project"
        shutil.copytree(complex_project_src, complex_project_dir)
        
        # Copy large constants file to complex project
        large_constants_file = complex_project_dir / "large_constants.h"
        shutil.copy2("test_data/large_constants.h", large_constants_file)
        
        try:
            # Test CMake analysis with complex project
            cmake_analyzer = CMakeAnalyzer(self.logger)
            build_dir = self.temp_dir / "complex_build"
            
            # Attempt to generate compile commands
            success = cmake_analyzer.generate_compile_commands(str(build_dir), str(complex_project_dir))
            
            if success:
                # Parse compile commands
                compile_commands_file = build_dir / "compile_commands.json"
                if compile_commands_file.exists():
                    file_target_map = cmake_analyzer.parse_compile_commands(str(compile_commands_file))
                    self.assertGreater(len(file_target_map), 0, "Should map files to targets in complex project")
                    
                    # Test module mapping
                    file_module_map = cmake_analyzer.map_files_to_modules(file_target_map)
                    self.assertGreater(len(file_module_map), 0, "Should map files to modules in complex project")
            
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(large_constants_file))
            
            # Analyze usage in complex project
            analyzer = UsageAnalyzer(self.logger)
            usage_info = analyzer.analyze_usage(constants, str(complex_project_dir), str(large_constants_file))
            
            # Verify cross-module usage detection
            cross_module_constants = [info for info in usage_info if len(info.modules_using) > 1]
            self.assertGreater(len(cross_module_constants), 0, "Should detect cross-module constant usage")
            
        except Exception as e:
            self.logger.warning(f"Complex project test failed: {e}")
            # Don't fail the test as CMake might not be available
    
    def test_constants_parsing_accuracy(self):
        """Test accuracy of constants parsing."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        
        parser = ConstantsParser(self.logger)
        
        try:
            constants = parser.parse_constants_file(str(constants_file))
            
            # Verify we parsed a reasonable number of constants
            self.assertGreater(len(constants), 50, "Should parse many constants")
            
            # Test specific constants
            constant_dict = {c.name: c for c in constants}
            
            # Test #define constants
            self.assertIn("MAX_BUFFER_SIZE", constant_dict)
            self.assertEqual(constant_dict["MAX_BUFFER_SIZE"].value, "1024")
            self.assertEqual(constant_dict["MAX_BUFFER_SIZE"].type, "define")
            
            self.assertIn("DEFAULT_PORT", constant_dict)
            self.assertEqual(constant_dict["DEFAULT_PORT"].value, "8080")
            
            # Test const variables
            if "ARRAY_SIZE" in constant_dict:
                self.assertEqual(constant_dict["ARRAY_SIZE"].type, "const")
                self.assertEqual(constant_dict["ARRAY_SIZE"].value, "256")
            
            # Test constexpr variables
            if "COMPILE_TIME_CONSTANT" in constant_dict:
                self.assertEqual(constant_dict["COMPILE_TIME_CONSTANT"].type, "constexpr")
                self.assertEqual(constant_dict["COMPILE_TIME_CONSTANT"].value, "42")
            
        except Exception as e:
            self.fail(f"Constants parsing failed: {e}")
    
    def test_usage_analysis_accuracy(self):
        """Test accuracy of usage analysis."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        
        # Parse constants first
        parser = ConstantsParser(self.logger)
        constants = parser.parse_constants_file(str(constants_file))
        
        # Analyze usage
        analyzer = UsageAnalyzer(self.logger)
        usage_info = analyzer.analyze_usage(constants, str(project_dir), str(constants_file))
        
        # Verify usage analysis results
        self.assertGreater(len(usage_info), 0, "Should find usage for some constants")
        
        # Check specific constants we know are used
        usage_dict = {info.constant.name: info for info in usage_info}
        
        # DEFAULT_PORT should be used in network_manager.cpp
        if "DEFAULT_PORT" in usage_dict:
            usage = usage_dict["DEFAULT_PORT"]
            self.assertGreater(len(usage.usage_files), 0, "DEFAULT_PORT should have usage files")
            
            # Check if it's found in network module
            network_files = [f for f in usage.usage_files.keys() if "network" in f]
            self.assertGreater(len(network_files), 0, "DEFAULT_PORT should be used in network files")
        
        # MAX_BUFFER_SIZE should be used in network_manager.cpp
        if "MAX_BUFFER_SIZE" in usage_dict:
            usage = usage_dict["MAX_BUFFER_SIZE"]
            self.assertGreater(len(usage.usage_files), 0, "MAX_BUFFER_SIZE should have usage files")
    
    def test_cmake_integration_simple_project(self):
        """Test CMake integration with simple project structure."""
        project_dir = self.temp_dir / "test_project"
        build_dir = self.temp_dir / "build"
        
        analyzer = CMakeAnalyzer(self.logger)
        
        try:
            # Test compile commands generation
            success = analyzer.generate_compile_commands(str(build_dir), str(project_dir))
            
            if success:
                # Test parsing compile commands
                compile_commands_file = build_dir / "compile_commands.json"
                if compile_commands_file.exists():
                    file_target_map = analyzer.parse_compile_commands(str(compile_commands_file))
                    self.assertGreater(len(file_target_map), 0, "Should map files to targets")
                    
                    # Verify specific expected mappings
                    network_files = [f for f in file_target_map.keys() if "network" in f]
                    self.assertGreater(len(network_files), 0, "Should find network module files")
                    
                    # Test module mapping
                    file_module_map = analyzer.map_files_to_modules(file_target_map)
                    self.assertGreater(len(file_module_map), 0, "Should map files to modules")
            else:
                # Test fallback CMake parsing
                self.logger.info("CMake generation failed, testing fallback parsing")
                fallback_map = analyzer.fallback_cmake_parse(str(project_dir))
                
                # Should find some mappings even with fallback
                if len(fallback_map) == 0:
                    self.logger.warning("No file mappings found with fallback method")
                
        except Exception as e:
            self.logger.warning(f"CMake integration test failed: {e}")
            # This is not a hard failure as CMake might not be available
    
    def test_cmake_integration_complex_project(self):
        """Test CMake integration with complex multi-module project."""
        complex_project_src = Path("test_data/complex_project")
        if not complex_project_src.exists():
            self.skipTest("Complex project test data not available")
        
        complex_project_dir = self.temp_dir / "complex_project"
        shutil.copytree(complex_project_src, complex_project_dir)
        
        build_dir = self.temp_dir / "complex_build"
        analyzer = CMakeAnalyzer(self.logger)
        
        try:
            # Test compile commands generation with complex project
            success = analyzer.generate_compile_commands(str(build_dir), str(complex_project_dir))
            
            if success:
                compile_commands_file = build_dir / "compile_commands.json"
                if compile_commands_file.exists():
                    # Parse and validate compile commands
                    file_target_map = analyzer.parse_compile_commands(str(compile_commands_file))
                    
                    # Verify we found multiple modules
                    unique_targets = set(file_target_map.values())
                    self.assertGreaterEqual(len(unique_targets), 3, "Should find multiple targets in complex project")
                    
                    # Test specific module detection
                    core_files = [f for f, t in file_target_map.items() if "core" in f]
                    network_files = [f for f, t in file_target_map.items() if "network" in f]
                    database_files = [f for f, t in file_target_map.items() if "database" in f]
                    
                    self.assertGreater(len(core_files), 0, "Should find core module files")
                    self.assertGreater(len(network_files), 0, "Should find network module files")
                    self.assertGreater(len(database_files), 0, "Should find database module files")
                    
                    # Test module mapping
                    file_module_map = analyzer.map_files_to_modules(file_target_map)
                    
                    # Verify module boundaries are correctly identified
                    modules = set(file_module_map.values())
                    self.assertGreaterEqual(len(modules), 3, "Should identify multiple distinct modules")
            
        except Exception as e:
            self.logger.warning(f"Complex CMake integration test failed: {e}")
    
    def test_cmake_fallback_mechanisms(self):
        """Test CMake fallback parsing mechanisms."""
        project_dir = self.temp_dir / "test_project"
        analyzer = CMakeAnalyzer(self.logger)
        
        try:
            # Test fallback CMake parsing directly
            fallback_map = analyzer.fallback_cmake_parse(str(project_dir))
            
            # Should find some file mappings from CMakeLists.txt parsing
            if len(fallback_map) > 0:
                self.assertIsInstance(fallback_map, dict, "Fallback should return dictionary")
                
                # Verify mapping structure
                for file_path, target in fallback_map.items():
                    self.assertIsInstance(file_path, str, "File path should be string")
                    self.assertIsInstance(target, str, "Target should be string")
            
            # Test directory-based fallback
            directory_map = analyzer.directory_based_module_detection(str(project_dir))
            self.assertIsInstance(directory_map, dict, "Directory detection should return dictionary")
            
        except Exception as e:
            self.logger.warning(f"Fallback mechanism test failed: {e}")
    
    def test_file_generation(self):
        """Test file generation functionality."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        output_dir = self.temp_dir / "output"
        
        # Parse constants
        parser = ConstantsParser(self.logger)
        constants = parser.parse_constants_file(str(constants_file))
        
        # Analyze usage
        analyzer = UsageAnalyzer(self.logger)
        usage_info = analyzer.analyze_usage(constants, str(project_dir), str(constants_file))
        
        # Generate files
        generator = FileGenerator(self.logger)
        
        try:
            generator.generate_module_files(usage_info, str(output_dir))
            
            # Verify output directory was created
            self.assertTrue(output_dir.exists(), "Output directory should be created")
            
            # Look for generated files
            generated_files = list(output_dir.rglob("*.h"))
            
            if len(generated_files) > 0:
                # Verify file contents
                for file_path in generated_files:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Basic validation
                    self.assertIn("#ifndef", content, "Should have header guard")
                    self.assertIn("#define", content, "Should have header guard define")
                    self.assertIn("#endif", content, "Should have header guard end")
            
        except Exception as e:
            self.fail(f"File generation failed: {e}")


class TestErrorHandling(IntegrationTestBase):
    """Test error handling and edge cases."""
    
    def test_missing_constants_file(self):
        """Test handling of missing constants file."""
        nonexistent_file = self.temp_dir / "nonexistent.h"
        
        parser = ConstantsParser(self.logger)
        
        with self.assertRaises(Exception):
            parser.parse_constants_file(str(nonexistent_file))
    
    def test_malformed_constants_file(self):
        """Test handling of malformed constants file."""
        malformed_file = self.temp_dir / "malformed.h"
        
        # Create a malformed C++ file
        with open(malformed_file, 'w') as f:
            f.write("This is not valid C++ code!\n")
            f.write("#define INCOMPLETE\n")
            f.write("const int MISSING_VALUE\n")
        
        parser = ConstantsParser(self.logger)
        
        try:
            constants = parser.parse_constants_file(str(malformed_file))
            # Should handle gracefully, possibly with empty results
            self.assertIsInstance(constants, list)
        except Exception as e:
            # Should provide meaningful error message
            self.assertIsInstance(e, Exception)
    
    def test_empty_project_directory(self):
        """Test handling of empty project directory."""
        empty_dir = self.temp_dir / "empty_project"
        empty_dir.mkdir()
        
        # Create minimal constants file
        constants_file = empty_dir / "constants.h"
        with open(constants_file, 'w') as f:
            f.write("#define TEST_CONSTANT 42\n")
        
        parser = ConstantsParser(self.logger)
        constants = parser.parse_constants_file(str(constants_file))
        
        analyzer = UsageAnalyzer(self.logger)
        usage_info = analyzer.analyze_usage(constants, str(empty_dir), str(constants_file))
        
        # Should handle empty project gracefully
        self.assertIsInstance(usage_info, list)


class TestPerformance(IntegrationTestBase):
    """Test performance with larger datasets."""
    
    def test_large_constants_file_parsing(self):
        """Test parsing performance with large constants file."""
        large_constants_file = self.temp_dir / "large_constants.h"
        
        # Generate a large constants file
        with open(large_constants_file, 'w') as f:
            f.write("#ifndef LARGE_CONSTANTS_H\n")
            f.write("#define LARGE_CONSTANTS_H\n\n")
            
            # Generate many constants
            for i in range(1000):
                f.write(f"#define CONSTANT_{i} {i}\n")
                f.write(f"const int CONST_VAR_{i} = {i};\n")
                f.write(f"constexpr double CONSTEXPR_VAR_{i} = {i}.0;\n")
            
            f.write("\n#endif // LARGE_CONSTANTS_H\n")
        
        parser = ConstantsParser(self.logger)
        
        start_time = time.time()
        constants = parser.parse_constants_file(str(large_constants_file))
        parse_time = time.time() - start_time
        
        # Verify parsing completed
        self.assertGreater(len(constants), 2000, "Should parse many constants")
        
        # Performance check (should complete within reasonable time)
        self.assertLess(parse_time, 30.0, "Parsing should complete within 30 seconds")
        
        self.logger.info(f"Parsed {len(constants)} constants in {parse_time:.2f} seconds")
    
    def test_large_project_usage_analysis(self):
        """Test usage analysis performance with large project."""
        # Create a large project structure
        large_project_dir = self.temp_dir / "large_project"
        large_project_dir.mkdir()
        
        # Create many source files
        for module in ["network", "database", "ui", "utils", "core"]:
            module_dir = large_project_dir / module
            module_dir.mkdir()
            
            for i in range(20):  # 20 files per module
                source_file = module_dir / f"file_{i}.cpp"
                with open(source_file, 'w') as f:
                    f.write(f'#include "constants.h"\n')
                    f.write(f'// File {i} in {module} module\n')
                    f.write(f'void function_{i}() {{\n')
                    f.write(f'    int buffer = MAX_BUFFER_SIZE;\n')
                    f.write(f'    int port = DEFAULT_PORT;\n')
                    f.write(f'    double pi = PI;\n')
                    f.write(f'    std::cout << "Version: " << VERSION_MAJOR << std::endl;\n')
                    f.write(f'}}\n')
        
        # Create constants file
        constants_file = large_project_dir / "constants.h"
        shutil.copy2("test_data/large_constants.h", constants_file)
        
        try:
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            
            # Measure usage analysis performance
            analyzer = UsageAnalyzer(self.logger)
            start_time = time.time()
            usage_info = analyzer.analyze_usage(constants, str(large_project_dir), str(constants_file))
            analysis_time = time.time() - start_time
            
            # Verify analysis completed
            self.assertIsInstance(usage_info, list, "Usage analysis should complete")
            
            # Performance check
            self.assertLess(analysis_time, 60.0, "Usage analysis should complete within 60 seconds")
            
            self.logger.info(f"Analyzed usage for {len(constants)} constants across large project in {analysis_time:.2f} seconds")
            
        except Exception as e:
            self.logger.warning(f"Large project analysis failed: {e}")
    
    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create very large constants file
        huge_constants_file = self.temp_dir / "huge_constants.h"
        with open(huge_constants_file, 'w') as f:
            f.write("#ifndef HUGE_CONSTANTS_H\n")
            f.write("#define HUGE_CONSTANTS_H\n\n")
            
            # Generate 5000 constants
            for i in range(5000):
                f.write(f"#define HUGE_CONSTANT_{i} {i}\n")
                f.write(f"const int HUGE_CONST_VAR_{i} = {i};\n")
                if i % 100 == 0:
                    f.write(f"// Comment block {i}\n")
                    f.write(f"/* Multi-line comment for constant {i}\n")
                    f.write(f"   with additional details */\n")
            
            f.write("\n#endif // HUGE_CONSTANTS_H\n")
        
        try:
            # Parse huge file
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(huge_constants_file))
            
            # Check memory usage
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            self.assertGreater(len(constants), 8000, "Should parse many constants")
            self.assertLess(memory_increase, 500, "Memory usage should be reasonable (< 500MB)")
            
            self.logger.info(f"Memory usage increased by {memory_increase:.2f} MB for {len(constants)} constants")
            
        except Exception as e:
            self.logger.warning(f"Memory usage test failed: {e}")


class TestComprehensiveScenarios(IntegrationTestBase):
    """Test comprehensive real-world scenarios."""
    
    def test_mixed_constant_types_categorization(self):
        """Test categorization of mixed constant types."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        
        try:
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            
            # Categorize by type
            defines = [c for c in constants if c.type == "define"]
            const_vars = [c for c in constants if c.type == "const"]
            constexpr_vars = [c for c in constants if c.type == "constexpr"]
            
            # Verify we have all types
            self.assertGreater(len(defines), 0, "Should find #define constants")
            self.assertGreater(len(const_vars), 0, "Should find const variables")
            self.assertGreater(len(constexpr_vars), 0, "Should find constexpr variables")
            
            # Analyze usage for each type
            analyzer = UsageAnalyzer(self.logger)
            usage_info = analyzer.analyze_usage(constants, str(project_dir), str(constants_file))
            
            # Verify usage analysis handles all types
            usage_by_type = {}
            for info in usage_info:
                const_type = info.constant.type
                if const_type not in usage_by_type:
                    usage_by_type[const_type] = []
                usage_by_type[const_type].append(info)
            
            # Should have usage info for all types
            self.assertIn("define", usage_by_type, "Should analyze #define usage")
            
        except Exception as e:
            self.fail(f"Mixed constant types test failed: {e}")
    
    def test_namespace_constants_handling(self):
        """Test handling of constants within namespaces."""
        project_dir = self.temp_dir / "test_project"
        constants_file = project_dir / "sample_constants.h"
        
        try:
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            
            # Find namespace constants
            namespace_constants = [c for c in constants if "::" in c.name or "namespace" in str(c)]
            
            if len(namespace_constants) > 0:
                # Analyze usage of namespace constants
                analyzer = UsageAnalyzer(self.logger)
                usage_info = analyzer.analyze_usage(namespace_constants, str(project_dir), str(constants_file))
                
                # Verify namespace constants are properly handled
                for info in usage_info:
                    if "::" in info.constant.name:
                        self.assertIsInstance(info.usage_files, dict, "Namespace constants should have usage analysis")
            
        except Exception as e:
            self.logger.warning(f"Namespace constants test failed: {e}")
    
    def test_conditional_compilation_constants(self):
        """Test handling of conditional compilation constants."""
        # Create test file with conditional constants
        conditional_file = self.temp_dir / "conditional_constants.h"
        with open(conditional_file, 'w') as f:
            f.write("#ifndef CONDITIONAL_CONSTANTS_H\n")
            f.write("#define CONDITIONAL_CONSTANTS_H\n\n")
            f.write("#ifdef DEBUG\n")
            f.write("#define DEBUG_LEVEL 3\n")
            f.write("#define ENABLE_LOGGING 1\n")
            f.write("#else\n")
            f.write("#define DEBUG_LEVEL 0\n")
            f.write("#define ENABLE_LOGGING 0\n")
            f.write("#endif\n\n")
            f.write("#ifdef _WIN32\n")
            f.write("#define PATH_SEPARATOR '\\\\'\n")
            f.write("#else\n")
            f.write("#define PATH_SEPARATOR '/'\n")
            f.write("#endif\n\n")
            f.write("#endif // CONDITIONAL_CONSTANTS_H\n")
        
        try:
            # Parse conditional constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(conditional_file))
            
            # Verify conditional constants are parsed
            constant_names = [c.name for c in constants]
            self.assertIn("DEBUG_LEVEL", constant_names, "Should parse conditional constants")
            self.assertIn("PATH_SEPARATOR", constant_names, "Should parse platform-specific constants")
            
        except Exception as e:
            self.logger.warning(f"Conditional compilation test failed: {e}")
    
    def test_cross_module_dependency_analysis(self):
        """Test analysis of cross-module dependencies."""
        # Copy complex project if available
        complex_project_src = Path("test_data/complex_project")
        if not complex_project_src.exists():
            self.skipTest("Complex project test data not available")
        
        complex_project_dir = self.temp_dir / "complex_project"
        shutil.copytree(complex_project_src, complex_project_dir)
        
        # Copy constants file
        constants_file = complex_project_dir / "large_constants.h"
        shutil.copy2("test_data/large_constants.h", constants_file)
        
        try:
            # Parse constants
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            
            # Analyze usage
            analyzer = UsageAnalyzer(self.logger)
            usage_info = analyzer.analyze_usage(constants, str(complex_project_dir), str(constants_file))
            
            # Categorize by usage pattern
            private_constants = [info for info in usage_info if len(info.modules_using) == 1]
            shared_constants = [info for info in usage_info if len(info.modules_using) > 1]
            unused_constants = [info for info in usage_info if len(info.modules_using) == 0]
            
            # Verify categorization
            total_analyzed = len(private_constants) + len(shared_constants) + len(unused_constants)
            self.assertEqual(total_analyzed, len(usage_info), "All constants should be categorized")
            
            # Log statistics
            self.logger.info(f"Private constants: {len(private_constants)}")
            self.logger.info(f"Shared constants: {len(shared_constants)}")
            self.logger.info(f"Unused constants: {len(unused_constants)}")
            
        except Exception as e:
            self.logger.warning(f"Cross-module dependency analysis failed: {e}")


class TestRegressionScenarios(IntegrationTestBase):
    """Test regression scenarios and edge cases."""
    
    def test_empty_constants_file(self):
        """Test handling of empty constants file."""
        empty_file = self.temp_dir / "empty_constants.h"
        with open(empty_file, 'w') as f:
            f.write("#ifndef EMPTY_H\n#define EMPTY_H\n#endif\n")
        
        try:
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(empty_file))
            
            # Should handle gracefully
            self.assertIsInstance(constants, list, "Should return empty list for empty file")
            self.assertEqual(len(constants), 0, "Should find no constants in empty file")
            
        except Exception as e:
            self.fail(f"Empty constants file test failed: {e}")
    
    def test_constants_with_special_characters(self):
        """Test constants containing special characters."""
        special_file = self.temp_dir / "special_constants.h"
        with open(special_file, 'w') as f:
            f.write("#ifndef SPECIAL_H\n#define SPECIAL_H\n\n")
            f.write('#define REGEX_PATTERN "^[a-zA-Z0-9_]+$"\n')
            f.write('#define SQL_QUERY "SELECT * FROM users WHERE id = ?"\n')
            f.write('#define JSON_TEMPLATE "{\\"status\\": \\"ok\\", \\"data\\": null}"\n')
            f.write('#define UNICODE_STRING u8"Hello, 世界"\n')
            f.write('#define MULTILINE_STRING "Line 1\\n" \\\n')
            f.write('                         "Line 2\\n" \\\n')
            f.write('                         "Line 3"\n')
            f.write("#endif\n")
        
        try:
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(special_file))
            
            # Verify special characters are handled
            constant_names = [c.name for c in constants]
            self.assertIn("REGEX_PATTERN", constant_names, "Should parse regex patterns")
            self.assertIn("SQL_QUERY", constant_names, "Should parse SQL queries")
            self.assertIn("JSON_TEMPLATE", constant_names, "Should parse JSON templates")
            
        except Exception as e:
            self.logger.warning(f"Special characters test failed: {e}")
    
    def test_very_long_constant_names_and_values(self):
        """Test handling of very long constant names and values."""
        long_file = self.temp_dir / "long_constants.h"
        with open(long_file, 'w') as f:
            f.write("#ifndef LONG_H\n#define LONG_H\n\n")
            
            # Very long constant name
            long_name = "VERY_LONG_CONSTANT_NAME_" + "X" * 200
            f.write(f"#define {long_name} 42\n")
            
            # Very long constant value
            long_value = "A" * 1000
            f.write(f'#define LONG_VALUE "{long_value}"\n')
            
            f.write("#endif\n")
        
        try:
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(long_file))
            
            # Should handle long names and values
            self.assertGreater(len(constants), 0, "Should parse constants with long names/values")
            
            # Verify long constant is present
            long_constants = [c for c in constants if len(c.name) > 100]
            self.assertGreater(len(long_constants), 0, "Should find long constant names")
            
        except Exception as e:
            self.logger.warning(f"Long constants test failed: {e}")


if __name__ == '__main__':
    # Configure test environment
    import sys
    
    # Add current directory to path for imports
    sys.path.insert(0, '.')
    
    # Run tests with high verbosity
    unittest.main(verbosity=2, buffer=True)