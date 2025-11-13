# Usage Guide

Complete guide for using the EXFO CTP10 API in both production and mock modes.

## Table of Contents
- [Quick Start](#quick-start)
- [Two Modes Explained](#two-modes-explained)
- [Environment Configuration](#environment-configuration)
- [Common Commands](#common-commands)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Production Mode (Real Hardware)
```bash
source .venv/bin/activate
fastapi dev app/main.py
```

### Mock Mode (No Hardware Required)
```bash
source .venv/bin/activate
MOCK_MODE=true fastapi dev app/main.py
```

---

## Two Modes Explained

### Production Mode
- **Connects to:** Real CTP10 hardware at `192.168.1.37:5025`
- **Use when:** In lab with hardware access
- **Returns:** Actual measurements from hardware
- **Requires:** CTP10 powered on and network accessible

### Mock Mode
- **Connects to:** FakeCTP10 (simulated hardware)
- **Use when:** Developing from home, testing, CI/CD
- **Returns:** Simulated realistic data
- **Requires:** Nothing - works anywhere!

---

## Environment Configuration

### Using Environment Variables

```bash
# Set mock mode
export MOCK_MODE=true
fastapi dev app/main.py

# Or inline
MOCK_MODE=true fastapi dev app/main.py
```

### Using .env File (Recommended)

Create or edit `.env` in project root:

```bash
# For development (mock mode)
MOCK_MODE=true
AUTO_CONNECT=false
LOG_LEVEL=DEBUG

# For production (real hardware)
MOCK_MODE=false
AUTO_CONNECT=true
CTP10_IP=192.168.1.37
CTP10_PORT=5025
```

Then simply run:
```bash
fastapi dev app/main.py
```

### All Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `false` | Use mock hardware instead of real CTP10 |
| `AUTO_CONNECT` | `true` | Auto-connect to hardware on startup |
| `CTP10_IP` | `192.168.1.37` | CTP10 IP address |
| `CTP10_PORT` | `5025` | CTP10 SCPI port |
| `CTP10_TIMEOUT_MS` | `120000` | Connection timeout (milliseconds) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8002` | API server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

---

## Common Commands

```bash
# Activate environment
source .venv/bin/activate

# Production mode (real hardware)
fastapi dev app/main.py

# Mock mode (no hardware)
MOCK_MODE=true fastapi dev app/main.py

# Production deployment
fastapi run app/main.py --host 0.0.0.0 --port 8002

# Mock deployment
MOCK_MODE=true fastapi run app/main.py --host 0.0.0.0 --port 8002

# With custom uvicorn options
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Mock with uvicorn
MOCK_MODE=true uvicorn app.main:app --reload
```

---

## API Endpoints

All endpoints work in both modes!

### Interactive Documentation
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc
- **OpenAPI:** http://localhost:8002/openapi.json

### Health & Status
```bash
# Health check
curl http://localhost:8002/health

# Connection status
curl http://localhost:8002/connection/status

# Condition register
curl http://localhost:8002/connection/condition
```

### Detector Operations
```bash
# Get 4-channel snapshot
curl http://localhost:8002/detector/snapshot

# Get detector config
curl http://localhost:8002/detector/config?module=4&channel=1

# Set detector config
curl -X POST http://localhost:8002/detector/config?module=4&channel=1 \
  -H "Content-Type: application/json" \
  -d '{"power_unit": "DBM"}'

# Get trace metadata
curl http://localhost:8002/detector/trace/metadata?module=4&channel=1&trace_type=1

# Get trace data (JSON)
curl http://localhost:8002/detector/trace/data?module=4&channel=1&trace_type=1
```

### TLS Operations
```bash
# Get TLS config (channel 1-4)
curl http://localhost:8002/tls/1/config

# Set TLS config
curl -X POST http://localhost:8002/tls/1/config \
  -H "Content-Type: application/json" \
  -d '{
    "start_wavelength_nm": 1520.0,
    "stop_wavelength_nm": 1580.0,
    "laser_power_dbm": 5.0
  }'

# Set TLS power
curl -X POST "http://localhost:8002/tls/1/power?power_dbm=7.0"
```

### RLaser Operations
```bash
# Get RLaser config (laser 1-10)
curl http://localhost:8002/rlaser/1/config

# Set RLaser power
curl -X POST "http://localhost:8002/rlaser/1/power?power_dbm=8.0"

# Turn laser on
curl -X POST http://localhost:8002/rlaser/1/on

# Turn laser off
curl -X POST http://localhost:8002/rlaser/1/off
```

### Measurement Operations
```bash
# Get sweep config
curl http://localhost:8002/measurement/config

# Set resolution
curl -X POST "http://localhost:8002/measurement/resolution?resolution_pm=10.0"

# Start sweep (non-blocking)
curl -X POST "http://localhost:8002/measurement/sweep/start?wait=false"

# Get sweep status
curl http://localhost:8002/measurement/sweep/status

# Abort sweep
curl -X POST http://localhost:8002/measurement/sweep/abort
```

### WebSocket Streaming
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8002/ws/power?module=4&interval=0.1');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`CH1: ${data.ch1_power} ${data.unit}`);
    console.log(`CH2: ${data.ch2_power} ${data.unit}`);
    console.log(`CH3: ${data.ch3_power} ${data.unit}`);
    console.log(`CH4: ${data.ch4_power} ${data.unit}`);
};
```

---

## Examples

### Example 1: Development from Home

```bash
# Set mock mode in .env
echo "MOCK_MODE=true" >> .env

# Start server
fastapi dev app/main.py

# Test with curl
curl http://localhost:8002/detector/snapshot

# Or open browser
open http://localhost:8002/docs
```

### Example 2: Production in Lab

```bash
# Ensure mock mode is disabled
sed -i '' '/MOCK_MODE/d' .env

# Or explicitly set to false
echo "MOCK_MODE=false" >> .env

# Start server
fastapi dev app/main.py

# Server connects to real hardware at 192.168.1.37
```

### Example 3: Quick Mode Switch

```bash
# Work in mock mode
MOCK_MODE=true fastapi dev app/main.py

# Switch to production (in another terminal)
fastapi dev app/main.py
```

### Example 4: Frontend Development

```bash
# Terminal 1: Start mock API
MOCK_MODE=true fastapi dev app/main.py

# Terminal 2: Start your frontend
cd frontend
npm start

# Frontend calls http://localhost:8002/api/*
# No hardware needed!
```

---

## Troubleshooting

### "Failed to connect to CTP10" (Production Mode)

**Check hardware:**
```bash
ping 192.168.1.37
```

**Disable auto-connect:**
```bash
export AUTO_CONNECT=false
fastapi dev app/main.py
```

**Verify settings:**
- Check `.env` file for correct CTP10_IP
- Ensure CTP10 is powered on
- Check network connectivity
- Verify firewall rules

### Mock Mode Not Working

**Verify MOCK_MODE is set:**
```bash
# Check environment
env | grep MOCK_MODE

# Should show: MOCK_MODE=true
```

**Check startup logs:**
Look for:
```
🎭 MOCK MODE - Using FakeCTP10 (NO REAL HARDWARE)
```

If you see:
```
🔧 PRODUCTION MODE - Using real CTP10 hardware
```
Then MOCK_MODE is not set correctly.

### Port Already in Use

```bash
# Find process using port 8002
lsof -i :8002

# Kill it or use different port
fastapi dev app/main.py --port 8003
```

### WebSocket Connection Issues

**Check CORS settings:**
The API allows all origins by default, but verify in `app/main.py`:
```python
allow_origins=["*"]
```

**Test WebSocket:**
```bash
# Use wscat (install: npm install -g wscat)
wscat -c ws://localhost:8002/ws/power?module=4&interval=0.5
```

---

## Best Practices

### Development Workflow

1. **Development (Home):**
   ```bash
   echo "MOCK_MODE=true" >> .env
   fastapi dev app/main.py
   ```

2. **Testing:**
   ```bash
   pytest tests/ -v
   ```

3. **Lab Testing (Real Hardware):**
   ```bash
   sed -i '' '/MOCK_MODE/d' .env
   fastapi dev app/main.py
   ```

4. **Production Deployment:**
   ```bash
   MOCK_MODE=false fastapi run app/main.py --host 0.0.0.0
   ```

### Configuration Management

**Local development:**
- Use `.env` file
- Add `.env` to `.gitignore`
- Keep `.env.example` with template

**Production:**
- Use environment variables (not .env file)
- Set via Docker, K8s, or systemd
- Never commit secrets

**CI/CD:**
- Always use `MOCK_MODE=true`
- Set in pipeline configuration
- No hardware required

---

## Additional Resources

- **Testing Guide:** [docs/TESTING.md](TESTING.md)
- **Deployment Guide:** [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- **Test Implementation:** [tests/README.md](../tests/README.md)
- **Main README:** [README.md](../README.md)
