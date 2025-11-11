#!/usr/bin/env python3
"""
EXFO CTP10 API - TLS Configuration and Sweep Example

This script demonstrates:
- Connecting to the CTP10 API
- Configuring TLS parameters (wavelength range, speed, power, trigger)
- Configuring sweep resolution and stabilization
- Starting a sweep
- Monitoring sweep status
- Aborting sweeps if needed

Key Concepts:
- TLS channels (1-4): Direct property access via API
- Sweep configuration: Resolution and stabilization settings
- Sweep control: Initiate, wait, abort, status

Based on: pymeasure-examples/exfo/exfo_ctp10_detector_example.py

Author: API Example
Date: November 10, 2025
"""
import requests
import time

# API Configuration
API_BASE = "http://localhost:8002"
TLS_CHANNEL = 1  # TLS channel (1-4)


def main():
    """Configure TLS and perform a sweep via API."""

    # 1. Connect to CTP10
    print("Connecting to CTP10 via API...")
    response = requests.post(f"{API_BASE}/connection/connect")
    response.raise_for_status()
    print(f"Connected: {response.json()['instrument_id']}\n")

    # 2. Get current TLS configuration
    print(f"Current TLS{TLS_CHANNEL} configuration:")
    response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/config")
    response.raise_for_status()
    current_config = response.json()
    print(f"  Channel: {current_config['channel']}")
    print(f"  Start wavelength: {current_config['start_wavelength_nm']:.2f} nm")
    print(f"  Stop wavelength: {current_config['stop_wavelength_nm']:.2f} nm")
    print(f"  Sweep speed: {current_config['sweep_speed_nmps']} nm/s")
    print(f"  Laser power: {current_config['laser_power_dbm']:.2f} dBm")
    print(f"  Trigger: {current_config['trigin']} (0=software, 1-8=TRIG IN port)")

    # 3. Configure TLS channel
    print(f"\nConfiguring TLS{TLS_CHANNEL}...")
    tls_config = {
        "start_wavelength_nm": 1500.0,
        "stop_wavelength_nm": 1600.0,
        "sweep_speed_nmps": 50,
        "laser_power_dbm": 5.0,
        "trigin": 0  # Software trigger
    }

    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/config",
        json=tls_config
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 4. Get current sweep configuration (resolution and stabilization)
    print("\nCurrent sweep configuration:")
    response = requests.get(f"{API_BASE}/measurement/config")
    response.raise_for_status()
    sweep_config = response.json()
    print(f"  Resolution: {sweep_config['resolution_pm']:.2f} pm")
    print(f"  Stabilization output: {sweep_config['stabilization_output']}")
    print(f"  Stabilization duration: {sweep_config['stabilization_duration']} s")

    # 5. Configure sweep parameters
    print("\nConfiguring sweep parameters...")
    sweep_config = {
        "resolution_pm": 10.0,
        "stabilization_output": False,  # False=OFF, True=ON
        "stabilization_duration": 0.0
    }

    response = requests.post(
        f"{API_BASE}/measurement/config",
        json=sweep_config
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 6. Start sweep (non-blocking)
    print("\nStarting sweep (non-blocking)...")
    response = requests.post(
        f"{API_BASE}/measurement/sweep/start",
        params={"wait": False}
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 7. Monitor sweep status
    print("\nMonitoring sweep progress...")
    sweep_duration = (tls_config["stop_wavelength_nm"] - tls_config["start_wavelength_nm"]) / tls_config["sweep_speed_nmps"]
    print(f"  Expected sweep duration: {sweep_duration:.1f} seconds")

    start_time = time.time()
    while True:
        response = requests.get(f"{API_BASE}/measurement/sweep/status")
        response.raise_for_status()
        status = response.json()

        elapsed = time.time() - start_time
        progress = min((elapsed / sweep_duration) * 100, 100) if sweep_duration > 0 else 0

        if status["is_sweeping"]:
            print(f"  Sweeping: {progress:.1f}% | Elapsed: {elapsed:.1f}s | Complete: {status['is_complete']}")
        else:
            print(f"  Sweep finished after {elapsed:.1f} seconds")
            print(f"  Is complete: {status['is_complete']}")
            break

        time.sleep(1.0)

        # Optional: Abort after 5 seconds for demo purposes
        # if elapsed > 5.0:
        #     print("\n  Aborting sweep for demo...")
        #     response = requests.post(f"{API_BASE}/measurement/sweep/abort")
        #     response.raise_for_status()
        #     print(f"    {response.json()['message']}")
        #     break

    # 8. Get final TLS configuration
    print(f"\nFinal TLS{TLS_CHANNEL} configuration:")
    response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/config")
    response.raise_for_status()
    final_config = response.json()
    print(f"  Start wavelength: {final_config['start_wavelength_nm']:.2f} nm")
    print(f"  Stop wavelength: {final_config['stop_wavelength_nm']:.2f} nm")
    print(f"  Sweep speed: {final_config['sweep_speed_nmps']} nm/s")
    print(f"  Laser power: {final_config['laser_power_dbm']:.2f} dBm")

    # 9. Example: Configure individual TLS parameters
    print("\nExample: Setting individual TLS parameters...")

    # Set wavelength range
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/wavelength",
        params={
            "start_nm": 1520.0,
            "stop_nm": 1580.0
        }
    )
    response.raise_for_status()
    print(f"  Wavelength: {response.json()['message']}")

    # Set power
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/power",
        params={"power_dbm": 3.0}
    )
    response.raise_for_status()
    print(f"  Power: {response.json()['message']}")

    # Set sweep speed
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/speed",
        params={"speed_nmps": 40}
    )
    response.raise_for_status()
    print(f"  Speed: {response.json()['message']}")

    # Set trigger
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/trigger",
        params={"trigin": 0}
    )
    response.raise_for_status()
    print(f"  Trigger: {response.json()['message']}")

    # 10. Check condition register
    print("\nChecking instrument condition register...")
    response = requests.get(f"{API_BASE}/connection/condition")
    response.raise_for_status()
    condition = response.json()
    print(f"  Register value: {condition['register_value']}")
    print(f"  Is idle: {condition['is_idle']}")
    print(f"  Bits: {condition['bits']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
