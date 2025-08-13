#!/usr/bin/env python3
"""
Simple integration test to verify the test setup is working
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, '.')

from constants_refactor import ConstantsParser, Logger

class SimpleIntegrationTest(unittest.TestCase):
    """Simple integration test to verify basic functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = Logger("SimpleTest", "INFO")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_parse_sample_constants(self):
        """Test parsing the sample constants file."""
        constants_file = Path("test_data/sample_constants.h")
        
        if not constants_file.exists():
            self.skipTest("Sample constants file not found")
        
        try:
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(constants_file))
            
            # Basic validation
            self.assertIsInstance(constants, list, "Should return a list of constants")
            self.assertGreater(len(constants), 10, "Should find multiple constants")
            
            # Check for specific constants
            constant_names = [c.name for c in constants]
            self.assertIn("MAX_BUFFER_SIZE", constant_names, "Should find MAX_BUFFER_SIZE")
            self.assertIn("DEFAULT_PORT", constant_names, "Should find DEFAULT_PORT")
            
            print(f"✓ Successfully parsed {len(constants)} constants")
            
        except Exception as e:
            self.fail(f"Failed to parse constants: {e}")
    
    def test_parse_large_constants(self):
        """Test parsing the large constants file."""
        large_constants_file = Path("test_data/large_constants.h")
        
        if not large_constants_file.exists():
            self.skipTest("Large constants file not found")
        
        try:
            parser = ConstantsParser(self.logger)
            constants = parser.parse_constants_file(str(large_constants_file))
            
            # Should have 100+ constants
            self.assertGreaterEqual(len(constants), 100, "Should have 100+ constants in large file")
            
            print(f"✓ Successfully parsed {len(constants)} constants from large file")
            
        except Exception as e:
            self.fail(f"Failed to parse large constants: {e}")

if __name__ == '__main__':
    print("Running simple integration test...")
    unittest.main(verbosity=2)