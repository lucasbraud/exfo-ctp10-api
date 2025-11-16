# WebSocket Gold Standard Implementation

## 🏆 Industry-Standard WebSocket Architecture

This document describes the **production-ready** WebSocket implementation with heartbeat, reconnection logic, and connection management.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Integration](#frontend-integration)
4. [Migration Guide](#migration-guide)
5. [Testing & Monitoring](#testing--monitoring)

---

## Architecture Overview

### Key Features

#### Backend (FastAPI)
- ✅ **Connection Manager** - Track multiple clients, broadcast support
- ✅ **Heartbeat/Ping-Pong** - Detect stale connections (30s interval)
- ✅ **Graceful Degradation** - Handle hardware errors without dropping connections
- ✅ **Backpressure Handling** - Proper error recovery
- ✅ **Multi-client Support** - Independent streams per client

#### Frontend (React)
- ✅ **Automatic Reconnection** - Exponential backoff (1s → 30s max)
- ✅ **Heartbeat Monitoring** - Detect silent connection drops (60s timeout)
- ✅ **Connection State Machine** - CONNECTING → CONNECTED → RECONNECTING → DISCONNECTED
- ✅ **Graceful Cleanup** - Proper unmount handling
- ✅ **TypeScript** - Full type safety

### Message Types

```typescript
// 1. Data Message (normal operation)
{
  type: "data",
  timestamp: 1234567890.123,
  module: 4,
  wavelength_nm: 1310.0,
  unit: "dBm",
  ch1_power: -17.85,
  ch2_power: -21.56,
  ch3_power: 6.94,
  ch4_power: -60.12
}

// 2. Heartbeat (every 30s from server)
{
  type: "heartbeat",
  timestamp: "2024-01-01T12:00:00",
  active_streams: 3
}

// 3. Error (recoverable)
{
  type: "error",
  message: "Hardware temporarily unavailable",
  timestamp: "2024-01-01T12:00:00",
  recoverable: true,
  error_count: 2
}

// 4. Reconnect Request (from server)
{
  type: "reconnect",
  reason: "Server maintenance",
  retry_after: 5
}
```

---

## Backend Implementation

### Step 1: Add New Router to `main.py`

```python
# app/main.py

from app.routers import connection, detector, measurement, tls, rlaser, websocket, websocket_v2

# ... existing code ...

# Include the V2 WebSocket router
app.include_router(websocket_v2.router)
```

### Step 2: Test the Endpoint

```bash
# Terminal 1: Start server
MOCK_MODE=true fastapi dev app/main.py --port=8002

# Terminal 2: Test with wscat (install: npm install -g wscat)
wscat -c "ws://localhost:8002/api/v1/ws/v2/power?module=4&interval=0.1"

# You should see:
# Connected
# < {"type":"data","timestamp":1234567890.123,...}
# < {"type":"data",...}
# < {"type":"heartbeat","timestamp":"2024-01-01T12:00:00","active_streams":1}
```

### Step 3: Health Check Endpoint

For lightweight connection monitoring:

```bash
wscat -c "ws://localhost:8002/api/v1/ws/v2/health"

# Send ping:
> ping

# Receive:
< {"type":"pong","timestamp":"2024-01-01T12:00:00"}
< {"type":"heartbeat","timestamp":"2024-01-01T12:00:00","active_streams":1}
```

---

## Frontend Integration

### Step 1: Use the Hook

Replace your existing WebSocket code in `laser.tsx`:

```typescript
// frontend/src/routes/_layout/laser.tsx

import { useWebSocketWithReconnect, WebSocketStatus } from '@/hooks/useWebSocketWithReconnect'

function LaserControl() {
  const queryClient = useQueryClient()
  
  // ... other state ...
  
  // Replace the existing useEffect WebSocket with this:
  const {
    status: wsStatus,
    lastMessage,
    reconnectAttempt
  } = useWebSocketWithReconnect({
    url: `${wsProtocol}//${parsed.host}/api/v1/ws/v2/power?module=${detectorModule}&interval=0.1`,
    shouldConnect: status?.connected === true,
    autoReconnect: true,
    maxReconnectAttempts: 10,
    heartbeatTimeout: 60000,
    onMessage: (message) => {
      if (message.type === 'data') {
        setWsData({
          ch1_power: message.ch1_power,
          ch2_power: message.ch2_power,
          ch3_power: message.ch3_power,
          ch4_power: message.ch4_power,
          wavelength_nm: message.wavelength_nm,
          unit: message.unit,
          timestamp: message.timestamp
        })
      } else if (message.type === 'error') {
        console.warn('WebSocket error:', message.message)
      }
    },
    onOpen: () => {
      console.log('WebSocket connected')
    },
    onClose: () => {
      console.log('WebSocket disconnected')
      setWsData(null)
    }
  })
  
  // Update UI based on status
  const wsConnected = wsStatus === WebSocketStatus.CONNECTED
  const wsReconnecting = wsStatus === WebSocketStatus.RECONNECTING
  
  // ... rest of component ...
  
  return (
    <Container>
      {/* Show connection status */}
      <HStack>
        {wsReconnecting && (
          <Badge colorPalette="orange">
            Reconnecting... (attempt {reconnectAttempt})
          </Badge>
        )}
        {wsConnected && (
          <Badge colorPalette="green">Live Data</Badge>
        )}
      </HStack>
      
      {/* ... rest of UI ... */}
    </Container>
  )
}
```

### Step 2: Update Badge Display

```typescript
// Show reconnection status in UI
{statusLoading ? (
  <Badge colorPalette="gray">Checking...</Badge>
) : statusError ? (
  <Badge colorPalette="red">Service Unavailable</Badge>
) : status?.connected ? (
  <>
    <Badge colorPalette="green">Connected</Badge>
    {wsStatus === WebSocketStatus.CONNECTED && (
      <Badge colorPalette="blue">Live Data</Badge>
    )}
    {wsStatus === WebSocketStatus.RECONNECTING && (
      <Badge colorPalette="orange">
        Reconnecting ({reconnectAttempt}/{10})
      </Badge>
    )}
  </>
) : (
  <Badge colorPalette="red">Disconnected</Badge>
)}
```

---

## Migration Guide

### Current Implementation (Basic)

```typescript
// ❌ OLD: Basic WebSocket (no reconnection)
useEffect(() => {
  const ws = new WebSocket(url)
  ws.onmessage = (e) => setData(JSON.parse(e.data))
  return () => ws.close()
}, [url])
```

### Gold Standard Implementation

```typescript
// ✅ NEW: Production-ready with reconnection
const { lastMessage, status } = useWebSocketWithReconnect({
  url,
  autoReconnect: true,
  onMessage: (msg) => {
    if (msg.type === 'data') setData(msg)
  }
})
```

### Migration Checklist

- [ ] Add `useWebSocketWithReconnect` hook to project
- [ ] Add `websocket_v2.py` router to backend
- [ ] Update `main.py` to include new router
- [ ] Replace existing `useEffect` WebSocket code
- [ ] Add connection status badges to UI
- [ ] Test reconnection behavior (kill server, restart)
- [ ] Monitor for memory leaks (cleanup on unmount)
- [ ] Add error logging/monitoring

---

## Testing & Monitoring

### Test Scenarios

#### 1. Normal Operation
```bash
# Start server, open frontend, verify data flows
# Expected: Green "Connected" + "Live Data" badges
```

#### 2. Server Restart
```bash
# Kill server (Ctrl+C), wait 5s, restart server
# Expected: UI shows "Reconnecting (1/10)", then reconnects automatically
```

#### 3. Network Drop
```bash
# Disconnect network, wait 10s, reconnect
# Expected: Exponential backoff, reconnects when network returns
```

#### 4. Heartbeat Timeout
```bash
# Let connection idle for 60s without data
# Expected: Client sends ping, server responds with pong
```

### Monitoring

Add logging to track:

```typescript
// Frontend monitoring
onOpen: () => {
  console.log('[WS] Connected', { timestamp: new Date().toISOString() })
  // Send to analytics/monitoring service
}

