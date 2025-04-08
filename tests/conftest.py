"""
Pytest configuration and fixtures for the RPLidarC1 tests.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_serial():
    """
    Fixture that provides a mock serial connection.

    This mock can be used to simulate serial communication without
    requiring actual hardware.
    """
    mock = MagicMock()
    mock.read.return_value = (
        b"\xa5\x5a\x05\x00\x00\x00\x40"  # Default response descriptor
    )
    mock.in_waiting = 10  # Default number of bytes waiting
    mock.is_open = True
    return mock


@pytest.fixture
def mock_lidar_response():
    """
    Fixture that provides mock response data for the RPLidar device.

    This can be used to simulate different types of responses from the device.
    """
    # Default health response (status: good)
    health_response = b"\x00\x00\x00"

    # Default scan response (quality: 15, angle: 45.33, distance: 1250mm)
    scan_response = b"\x3c\x5b\x01\x22\x01"

    return {"health": health_response, "scan": scan_response}


@pytest.fixture
def event_loop():
    """
    Fixture that provides an event loop for asyncio tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_queue():
    """
    Fixture that provides a mock asyncio Queue.
    """
    queue = MagicMock(spec=asyncio.Queue)
    queue.empty.return_value = False

    async def mock_get():
        return {"a_deg": 45.33, "d_mm": 1250, "q": 15}

    async def mock_put(x):
        return None

    queue.get = mock_get
    queue.put = mock_put
    queue.task_done = MagicMock()
    return queue


@pytest.fixture
def mock_stop_event():
    """
    Fixture that provides a mock asyncio Event for stopping operations.
    """
    event = MagicMock(spec=asyncio.Event)
    event.is_set.return_value = False
    event.set = MagicMock()
    event.clear = MagicMock()
    return event
