# Testing Guide for EXFO CTP10 API

This guide walks you through testing the refactored CTP10 API step by step.

## Prerequisites

1. **CTP10 Hardware**: Ensure your CTP10 is powered on and connected to the network
2. **Network Access**: Verify you can ping the CTP10 IP address (default: 192.168.1.37)
3. **Python Environment**: Ensure dependencies are installed

## Step 1: Verify Configuration

Check your `.env` file or configuration settings:

```bash
# View current configuration
cat app/.env
```

Expected values:
```env
CTP10_ADDRESS=TCPIP::192.168.1.37::5025::SOCKET
API_PORT=8002
LOG_LEVEL=INFO
AUTO_CONNECT=true
CTP10_TIMEOUT_MS=120000
```

**Note**: If `AUTO_CONNECT=true`, the API will attempt to connect to the CTP10 on startup.

## Step 2: Start the API Server

### Option A: Development Mode (Recommended for Testing)

```bash
# From the exfo-ctp10-api directory
fastapi dev app/main.py --port 8002
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting EXFO CTP10 API...
INFO:     CTP10 address: TCPIP::192.168.1.37::5025::SOCKET
INFO:     CTP10 manager initialized
INFO:     Auto-connect successful: EXFO,CTP10,<serial>,<firmware>
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002
```

### Option B: Production Mode

```bash
fastapi run app/main.py
```

## Step 3: Check API Health

Open a new terminal and test basic connectivity:

```bash
# Test root endpoint
curl http://localhost:8002/

# Expected: {"service":"EXFO CTP10 Vector Analyzer API","version":"1.0.0","status":"running"}

# Test health endpoint
curl http://localhost:8002/health

# Expected: {"status":"healthy","connected":true,"timestamp":"2025-11-10T..."}
```

## Step 4: Interactive API Documentation

Open your web browser and navigate to:

```
http://localhost:8002/docs
```

This provides an interactive Swagger UI where you can:
- Browse all available endpoints
- Test endpoints directly from the browser
- View request/response schemas
- See example values

## Step 5: Test Connection Endpoints

### Check Connection Status

```bash
curl http://localhost:8002/connection/status
```

Expected response:
```json
{
  "connected": true,
  "instrument_id": "EXFO,CTP10,<serial>,<firmware>",
  "address": "TCPIP::192.168.1.37::5025::SOCKET"
}
```

### Manual Connect (if AUTO_CONNECT=false)

```bash
curl -X POST http://localhost:8002/connection/connect
```

### Check Condition Register

```bash
curl http://localhost:8002/connection/condition
```

Expected response:
```json
{
  "register_value": 0,
  "is_idle": true,
  "bits": {
    "zeroing": false,
    "calibrating": false,
    "scanning": false,
    "analyzing": false,
    "aborting": false,
    "armed": false,
    "referencing": false,
    "quick_referencing": false
  }
}
```

## Step 6: Test Detector Endpoints

### Read Power

```bash
# Default module/channel (4/1)
curl "http://localhost:8002/detector/power?module=4&channel=1"
```

Expected response:
```json
{
  "module": 4,
  "channel": 1,
  "power": -15.23,
  "unit": "DBM"
}
```

### Get Detector Configuration

```bash
curl "http://localhost:8002/detector/config?module=4&channel=1"
```

Expected response:
```json
{
  "module": 4,
  "channel": 1,
  "power_unit": "DBM",
  "spectral_unit": "WAV",
  "trigger": 0
}
```

## Step 7: Test TLS Endpoints

### Get TLS Configuration

```bash
curl http://localhost:8002/tls/1/config
```

Expected response:
```json
{
  "channel": 1,
  "start_wavelength_nm": 1500.0,
  "stop_wavelength_nm": 1600.0,
  "sweep_speed_nmps": 50,
  "laser_power_dbm": 5.0,
  "trigin": 0
}
```

### Configure TLS

```bash
curl -X POST http://localhost:8002/tls/1/config \
  -H "Content-Type: application/json" \
  -d '{
    "start_wavelength_nm": 1520.0,
    "stop_wavelength_nm": 1580.0,
    "sweep_speed_nmps": 40,
    "laser_power_dbm": 3.0
  }'
```

## Step 8: Test RLaser Endpoints

### Get RLaser Configuration

```bash
curl http://localhost:8002/rlaser/1/config
```

Expected response:
```json
{
  "laser_number": 1,
  "id": "EXFO,T100S-HP,0,6.06",
  "wavelength_nm": 1550.0,
  "power_dbm": 5.0,
  "is_on": false
}
```

### Get RLaser ID

```bash
curl http://localhost:8002/rlaser/1/id
```

## Step 9: Test Measurement/Sweep Endpoints

### Get Sweep Configuration

```bash
curl http://localhost:8002/measurement/config
```

Expected response:
```json
{
  "resolution_pm": 10.0,
  "stabilization_output": 0,
  "stabilization_duration": 0.0
}
```

### Start a Sweep (Non-blocking)

```bash
# Start sweep without waiting
curl -X POST "http://localhost:8002/measurement/sweep/start?wait=false"
```

### Check Sweep Status

```bash
curl http://localhost:8002/measurement/sweep/status
```

