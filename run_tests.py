#!/usr/bin/env python3
"""
Script to run the RPLidarC1 tests.

This script provides a convenient way to run the tests for the RPLidarC1 library.
It checks for the required dependencies and runs the tests using pytest.
"""

import subprocess
import sys
import os


def check_dependencies():
    """
    Check if the required dependencies are installed.

    Returns:
        bool: True if all dependencies are installed, False otherwise.
    """
    try:
        import pytest
        import pytest_asyncio
        import serial

        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install the required dependencies:")
        print("  pip install -r requirements.txt")
        return False


def run_tests():
    """
    Run the tests using pytest.

    Returns:
        int: The exit code from pytest.
    """
    print("Running RPLidarC1 tests...")

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Change to the script directory
    os.chdir(script_dir)

    # Run pytest with the specified arguments
    result = subprocess.run(
        ["pytest", "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Print the output
    print(result.stdout)
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    if check_dependencies():
        sys.exit(run_tests())
    else:
        sys.exit(1)
