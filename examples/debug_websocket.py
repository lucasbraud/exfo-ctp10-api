#!/usr/bin/env python3
"""
Debug WebSocket messages to see the actual data being sent.
"""
import asyncio
import json
import requests
import websockets

API_BASE = "http://localhost:8002"
WS_URL = "ws://localhost:8002/ws/v2/power?module=4&interval=0.1"

async def monitor_websocket():
    # First, ensure we're connected via REST API
    print("Connecting to CTP10 via REST API...")
    try:
        response = requests.post(f"{API_BASE}/connection/connect")
        response.raise_for_status()
        print(f"Connected: {response.json()['instrument_id']}\n")
    except Exception as e:
        print(f"Warning: Could not connect via REST: {e}")
        print("Continuing anyway (may be in mock mode)...\n")
    
    print(f"Connecting to WebSocket: {WS_URL}...")

    async with websockets.connect(WS_URL) as websocket:
        print("Connected! Receiving messages...\n")

        message_count = 0
        try:
            while message_count < 20:  # Show first 20 messages
                message = await websocket.recv()
                data = json.loads(message)

                message_count += 1
                print(f"=== Message {message_count} ===")
                print(f"Timestamp: {data.get('timestamp', 'N/A')}")
                print(f"Module: {data.get('module', 'N/A')}")
                print(f"Wavelength: {data.get('wavelength_nm', 'N/A')} nm")
                print(f"Unit: {data.get('unit', 'N/A')}")
                print("Power Readings:")
                print(f"  Channel 1: {data.get('ch1_power', 'N/A'):.3f} {data.get('unit', '')}")
                print(f"  Channel 2: {data.get('ch2_power', 'N/A'):.3f} {data.get('unit', '')}")
                print(f"  Channel 3: {data.get('ch3_power', 'N/A'):.3f} {data.get('unit', '')}")
                print(f"  Channel 4: {data.get('ch4_power', 'N/A'):.3f} {data.get('unit', '')}")
                print()

        except KeyboardInterrupt:
            print("\nStopped by user")

if __name__ == "__main__":
    asyncio.run(monitor_websocket())
