import asyncio
import math
import serial
import logging
import time

from typing import Optional, Tuple, List, Coroutine


class RPLidar:

    # General Protocol Bytes
    SYNC_BYTE = b"\xa5"

    # Request Bytes
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

    # Response Bytes
    RESPONSE_HEALTH_BYTE = b"\x03"
    RESPONSE_SCAN_BYTE = b"\x03"

    RESPONSE_HEADER_LENGTH = 7

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self._serial: Optional[serial.Serial] = None
        self.logger = logging.getLogger("rplidarc1")
        self.output_queue = asyncio.Queue()
        self.coro_list: List[Coroutine] = []
        self.stop_event = asyncio.Event()

        self.startup_sequence()

    def connect(self):
        if self._serial is not None:
            self.disconnect()

        try:
            self._serial = serial.Serial(self.port, self.baudrate)

            self._serial.dtr = False
            self._serial.rts = False
        except:
            raise ConnectionError()

    def disconnect(self):
        self._send_command(self.STOP_BYTE)
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def _send_command(self, command):
        if self._serial is None:
            self.logger.warning(
                "_send_command called without serial connection. Weird. Creating conn first."
            )
            self.connect()
            assert (
                self._serial is not None
            ), "Serial still not initialised after connect()."
        cmd = self.SYNC_BYTE + command
        self._serial.write(cmd)
        self._serial.flush()

    def _read_data(self):
        if self._serial is None:
            self.logger.warning(
                "_read_data called without serial connection. Weird. Creating conn first."
            )
            self.connect()
            assert (
                self._serial is not None
            ), "Serial still not initialised after connect()."
        if self._serial.in_waiting > 0:
            self._serial.reset_input_buffer

        read_bytes = bytearray(self._serial.read(7))
        length, mode = self._parse_response_descriptor(read_bytes)

        self.logger.warning(read_bytes.hex())

        if mode == 0:
            self.logger.debug("Single Response expected.")
            out = self._serial.read(length)
            return out

        elif mode == 1:
            self.logger.debug(
                "Response contains multiple data packets. Returning processor."
            )
            self.output_queue = asyncio.Queue()  # create new empty queue
            self.logger.debug("Create response handler worker coroutine.")
            self.coro_list.append(self.multi_response_reader(length))

        else:
            self.logger.error(
                "mode is neither 0 or 1. This is not expected. There is no handling for such a case."
            )

    def _parse_response_descriptor(self, response_bytes: bytearray) -> Tuple[int, int]:
        byte1, byte2, byte3, byte4 = response_bytes[2:6]
        composite_32_bit = (
            byte1 | (byte2 << 8) | (byte3 << 16) | (byte4 << 24)
        )  # little endian 32 bit
        mask_30_bit = 0b00111111_11111111_11111111_11111111  # mask with first 2 bits 0
        mask_2_bit = 0b11  # mask to ensure only 2 bits
        length = composite_32_bit & mask_30_bit  # bitwise AND operation with mask
        mode = (
            composite_32_bit >> 30
        ) & mask_2_bit  # right shift to get 2 bit and mask

        return length, mode

    def healthcheck(self):
        self._send_command(self.GET_HEALTH_BYTE)
        time.sleep(0.5)
        response = self._read_data()
        assert type(response) == bytes
        hp = response[0]
        match hp:
            case 0:
                print("healthy")
            case 1:
                print("warn")
            case 2:
                print("error")

    def start_scan(self):
        self.clear_input_buffer()
        self._send_command(self.SCAN_BYTE)
        self._read_data()

    def get_info(self):
        self._send_command(self.GET_INFO_BYTE)
        time.sleep(0.5)

        self._read_data()

    def startup_sequence(self):
        """
        Startup sequence as per protocl docs:
        Healthcheck -> if response ok -> if no response -> raise comm error
        If Protection Stop -> Send Reset and start again -> if second iteration same raise hardware error
        Ready for Scan
        """
        self.logger.debug("Doing startup sequence.")
        self.connect()
        self.healthcheck()
        self.logger.debug("Completed startup sequence.")

    def clear_input_buffer(self):
        if self._serial is not None:
            self._serial.reset_input_buffer()

    async def multi_response_reader(self, length: int):
        self.logger.debug("Starting response queue worker")
        self._create_output_dict()
        assert self._serial is not None
        while not self.stop_event.is_set():
            if self._serial.in_waiting < 10:
                self.logger.debug("Worker sleeping")
                await asyncio.sleep(0.1)
            quality, angle, distance = self._parse_simple_scan_result(
                self._serial.read(length)
            )
            distance = "invalid" if distance == 0 else distance
            self.output_dict[angle] = distance
            await self.output_queue.put(
                {"q": quality, "a_deg": angle, "d_mm": distance}
            )
        self.output_queue.task_done()

    def _parse_simple_scan_result(self, response: bytes) -> Tuple[int, int, int]:
        quality = (response[0] >> 2) & 0b111111
        angle = round(((response[1] >> 1) & 0b01111111 | (response[2] << 7)) / 64)
        distance = round((response[3] | (response[4] << 8)) / 4)
        return quality, angle, distance

    def _create_output_dict(self):
        self.output_dict = dict.fromkeys(range(361))
