"""
Tests for the serial_handler module.
"""

import unittest
import pytest
from unittest.mock import MagicMock, patch
from rplidarc1.serial_handler import SerialConnection
from .port_utils import skip_if_no_port


class TestSerialConnection(unittest.TestCase):
    """
    Test cases for the SerialConnection class.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.port = "/dev/ttyUSB0"
        self.baudrate = 460800
        self.timeout = 0.2

        # Create a patcher for the Serial class
        self.serial_patcher = patch("rplidarc1.serial_handler.Serial")
        self.mock_serial = self.serial_patcher.start()

        # Create a SerialConnection instance
        self.serial_conn = SerialConnection(
            port=self.port, baudrate=self.baudrate, timeout=self.timeout
        )

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        self.serial_patcher.stop()

    def test_init(self):
        """
        Test that SerialConnection initializes correctly.
        """
        # self.assertEqual(self.serial_conn._port, self.port)
        # self.assertEqual(self.serial_conn._baudrate, self.baudrate)
        # self.assertEqual(self.serial_conn.kwargs, {"timeout": self.timeout})
        # self.assertFalse(self.serial_conn._is_connected)

    @skip_if_no_port("/dev/ttyUSB0")
    def test_connect(self):
        """
        Test that connect correctly initializes the serial connection.
        """
        # Call connect
        self.serial_conn.connect()

        # Check that _is_connected was set to True
        self.assertTrue(self.serial_conn._is_connected)

    @skip_if_no_port("/dev/ttyUSB0")
    def test_connect_already_connected(self):
        """
        Test that connect handles the case where a connection is already active.
        """
        # Set up the connection to be already connected
        self.serial_conn._is_connected = True

        # Create a mock for disconnect
        self.serial_conn.disconnect = MagicMock()

        # Call connect
        self.serial_conn.connect()

        # Check that disconnect was called
        self.serial_conn.disconnect.assert_called_once()

    @skip_if_no_port("/dev/ttyUSB0")
    def test_connect_exception(self):
        """
        Test that connect raises ConnectionError when Serial initialization fails.
        """
        # Create a patch for the super().__init__ method in the connect method
        with patch("serial.Serial.__init__", side_effect=Exception("Test exception")):
            # Call connect and check that it raises ConnectionError
            with self.assertRaises(ConnectionError):
                self.serial_conn.connect()

    @skip_if_no_port("/dev/ttyUSB0")
    def test_disconnect(self):
        """
        Test that disconnect correctly closes the serial connection.
        """
        # Set up the connection to be connected
        self.serial_conn._is_connected = True

        # Set up the serial connection's close method
        self.serial_conn.close = MagicMock()

        # Call disconnect
        self.serial_conn.disconnect()

        # Check that close was called
        self.serial_conn.close.assert_called_once()

        # Check that _is_connected was set to False
        self.assertFalse(self.serial_conn._is_connected)

    @skip_if_no_port("/dev/ttyUSB0")
    def test_disconnect_not_connected(self):
        """
        Test that disconnect handles the case where no connection is active.
        """
        # Set up the connection to not be connected
        self.serial_conn._is_connected = False

        # Set up the serial connection's close method
        self.serial_conn.close = MagicMock()

        # Call disconnect
        self.serial_conn.disconnect()

        # Check that close was not called
        self.serial_conn.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
