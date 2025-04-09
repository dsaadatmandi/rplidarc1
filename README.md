# RPLidarC1

A Python library for interfacing with the RPLidar C1 360-degree laser scanner. This library provides an asynchronous API for controlling the RPLidar device and processing scan data.

## Features

- Asynchronous API for non-blocking operation
- Simple interface for connecting to and controlling the RPLidar device
- Health status checking
- Device reset functionality
- Scan data processing with angle and distance measurements
- Support for both queue-based and dictionary-based data output

## Requirements

- Python 3.10+ (for asyncio TaskGroup support)
- pyserial

## Installation

```bash
# Clone the repository
git clone https://github.com/dsaadatmandi/rplidarc1.git
cd rplidarc1

# Install dependencies
pip install pyserial
```

## Usage

### Basic Usage

```python
from scanner import RPLidar
import asyncio

# Initialize the RPLidar with the appropriate port and baudrate
lidar = RPLidar("/dev/ttyUSB0", 460800)

# Perform a simple scan
async def scan_example():
    # Start a scan and get the coroutine
    scan_coroutine = lidar.simple_scan()
    
    # Create a task to process the scan data
    async with asyncio.TaskGroup() as tg:
        tg.create_task(scan_coroutine)
        # Add other tasks as needed
    
    # Reset the device when done
    lidar.reset()

# Run the example
try:
    asyncio.run(scan_example())
except KeyboardInterrupt:
    # Ensure proper shutdown on keyboard interrupt
    lidar.reset()
```

### Processing Scan Data

```python
from scanner import RPLidar
import asyncio

lidar = RPLidar("/dev/ttyUSB0", 460800)

async def process_scan_data():
    # Start a scan with dictionary output
    async with asyncio.TaskGroup() as tg:
        # Create a task to stop scanning after 5 seconds
        tg.create_task(wait_and_stop(5, lidar.stop_event))
        
        # Create a task to process data from the queue
        tg.create_task(process_queue(lidar.output_queue, lidar.stop_event))
        
        # Start the scan with dictionary output
        tg.create_task(lidar.simple_scan(make_return_dict=True))
    
    # Access the scan data dictionary
    print(lidar.output_dict)
    
    # Reset the device
    lidar.reset()

async def wait_and_stop(seconds, event):
    await asyncio.sleep(seconds)
    event.set()

async def process_queue(queue, stop_event):
    while not stop_event.is_set():
        if not queue.empty():
            data = await queue.get()
            # Process the data
            print(f"Angle: {data['a_deg']}°, Distance: {data['d_mm']}mm, Quality: {data['q']}")
        else:
            await asyncio.sleep(0.1)

# Run the example
try:
    asyncio.run(process_scan_data())
except KeyboardInterrupt:
    lidar.reset()
```

## API Reference

### RPLidar Class

```python
RPLidar(port="/dev/ttyUSB0", baudrate=460800, timeout=0.2)
```

**Parameters:**
- `port` (str): Serial port to connect to
- `baudrate` (int): Baud rate for the serial connection
- `timeout` (float): Timeout for serial operations

**Methods:**
- `healthcheck()`: Check the health status of the device
- `shutdown()`: Properly shut down the device
- `reset()`: Reset the device
- `simple_scan(make_return_dict=False)`: Start a scan and return a coroutine for processing scan data
  - `make_return_dict` (bool): If True, scan data will also be stored in `output_dict`

**Properties:**
- `output_queue` (asyncio.Queue): Queue containing scan data
- `output_dict` (dict): Dictionary containing scan data (angle -> distance)
- `stop_event` (asyncio.Event): Event to signal stopping the scan

## Data Format

Scan data is provided in the following format:

```python
{
    "a_deg": 45.33,  # Angle in degrees (0-360)
    "d_mm": 1250,    # Distance in millimeters
    "q": 15          # Quality of the measurement (0-63)
}
```

## Project Structure

- `scanner.py`: Main RPLidar class implementation
- `protocol.py`: Implementation of the RPLidar communication protocol
- `serial_handler.py`: Serial connection management
- `utils.py`: Utility classes and functions
- `examples/`: Example scripts demonstrating usage
- `tests/`: Unit and integration tests

## Testing

The project includes a comprehensive test suite that covers all major components of the library. The tests use pytest and mock the hardware to allow testing without an actual RPLidar device.

### Running Tests

To run the tests, first install the testing dependencies:

```bash
pip install -r requirements.txt
```

Then run the tests using pytest:

```bash
pytest
```

For more information about the tests, see the [tests README](tests/README.md).

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
