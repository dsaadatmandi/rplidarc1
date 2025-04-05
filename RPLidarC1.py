import serial
import logging
import time

class RPLidar:
    
    # General Protocol Bytes
    SYNC_BYTE = b'\xA5'

    # Request Bytes
    STOP_BYTE = b'\x25' # wait 10ms
    SCAN_BYTE = b'\x20'
    FORCE_SCAN_BYTE = b'\x21'
    INFO_BYTE = b'\x50'
    GET_HEALTH_BYTE = b'\x52'
    RESET_BYTE = b'\x40' # wait 500ms
    EXPRESS_SCAN_BYTE = b'\x82'
    GET_INFO_BYTE = b'\x50'
    GET_SAMPLE_RATE = b'\x59'
    GET_LIDAR_CONF = b'\x84'

    # Response Bytes
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
            
        read_bytes = self._serial.read(7)
        length, mode = self._calculate_response_details(read_bytes)

        self.logger.warning(read_bytes.hex())

        print(mode)

        if mode == 0:
            return

        else:
            while True:
                out = self._serial.read(length)
                print(out.hex())
            
            
    def _calculate_response_details(self, response_bytes: bytearray):
        byte1, byte2, byte3, byte4 = response_bytes[2:6]
        composite_32_bit = byte1 | (byte2 << 8) | (byte3 << 16) | (byte4 << 24) # little endian 32 bit
        mask_30_bit = 0b00111111_11111111_11111111_11111111 # mask with first 2 bits 0
        mask_2_bit = 0b11
        length = composite_32_bit & mask_30_bit # bitwise AND operation with mask
        mode = (composite_32_bit >> 30) & mask_2_bit

        return length, mode
        
    def healthcheck(self):
        self._send_command(self.GET_HEALTH_BYTE)
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

    def get_info(self):
        self._send_command(self.GET_INFO_BYTE)
        time.sleep(0.5)

        self._read_data()