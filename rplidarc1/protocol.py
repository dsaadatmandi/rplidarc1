import asyncio
import logging
from typing import Coroutine, Optional, Tuple, Union
from enum import IntEnum

import serial
from .utils import ByteEnum

"""
This module implements the RPLidar protocol for communication with the device.
It defines request and response handling, byte definitions, and data parsing
according to the RPLidar C1 specifications.
"""


class CommonBytes(ByteEnum):
    """
    Common bytes used in the RPLidar protocol for both requests and responses.
    """

    SYNC_BYTE = b"\xa5"


class RequestBytes(ByteEnum):
    """
    Command bytes used for sending requests to the RPLidar device.

    These bytes are combined with the SYNC_BYTE to form complete commands.
    Some commands require waiting after sending for the device to process.
    """

    STOP_BYTE = b"\x25"  # wait 10ms
    SCAN_BYTE = b"\x20"
    FORCE_SCAN_BYTE = b"\x21"
    INFO_BYTE = b"\x50"
    GET_HEALTH_BYTE = b"\x52"
    RESET_BYTE = b"\x40"  # wait 500ms
    EXPRESS_SCAN_BYTE = b"\x82"
    GET_INFO_BYTE = b"\x50"
    GET_SAMPLE_RATE = b"\x59"
    GET_LIDAR_CONF = b"\x84"


class ResponseBytes(ByteEnum):
    """
    Bytes used in responses from the RPLidar device.

    These bytes help identify and validate the response type.
    """

    RESPONSE_SYNC_BYTE = b"\x5a"
    RESPONSE_HEALTH_BYTE = b"\x03"
    RESPONSE_SCAN_BYTE = b"\x81"


class ResponseMode(IntEnum):
    """
    Enumeration of response modes from the RPLidar device.

    SINGLE_RESPONSE: The device will send a single response packet.
    MUTLI_RESPONSE: The device will send multiple response packets.
    """

    SINGLE_RESPONSE = 0
    MUTLI_RESPONSE = 1


class HealthStatus(IntEnum):
    """
    Enumeration of health status codes returned by the RPLidar device.

    GOOD: The device is functioning normally.
    WARNING: The device has detected a potential issue.
    ERROR: The device has detected a critical error.
    """

    GOOD = 0
    WARNING = 1
    ERROR = 2


class Request:
    """
    Class for creating and sending requests to the RPLidar device.

    This class provides static methods to create properly formatted request
    packets and send them to the device over a serial connection.
    """

    @staticmethod
    def create_request(command: RequestBytes) -> bytes:
        """
        Create a properly formatted request packet.

        Args:
            command (RequestBytes): The command byte to include in the request.

        Returns:
            bytes: The complete request packet (SYNC_BYTE + command).
        """
        request = CommonBytes.SYNC_BYTE + command
        return request

    @staticmethod
    def send_request(serial: serial.Serial, request: bytes):
        """
        Send a request packet to the RPLidar device.

        Args:
            serial (serial.Serial): The serial connection to the device.
            request (bytes): The request packet to send.
        """
        serial.write(request)
        serial.flush()


