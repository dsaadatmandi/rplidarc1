import asyncio
import logging
import time
from types import CoroutineType
from protocol import Request, Response
from serial_handler import SerialConnection
import protocol


class RPLidar:
    def __init__(self, port="/dev/ttyUSB0", baudrate=460800, timeout=0.2) -> None:
        self._serial = SerialConnection(port, baudrate, timeout=timeout)
        self.logger = logging.getLogger("RPLidar")
        self.stop_event = asyncio.Event()
        self.output_queue = asyncio.Queue()
        self.output_dict = None

        self._initialize()

    def _initialize(self):
        """
        Startup sequence as per protocl docs:
        Healthcheck -> if response ok -> if no response -> raise comm error
        If Protection Stop -> Send Reset and start again -> if second iteration same raise hardware error
        Ready for Scan
        """
        self.logger.debug("Commencing startup sequence.")
        self._serial.connect()
        self.logger.debug("Connected Serial.")
        self.healthcheck()
        self.logger.debug("Completed startup sequence.")

    def healthcheck(self):
        self.logger.debug("Starting healthcheck.")
        request = Request.create_request(protocol.RequestBytes.GET_HEALTH_BYTE)
        Request.send_request(self._serial, request)
        length, mode = Response.parse_response_descriptor(self._serial)
        response = Response.handle_response(serial=self._serial, length=length)
        if response is None:
            self.logger.error("No response received within defined timeout period.")
            raise ConnectionError
        elif type(response) != bytes:
            self.logger.error("Somehow this did not return bytes type. Unexpected.")
            raise TypeError
        status = protocol.HealthStatus(response[0])
        if status == 2:
            self.logger.error(f"Healthcheck returned error code: {status}.")
            raise Exception
        self.logger.debug(f"Status: {status}")
        self.logger.debug("Completed healthcheck successfully.")

    def shutdown(self):
        self.logger.debug("Starting shutdown sequence.")
        stop_request = Request.create_request(protocol.RequestBytes.STOP_BYTE)
        Request.send_request(self._serial, stop_request)
        self._serial.disconnect()
        self.logger.debug("Completed shutdown sequence.")

    def reset(self):
        self.logger.debug("Starting reset sequence.")
        stop_request = Request.create_request(protocol.RequestBytes.STOP_BYTE)
        Request.send_request(self._serial, stop_request)
        reset_request = Request.create_request(protocol.RequestBytes.RESET_BYTE)
        Request.send_request(self._serial, reset_request)
        self.logger.debug("Sleeping 0.5s while reset occurs.")
        time.sleep(0.5)
        self.logger.debug("Completed reset sequence.")

    def get_info(self):
        raise NotImplementedError

    def simple_scan(self, make_return_dict: bool = False) -> CoroutineType:
        self.logger.debug("Starting reset sequence.")
        if make_return_dict:
            self._init_return_dict()
        scan_request = Request.create_request(protocol.RequestBytes.SCAN_BYTE)
        Request.send_request(self._serial, scan_request)
        length, mode = Response.parse_response_descriptor(self._serial)
        if mode != protocol.ResponseMode.MUTLI_RESPONSE:
            self.logger.error(
                "Somehow got single response mode marker for scan request. This is incorrect."
            )
            raise Exception
        response_handler = Response.handle_response(
            serial=self._serial,
            stop_event=self.stop_event,
            output_queue=self.output_queue,
            length=length,
            output_dict=self.output_dict,
        )
        if type(response_handler) != CoroutineType:
            self.logger.error("Somehow this did not return Coroutine type. Unexpected.")
            raise TypeError
        return response_handler

    def _clear_input_buffer(self) -> None:
        if self._serial is not None:
            self._serial.reset_input_buffer()

    def _init_return_dict(self) -> None:
        self.output_dict = {}
