# EXFO CTP10 Vector Analyzer API

FastAPI server for controlling EXFO CTP10 vector analyzers via Pymeasure.

**Works with or without hardware!** Use mock mode for development anywhere, production mode for real measurements.

## ✨ Features

- **🎭 Mock Mode** - Develop and test without hardware
- **🔧 Production Mode** - Control real CTP10 hardware
- **📡 Real-time Streaming** - WebSocket power monitoring
- **⚡ Fast** - Binary trace data (~940k points, ~3.76MB)
- **📊 Complete Control** - TLS, RLaser, detectors, sweeps
- **✅ Tested** - 100 automated tests, 74% coverage
- **📚 Documented** - Interactive API docs (Swagger/ReDoc)

---

## 🚀 Quick Start

### Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# Clone repository
git clone <repo-url>
cd exfo-ctp10-api

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Run in Production Mode (Real Hardware)

```bash
fastapi dev app/main.py
```

Server runs on: http://localhost:8000

**Requires:** CTP10 hardware at `192.168.1.37:5025`

**Note:** FastAPI dev uses port 8000 by default. Use `--port 8002` if needed.

### Run in Mock Mode (No Hardware)

```bash
MOCK_MODE=true fastapi dev app/main.py
```

**No hardware required!** Perfect for:
- 🏠 Development from home
- 🧪 Testing and CI/CD
- 📝 Frontend development
- 🎓 Demos and training

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[Usage Guide](docs/USAGE.md)** | Complete usage for both modes, API endpoints, examples |
| **[Testing Guide](docs/TESTING.md)** | Running tests, writing tests, CI/CD integration |
| **[Deployment Guide](docs/DEPLOYMENT.md)** | Docker, Kubernetes, production deployment |
| **[Test Implementation](tests/README.md)** | Technical details of test architecture |

---

## 🔧 Configuration

### Using Environment Variables

```bash
# Mock mode (no hardware)
export MOCK_MODE=true

# Production mode (real hardware)
export MOCK_MODE=false
export CTP10_IP=192.168.1.37
```

### Using .env File

Create `.env` file in project root:

```env
# Mode selection
MOCK_MODE=true          # Set to false for real hardware

# Hardware connection (production only)
CTP10_IP=192.168.1.37
CTP10_PORT=5025
CTP10_TIMEOUT_MS=120000

# API settings
AUTO_CONNECT=true
LOG_LEVEL=INFO
API_PORT=8002
```

**See [docs/USAGE.md](docs/USAGE.md) for all configuration options.**

---

## 📡 API Endpoints

Access interactive documentation at http://localhost:8002/docs

### Connection & Status
- `GET /health` - Health check
- `GET /connection/status` - Connection status
- `POST /connection/connect` - Connect to CTP10
- `POST /connection/disconnect` - Disconnect from CTP10

### Detector Operations
- `GET /detector/snapshot` - Get 4-channel power snapshot
- `GET /detector/config` - Get detector configuration
- `POST /detector/config` - Set detector configuration
- `GET /detector/trace/data` - Get trace data (JSON)
- `GET /detector/trace/binary` - Get trace data (binary NPY)

### TLS Control (4 channels)
- `GET /tls/{channel}/config` - Get TLS configuration
- `POST /tls/{channel}/config` - Set TLS configuration
- `POST /tls/{channel}/power` - Set laser power
- `POST /tls/{channel}/wavelength` - Set wavelength range

### Reference Laser Control (10 lasers)
- `GET /rlaser/{laser}/config` - Get laser configuration
- `POST /rlaser/{laser}/config` - Set laser configuration
- `POST /rlaser/{laser}/on` - Turn laser on
- `POST /rlaser/{laser}/off` - Turn laser off

### Sweep Control
- `GET /measurement/config` - Get sweep configuration
- `POST /measurement/config` - Set sweep configuration
- `POST /measurement/sweep/start` - Start sweep
- `GET /measurement/sweep/status` - Get sweep status
- `POST /measurement/sweep/abort` - Abort sweep

### WebSocket Streaming
- `WS /ws/power` - Real-time 4-channel power streaming

**Full API documentation:** http://localhost:8002/docs

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

**Result:** 100 tests pass in ~4 seconds ✅

### Run Specific Tests

```bash
# Test specific module
pytest tests/test_detector.py -v

# Test with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

**Tests use mock automatically** - no hardware required!

**See [docs/TESTING.md](docs/TESTING.md) for complete testing guide.**

---

## 🐳 Docker

```bash
# Build image
docker build -t ctp10-api .

# Run in production mode
docker run -p 8002:8002 -e MOCK_MODE=false ctp10-api

