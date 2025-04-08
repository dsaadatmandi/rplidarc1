"""
RPLidarC1 - A Python library for interfacing with the RPLidar C1 360-degree laser scanner.

This library provides an asynchronous API for controlling the RPLidar device and
processing scan data.
"""

from .scanner import RPLidar
from .protocol import (
    CommonBytes,
    RequestBytes,
    ResponseBytes,
    ResponseMode,
    HealthStatus,
    Request,
    Response,
)
from .serial_handler import SerialConnection
from .utils import ByteEnum

__version__ = "0.1.0"
__all__ = [
    "RPLidar",
    "CommonBytes",
    "RequestBytes",
    "ResponseBytes",
    "ResponseMode",
    "HealthStatus",
    "Request",
    "Response",
    "SerialConnection",
    "ByteEnum",
]
