# EXFO CTP10 API - Example Scripts

This directory contains example scripts demonstrating how to use the EXFO CTP10 Vector Analyzer REST API. These examples are based on the [pymeasure-examples](https://github.com/lucasbraud/pymeasure/tree/dev-all-instruments) for the CTP10.

## Prerequisites

```bash
# Install required Python packages
pip install requests numpy matplotlib
```

## API Configuration

All examples assume the API is running locally on port 8000 (FastAPI dev default). Update the `API_BASE` constant in each script if your configuration differs:

```python
API_BASE = "http://localhost:8000"
```

### Starting the API

```bash
# From the exfo-ctp10-api directory
fastapi dev app/main.py

# Or with custom port
fastapi dev app/main.py --port 8002
```

## Example Scripts

### 1. `test_snapshot.py`

**Purpose**: Demonstrates the simplified 4-channel power snapshot API.

**Features**:
- Get all 4 channel power readings in a single request
- Continuous power monitoring (5 samples)
- Channel mapping: IN1, IN2, TLS IN, OUT TO DUT
- Simplest way to read detector power

**Usage**:
```bash
python examples/test_snapshot.py
```

**Key Endpoints Used**:
- `GET /detector/snapshot` - Get 4-channel power snapshot

---

### 2. `test_trace_retrieval.py`

**Purpose**: Demonstrates trace data retrieval and plotting with binary download.

**Based on**: `pymeasure-examples/exfo/exfo_ctp10_detector_example.py`

**Features**:
- Connect to CTP10 and read sweep configuration
- Configure TLS parameters (wavelength range, speed, power)
- Initiate sweep and wait for completion
- Configure detector settings (power unit, spectral unit)
- Read instantaneous power
- Get trace metadata (length, sampling, start wavelength)
- Download trace data in efficient binary NPY format (~940k points)
- Plot multiple traces: TF live, Raw live, Raw reference

**Trace Types**:
- `trace_type=1`: TF live (Transmission Function, calibrated)
- `trace_type=11`: Raw live
- `trace_type=12`: Raw reference
- `trace_type=13`: Raw quick reference

**Usage**:
```bash
python examples/test_trace_retrieval.py
```

**Key Endpoints Used**:
- `POST /connection/connect` - Connect to instrument
- `GET /measurement/config` - Get sweep configuration
- `GET /tls/{channel}/config` - Get TLS configuration
- `POST /measurement/sweep/start?wait=true` - Start sweep and wait
- `POST /detector/config` - Configure detector units
- `GET /detector/power` - Read instantaneous power
- `GET /detector/trace/metadata` - Get trace information
- `GET /detector/trace/binary` - Download binary trace data (NPY format)

**Binary Format**:
The binary endpoint returns numpy NPY format with structured array:
```python
data = np.load(buffer)
wavelengths = data['wavelengths']  # nm
values = data['values']  # dB
```

---

### 3. `test_rlaser_config.py`

**Purpose**: Demonstrates reference laser configuration and control.

**Features**:
- Connect to CTP10 via API
- Get reference laser identification (manufacturer, model, serial, firmware)
- Get complete laser configuration (wavelength, power, state)
- Read individual laser parameters
- Configure laser wavelength and power
- Control laser output state (on/off)
- Configure multiple parameters at once
- Query multiple lasers

**RLaser Channels**: 1-10 (access via API endpoint path parameter)

**Usage**:
```bash
python examples/test_rlaser_config.py
```

**Key Endpoints Used**:
- `POST /connection/connect` - Connect to instrument
- `GET /rlaser/{laser_number}/id` - Get laser identification
- `GET /rlaser/{laser_number}/config` - Get complete configuration
- `POST /rlaser/{laser_number}/config` - Configure multiple parameters
- `GET /rlaser/{laser_number}/wavelength` - Get wavelength
- `POST /rlaser/{laser_number}/wavelength` - Set wavelength
- `GET /rlaser/{laser_number}/power` - Get power
- `POST /rlaser/{laser_number}/power` - Set power
- `GET /rlaser/{laser_number}/state` - Get output state
- `POST /rlaser/{laser_number}/on` - Turn laser on
- `POST /rlaser/{laser_number}/off` - Turn laser off

---

## API Structure Overview

The API follows a hardware-centric structure matching the CTP10 architecture:

### Connection
- `/connection/connect` - Connect to CTP10
- `/connection/disconnect` - Disconnect from CTP10
- `/connection/status` - Get connection status
- `/connection/condition` - Get condition register
- `/connection/check_errors` - Check for instrument errors

### Detector (Module 1-20, Channel 1-6)
- `/detector/power?module=4&channel=1` - Read instantaneous power
- `/detector/config?module=4&channel=1` - Get/set detector configuration
- `/detector/reference?module=4&channel=1` - Create reference trace
- `/detector/trace/metadata?module=4&channel=1&trace_type=1` - Get trace metadata
- `/detector/trace/data?module=4&channel=1&trace_type=1` - Get trace data (JSON)
- `/detector/trace/binary?module=4&channel=1&trace_type=1` - Get trace data (NPY)

### Measurement (Sweep Control)
- `/measurement/config` - Get/set sweep configuration (resolution, stabilization)
- `/measurement/resolution` - Get/set wavelength sampling resolution
- `/measurement/stabilization` - Get/set laser stabilization settings
- `/measurement/sweep/start?wait=false` - Initiate sweep
- `/measurement/sweep/abort` - Abort sweep
- `/measurement/sweep/status` - Get sweep status
- `/measurement/sweep/wavelengths` - Get/set global instrument sweep start/stop wavelengths (CTP10-level)

### TLS (Channels 1-4)

**Note**: Setting the `identifier` property automatically configures all TLS parameters for the selected laser:
- **identifier=1** (C-band): Configures wavelength range (1502-1627nm), power (8dBm), sweep speed (20nm/s), trigin (1)
- **identifier=2** (O-band): Configures wavelength range (1262.5-1355nm), power (10dBm), sweep speed (20nm/s), trigin (2)

**Endpoints**:
- `/tls/{channel}/config` - Get/set complete TLS configuration
- `/tls/{channel}/wavelength` - Get/set wavelength range
- `/tls/{channel}/power` - Get/set laser power
- `/tls/{channel}/speed` - Get/set sweep speed
- `/tls/{channel}/trigger` - Get/set trigger input

### RLaser (Channels 1-10)
- `/rlaser/{laser_number}/config` - Get/set complete laser configuration
- `/rlaser/{laser_number}/id` - Get laser identification
- `/rlaser/{laser_number}/wavelength` - Get/set wavelength
- `/rlaser/{laser_number}/power` - Get/set power
- `/rlaser/{laser_number}/state` - Get output state
- `/rlaser/{laser_number}/on` - Turn laser on
- `/rlaser/{laser_number}/off` - Turn laser off

## Default Values

The API uses these default values from the pymeasure examples:

```python
MODULE = 4              # SENSe module (1-20)
CHANNEL = 1             # Detector channel (1-6)
RESOLUTION_PM = 10.0    # Wavelength sampling resolution (pm)
```

## Common Patterns

### Error Handling
All examples use `response.raise_for_status()` to check for HTTP errors:

```python
response = requests.get(f"{API_BASE}/detector/power", params={"module": 4, "channel": 1})
response.raise_for_status()  # Raises exception for 4xx/5xx errors
data = response.json()
```

### Query Parameters vs JSON Body
- **Query parameters**: Used for simple values (module, channel, trace_type)
- **JSON body**: Used for complex configuration objects

```python
# Query parameters
response = requests.get("/detector/power", params={"module": 4, "channel": 1})

# JSON body
response = requests.post("/tls/1/config", json={"start_wavelength_nm": 1500.0, ...})
```

### Binary Data Download
For efficient transfer of large trace datasets (~940k points):

```python
response = requests.get("/detector/trace/binary", params={...}, timeout=120)
buffer = io.BytesIO(response.content)
data = np.load(buffer)
wavelengths = data['wavelengths']
values = data['values']
```

## Troubleshooting

### Connection Issues
- Ensure the API server is running: `fastapi dev app/main.py`
- Check the CTP10 IP address in `app/.env` or `app/config.py`
- Verify network connectivity to the CTP10

### Timeout Errors
- Increase timeout for large binary transfers: `timeout=120`
- Check CTP10 connection timeout in API configuration (default: 120000ms)

### Sweep Not Completing
- Check sweep configuration (wavelength range, speed)
- Monitor sweep status: `GET /measurement/sweep/status`
- Check condition register: `GET /connection/condition`

## API Documentation

Access the interactive API documentation (Swagger UI) when the server is running:

```
http://localhost:8000/docs
```

## Related Resources

- [Pymeasure CTP10 Driver](https://github.com/lucasbraud/pymeasure/tree/dev-all-instruments)
- [Pymeasure Examples](https://github.com/lucasbraud/pymeasure/tree/dev-all-instruments/examples/exfo)
- [EXFO CTP10 Documentation](https://www.exfo.com/en/products/optical-test/lab-and-manufacturing-solutions/ctp10-component-test-platform/)

---

### 4. `instrument_sweep_wavelength.py`

**Purpose**: Demonstrates instrument-level (global) sweep wavelength configuration distinct from TLS channel settings.

**Features**:
- Query current global sweep start/stop wavelengths
- Set one or both limits and view effective (normalized) values returned by firmware
- Re-query to confirm final state

**Usage**:
```bash
python examples/instrument_sweep_wavelength.py --host http://localhost:8000 --start 1525 --stop 1565
```

**Key Endpoint Used**:
- `GET /measurement/sweep/wavelengths`
- `POST /measurement/sweep/wavelengths`

Note: These limits are global and may auto-adjust interplay; always re-query after setting.
