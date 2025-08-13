#!/usr/bin/env python3
"""
Test runner for the C++ Constants Refactor Tool

Runs both unit tests and integration tests with proper setup and reporting.
"""

import sys
import unittest
import argparse
import os
from pathlib import Path


def setup_test_environment():
    """Set up the test environment."""
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Verify test data exists
    test_data_dir = current_dir / "test_data"
    if not test_data_dir.exists():
        print("Warning: test_data directory not found. Some integration tests may be skipped.")
    
    return True


def run_unit_tests():
    """Run unit tests."""
    print("=" * 60)
    print("Running Unit Tests")
    print("=" * 60)
    
    try:
        # Import and run unit tests
        from test_constants_refactor import (
            TestConstantsParser, TestUsageAnalyzer, TestCMakeAnalyzer,
            TestFileGenerator, TestErrorHandling, TestLogger
        )
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add unit test classes
        suite.addTests(loader.loadTestsFromTestCase(TestConstantsParser))
        suite.addTests(loader.loadTestsFromTestCase(TestUsageAnalyzer))
        suite.addTests(loader.loadTestsFromTestCase(TestCMakeAnalyzer))
        suite.addTests(loader.loadTestsFromTestCase(TestFileGenerator))
        suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestLogger))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing unit tests: {e}")
        print("Make sure test_constants_refactor.py exists and is valid.")
        return False
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False


def run_integration_tests():
    """Run integration tests."""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)
    
    try:
        # Import and run integration tests
        from test_integration import (
            TestEndToEndPipeline, TestErrorHandling, TestPerformance
        )
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add integration test classes
        suite.addTests(loader.loadTestsFromTestCase(TestEndToEndPipeline))
        suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing integration tests: {e}")
        print("Make sure test_integration.py exists and is valid.")
        return False
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False


def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"Running specific test: {test_name}")
    
    try:
        # Try to load and run the specific test
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for C++ Constants Refactor Tool")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--test", type=str, help="Run specific test by name")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    # Set up test environment
    if not setup_test_environment():
        print("Failed to set up test environment")
        return 1
    
    # List available tests
    if args.list:
        print("Available test categories:")
        print("  --unit: Unit tests for individual components")
        print("  --integration: End-to-end integration tests")
        print("\nSpecific tests can be run with --test <test_name>")
        print("Example: --test test_integration.TestEndToEndPipeline.test_complete_pipeline_sandbox_mode")
        return 0
    
    success = True
    
    # Run specific test
    if args.test:
        success = run_specific_test(args.test)
    
    # Run unit tests
    elif args.unit:
        success = run_unit_tests()
    
    # Run integration tests
    elif args.integration:
        success = run_integration_tests()
    
    # Run all tests by default
    else:
        print("Running all tests...")
        unit_success = run_unit_tests()
        integration_success = run_integration_tests()
        success = unit_success and integration_success
    
    # Print summary
    print("\n" + "=" * 60)
    if success:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())