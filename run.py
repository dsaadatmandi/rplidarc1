from RPLidarC1 import RPLidar

if __name__ == "__main__":
    lidar = RPLidar('/dev/ttyUSB0', 460800)
    lidar.connect()
    # lidar.healthcheck()
    lidar.start_scan()