onClose: () => {
  console.log('[WS] Disconnected', { timestamp: new Date().toISOString() })
}

onError: (error) => {
  console.error('[WS] Error', { error, timestamp: new Date().toISOString() })
  // Send to error tracking (Sentry, etc.)
}
```

```python
# Backend monitoring (add to websocket_v2.py)
@router.on_event("startup")
async def log_websocket_stats():
    """Log WebSocket statistics every minute."""
    while True:
        await asyncio.sleep(60)
        logger.info(
            f"WebSocket Stats: {len(stream_manager.active_streams)} active streams"
        )
```

---

## Performance Comparison

### Before (Basic WebSocket)
- ❌ No reconnection (user must refresh page)
- ❌ No heartbeat (stale connections undetected)
- ❌ No error recovery (crashes on hardware errors)
- ❌ Single client design (no broadcast support)
- ⚠️ Memory leaks possible (no cleanup)

### After (Gold Standard)
- ✅ Automatic reconnection with exponential backoff
- ✅ Heartbeat every 30s (detect stale connections)
- ✅ Graceful degradation (hardware errors don't crash)
- ✅ Multi-client support (ConnectionManager)
- ✅ Proper cleanup (no memory leaks)
- ✅ Production monitoring (logs, metrics)

### Network Usage

**Before:**
- REST polling: 10-15 req/s × ~500 bytes = **5-7.5 KB/s**
- No reconnection overhead

**After:**
- WebSocket: ~10 messages/s × 200 bytes = **2 KB/s** (60% reduction)
- Heartbeat: 1 message/30s = **7 bytes/s** (negligible)
- Reconnection: Exponential backoff prevents spam

**Net Result: ~70% bandwidth reduction + better UX**

---

## Conclusion

This gold-standard implementation provides:

1. ✅ **Reliability** - Automatic reconnection, error recovery
2. ✅ **Performance** - 70% bandwidth reduction vs polling
3. ✅ **Scalability** - Multi-client support, connection manager
4. ✅ **Observability** - Logging, monitoring, metrics
5. ✅ **User Experience** - Seamless reconnection, status visibility

### Next Steps

1. Integrate `websocket_v2.py` into your backend
2. Replace frontend WebSocket with `useWebSocketWithReconnect`
3. Test all scenarios (normal, restart, network drop)
4. Add monitoring/analytics
5. Consider adding WebSocket for other real-time features (sweep progress, laser state changes)

**You now have production-grade WebSocket infrastructure! 🚀**
