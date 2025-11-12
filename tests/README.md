# Test Suite for EXFO CTP10 API

Comprehensive test suite for the FastAPI-based CTP10 Vector Analyzer API, designed to run **without requiring real hardware**.

## Overview

This test suite implements industry-standard testing practices for FastAPI applications:

- **100 automated tests** covering all API endpoints
- **Zero hardware dependency** - uses mock CTP10 instrument
- **Fast execution** - complete suite runs in ~4 seconds
- **Comprehensive coverage** - HTTP endpoints, WebSockets, validation, error handling
- **Dependency injection** - leverages FastAPI's override mechanism

## Test Structure

```
tests/
├── README.md                  # This file
├── conftest.py                # Pytest fixtures and configuration
├── mocks/
│   ├── __init__.py
│   └── mock_ctp10.py          # FakeCTP10 instrument implementation
├── test_connection.py         # Connection & health endpoints (10 tests)
├── test_detector.py           # Detector channel operations (15 tests)
├── test_websocket.py          # WebSocket streaming (9 tests)
├── test_tls.py                # TLS configuration (22 tests)
├── test_rlaser.py             # Reference laser control (25 tests)
└── test_measurement.py        # Sweep & measurement control (19 tests)
```

## Running Tests

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

### Run Specific Test Files

```bash
# Test only connection endpoints
pytest tests/test_connection.py -v

# Test only WebSocket functionality
pytest tests/test_websocket.py -v

# Test only detector endpoints
pytest tests/test_detector.py -v
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_tls.py::TestTLSConfig -v

# Run specific test function
pytest tests/test_detector.py::TestDetectorSnapshot::test_get_detector_snapshot_default_module -v
```

### Run Tests Matching a Pattern

```bash
# Run all tests with "websocket" in the name
pytest tests/ -k websocket -v

# Run all validation tests
pytest tests/ -k validation -v
```

## Architecture

### Dependency Injection Pattern

The test suite uses FastAPI's dependency override system to replace real hardware with mocks:

```python
# In conftest.py
app.dependency_overrides[get_ctp10] = lambda: mock_ctp10_instrument
```

This means:
- ✅ **100% of your application code is tested** (no changes needed)
- ✅ **Tests are isolated** from real hardware
- ✅ **Fast and deterministic** execution

### Mock Hardware (FakeCTP10)

The `FakeCTP10` class in `tests/mocks/mock_ctp10.py` implements the complete pymeasure CTP10 interface:

**Features:**
- Stateful configuration (settings persist across calls)
- Realistic detector readings with variation
- Simulated sweep lifecycle (start → scanning → complete)
- All TLS channels (1-4)
- All RLaser units (1-10)
- Mock trace data generation

**Example:**
```python
# Mock remembers configuration
fake_ctp10.tls1.laser_power_dbm = 5.0
assert fake_ctp10.tls1.laser_power_dbm == 5.0  # Stateful!
```

## Test Coverage

### Connection Endpoints (10 tests)
- ✅ Connection status (connected/disconnected)
- ✅ Manual connect/disconnect
- ✅ Condition register reading
- ✅ Error checking
- ✅ Health checks

### Detector Endpoints (15 tests)
- ✅ 4-channel power snapshot
- ✅ Detector configuration (units, wavelength)
- ✅ Reference trace creation
- ✅ Trace metadata retrieval
- ✅ Trace data (JSON and binary formats)
- ✅ Parameter validation

### WebSocket Streaming (9 tests)
- ✅ Connection and data reception
- ✅ Multiple message streaming
- ✅ Custom module/interval parameters
- ✅ Data structure validation
- ✅ Error handling (disconnected hardware)

### TLS Endpoints (22 tests)
- ✅ Full and partial configuration
- ✅ Wavelength range control
- ✅ Laser power settings
- ✅ Sweep speed configuration
- ✅ Trigger input control
- ✅ All 4 TLS channels
- ✅ Parameter validation

### RLaser Endpoints (25 tests)
- ✅ Laser identification
- ✅ Wavelength/power configuration
- ✅ On/off state control
- ✅ Multiple laser independence
- ✅ All 10 laser units
- ✅ Parameter validation

### Measurement Endpoints (19 tests)
- ✅ Resolution configuration
- ✅ Stabilization settings
- ✅ Sweep start (blocking/non-blocking)
- ✅ Sweep status monitoring
- ✅ Sweep abort
- ✅ Condition register tracking
- ✅ Complete sweep lifecycle

