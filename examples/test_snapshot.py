#!/usr/bin/env python3
"""
Test the new simplified detector snapshot API.
"""
import requests
import time

API_BASE = "http://localhost:8002"

def main():
    print("Testing GET /detector/snapshot endpoint...\n")

    # Single request gets all 4 channels
    response = requests.get(f"{API_BASE}/detector/snapshot")
    response.raise_for_status()

    snapshot = response.json()

    print(f"Timestamp: {snapshot['timestamp']}")
    print(f"Module: {snapshot['module']}")
    print(f"Wavelength: {snapshot['wavelength_nm']:.4f} nm")
    print(f"Unit: {snapshot['unit']}")
    print()
    print("Channel Powers:")
    print(f"  IN1 (CH1):      {snapshot['ch1_power']:+.3f} {snapshot['unit']}")
    print(f"  IN2 (CH2):      {snapshot['ch2_power']:+.3f} {snapshot['unit']}")
    print(f"  TLS IN (CH3):   {snapshot['ch3_power']:+.3f} {snapshot['unit']}")
    print(f"  OUT TO DUT (CH4): {snapshot['ch4_power']:+.3f} {snapshot['unit']}")
    print()

    # Monitor for a few readings
    print("Monitoring power (5 readings)...")
    for i in range(5):
        response = requests.get(f"{API_BASE}/detector/snapshot")
        response.raise_for_status()
        snapshot = response.json()

        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] IN1:{snapshot['ch1_power']:+7.3f} | IN2:{snapshot['ch2_power']:+7.3f} | TLS:{snapshot['ch3_power']:+7.3f} | DUT:{snapshot['ch4_power']:+7.3f} {snapshot['unit']}")

        time.sleep(0.5)

    print("\nDone!")


if __name__ == "__main__":
    main()
