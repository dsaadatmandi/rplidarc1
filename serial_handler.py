from serial import Serial
import logging


class SerialConnection(Serial):

    def __init__(self, port: str, baudrate: int, **kwargs) -> None:
        self._port = port
        self._baudrate = baudrate
        self.logger = logging.getLogger("serial")
        self.kwargs = kwargs

        self._is_connected = False

    def connect(self):
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
        except Exception as e:
            raise ConnectionError(e)

    def disconnect(self):
        if self.is_open:
            self.logger.debug(f"Closing serial connection on port: {self.port}.")
            self.close()
            return
        self.logger.warning(
            "disconnect called while there is no active serial connection. Continuing."
        )
