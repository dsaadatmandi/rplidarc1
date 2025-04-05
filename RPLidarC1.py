import serial
import logging
import time

class RPLidar:
    
    SYNC_BYTE = b'\xA5'
    STOP_BYTE = b'\x25'
    SCAN_BYTE = b'\x20'
    FORCE_SCAN_BYTE = b'\x21'
    INFO_BYTE = b'\x50'
    HEALTH_BYTE = b'\x52'
    RESET_BYTE = b'\x40'
    
    RESPONSE_HEALTH_BYTE = b'\x03'
    RESPONSE_SCAN_BYTE = b'\x03'
    
    RESPONSE_HEADER_LENGTH = 7
    
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self.logger = logging.getLogger("rplidarc1")
        
    def connect(self):
        if self._serial is not None:
            self.disconnect()
        
        self._serial = serial.Serial(
            self.port,
            self.baudrate
        )
        
        self._serial.dtr = False
        self._serial.rts = False
            
            
            
    def disconnect(self):
        if self._serial is not None:
            self._serial.close()
            self._serial = None
        
    def _send_command(self, command):
        if self._serial is None:
            self.logger.warning('_send_command called without serial connection. Weird. Creating conn first.')
            self.connect()
        cmd = self.SYNC_BYTE + command
        self._serial.write(cmd)
        self._serial.flush()
        
    def _read_data(self):
        if self._serial is None:
            self.logger.warning('_read_data called without serial connection. Weird. Creating conn first.')
            self.connect()
        if self._serial.in_waiting > 0:
            self._serial.reset_input_buffer
            
        while True:
            read_bytes = self._serial.read(self.RESPONSE_HEADER_LENGTH)
            length = self._calculate_length(read_bytes)
            print(read_bytes.hex(), length)
            # print(self._serial.in_waiting)
            # cur_byte = self._serial.read()
            # print(f'{cur_byte.hex()}')
            
            
            
    def _calculate_length(self, response_bytes):
        byte1, byte2, byte3 = response_bytes[4:7]
        length = byte3 << 16 | byte2 << 8 | byte1
        return length
        
    def healthcheck(self):
        self._send_command(self.HEALTH_BYTE)
        time.sleep(0.5)
        self._read_data()
        
    def start_scan(self):
        self._send_command(self.SCAN_BYTE)
        time.sleep(0.5)
        
        try:
            self._read_data()
        except KeyboardInterrupt:
            self._send_command(self.STOP_BYTE)
            self.disconnect()