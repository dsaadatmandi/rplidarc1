# RPLidarC1 Tests

This directory contains tests for the RPLidarC1 library. The tests are written using the pytest framework and cover all major components of the library.

## Test Structure

The tests are organized by module:

- `test_utils.py`: Tests for utility classes and functions
- `test_protocol.py`: Tests for the RPLidar protocol implementation
- `test_serial_handler.py`: Tests for the serial connection handler
- `test_scanner.py`: Tests for the main RPLidar class

## Running the Tests

### Prerequisites

Before running the tests, make sure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Tests

To run tests for a specific module:

```bash
pytest tests/test_utils.py
```

To run a specific test:

```bash
pytest tests/test_utils.py::TestByteEnum::test_bytes_conversion
```

## Test Coverage

The tests cover the following aspects of the library:

### Utils Module
- ByteEnum class and its operations

### Protocol Module
- Enumeration classes (CommonBytes, RequestBytes, ResponseBytes, ResponseMode, HealthStatus)
- Request creation and sending
- Response parsing and handling
- Scan data processing

### Serial Handler Module
- Connection initialization and management
- Error handling

### Scanner Module
- Device initialization
- Health status checking
- Device control (shutdown, reset)
- Scan operations
- Asynchronous data processing

## Mocking

The tests use mocking to simulate the RPLidar device and avoid the need for actual hardware. The following components are mocked:

- Serial connection
- Device responses
- Asynchronous events and queues

## Fixtures

Common test fixtures are defined in `conftest.py`:

- `mock_serial`: A mock serial connection
- `mock_lidar_response`: Mock response data for the RPLidar device
- `event_loop`: An event loop for asyncio tests
- `mock_queue`: A mock asyncio Queue
- `mock_stop_event`: A mock asyncio Event for stopping operations
