import os
import pytest

"""
Utility functions for handling port availability in RPLidar tests.
"""


def is_port_available(port_path):
    """
    Check if a serial port is available on the system.

    This function first checks the RPLIDAR_PORT_AVAILABLE environment variable.
    If it's set to "0", it returns False regardless of whether the port exists.
    This is useful for CI/CD environments where we want to skip port-dependent tests.

    Args:
        port_path (str): The path to the serial port (e.g., "/dev/ttyUSB0").

    Returns:
        bool: True if the port exists and is available, False otherwise.
    """
    # Check environment variable first
    env_available = os.environ.get("RPLIDAR_PORT_AVAILABLE")
    if env_available == "0":
        return False

    # Otherwise check if the port actually exists
    return os.path.exists(port_path)


def skip_if_no_port(port_path):
    """
    Decorator to skip a test if the specified port is not available.

    Args:
        port_path (str): The path to the serial port (e.g., "/dev/ttyUSB0").

    Returns:
        function: A decorator that skips the test if the port is not available.
    """
    return pytest.mark.skipif(
        not is_port_available(port_path), reason=f"Port {port_path} is not available"
    )
