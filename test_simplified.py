#!/usr/bin/env python3
"""
Simple test for simplified_cst_refactor.py

Just validates that the basic functionality works.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Import the module to test
from simplified_cst_refactor import SimplifiedConstantsRefactor, Constant


def test_extract_constants():
    """Test that we can extract constants from a file."""
    print("[TEST 1] Extract constants from file")

    # Create a temporary constants file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False, encoding='utf-8') as f:
        f.write("""
// Test constants file
#define MAX_SIZE 100
#define MIN_SIZE 10
const int DEFAULT_VALUE = 42;
constexpr int BUFFER_SIZE = 1024;
        """)
        temp_file = f.name

    try:
        analyzer = SimplifiedConstantsRefactor(temp_file, '.')
        constants = analyzer.extract_constants()

        assert len(constants) >= 4, f"Expected at least 4 constants, got {len(constants)}"
        names = [c.name for c in constants]
        assert 'MAX_SIZE' in names, "MAX_SIZE not found"
        assert 'MIN_SIZE' in names, "MIN_SIZE not found"
        assert 'DEFAULT_VALUE' in names, "DEFAULT_VALUE not found"
        assert 'BUFFER_SIZE' in names, "BUFFER_SIZE not found"

        print("   [PASS] Extracted constants correctly")
        return True

    finally:
        Path(temp_file).unlink()


def test_find_modules():
    """Test that we can find modules (3-5 letter directories)."""
    print("\n[TEST 2] Find modules in project")

    # Create a temporary directory structure
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create some module directories (3-5 letters)
        (temp_dir / 'core').mkdir()
        (temp_dir / 'net').mkdir()
        (temp_dir / 'ui').mkdir()
        (temp_dir / 'data').mkdir()

        # Create some non-module directories
        (temp_dir / 'documentation').mkdir()  # Too long
        (temp_dir / 'ab').mkdir()  # Too short
        (temp_dir / 'build').mkdir()  # Valid length but still should be found

        analyzer = SimplifiedConstantsRefactor('dummy.h', str(temp_dir))
        modules = analyzer.find_modules()

        assert len(modules) >= 4, f"Expected at least 4 modules, got {len(modules)}: {modules}"
        # Check that we found most of the expected modules
        expected = ['core', 'net', 'ui', 'data']
        found_count = sum(1 for m in expected if m in modules)
        assert found_count >= 3, f"Expected at least 3 of {expected}, found {found_count}"

        print(f"   [PASS] Found {len(modules)} modules correctly")
        return True

    finally:
        shutil.rmtree(temp_dir)


def test_full_analysis():
    """Test a complete analysis run."""
    print("\n[TEST 3] Full analysis on test data")

    # Use the real test data if it exists
    test_constants = Path('test_data/sample_constants.h')
    test_project = Path('test_data')

    if not test_constants.exists():
        print("   [SKIP] test_data/sample_constants.h not found")
        return True

    analyzer = SimplifiedConstantsRefactor(str(test_constants), str(test_project))
    result = analyzer.run()

    assert result is not None, "Analysis returned None"
    assert 'unused' in result, "Result missing 'unused' category"
    assert 'shared' in result, "Result missing 'shared' category"

    print("   [PASS] Full analysis completed")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("RUNNING SIMPLIFIED CONSTANTS REFACTOR TESTS")
    print("="*80 + "\n")

    tests = [
        test_extract_constants,
        test_find_modules,
        test_full_analysis,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"   [FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"   [ERROR] {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80 + "\n")

    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
