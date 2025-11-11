#!/usr/bin/env python3
"""
EXFO CTP10 API - Power Measurement Example

This script demonstrates how to:
1. Connect to the CTP10 API
2. Access different detector channels
3. Read optical power measurements from detectors
4. Continuous power monitoring

Based on: pymeasure-examples/exfo/exfo_ctp10_power_measurement_example.py

Author: API Example
Date: November 10, 2025
"""
import requests
import time

# API Configuration
API_BASE = "http://localhost:8002"
MODULE = 4  # Module number (SENSe[1-20])
DEFAULT_CHANNEL = 1  # Default detector channel (1-6)


def channel_label(ch: int) -> str:
    """Return human-readable channel label."""
    return {
        1: "IN1",
        2: "IN2",
        3: "TLS IN",
        4: "OUT TO DUT"
    }.get(ch, f"CH{ch}")


def main():
    """Read and monitor power from CTP10 via API."""

    # 1. Connect to CTP10
    print("Connecting to CTP10 via API...")
    response = requests.post(f"{API_BASE}/connection/connect")
    response.raise_for_status()
    print(f"Connected: {response.json()['instrument_id']}\n")

    # 2. Get detector configuration
    print(f"Getting detector configuration (Module {MODULE}, Channel {DEFAULT_CHANNEL})...")
    response = requests.get(
        f"{API_BASE}/detector/config",
        params={
            "module": MODULE,
            "channel": DEFAULT_CHANNEL
        }
    )
    response.raise_for_status()
    config = response.json()
    print(f"  Power unit: {config['power_unit']}")
    print(f"  Spectral unit: {config['spectral_unit']}")

    # 3. Read single power measurement
    print(f"\nReading power from {channel_label(DEFAULT_CHANNEL)} (Channel {DEFAULT_CHANNEL})...")
    response = requests.get(
        f"{API_BASE}/detector/power",
        params={
            "module": MODULE,
            "channel": DEFAULT_CHANNEL
        }
    )
    response.raise_for_status()

    reading = response.json()
    print(f"  Module: {reading['module']}")
    print(f"  Channel: {reading['channel']}")
    print(f"  Power: {reading['power']:.3f} {reading['unit']}")
    print(f"  Wavelength: {reading['wavelength_nm']:.4f} nm")

    # 4. Read power from multiple channels
    channels_to_read = [1, 2, 3, 4]
    print(f"\nReading power from channels {channels_to_read} on Module {MODULE}...")
    for ch in channels_to_read:
        try:
            response = requests.get(
                f"{API_BASE}/detector/power",
                params={
                    "module": MODULE,
                    "channel": ch
                }
            )
            response.raise_for_status()
            reading = response.json()
            print(f"  {channel_label(ch)} (Channel {ch}): {reading['power']:.2f} {reading['unit']} @ {reading['wavelength_nm']:.2f} nm")
        except Exception as e:
            print(f"  Channel {ch}: Error - {e}")

    # 5. Continuous monitoring (10 readings)
    print(f"\nMonitoring power from {channel_label(DEFAULT_CHANNEL)} (10 samples)...")
    for i in range(10):
        response = requests.get(
            f"{API_BASE}/detector/power",
            params={
                "module": MODULE,
                "channel": DEFAULT_CHANNEL
            }
        )
        response.raise_for_status()

        reading = response.json()
        timestamp = time.strftime("%H:%M:%S")
        print(f"  [{timestamp}] {reading['power']:+.3f} {reading['unit']}")

        time.sleep(1.0)

    # 6. Read TLS IN power (channel 3)
    print(f"\nReading TLS IN power (Channel 3)...")
    try:
        response = requests.get(
            f"{API_BASE}/detector/power",
            params={
                "module": MODULE,
                "channel": 3
            }
        )
        response.raise_for_status()
        reading = response.json()
        print(f"  TLS IN power: {reading['power']:.2f} {reading['unit']}")
    except Exception as e:
        print(f"  Error reading TLS IN power: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
