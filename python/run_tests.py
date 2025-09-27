#!/usr/bin/env python3
"""Simple test runner for the PvPoke Python test suite."""

import sys
import unittest
from pathlib import Path

def run_all_tests():
    """Run all tests in the test directory."""
    # Get the test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern="test_*.py")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on success
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
