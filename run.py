from RPLidarC1 import RPLidar

import logging

if __name__ == "__main__":
    logging.getLogger("rplidarc1").setLevel(logging.DEBUG)
    lidar = RPLidar('/dev/ttyUSB0', 460800)
    lidar.connect()
    # lidar.healthcheck()
    lidar.start_scan()
    # lidar.get_info()