class Response:
    """
    Class for handling responses from the RPLidar device.

    This class provides static methods to parse response descriptors,
    handle different types of responses, and extract data from response packets.
    """

    logger = logging.getLogger(__name__)

    RESPONSE_DESCRIPTOR_LENGTH = 7  # Length of the response descriptor in bytes

    @staticmethod
    def parse_response_descriptor(serial: serial.Serial) -> Tuple[int, ResponseMode]:
        """
        Parse the response descriptor from the RPLidar device.

        The response descriptor contains information about the length and mode
        of the response data that follows.

        Args:
            serial (serial.Serial): The serial connection to the device.

        Returns:
            Tuple[int, ResponseMode]: A tuple containing the length of the response
                data and the response mode (single or multi).

        Raises:
            ValueError: If the response descriptor does not contain the expected sync bytes.
        """
        Response.logger.debug("Parsing Response Descriptor.")
        descriptor = serial.read(Response.RESPONSE_DESCRIPTOR_LENGTH)
        Response._check_response_sync_bytes(descriptor)

        length, mode, check = Response._calculate_request_details(descriptor)

        response_mode = ResponseMode(mode)

        Response.logger.warning(f"In waiting: {serial.in_waiting}")

        return length, response_mode

    @staticmethod
    def handle_response(*args, **kwargs) -> Union[bytes, Coroutine]:
        """
        Handle a response from the RPLidar device.

        This method determines the appropriate response handler based on the
        provided arguments and delegates to either parse_single_response or
        multi_response_handler.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments. Expected keys depend on the
                response type:
                - For single responses: 'serial' and 'length'
                - For multi responses: 'serial', 'stop_event', 'output_queue', and 'length'

        Returns:
            Union[bytes, Coroutine]: Either the parsed response data for a single
                response, or a coroutine for handling multi responses.

        Raises:
            NotImplementedError: If the provided arguments do not match the
                expected patterns for either single or multi responses.
        """
        if len(args) + len(kwargs) == 2 and all(
            p in kwargs for p in ["serial", "length"]
        ):
            return Response.parse_single_response(*args, **kwargs)
        elif all(
            p in kwargs for p in ["serial", "stop_event", "output_queue", "length"]
        ):
            Response.logger.debug("Creating async multi response coroutine.")
            return Response.multi_response_handler(*args, **kwargs)
        else:
            raise NotImplementedError

    @staticmethod
    def parse_single_response(serial: serial.Serial, length: int) -> bytes:
        """
        Parse a single response from the RPLidar device.

        Args:
            serial (serial.Serial): The serial connection to the device.
            length (int): The length of the response data to read.

        Returns:
            bytes: The response data.
        """
        data = serial.read(length)
        return data

    @staticmethod
    async def multi_response_handler(
        serial: serial.Serial,
        stop_event: asyncio.Event,
        output_queue: asyncio.Queue,
        length: int,
        output_dict: Optional[dict],
    ):
        """
        Handle multiple responses from the RPLidar device.

        This coroutine continuously reads scan data from the device until
        the stop_event is set. Each scan result is parsed and added to the
        output_queue and optionally to the output_dict.

        Args:
            serial (serial.Serial): The serial connection to the device.
            stop_event (asyncio.Event): Event to signal when to stop reading.
            output_queue (asyncio.Queue): Queue to store the parsed scan results.
            length (int): The length of each response data packet.
            output_dict (Optional[dict]): Dictionary to store the scan results
                indexed by angle. If None, results are only added to the queue.
        """
        Response.logger.debug("Creating multiresponse coroutine.")
        byte_error_handling = False
        data_out_buffer: bytes = bytes(0)
        while not stop_event.is_set():
            if serial.in_waiting < 5:
                Response.logger.debug("Waiting for data.")
                await asyncio.sleep(0.1)
                continue

            if not byte_error_handling:
                data_out_buffer = serial.read(length)
            elif data_out_buffer:
                data_out_buffer = data_out_buffer[1:] + serial.read(1)

            if not Response._check_byte_alignment(
                data_out_buffer[0], data_out_buffer[1]
            ):
                byte_error_handling = True
                Response.logger.warning(
                    "Verification bytes not matching. Continuing one byte along."
                )
                continue
            else:
                byte_error_handling = False

            parsed_tuple = Response._parse_simple_scan_result(data_out_buffer)
            if parsed_tuple is None:
                continue
            quality, angle, distance = parsed_tuple
            distance = None if distance == 0 else distance
            if output_dict is not None:
                output_dict[angle] = distance
            await output_queue.put({"q": quality, "a_deg": angle, "d_mm": distance})
        output_queue.task_done()
        Response.logger.info("Completed processing.")
        await asyncio.sleep(0)

    @staticmethod
    def _check_byte_alignment(b1: int, b2: int):
        control_s_bit = b1 & 0b1
        control_s_bar_bit = (b1 >> 1) & 0b1
        if control_s_bit == control_s_bar_bit:
            Response.logger.warning("S bit verification failed. Realigning.")
            return False
        control_c_bit = b2 & 0b1
        if control_c_bit != 1:
            Response.logger.warning("C bit verification failed. Realigning.")
            return False
        return True

    @staticmethod
    def _parse_simple_scan_result(
        response: bytes,
    ) -> Optional[Tuple[int, float, float]]:
        """
        Parse a simple scan result from the RPLidar device.

        Args:
            response (bytes): The response data to parse.

        Returns:
            Tuple[int, float, float]: A tuple containing:
                - quality: The quality of the scan point (0-63)
                - angle: The angle of the scan point in degrees (0-359.99)
                - distance: The distance of the scan point in millimeters
        """
        quality = (response[0] >> 2) & 0b111111
        angle = ((response[1] & 0b01111111) | (response[2] << 7)) / 64
        angle = round(
            (round(angle * 3) / 3), 2
        )  # round to closest 0.33 which is precision of rplidarc1
        if angle >= 360:
            Response.logger.error(f"calculated angle {angle} from {response}")
            return None
        distance = (response[3] | (response[4] << 8)) / 4
        return quality, angle, distance

    @staticmethod
    def _check_response_sync_bytes(descriptor: bytes):
        """
        Check that the response descriptor contains the expected sync bytes.

        Args:
            descriptor (bytes): The response descriptor to check.

        Raises:
            ValueError: If the descriptor does not contain the expected sync bytes.
        """
        if not descriptor[0:1] == CommonBytes.SYNC_BYTE:
            raise ValueError
        if not descriptor[1:2] == ResponseBytes.RESPONSE_SYNC_BYTE:
            raise ValueError

    @staticmethod
    def _calculate_request_details(
        descriptor: bytes,
    ) -> Tuple[int, int, Optional[ResponseBytes]]:
        """
        Calculate the length and mode from the response descriptor.

        Args:
            descriptor (bytes): The response descriptor to parse.

        Returns:
            Tuple[int, int]: A tuple containing the length of the response data
                and the response mode (0 for single, 1 for multi).
        """
        b1, b2, b3, b4, b5 = descriptor[2:7]
        composite_32_bit = (
            b1 | (b2 << 8) | (b3 << 16) | (b4 << 24)
        )  # little endian 32 bit
        mask_30_bit = 0b00111111_11111111_11111111_11111111  # mask with first 2 bits 0
        mask_2_bit = 0b11  # mask to ensure only 2 bits
        length = composite_32_bit & mask_30_bit  # bitwise AND operation with mask
        mode = (
            composite_32_bit >> 30
        ) & mask_2_bit  # right shift to get 2 bit and mask

        check = ResponseBytes.RESPONSE_SCAN_BYTE if b5 == 129 else None
        return length, mode, check

    @staticmethod
    def parse_error_code(response: bytes) -> int:
        """
        Parse an error code from a response.

        Args:
            response (bytes): The response data containing the error code.

        Returns:
            int: The parsed error code.
        """
        b1, b2 = response[1:3]
        return b1 | (b2 << 8)
