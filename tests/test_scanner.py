"""
Tests for the scanner module.
"""

import unittest
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from rplidarc1.scanner import RPLidar
from rplidarc1 import protocol


class TestRPLidar(unittest.TestCase):
    """
    Test cases for the RPLidar class.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create patchers for the dependencies
        self.serial_patcher = patch("rplidarc1.scanner.SerialConnection")
        self.request_patcher = patch("rplidarc1.scanner.Request")
        self.response_patcher = patch("rplidarc1.scanner.Response")

        # Start the patchers
        self.mock_serial_class = self.serial_patcher.start()
        self.mock_request = self.request_patcher.start()
        self.mock_response = self.response_patcher.start()

        # Set up the mock serial connection
        self.mock_serial = MagicMock()
        self.mock_serial_class.return_value = self.mock_serial

        # Set up the mock response
        self.mock_response.parse_response_descriptor.return_value = (
            3,
            protocol.ResponseMode.SINGLE_RESPONSE,
        )
        self.mock_response.handle_response.return_value = (
            b"\x00\x00\x00"  # Good health status
        )

        # Create an RPLidar instance
        self.lidar = RPLidar(port="/dev/ttyUSB0", baudrate=460800, timeout=0.2)

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        self.serial_patcher.stop()
        self.request_patcher.stop()
        self.response_patcher.stop()

    def test_init(self):
        """
        Test that RPLidar initializes correctly.
        """
        # Check that SerialConnection was initialized with the correct parameters
        self.mock_serial_class.assert_called_once_with(
            "/dev/ttyUSB0", 460800, timeout=0.2
        )

        # Check that the serial connection was connected
        self.mock_serial.connect.assert_called_once()

        # Check that healthcheck was called
        self.mock_request.create_request.assert_called_once_with(
            protocol.RequestBytes.GET_HEALTH_BYTE
        )
        self.mock_request.send_request.assert_called_once()
        self.mock_response.parse_response_descriptor.assert_called_once()
        self.mock_response.handle_response.assert_called_once()

        # Check that the stop event and output queue were created
        self.assertIsInstance(self.lidar.stop_event, asyncio.Event)
        self.assertIsInstance(self.lidar.output_queue, asyncio.Queue)
        self.assertIsNone(self.lidar.output_dict)

    def test_healthcheck(self):
        """
        Test that healthcheck correctly checks the health status of the device.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()
        self.mock_response.reset_mock()

        # Call healthcheck
        self.lidar.healthcheck()

        # Check that the request was created and sent
        self.mock_request.create_request.assert_called_once_with(
            protocol.RequestBytes.GET_HEALTH_BYTE
        )
        self.mock_request.send_request.assert_called_once_with(
            self.mock_serial, self.mock_request.create_request.return_value
        )

        # Check that the response was parsed
        self.mock_response.parse_response_descriptor.assert_called_once_with(
            self.mock_serial
        )
        self.mock_response.handle_response.assert_called_once_with(
            serial=self.mock_serial, length=3
        )

    def test_healthcheck_no_response(self):
        """
        Test that healthcheck raises ConnectionError when no response is received.
        """
        # Set up the mock to return None for handle_response
        self.mock_response.handle_response.return_value = None

        # Call healthcheck and check that it raises ConnectionError
        with self.assertRaises(ConnectionError):
            self.lidar.healthcheck()

    def test_healthcheck_wrong_type(self):
        """
        Test that healthcheck raises TypeError when the response is not bytes.
        """
        # Set up the mock to return a non-bytes value for handle_response
        self.mock_response.handle_response.return_value = "not bytes"

        # Call healthcheck and check that it raises TypeError
        with self.assertRaises(TypeError):
            self.lidar.healthcheck()

    def test_healthcheck_error_status(self):
        """
        Test that healthcheck raises Exception when the device reports an error.
        """
        # Set up the mock to return an error status
        self.mock_response.handle_response.return_value = (
            b"\x02\x00\x00"  # Error status
        )

        # Call healthcheck and check that it raises Exception
        with self.assertRaises(Exception):
            self.lidar.healthcheck()

    def test_shutdown(self):
        """
        Test that shutdown correctly shuts down the device.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()

        # Call shutdown
        self.lidar.shutdown()

        # Check that the stop request was created and sent
        self.mock_request.create_request.assert_called_once_with(
            protocol.RequestBytes.STOP_BYTE
        )
        self.mock_request.send_request.assert_called_once_with(
            self.mock_serial, self.mock_request.create_request.return_value
        )

        # Check that the serial connection was disconnected
        self.mock_serial.disconnect.assert_called_once()

    def test_reset(self):
        """
        Test that reset correctly resets the device.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()

        # Create a patcher for time.sleep
        with patch("rplidarc1.scanner.time.sleep") as mock_sleep:
            # Call reset
            self.lidar.reset()

            # Check that the stop request was created and sent
            self.mock_request.create_request.assert_any_call(
                protocol.RequestBytes.STOP_BYTE
            )
            self.mock_request.send_request.assert_any_call(
                self.mock_serial, self.mock_request.create_request.return_value
            )

            # Check that the reset request was created and sent
            self.mock_request.create_request.assert_any_call(
                protocol.RequestBytes.RESET_BYTE
            )

            # Check that time.sleep was called with 0.5
            mock_sleep.assert_called_once_with(0.5)

    def test_get_info_not_implemented(self):
        """
        Test that get_info raises NotImplementedError.
        """
        with self.assertRaises(NotImplementedError):
            self.lidar.get_info()

    def test_simple_scan(self):
        """
        Test that simple_scan correctly initiates a scan.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()
        self.mock_response.reset_mock()

        # Set up the mock to return a multi-response mode
        self.mock_response.parse_response_descriptor.return_value = (
            5,
            protocol.ResponseMode.MUTLI_RESPONSE,
        )

        # Create a simple coroutine object
        async def mock_coroutine():
            pass

        # Mock the handle_response to return a coroutine
        self.mock_response.handle_response.return_value = mock_coroutine()

        # Call simple_scan
        result = self.lidar.simple_scan()

        # Check that the scan request was created and sent
        self.mock_request.create_request.assert_called_once_with(
            protocol.RequestBytes.SCAN_BYTE
        )
        self.mock_request.send_request.assert_called_once_with(
            self.mock_serial, self.mock_request.create_request.return_value
        )

        # Check that the response descriptor was parsed
        self.mock_response.parse_response_descriptor.assert_called_once_with(
            self.mock_serial
        )

        # Check that handle_response was called with the correct parameters
        self.mock_response.handle_response.assert_called_once_with(
            serial=self.mock_serial,
            stop_event=self.lidar.stop_event,
            output_queue=self.lidar.output_queue,
            length=5,
            output_dict=None,
        )

        # Check that the result is a coroutine
        self.assertTrue(asyncio.iscoroutine(result))

    def test_simple_scan_with_dict(self):
        """
        Test that simple_scan correctly initializes the output dictionary.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()
        self.mock_response.reset_mock()

        # Set up the mock to return a multi-response mode
        self.mock_response.parse_response_descriptor.return_value = (
            5,
            protocol.ResponseMode.MUTLI_RESPONSE,
        )

        # Create a simple coroutine object
        async def mock_coroutine():
            pass

        # Mock the handle_response to return a coroutine
        self.mock_response.handle_response.return_value = mock_coroutine()

        # Call simple_scan with make_return_dict=True
        result = self.lidar.simple_scan(make_return_dict=True)

        # Check that the output dictionary was initialized
        self.assertIsInstance(self.lidar.output_dict, dict)

        # Check that handle_response was called with the output dictionary
        self.mock_response.handle_response.assert_called_once_with(
            serial=self.mock_serial,
            stop_event=self.lidar.stop_event,
            output_queue=self.lidar.output_queue,
            length=5,
            output_dict=self.lidar.output_dict,
        )

    def test_simple_scan_wrong_mode(self):
        """
        Test that simple_scan raises Exception when the response mode is not MUTLI_RESPONSE.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()
        self.mock_response.reset_mock()

        # Set up the mock to return a single-response mode
        self.mock_response.parse_response_descriptor.return_value = (
            5,
            protocol.ResponseMode.SINGLE_RESPONSE,
        )

        # Call simple_scan and check that it raises Exception
        with self.assertRaises(Exception):
            self.lidar.simple_scan()

    def test_simple_scan_wrong_return_type(self):
        """
        Test that simple_scan raises TypeError when handle_response does not return a coroutine.
        """
        # Reset the mocks to clear the initialization calls
        self.mock_request.reset_mock()
        self.mock_response.reset_mock()

        # Set up the mock to return a multi-response mode
        self.mock_response.parse_response_descriptor.return_value = (
            5,
            protocol.ResponseMode.MUTLI_RESPONSE,
        )

        # Set up the mock to return a non-coroutine for handle_response
        self.mock_response.handle_response.return_value = "not a coroutine"

        # Call simple_scan and check that it raises TypeError
        with self.assertRaises(TypeError):
            self.lidar.simple_scan()

    def test_clear_input_buffer(self):
        """
        Test that _clear_input_buffer correctly clears the input buffer.
        """
        # Call _clear_input_buffer
        self.lidar._clear_input_buffer()

        # Check that reset_input_buffer was called on the serial connection
        self.mock_serial.reset_input_buffer.assert_called_once()

    def test_init_return_dict(self):
        """
        Test that _init_return_dict correctly initializes the output dictionary.
        """
        # Call _init_return_dict
        self.lidar._init_return_dict()

        # Check that output_dict was initialized to an empty dictionary
        self.assertEqual(self.lidar.output_dict, {})


class TestRPLidarAsync:
    """
    Test cases for the asynchronous methods of the RPLidar class.
    """

    @pytest.mark.asyncio
    async def test_simple_scan_async(self, mock_serial, mock_stop_event, mock_queue):
        """
        Test that simple_scan correctly processes scan data asynchronously.
        """
        # Create patchers for the dependencies
        with patch(
            "rplidarc1.scanner.SerialConnection", return_value=mock_serial
        ), patch("rplidarc1.scanner.Request") as mock_request, patch(
            "rplidarc1.scanner.Response"
        ) as mock_response:
            # Set up the mock to return a multi-response mode
            mock_response.parse_response_descriptor.return_value = (
                5,
                protocol.ResponseMode.MUTLI_RESPONSE,
            )

            # Create a simple coroutine object
            async def mock_coroutine():
                await asyncio.sleep(0.1)

            # Mock the handle_response to return a coroutine
            mock_response.handle_response.return_value = mock_coroutine()

            # Create an RPLidar instance with the mocked dependencies
            lidar = RPLidar(port="/dev/ttyUSB0", baudrate=460800, timeout=0.2)

            # Replace the stop_event and output_queue with our mocks
            lidar.stop_event = mock_stop_event
            lidar.output_queue = mock_queue

            # Call simple_scan
            scan_coroutine = lidar.simple_scan()

            # Create a task to run the scan coroutine
            task = asyncio.create_task(scan_coroutine)

            # Wait a short time for the task to start
            await asyncio.sleep(0.2)

            # Set the stop event to stop the scan
            mock_stop_event.is_set.return_value = True

            # Wait for the task to complete
            await task

            # Check that the scan request was created and sent
            mock_request.create_request.assert_any_call(protocol.RequestBytes.SCAN_BYTE)
            mock_request.send_request.assert_any_call(
                mock_serial, mock_request.create_request.return_value
            )

            # Check that the response descriptor was parsed
            mock_response.parse_response_descriptor.assert_called_with(mock_serial)

            # Check that handle_response was called with the correct parameters
            mock_response.handle_response.assert_called_with(
                serial=mock_serial,
                stop_event=mock_stop_event,
                output_queue=mock_queue,
                length=5,
                output_dict=None,
            )


if __name__ == "__main__":
    unittest.main()
