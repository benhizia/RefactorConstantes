#!/usr/bin/env python3
"""
Comprehensive integration test runner for C++ Constants Refactor Tool
Executes all integration tests with detailed reporting and performance metrics
"""

import unittest
import sys
import time
import json
import os
from pathlib import Path
from io import StringIO

def setup_test_environment():
    """Set up the test environment."""
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Ensure test data directory exists
    test_data_dir = current_dir / "test_data"
    if not test_data_dir.exists():
        print("ERROR: test_data directory not found!")
        return False
    
    # Check for required test files
    required_files = [
        "test_data/sample_constants.h",
        "test_data/large_constants.h",
        "test_data/edge_cases_constants.h",
        "test_data/CMakeLists.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("WARNING: Missing test files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("Some tests may be skipped.")
    
    return True

def run_integration_tests():
    """Run all integration tests with comprehensive reporting."""
    print("=" * 80)
    print("C++ Constants Refactor Tool - Integration Test Suite")
    print("=" * 80)
    
    # Setup environment
    if not setup_test_environment():
        return False
    
    # Import test modules
    try:
        from test_integration import (
            TestEndToEndPipeline,
            TestErrorHandling,
            TestPerformance,
            TestComprehensiveScenarios,
            TestRegressionScenarios
        )
    except ImportError as e:
        print(f"ERROR: Failed to import test modules: {e}")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestEndToEndPipeline,
        TestErrorHandling,
        TestPerformance,
        TestComprehensiveScenarios,
        TestRegressionScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True,
        failfast=False
    )
    
    print(f"Running {test_suite.countTestCases()} integration tests...")
    print("-" * 80)
    
    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    
    # Detailed failure/error reporting
    if result.failures:
        print("\nFAILURES:")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"FAIL: {test}")
            print(traceback)
            print("-" * 40)
    
    if result.errors:
        print("\nERRORS:")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"ERROR: {test}")
            print(traceback)
            print("-" * 40)
    
    # Generate JSON report
    generate_test_report(result, end_time - start_time)
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0

def generate_test_report(result, total_time):
    """Generate a JSON test report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_time": total_time,
        "summary": {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
        },
        "failures": [
            {
                "test": str(test),
                "traceback": traceback
            }
            for test, traceback in result.failures
        ],
        "errors": [
            {
                "test": str(test),
                "traceback": traceback
            }
            for test, traceback in result.errors
        ]
    }
    
    # Write report to file
    report_file = Path("integration_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed test report saved to: {report_file}")

def run_specific_test_class(class_name):
    """Run tests from a specific test class."""
    print(f"Running tests from class: {class_name}")
    
    # Setup environment
    if not setup_test_environment():
        return False
    
    try:
        import test_integration
        
        # Get the test class
        test_class = getattr(test_integration, class_name, None)
        if not test_class:
            print(f"ERROR: Test class '{class_name}' not found")
            return False
        
        # Run the specific test class
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except ImportError as e:
        print(f"ERROR: Failed to import test modules: {e}")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test class
        class_name = sys.argv[1]
        success = run_specific_test_class(class_name)
    else:
        # Run all tests
        success = run_integration_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()