Expected response (while sweeping):
```json
{
  "is_sweeping": true,
  "is_complete": false,
  "condition_register": 4
}
```

Expected response (after completion):
```json
{
  "is_sweeping": false,
  "is_complete": true,
  "condition_register": 0
}
```

## Step 10: Run Example Scripts

### Test Power Reading

```bash
cd examples
python test_power_reading.py
```

Expected output:
```
Connecting to CTP10 via API...
Connected: EXFO,CTP10,<serial>,<firmware>

Getting detector configuration (Module 4, Channel 1)...
  Power unit: DBM
  Spectral unit: WAV
  Trigger: 0

Reading power from IN1 (Channel 1)...
  Module: 4
  Channel: 1
  Power: -15.234 DBM
...
```

### Test Trace Retrieval (Full Sweep)

**Warning**: This will perform a full sweep and download ~940k points. It may take 2-5 minutes.

```bash
python test_trace_retrieval.py
```

Expected output:
```
Connecting to CTP10 via API...
Connected: EXFO,CTP10,<serial>,<firmware>

Current sweep configuration:
  Resolution: 10.00 pm
  ...

Initiating sweep...
  Sweep completed!

Downloading trace data in binary format...
  Downloaded TF live: 937984 points
  Downloaded Raw live: 937984 points
  Downloaded Raw reference: 937984 points

Generating plot...
[Plot window opens]
```

### Test TLS Sweep

```bash
python test_tls_sweep.py
```

### Test RLaser Configuration

```bash
python test_rlaser_config.py
```

## Step 11: Test with HTTP Client Tools

### Using HTTPie (if installed)

```bash
# Install HTTPie
pip install httpie

# Test endpoints
http GET localhost:8002/health
http GET localhost:8002/detector/power module==4 channel==1
http POST localhost:8002/tls/1/config start_wavelength_nm:=1520.0 stop_wavelength_nm:=1580.0
```

### Using Postman

1. Import the OpenAPI schema from `http://localhost:8002/openapi.json`
2. Test endpoints interactively

## Troubleshooting

### Issue: "Not connected to CTP10"

**Solution**:
```bash
# Check connection status
curl http://localhost:8002/connection/status

# If not connected, connect manually
curl -X POST http://localhost:8002/connection/connect
```

### Issue: Connection timeout

**Symptoms**: API hangs during startup or connection

**Solutions**:
1. Check CTP10 is powered on and accessible:
   ```bash
   ping 192.168.1.37
   ```

2. Verify VISA address in configuration:
   ```bash
   cat app/.env
   # Should be: TCPIP::192.168.1.37::5025::SOCKET
   ```

3. Set `AUTO_CONNECT=false` to start API without connecting:
   ```env
   AUTO_CONNECT=false
   ```

### Issue: Example script fails with connection error

**Solution**:
1. Ensure API server is running on port 8002
2. Check `API_BASE` in example script matches server port
3. Test basic connectivity: `curl http://localhost:8002/health`

### Issue: Binary trace download times out

**Symptoms**: Request times out when downloading trace data

**Solution**:
Increase timeout in example scripts:
```python
response = requests.get(
    f"{API_BASE}/detector/trace/binary",
    params={...},
    timeout=300  # Increase from 120 to 300 seconds
)
```

### Issue: Sweep never completes

**Solution**:
1. Check sweep status: `curl http://localhost:8002/measurement/sweep/status`
2. Check condition register: `curl http://localhost:8002/connection/condition`
3. Abort and retry: `curl -X POST http://localhost:8002/measurement/sweep/abort`
4. Verify TLS configuration is valid

### Issue: Port 8002 already in use

**Solution**:
```bash
# Find process using port 8002
netstat -ano | findstr :8002

# Kill the process or use a different port
fastapi dev app/main.py --port 8003
```

## Quick Test Checklist

- [ ] API server starts without errors
- [ ] `/health` endpoint returns "healthy" status
- [ ] `/connection/status` shows "connected: true"
- [ ] Can read detector power
- [ ] Can get TLS configuration
- [ ] Can get RLaser configuration
- [ ] Can get sweep configuration
- [ ] Can start and monitor a sweep
- [ ] `test_power_reading.py` runs successfully
- [ ] API documentation accessible at `/docs`

## Testing Best Practices

1. **Start Simple**: Test basic endpoints before complex operations
2. **Check Logs**: Monitor API server logs for errors
3. **Use /docs**: Interactive documentation is the fastest way to test
4. **Verify Hardware**: Ensure CTP10 is in a known good state before testing
5. **Incremental Testing**: Test one router at a time (connection → detector → tls → rlaser → measurement)

## Next Steps After Testing

Once basic testing is complete:

1. **Integration Testing**: Test full workflows (configure → sweep → retrieve data)
2. **Performance Testing**: Measure trace download times with different formats
3. **Error Handling**: Test invalid inputs and error conditions
4. **Hardware Validation**: Compare API results with CTP10 front panel readings

## Need Help?

- Check API logs in the terminal where server is running
- Review endpoint documentation at `/docs`
- Examine example scripts in `examples/` directory
- Check `examples/README.md` for detailed endpoint reference
