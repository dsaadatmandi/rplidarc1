import asyncio
import logging
import time
from types import CoroutineType
from .protocol import Request, Response
from .serial_handler import SerialConnection
from . import protocol


class RPLidar:
    """
    Main class for interacting with the RPLidar device.

    This class provides methods to initialize, control, and retrieve data from
    an RPLidar sensor. It handles the serial communication, command sending,
    and response parsing according to the RPLidar protocol.
    """

    def __init__(self, port="/dev/ttyUSB0", baudrate=460800, timeout=0.2) -> None:
        """
        Initialize the RPLidar interface.

        Args:
            port (str): Serial port to connect to the RPLidar device.
                Default is "/dev/ttyUSB0".
            baudrate (int): Communication speed in bits per second.
                Default is 460800.
            timeout (float): Serial read timeout in seconds.
                Default is 0.2.
        """
        self._serial = SerialConnection(port, baudrate, timeout=timeout)
        self.logger = logging.getLogger("RPLidar")
        self.stop_event = asyncio.Event()
        self.output_queue = asyncio.Queue()
        self.output_dict = None

        self._initialize()

    def _initialize(self):
        """
        Perform the startup sequence for the RPLidar device.

        Startup sequence as per protocol docs:
        1. Establish serial connection
        2. Perform healthcheck
        3. If response ok -> ready for scan
        4. If no response -> raise communication error
        5. If Protection Stop -> Send Reset and start again
        6. If second iteration same -> raise hardware error
        """
        self.logger.debug("Commencing startup sequence.")
        self._serial.connect()
        self.logger.debug("Connected Serial.")
        self.healthcheck()
        self.logger.debug("Completed startup sequence.")

    def healthcheck(self):
        """
        Perform a health check on the RPLidar device.

        Sends a health check request to the device and processes the response.
        Raises appropriate exceptions if the device is not responding or
        reports an error status.

        Raises:
            ConnectionError: If no response is received within the timeout period.
            TypeError: If the response is not of bytes type.
            Exception: If the device reports an error status.
        """
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
        """
        Perform a clean shutdown of the RPLidar device.

        Sends a stop command to the device and disconnects the serial connection.
        """
        self.logger.debug("Starting shutdown sequence.")
        stop_request = Request.create_request(protocol.RequestBytes.STOP_BYTE)
        Request.send_request(self._serial, stop_request)
        self._serial.disconnect()
        self.logger.debug("Completed shutdown sequence.")

    def reset(self):
        """
        Reset the RPLidar device.

        Sends a stop command followed by a reset command to the device.
        Waits for 0.5 seconds to allow the device to complete the reset process.
        """
        self.logger.debug("Starting reset sequence.")
        stop_request = Request.create_request(protocol.RequestBytes.STOP_BYTE)
        Request.send_request(self._serial, stop_request)
        reset_request = Request.create_request(protocol.RequestBytes.RESET_BYTE)
        Request.send_request(self._serial, reset_request)
        self.logger.debug("Sleeping 0.5s while reset occurs.")
        time.sleep(0.5)
        self.logger.debug("Completed reset sequence.")

    def get_info(self):
        """
        Get device information from the RPLidar.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError

    def simple_scan(self, make_return_dict: bool = False) -> CoroutineType:
        """
        Start a simple scan operation on the RPLidar device.

        This method initiates a scan and returns a coroutine that will
        continuously read scan data from the device until stopped.

        Args:
            make_return_dict (bool): If True, scan results will also be stored
                in the output_dict attribute. Default is False.

        Returns:
            CoroutineType: A coroutine that handles the scan response data.

        Raises:
            Exception: If an unexpected response mode is received.
            TypeError: If the response handler is not a coroutine.
        """
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
        """
        Clear the input buffer of the serial connection.

        This method is used to discard any unread data in the serial input buffer.
        """
        if self._serial is not None:
            self._serial.reset_input_buffer()

    def _init_return_dict(self) -> None:
        """
        Initialize the output dictionary for storing scan results.

        This method is called when make_return_dict is set to True in simple_scan.
        """
        self.output_dict = {}