# Run in mock mode
docker run -p 8002:8002 -e MOCK_MODE=true ctp10-api
```

**See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Kubernetes, systemd, and more.**

---

## 💡 Examples

The `examples/` directory contains usage examples:

```bash
# Start API server first
fastapi dev app/main.py

# In another terminal, run examples
python examples/test_snapshot.py          # 4-channel power snapshot
python examples/test_trace_retrieval.py   # Get full trace data
python examples/debug_websocket.py        # WebSocket streaming
```

**Examples work in both modes!**

---

## 🏗️ Architecture

### Production Mode
```
FastAPI → CTP10Manager → Real Hardware (192.168.1.37)
```

### Mock Mode
```
FastAPI → CTP10Manager → FakeCTP10 (in-memory)
```

**Same API, different backend!** Toggle with `MOCK_MODE` environment variable.

### Tech Stack

- **FastAPI** - Modern async web framework
- **Pymeasure** - Instrument control library
- **Pydantic** - Data validation
- **HTTPX** - HTTP client (for testing)
- **Pytest** - Testing framework
- **NumPy** - Numerical data handling

---

## 🔍 How It Works

### Mock Mode (`MOCK_MODE=true`)

1. API starts with `FakeCTP10` (simulated hardware)
2. All endpoints return realistic simulated data
3. No network connection required
4. Perfect for development, testing, CI/CD

### Production Mode (`MOCK_MODE=false`)

1. API connects to real CTP10 at `192.168.1.37:5025`
2. All endpoints control real hardware
3. Returns actual measurements
4. Requires hardware access

**See [docs/USAGE.md](docs/USAGE.md) for detailed explanation.**

---

## 🛠️ Development

```bash
# Install development dependencies
uv sync

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app

# Format code
ruff format app/

# Lint code
ruff check app/

# Type check
mypy app/
```

### Updating Pymeasure Dependency

This project uses a custom fork of Pymeasure from the `dev-all-instruments` branch. When changes are made to that branch, you need to update the lock file:

```bash
# Update pymeasure to latest commit from dev-all-instruments branch
uv lock --upgrade-package pymeasure

# Install the updated version
uv sync

# Restart the FastAPI server to load the new version
# (Stop the server with Ctrl+C and restart it)
```

**Why this is needed:** UV locks dependencies to specific git commits in `uv.lock`. Running `uv sync` alone will install the locked commit, not the latest one. You must use `uv lock --upgrade-package pymeasure` to fetch and lock the latest commit from the branch.

---

## 📊 Project Status

| Metric | Status |
|--------|--------|
| Tests | 100 passing ✅ |
| Coverage | 74% ✅ |
| Mock Mode | ✅ Full support |
| Production Mode | ✅ Full support |
| Documentation | ✅ Complete |
| CI/CD Ready | ✅ Yes |

---

## 🔗 API Documentation

- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc
- **OpenAPI JSON:** http://localhost:8002/openapi.json

---

## 📦 Technical Details

### Trace Data
- Up to ~940,000 points per trace
- Binary format for efficiency (~3.76MB)
- Multiple trace types (TF, Raw, Reference)
- JSON and NPY formats supported

### Connection
- VISA address format: `TCPIP::<IP>::<PORT>::SOCKET`
- Default: `TCPIP::192.168.1.37::5025::SOCKET`
- 120-second timeout for large transfers
- Auto-connect on startup (configurable)

### Module Addressing
- **Module**: SENSe module (1-20), typically 4
- **Channel**: Detector channel (1-6)
- **TLS**: Tunable laser (1-4)
- **RLaser**: Reference laser (1-10)

---

## 📚 Additional Resources

- **[Usage Guide](docs/USAGE.md)** - Comprehensive usage documentation
- **[Testing Guide](docs/TESTING.md)** - Testing and CI/CD
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Docker, Kubernetes, production
- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - FastAPI framework
- **[Pymeasure Docs](https://pymeasure.readthedocs.io/)** - Instrument control

---

## 🤝 Related Projects

- [zero-db](../zero-db) - Main measurement control application
- [suruga-seiki-ew51-api](../suruga-seiki-ew51-api) - Probe station control API

---

## 📄 License

MIT

---

## 🎯 Quick Reference

```bash
# Production mode (real hardware)
fastapi dev app/main.py

# Mock mode (no hardware)
MOCK_MODE=true fastapi dev app/main.py

# Run tests
pytest tests/ -v

# API docs
open http://localhost:8002/docs
```

**For detailed usage, see [docs/USAGE.md](docs/USAGE.md)**
