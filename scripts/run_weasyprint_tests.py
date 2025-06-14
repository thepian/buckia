#!/usr/bin/env python3
"""
Run WeasyPrint Integration Tests

This script runs the WeasyPrint integration tests to verify that we can generate
PDF files at the level of WeasyPrint samples.
"""

import sys
import subprocess
import os
from pathlib import Path


def main():
    """Run the WeasyPrint integration tests"""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Running WeasyPrint Integration Tests")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        subprocess.run([sys.executable, "-c", "import pytest"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
    
    # Check if requests is available
    try:
        subprocess.run([sys.executable, "-c", "import requests"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ requests not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    
    # Run the tests
    test_file = "tests/test_weasyprint_integration.py"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    print(f"🚀 Running tests from {test_file}")
    print()
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        test_file,
        "-v",
        "--tb=short",
        "--capture=no",  # Show print statements
        "-s"  # Don't capture stdout
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print()
            print("✅ All tests passed!")
            print()
            print("📋 Test Summary:")
            print("- ✅ Reference files downloaded")
            print("- ✅ HTML structure validation")
            print("- ✅ PDF generation with Buckia")
            print("- ✅ Visual comparison (smoke test)")
            print("- ✅ WeasyPrint warnings detection")
            
        else:
            print()
            print("❌ Some tests failed!")
            print("Check the output above for details.")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