## Fixtures

### Available Fixtures (in conftest.py)

**`client`** - Connected TestClient with mock hardware
```python
def test_example(client):
    response = client.get("/detector/snapshot")
    assert response.status_code == 200
```

**`disconnected_client`** - TestClient without connection
```python
def test_example(disconnected_client):
    response = disconnected_client.get("/detector/snapshot")
    assert response.status_code == 503  # Not connected
```

**`mock_ctp10_instrument`** - Direct access to FakeCTP10
```python
def test_example(mock_ctp10_instrument):
    mock_ctp10_instrument.tls1.laser_power_dbm = 7.0
    assert mock_ctp10_instrument.tls1.laser_power_dbm == 7.0
```

**`mock_manager`** - CTP10Manager with mock instrument
```python
def test_example(mock_manager):
    assert mock_manager.is_connected is True
    ctp = mock_manager.ctp
```

## Writing New Tests

### Example: Testing a New Endpoint

```python
# tests/test_my_feature.py
import pytest

class TestMyFeature:
    """Test my new feature."""

    def test_get_feature(self, client):
        """Test getting feature data."""
        response = client.get("/my-feature")

        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data

    def test_set_feature(self, client):
        """Test setting feature configuration."""
        config_data = {"param": "value"}

        response = client.post("/my-feature", json=config_data)

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_feature_not_connected(self, disconnected_client):
        """Test feature fails when not connected."""
        response = disconnected_client.get("/my-feature")

        assert response.status_code == 503
```

### Testing WebSocket Endpoints

```python
def test_my_websocket(client):
    """Test WebSocket endpoint."""
    with client.websocket_connect("/ws/my-stream") as websocket:
        # Receive data
        data = websocket.receive_json()

        # Validate structure
        assert "field" in data
        assert isinstance(data["field"], (int, float))
```

## Best Practices

1. **Use descriptive test names** - Test name should describe what is being tested
2. **One assertion per concept** - Keep tests focused
3. **Test both success and failure** - Happy path AND error cases
4. **Use parametrize for variations** - Test multiple inputs efficiently
5. **Verify state changes** - After POST, GET to confirm changes applied
6. **Clean fixtures** - Let conftest handle setup/teardown

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      - name: Run tests
        run: pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Run with detailed output
```bash
pytest tests/ -vv --tb=long
```

### Run with print statements visible
```bash
pytest tests/ -s
```

### Drop into debugger on failure
```bash
pytest tests/ --pdb
```

### Run only failed tests from last run
```bash
pytest tests/ --lf
```

## Performance

- **Total tests:** 100
- **Execution time:** ~4 seconds
- **Average per test:** 40ms

The test suite is designed for speed:
- No network I/O
- No hardware delays
- Minimal async overhead
- Efficient fixtures

## Extending the Mock

To add new hardware features to `FakeCTP10`:

```python
# tests/mocks/mock_ctp10.py

class FakeCTP10:
    def __init__(self):
        # ... existing code ...
        self._my_new_feature = 0

    @property
    def my_new_feature(self):
        return self._my_new_feature

    @my_new_feature.setter
    def my_new_feature(self, value):
        self._my_new_feature = value
```

Then write tests that use the mock:

```python
def test_new_feature(client):
    response = client.get("/my-feature")
    # Mock will return the value set in FakeCTP10
```

## Troubleshooting

**Issue:** Tests fail with "Not connected to CTP10"
- **Solution:** Use the `client` fixture, not `disconnected_client`

**Issue:** WebSocket test hangs
- **Solution:** Ensure you're using `with client.websocket_connect()` context manager

**Issue:** Test passes locally but fails in CI
- **Solution:** Check for timing assumptions; add appropriate timeouts

**Issue:** Mock behavior doesn't match real hardware
- **Solution:** Update `FakeCTP10` in `tests/mocks/mock_ctp10.py`

## Resources

- [FastAPI Testing Docs](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI WebSocket Testing](https://fastapi.tiangolo.com/advanced/testing-websockets/)

## Summary

✅ **100 tests passing**
✅ **Zero hardware dependency**
✅ **Fast and deterministic**
✅ **Industry-standard patterns**
✅ **Easy to extend**

You can now develop and test your CTP10 API from anywhere - home, CI/CD, or in the lab!
