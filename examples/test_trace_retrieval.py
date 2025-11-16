#!/usr/bin/env python3
"""
EXFO CTP10 API - Detector Channel and Trace Retrieval Example

This script demonstrates the detector-centric API for accessing
trace data on the EXFO CTP10 via REST API.

Key Features:
- Access detectors via API endpoints with module/channel parameters
- Detector-level operations: power, trigger, units, create_reference
- Trace data retrieval with explicit trace_type parameter:
  * trace_type=1: TF live trace (Transmission Function)
  * trace_type=11: Raw live trace
  * trace_type=12: Raw reference trace
  * trace_type=13: Raw quick reference trace
- Binary trace data download for efficiency (~940k points)

Based on: pymeasure-examples/exfo/exfo_ctp10_detector_example.py

Author: API Example
Date: November 10, 2025
"""
import requests
import numpy as np
import matplotlib.pyplot as plt
import io

# API Configuration
API_BASE = "http://localhost:8015"
MODULE = 4  # Module number (SENSe[1-20])
CHANNEL = 1  # Detector channel (CHANnel[1-6])


def main():
    """Fetch and plot CTP10 trace data via API."""

    # 1. Connect to CTP10
    print("Connecting to CTP10 via API...")
    response = requests.post(f"{API_BASE}/connection/connect")
    response.raise_for_status()
    print(f"Connected: {response.json()['instrument_id']}\n")

    # 2. Configure TLS1 parameters
    print("Configuring TLS1 for O-band...")
    # Setting identifier=2 automatically configures O-band parameters:
    # - Wavelength range: 1262.5-1355.0 nm
    # - Sweep speed: 20 nm/s
    # - Laser power: 10.0 dBm
    # - Trigin: 2
    tls_config = {
        "identifier": 2  # O-band laser (auto-configures all parameters)
    }
    response = requests.post(f"{API_BASE}/tls/1/config", json=tls_config)
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 3. Configure detector settings (including resolution)
    print("Configuring detector settings...")
    detector_config = {
        "power_unit": "DBM",
        "spectral_unit": "WAV",
        "resolution_pm": 0.1
    }
    response = requests.post(
        f"{API_BASE}/detector/config",
        params={
            "module": MODULE,
            "channel": CHANNEL
        },
        json=detector_config
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 4. Enable stabilization output (True)
    print("\nConfiguring stabilization (laser output after scan)...")
    response = requests.post(
        f"{API_BASE}/measurement/config",
        json={
            "stabilization_output": True,
            "stabilization_duration": 0.0
        }
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 5. Read current sweep configuration
    print("\nCurrent sweep configuration:")
    
    # Get detector config (includes resolution)
    response = requests.get(
        f"{API_BASE}/detector/config",
        params={
            "module": MODULE,
            "channel": CHANNEL
        }
    )
    response.raise_for_status()
    detector_config = response.json()
    print(f"  Resolution: {detector_config['resolution_pm']:.2f} pm")
    
    # Get measurement config (stabilization)
    response = requests.get(f"{API_BASE}/measurement/config")
    response.raise_for_status()
    config = response.json()
    print(f"  Stabilization output: {config['stabilization_output']}")
    print(f"  Stabilization duration: {config['stabilization_duration']} s")

    # Get TLS1 configuration
    response = requests.get(f"{API_BASE}/tls/1/config")
    response.raise_for_status()
    tls_config = response.json()
    laser_type = 'C-band' if tls_config['identifier'] == 1 else 'O-band' if tls_config['identifier'] == 2 else 'Unknown'
    print(f"  TLS1 Identifier: {tls_config['identifier']} ({laser_type})")
    print(f"  TLS1 Start: {tls_config['start_wavelength_nm']:.2f} nm")
    print(f"  TLS1 Stop: {tls_config['stop_wavelength_nm']:.2f} nm")
    print(f"  TLS1 Speed: {tls_config['sweep_speed_nmps']} nm/s")
    print(f"  TLS1 Power: {tls_config['laser_power_dbm']:.2f} dBm")
    print(f"  TLS1 Trigger Input: {tls_config['trigin']}")

    # 6. Initiate sweep and wait for completion
    print("\nInitiating sweep...")
    response = requests.post(
        f"{API_BASE}/measurement/sweep/start",
        params={"wait": True}  # Block until complete
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 7. Get detector power snapshot
    print(f"\nGetting detector power snapshot (Module {MODULE}, Channel {CHANNEL})...")
    response = requests.get(
        f"{API_BASE}/detector/snapshot",
        params={"module": MODULE}
    )
    response.raise_for_status()
    snapshot = response.json()
    print(f"  Current power (CH{CHANNEL}): {snapshot[f'ch{CHANNEL}_power']:.2f} {snapshot['unit']}")

        # 7. Get trace metadata before downloading
    print("\nAccessing trace metadata...")
    trace_types = [
        (1, "TF live"),
        (11, "Raw live"),
        (12, "Raw reference")
    ]

    for trace_type, trace_name in trace_types:
        response = requests.get(
            f"{API_BASE}/detector/trace/metadata",
            params={
                "module": MODULE,
                "channel": CHANNEL,
                "trace_type": trace_type
            }
        )
        response.raise_for_status()
        metadata = response.json()
        print(f"  - {trace_name} (trace_type={trace_type})")
        print(f"    Length: {metadata['num_points']} points")
    # Sampling omitted; resolution is reported in detector config

    # 8. Download trace data in binary format (efficient)

    # 8. Download trace data in binary format (efficient)
    print("\nDownloading trace data in binary format...")
    print("  Note: Large dataset (~940k points), using binary NPY format...")

    traces = {}
    for trace_type, trace_name in trace_types:
        response = requests.get(
            f"{API_BASE}/detector/trace/binary",
            params={
                "module": MODULE,
                "channel": CHANNEL,
                "trace_type": trace_type
            },
            timeout=120  # Large timeout for binary transfer
        )
        response.raise_for_status()

        # Load NPY data from response
        buffer = io.BytesIO(response.content)
        data = np.load(buffer)
        traces[trace_name] = {
            "wavelengths": data['wavelengths'],
            "values": data['values']
        }
        print(f"  Downloaded {trace_name}: {len(data['wavelengths'])} points")

    # Print wavelength range and power statistics for each trace
    print()
    for trace_name, trace_data in traces.items():
        wavelengths = trace_data["wavelengths"]
        values = trace_data["values"]
        print(f"  {trace_name}:")
        print(f"    Wavelength range: {wavelengths[0]:.4f} - {wavelengths[-1]:.4f} nm")
        print(f"    Power range: {values.min():.2f} to {values.max():.2f} dB")

    # 9. Optional: Create reference trace
    # print("\nCreating reference trace...")
    # response = requests.post(
    #     f"{API_BASE}/detector/reference",
    #     params={
    #         "module": MODULE,
    #         "channel": CHANNEL
    #     }
    # )
    # response.raise_for_status()
    # print(f"  {response.json()['message']}")

    # 10. Plot the results
    print("\nGenerating plot...")
    plt.figure(figsize=(14, 7))

    plt.plot(
        traces["Raw live"]["wavelengths"],
        traces["Raw live"]["values"],
        label='Raw Live',
        linewidth=0.8,
        alpha=0.7,
        color='blue'
    )
    plt.plot(
        traces["TF live"]["wavelengths"],
        traces["TF live"]["values"],
        label='TF Live',
        linewidth=1.2,
        color='green'
    )
    plt.plot(
        traces["Raw reference"]["wavelengths"],
        traces["Raw reference"]["values"],
        label='Raw Reference',
        linewidth=1,
        alpha=0.8,
        linestyle='--',
        color='red'
    )

    plt.xlabel('Wavelength (nm)', fontsize=12)
    plt.ylabel('Power (dB)', fontsize=12)
    plt.title(
        f'EXFO CTP10 Detector Traces - Module {MODULE}, Channel {CHANNEL}',
        fontsize=14
    )
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Show plot
    plt.show()

    print("\nDone!")


if __name__ == "__main__":
    main()
