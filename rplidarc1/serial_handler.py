from serial import Serial
import logging

"""
This module provides a wrapper around the serial.Serial class for handling
serial communication with the RPLidar device.
"""


class SerialConnection(Serial):
    """
    A wrapper around the serial.Serial class for handling serial communication
    with the RPLidar device.

    This class provides methods to connect to and disconnect from the device,
    as well as handling error conditions and logging.
    """

    def __init__(self, port: str, baudrate: int, **kwargs) -> None:
        """
        Initialize a serial connection to the RPLidar device.

        Args:
            port (str): The serial port to connect to (e.g., "/dev/ttyUSB0").
            baudrate (int): The baud rate for the serial connection.
            **kwargs: Additional keyword arguments to pass to the serial.Serial constructor.
        """
        self._port = port
        self._baudrate = baudrate
        self.logger = logging.getLogger("serial")
        self.kwargs = kwargs

        self._is_connected = False
        self.is_open = False

    def connect(self):
        """
        Establish a serial connection to the RPLidar device.

        If a connection is already active, it will be disconnected first.

        Raises:
            ConnectionError: If the connection cannot be established.
        """
        if self._is_connected:
            self.logger.warning(
                "connect called while there is an active serial connection. Disconnecting first."
            )
            self.disconnect()
        try:
            self.logger.debug(
                f"Creating serial connetion with port: {self._port} and baudrate: {self.baudrate}."
            )
            super().__init__(port=self._port, baudrate=self._baudrate, **self.kwargs)

            self.dtr = False
            self.rts = False
            self._is_connected = True
            self.is_open = True
        except Exception as e:
            raise ConnectionError(e)

    def disconnect(self):
        """
        Disconnect from the RPLidar device.

        If no connection is active, a warning will be logged but no error will be raised.
        """
        if self._is_connected:
            self.logger.debug(f"Closing serial connection on port: {self.port}.")
            self.close()
            self._is_connected = False
            self.is_open = False
            return
        self.logger.warning(
            "disconnect called while there is no active serial connection. Continuing."
        )
