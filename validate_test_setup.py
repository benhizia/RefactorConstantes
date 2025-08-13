#!/usr/bin/env python3
"""
Validation script to check if the test environment is properly set up.
"""

import os
import sys
from pathlib import Path
import json


def check_file_exists(file_path, description):
    """Check if a file exists and report the result."""
    path = Path(file_path)
    if path.exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (NOT FOUND)")
        return False


def check_directory_structure():
    """Check if the test directory structure is correct."""
    print("Checking test directory structure...")
    
    required_files = [
        ("constants_refactor.py", "Main implementation file"),
        ("test_constants_refactor.py", "Unit tests"),
        ("test_integration.py", "Integration tests"),
        ("run_tests.py", "Test runner"),
        ("test_config.json", "Test configuration"),
        ("test_data/sample_constants.h", "Sample constants file"),
        ("test_data/CMakeLists.txt", "Test project CMake file"),
        ("test_data/src/main.cpp", "Test main file"),
        ("test_data/src/network/network_manager.cpp", "Network module source"),
        ("test_data/src/config/config_loader.cpp", "Config module source"),
        ("test_data/src/utils/file_utils.cpp", "Utils module source"),
    ]
    
    additional_files = [
        ("test_data/large_constants.h", "Large constants file (100+ constants)"),
        ("test_data/edge_cases_constants.h", "Edge cases constants file"),
        ("test_data/complex_project/CMakeLists.txt", "Complex project CMake file"),
        ("test_data/simple_project/CMakeLists.txt", "Simple project CMake file"),
        ("run_integration_tests.py", "Integration test runner"),
    ]
    
    all_exist = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    print("\nChecking additional test files...")
    additional_count = 0
    for file_path, description in additional_files:
        if check_file_exists(file_path, description):
            additional_count += 1
    
    print(f"Found {additional_count}/{len(additional_files)} additional test files")
    
    return all_exist


def check_test_data_content():
    """Check if test data files have expected content."""
    print("\nChecking test data content...")
    
    # Check sample constants file
    constants_file = Path("test_data/sample_constants.h")
    if constants_file.exists():
        with open(constants_file, 'r') as f:
            content = f.read()
        
        # Check for expected constants
        expected_constants = [
            "MAX_BUFFER_SIZE", "DEFAULT_PORT", "ARRAY_SIZE", 
            "COMPILE_TIME_CONSTANT", "VERSION_MAJOR"
        ]
        
        found_constants = []
        for const in expected_constants:
            if const in content:
                found_constants.append(const)
        
        print(f"✓ Found {len(found_constants)}/{len(expected_constants)} expected constants")
        
        if len(found_constants) < len(expected_constants):
            missing = set(expected_constants) - set(found_constants)
            print(f"  Missing constants: {', '.join(missing)}")
    
    # Check large constants file
    large_constants_file = Path("test_data/large_constants.h")
    if large_constants_file.exists():
        with open(large_constants_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        define_count = len([line for line in lines if line.strip().startswith('#define')])
        const_count = len([line for line in lines if 'const ' in line and '=' in line])
        constexpr_count = len([line for line in lines if 'constexpr ' in line])
        
        total_constants = define_count + const_count + constexpr_count
        print(f"✓ Large constants file: {total_constants} total constants ({define_count} #defines, {const_count} const, {constexpr_count} constexpr)")
        
        if total_constants < 100:
            print(f"⚠ Warning: Large constants file has only {total_constants} constants (expected 100+)")
    
    # Check CMakeLists.txt files
    cmake_files = [
        "test_data/CMakeLists.txt",
        "test_data/complex_project/CMakeLists.txt",
        "test_data/simple_project/CMakeLists.txt"
    ]
    
    for cmake_file_path in cmake_files:
        cmake_file = Path(cmake_file_path)
        if cmake_file.exists():
            with open(cmake_file, 'r') as f:
                content = f.read()
            
            if "CMAKE_EXPORT_COMPILE_COMMANDS" in content:
                print(f"✓ {cmake_file_path} has compile commands export enabled")
            else:
                print(f"⚠ {cmake_file_path} missing compile commands export")
    
    # Check that test projects use constants
    test_projects = [
        ("test_data/src", "Main test project"),
        ("test_data/complex_project/src", "Complex test project"),
        ("test_data/simple_project", "Simple test project")
    ]
    
    for project_path, project_name in test_projects:
        project_dir = Path(project_path)
        if project_dir.exists():
            cpp_files = list(project_dir.rglob("*.cpp"))
            files_with_constants = 0
            
            for cpp_file in cpp_files:
                try:
                    with open(cpp_file, 'r') as f:
                        content = f.read()
                        if any(const in content for const in ['MAX_BUFFER_SIZE', 'DEFAULT_PORT', 'VERSION_MAJOR']):
                            files_with_constants += 1
                except:
                    pass
            
            if cpp_files:
                print(f"✓ {project_name}: {files_with_constants}/{len(cpp_files)} files use constants")
            else:
                print(f"⚠ {project_name}: No .cpp files found")


def check_python_imports():
    """Check if required Python modules can be imported."""
    print("\nChecking Python imports...")
    
    required_modules = [
        "unittest", "tempfile", "shutil", "json", "subprocess", 
        "pathlib", "argparse", "os", "sys"
    ]
    
    optional_modules = [
        "pygccxml"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (REQUIRED)")
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module} (optional)")
        except ImportError:
            print(f"⚠ {module} (optional, some tests may be skipped)")


def check_test_config():
    """Check if test configuration is valid."""
    print("\nChecking test configuration...")
    
    config_file = Path("test_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check required sections
            required_sections = ["test_configurations", "module_mappings", "test_settings"]
            for section in required_sections:
                if section in config:
                    print(f"✓ Config section: {section}")
                else:
                    print(f"✗ Config section: {section} (MISSING)")
            
        except json.JSONDecodeError as e:
            print(f"✗ Test config JSON is invalid: {e}")
    else:
        print("✗ Test config file not found")


def main():
    """Main validation function."""
    print("Validating C++ Constants Refactor Tool Test Setup")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Check directory structure
    if not check_directory_structure():
        all_checks_passed = False
    
    # Check test data content
    check_test_data_content()
    
    # Check Python imports
    check_python_imports()
    
    # Check test configuration
    check_test_config()
    
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ Test setup validation PASSED!")
        print("\nYou can now run tests with:")
        print("  python run_tests.py                 # Run all tests")
        print("  python run_tests.py --unit          # Run unit tests only")
        print("  python run_tests.py --integration   # Run integration tests only")
        return 0
    else:
        print("✗ Test setup validation FAILED!")
        print("\nPlease fix the issues above before running tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())