"""
Tests for the protocol module.
"""

import unittest
import pytest
from unittest.mock import MagicMock, AsyncMock
from rplidarc1.protocol import (
    CommonBytes,
    RequestBytes,
    ResponseBytes,
    ResponseMode,
    HealthStatus,
    Request,
    Response,
)


class TestProtocolEnums(unittest.TestCase):
    """
    Test cases for the protocol enumeration classes.
    """

    def test_common_bytes(self):
        """
        Test that CommonBytes enum has the correct values.
        """
        self.assertEqual(CommonBytes.SYNC_BYTE, b"\xa5")

    def test_request_bytes(self):
        """
        Test that RequestBytes enum has the correct values.
        """
        self.assertEqual(RequestBytes.STOP_BYTE, b"\x25")
        self.assertEqual(RequestBytes.SCAN_BYTE, b"\x20")
        self.assertEqual(RequestBytes.RESET_BYTE, b"\x40")
        # Add more assertions for other request bytes

    def test_response_bytes(self):
        """
        Test that ResponseBytes enum has the correct values.
        """
        self.assertEqual(ResponseBytes.RESPONSE_SYNC_BYTE, b"\x5a")
        self.assertEqual(ResponseBytes.RESPONSE_HEALTH_BYTE, b"\x03")
        self.assertEqual(ResponseBytes.RESPONSE_SCAN_BYTE, b"\x81")

    def test_response_mode(self):
        """
        Test that ResponseMode enum has the correct values.
        """
        self.assertEqual(ResponseMode.SINGLE_RESPONSE, 0)
        self.assertEqual(ResponseMode.MUTLI_RESPONSE, 1)

    def test_health_status(self):
        """
        Test that HealthStatus enum has the correct values.
        """
        self.assertEqual(HealthStatus.GOOD, 0)
        self.assertEqual(HealthStatus.WARNING, 1)
        self.assertEqual(HealthStatus.ERROR, 2)


class TestRequest(unittest.TestCase):
    """
    Test cases for the Request class.
    """

    def test_create_request(self):
        """
        Test that create_request correctly formats request packets.
        """
        request = Request.create_request(RequestBytes.SCAN_BYTE)
        self.assertEqual(request, b"\xa5\x20")

        request = Request.create_request(RequestBytes.STOP_BYTE)
        self.assertEqual(request, b"\xa5\x25")

        request = Request.create_request(RequestBytes.RESET_BYTE)
        self.assertEqual(request, b"\xa5\x40")

    def test_send_request(self):
        """
        Test that send_request correctly sends the request to the serial connection.
        """
        mock_serial = MagicMock()
        request = b"\xa5\x20"

        Request.send_request(mock_serial, request)

        mock_serial.write.assert_called_once_with(request)
        mock_serial.flush.assert_called_once()


class TestResponse:
    """
    Test cases for the Response class.
    """

    def test_parse_response_descriptor(self, mock_serial):
        """
        Test that parse_response_descriptor correctly parses the response descriptor.
        """
        # Set up the mock to return a valid response descriptor
        mock_serial.read.return_value = b"\xa5\x5a\x05\x00\x00\x00\x40"

        length, mode = Response.parse_response_descriptor(mock_serial)

        mock_serial.read.assert_called_once_with(Response.RESPONSE_DESCRIPTOR_LENGTH)
        assert length == 5
        assert mode == ResponseMode.SINGLE_RESPONSE

    def test_parse_response_descriptor_invalid_sync_byte(self, mock_serial):
        """
        Test that parse_response_descriptor raises ValueError for invalid sync bytes.
        """
        # Set up the mock to return an invalid response descriptor (wrong first byte)
        mock_serial.read.return_value = b"\x00\x5a\x05\x00\x00\x00\x40"

        with pytest.raises(ValueError):
            Response.parse_response_descriptor(mock_serial)

        # Set up the mock to return an invalid response descriptor (wrong second byte)
        mock_serial.read.return_value = b"\xa5\x00\x05\x00\x00\x00\x40"

        with pytest.raises(ValueError):
            Response.parse_response_descriptor(mock_serial)

    def test_parse_single_response(self, mock_serial):
        """
        Test that parse_single_response correctly reads and returns the response data.
        """
        mock_serial.read.return_value = b"\x00\x01\x02"
        length = 3

        data = Response.parse_single_response(mock_serial, length)

        mock_serial.read.assert_called_once_with(length)
        assert data == b"\x00\x01\x02"

    def test_handle_response_single(self, mock_serial):
        """
        Test that handle_response correctly handles single responses.
        """
        mock_serial.read.return_value = b"\x00\x01\x02"
        length = 3

        data = Response.handle_response(serial=mock_serial, length=length)

        mock_serial.read.assert_called_once_with(length)
        assert data == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_multi_response_handler(
        self, mock_serial, mock_stop_event, mock_queue
    ):
        """
        Test that multi_response_handler correctly processes multiple responses.
        """
        # Set up async queue
        mock_queue = AsyncMock()

        # Set up the mock to return a valid scan response
        mock_serial.read.return_value = b"\x3d\x5b\x01\x22\x01"
        mock_serial.in_waiting = 10

        # Set up the stop event to be set after one iteration
        mock_stop_event.is_set.side_effect = [False, True]

        # Call the multi_response_handler
        await Response.multi_response_handler(
            serial=mock_serial,
            stop_event=mock_stop_event,
            output_queue=mock_queue,
            length=5,
            output_dict={},
        )

        # Check that the queue.put was called with the correct data
        mock_queue.put.assert_called_once()
        mock_queue.task_done.assert_called_once()

    def test_parse_simple_scan_result(self):
        """
        Test that _parse_simple_scan_result correctly parses scan data.
        """
        # Quality: 15, Angle: 45.33, Distance: 1250mm
        response = b"\x3c\x55\x16\x88\x13"

        result = Response._parse_simple_scan_result(response)

        assert result is not None

        quality, angle, distance = result

        assert quality == 15
        assert angle == 45.33
        assert distance == 1250

    def test_calculate_request_details(self):
        """
        Test that _calculate_request_details correctly extracts length and mode.
        """
        # Length: 5, Mode: 0 (SINGLE_RESPONSE)
        descriptor = b"\xa5\x5a\x05\x00\x00\x00\x00"

        length, mode, check = Response._calculate_request_details(descriptor)

        assert length == 5
        assert mode == 0
        assert check == None

        # Length: 5, Mode: 1 (MUTLI_RESPONSE)
        descriptor = b"\xa5\x5a\x05\x00\x00\x40\x40"

        length, mode, check = Response._calculate_request_details(descriptor)

        assert length == 5
        assert mode == 1
        assert check == None

    def test_parse_error_code(self):
        """
        Test that parse_error_code correctly extracts error codes.
        """
        # Error code: 0x0201 (513)
        response = b"\x00\x01\x02"

        error_code = Response.parse_error_code(response)

        assert error_code == 513


if __name__ == "__main__":
    unittest.main()
