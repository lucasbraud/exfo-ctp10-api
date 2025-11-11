# EXFO CTP10 Vector Analyzer API

FastAPI server for controlling EXFO CTP10 vector analyzers via Pymeasure.

## Features

- TLS (Tunable Laser Source) configuration and sweep control (4 channels)
- Reference laser control (10 fixed-wavelength lasers)
- Trace data retrieval with binary format support (~940k points, ~3.76MB)
- Real-time power measurements
- Auto-connect on startup
- Comprehensive API documentation

## Requirements

- Python 3.10+
- EXFO CTP10 hardware
- VISA-compatible interface (TCPIP SOCKET)

## Installation

Install uv here: https://docs.astral.sh/uv/getting-started/installation/

```bash
# Clone repository
git clone <repo-url>
cd exfo-ctp10-api

# Install dependencies (includes Pymeasure from GitHub)
uv sync

# Activate virtual environment
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac
```

## Usage

```bash
# Development mode
fastapi dev app/main.py

# Production mode
fastapi run app/main.py --host 0.0.0.0 --port 8002
```

Server runs on: http://localhost:8002

API Documentation:
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc

## Configuration

Create `.env` file:

```env
# EXFO CTP10 Connection
CTP10_IP=192.168.1.37
CTP10_PORT=5025
CTP10_TIMEOUT_MS=120000

# Default Configuration
DEFAULT_MODULE=4
AUTO_CONNECT=true

# API Server
API_HOST=0.0.0.0
API_PORT=8002

# Logging
LOG_LEVEL=INFO
```

## Development

```bash
# Run tests
pytest

# Format code
ruff format app/

# Lint code
ruff check app/

# Type check
mypy app/
```

## Docker

```bash
# Build
docker build -t exfo-ctp10-api .

# Run
docker run -p 8002:8002 exfo-ctp10-api
```

## Examples

The `examples/` directory contains usage examples:
- `test_trace_retrieval.py` - Fetch and plot transmission spectrum
- `test_tls_sweep.py` - Configure TLS and perform sweep
- `test_power_reading.py` - Monitor detector power readings

Run examples:
```bash
# Make sure API server is running first
fastapi dev app/main.py

# In another terminal
python examples/test_trace_retrieval.py
```

## API Endpoints

See `/docs` for full API documentation.

### Connection
- `POST /connection/connect` - Connect to CTP10
- `POST /connection/disconnect` - Disconnect from CTP10
- `GET /connection/status` - Get connection status

### TLS Control
- `POST /tls/configure` - Configure TLS channel (wavelength, speed, power)
- `GET /tls/status/{channel}` - Get TLS channel status

### Sweep Control
- `POST /sweep/start` - Start TLS sweep
- `POST /sweep/stop` - Stop TLS sweep
- `GET /sweep/status` - Get sweep status

### Trace Data
- `POST /trace/get` - Retrieve trace data (binary format)

### Power Measurement
- `POST /power/read` - Read detector power

### Reference Lasers
- `POST /rlaser/configure` - Configure reference laser power
- `POST /rlaser/turn_on/{laser_number}` - Turn on reference laser
- `POST /rlaser/turn_off/{laser_number}` - Turn off reference laser
- `GET /rlaser/status/{laser_number}` - Get reference laser status

## Technical Details

### Trace Data Format

Trace data is retrieved in binary format for efficiency:
- **Trace Type 1**: TF live (calibrated transmission function)
- **Trace Type 11**: Raw live (uncalibrated live data)
- **Trace Type 12**: Raw reference (uncalibrated reference data)
- **Trace Type 13**: Quick reference (quick reference calibration)

Each trace can contain up to ~940,000 points (~3.76MB).

### Module and Channel Addressing

- **Module**: SENSe module number (1-20), typically 4 for vector analyzer
- **Channel**: Detector channel (1-6)
- **TLS Channel**: Tunable laser source (1-4)
- **RLaser**: Reference laser (1-10)

### Connection

VISA address format: `TCPIP::<IP>::<PORT>::SOCKET`

Default: `TCPIP::192.168.1.37::5025::SOCKET`

120-second timeout is configured for large binary transfers.

## Pymeasure Integration

This API uses the EXFO CTP10 driver from Pymeasure, installed directly from GitHub:

```
pymeasure @ git+https://github.com/lucasbraud/pymeasure.git@dev-all-instruments
```

The driver provides:
- Full SCPI command support
- Binary data format for efficient large dataset transfers
- IEEE 488.2 compliance
- 100% test coverage

## Related Projects

- [zero-db](../zero-db) - Main measurement control application
- [suruga-seiki-ew51-api](../suruga-seiki-ew51-api) - Probe station control API

## License

MIT
