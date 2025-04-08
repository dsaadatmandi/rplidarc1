import asyncio
import logging
from typing import Coroutine, Optional, Tuple, Union
from enum import IntEnum

import serial
from utils import ByteEnum


class CommonBytes(ByteEnum):
    SYNC_BYTE = b"\xa5"


class RequestBytes(ByteEnum):
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
    RESPONSE_SYNC_BYTE = b"\x5a"
    RESPONSE_HEALTH_BYTE = b"\x03"
    RESPONSE_SCAN_BYTE = b"\x03"


class ResponseMode(IntEnum):
    SINGLE_RESPONSE = 0
    MUTLI_RESPONSE = 1


class HealthStatus(IntEnum):
    GOOD = 0
    WARNING = 1
    ERROR = 2


class Request:

    @staticmethod
    def create_request(command: RequestBytes) -> bytes:
        request = CommonBytes.SYNC_BYTE + command
        return request

    @staticmethod
    def send_request(serial: serial.Serial, request: bytes):
        serial.write(request)
        serial.flush()


class Response:

    logger = logging.getLogger(__name__)

    RESPONSE_DESCRIPTOR_LENGTH = 7

    @staticmethod
    def parse_response_descriptor(serial: serial.Serial) -> Tuple[int, ResponseMode]:
        Response.logger.debug("Parsing Response Descriptor.")
        descriptor = serial.read(Response.RESPONSE_DESCRIPTOR_LENGTH)
        Response._check_response_sync_bytes(descriptor)

        length, mode = Response._calculate_request_details(descriptor)

        response_mode = ResponseMode(mode)

        return length, response_mode

    @staticmethod
    def handle_response(*args, **kwargs) -> Union[bytes, Coroutine]:
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
        Response.logger.debug("Creating multiresponse coroutine.")
        while not stop_event.is_set():
            if serial.in_waiting == 0:
                await asyncio.sleep(0.5)
                continue
            if serial.in_waiting < 10:
                Response.logger.debug("Worker sleeping")
                await asyncio.sleep(0.1)
            quality, angle, distance = Response._parse_simple_scan_result(
                serial.read(length)
            )
            distance = None if distance == 0 else distance
            if output_dict is not None:
                output_dict[angle] = distance
            await output_queue.put({"q": quality, "a_deg": angle, "d_mm": distance})
        output_queue.task_done()

    @staticmethod
    def _parse_simple_scan_result(response: bytes) -> Tuple[int, float, float]:
        quality = (response[0] >> 2) & 0b111111
        angle = ((response[1] >> 1) & 0b01111111 | (response[2] << 7)) / 64
        angle = round(
            (round(angle * 3) / 3), 2
        )  # round to closest 0.33 which is precision of rplidarc1
        distance = (response[3] | (response[4] << 8)) / 4
        return quality, angle, distance

    @staticmethod
    def _check_response_sync_bytes(descriptor: bytes):
        if not descriptor[0:1] == CommonBytes.SYNC_BYTE:
            raise ValueError
        if not descriptor[1:2] == ResponseBytes.RESPONSE_SYNC_BYTE:
            raise ValueError

    @staticmethod
    def _calculate_request_details(descriptor: bytes) -> Tuple[int, int]:
        b1, b2, b3, b4 = descriptor[2:6]
        composite_32_bit = (
            b1 | (b2 << 8) | (b3 << 16) | (b4 << 24)
        )  # little endian 32 bit
        mask_30_bit = 0b00111111_11111111_11111111_11111111  # mask with first 2 bits 0
        mask_2_bit = 0b11  # mask to ensure only 2 bits
        length = composite_32_bit & mask_30_bit  # bitwise AND operation with mask
        mode = (
            composite_32_bit >> 30
        ) & mask_2_bit  # right shift to get 2 bit and mask

        return length, mode

    @staticmethod
    def parse_error_code(response: bytes) -> int:
        b1, b2 = response[1:3]
        return b1 | (b2 << 8)
