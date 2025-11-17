#!/usr/bin/env python3
"""
EXFO CTP10 API - Reference Laser Configuration Example

This script demonstrates how to:
- Connect to the CTP10 API
- Access reference laser channels (1-10)
- Configure reference laser parameters (wavelength, power, state)
- Read reference laser identification and status
- Control laser output (on/off)

Key Concepts:
- RLaser channels: Array indexing (ctp.rlaser[1] through ctp.rlaser[10])
- Laser configuration: Wavelength (nm), Power (dBm), State (on/off)
- Laser identification: Manufacturer, model, serial, firmware

Author: API Example
Date: November 10, 2025
"""
import requests

# API Configuration
API_BASE = "http://localhost:8002"
LASER_NUMBER = 2  # Reference laser number (1-10)
                  # Laser 1 = C-band laser (may not be present)
                  # Laser 2 = O-band laser


def main():
    """Configure and control reference lasers via API."""

    # 1. Connect to CTP10
    print("Connecting to CTP10 via API...")
    response = requests.post(f"{API_BASE}/connection/connect")
    response.raise_for_status()
    print(f"Connected: {response.json()['instrument_id']}\n")

    # 2. Get reference laser identification
    print(f"Reference Laser {LASER_NUMBER} Identification:")
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/id")
    response.raise_for_status()
    laser_id = response.json()
    print(f"  Full ID: {laser_id['id']}")
    print(f"  Manufacturer: {laser_id['manufacturer']}")
    print(f"  Model: {laser_id['model']}")
    print(f"  Serial: {laser_id['serial']}")
    print(f"  Firmware: {laser_id['firmware']}")

    # 3. Get complete laser configuration
    print(f"\nReference Laser {LASER_NUMBER} Configuration:")
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/config")
    response.raise_for_status()
    config = response.json()
    print(f"  Laser number: {config['laser_number']}")
    print(f"  Wavelength: {config['wavelength_nm']:.2f} nm")
    print(f"  Power: {config['power_dbm']:.2f} dBm")
    print(f"  State: {'ON' if config['is_on'] else 'OFF'}")

    # 4. Get individual laser parameters
    print(f"\nReading individual parameters for Laser {LASER_NUMBER}:")

    # Get wavelength
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/wavelength")
    response.raise_for_status()
    wavelength = response.json()
    print(f"  Wavelength: {wavelength['wavelength_nm']:.2f} nm")

    # Get power
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/power")
    response.raise_for_status()
    power = response.json()
    print(f"  Power: {power['power_dbm']:.2f} dBm")

    # Get state
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/state")
    response.raise_for_status()
    state = response.json()
    print(f"  State: {'ON' if state['is_on'] else 'OFF'} (raw: {state['state']})")

    # 5. Configure laser (wavelength and power)
    print(f"\nConfiguring Laser {LASER_NUMBER}...")
    laser_config = {
        "wavelength_nm": 1550.0,
        "power_dbm": 3.0
        # Note: power_state not set, so it won't be changed
    }

    response = requests.post(
        f"{API_BASE}/rlaser/{LASER_NUMBER}/config",
        json=laser_config
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # 6. Set individual parameters
    print(f"\nSetting individual parameters for Laser {LASER_NUMBER}...")

    # Set wavelength
    response = requests.post(
        f"{API_BASE}/rlaser/{LASER_NUMBER}/wavelength",
        params={"wavelength_nm": 1545.0}
    )
    response.raise_for_status()
    print(f"  Wavelength: {response.json()['message']}")

    # Set power
    response = requests.post(
        f"{API_BASE}/rlaser/{LASER_NUMBER}/power",
        params={"power_dbm": 5.0}
    )
    response.raise_for_status()
    print(f"  Power: {response.json()['message']}")

    # 7. Control laser output state
    print(f"\nControlling Laser {LASER_NUMBER} output state...")

    # Turn laser ON
    print("  Turning laser ON...")
    response = requests.post(f"{API_BASE}/rlaser/{LASER_NUMBER}/on")
    response.raise_for_status()
    print(f"    {response.json()['message']}")

    # Verify state
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/state")
    response.raise_for_status()
    state = response.json()
    print(f"    Current state: {'ON' if state['is_on'] else 'OFF'}")

    # Turn laser OFF
    print("\n  Turning laser OFF...")
    response = requests.post(f"{API_BASE}/rlaser/{LASER_NUMBER}/off")
    response.raise_for_status()
    print(f"    {response.json()['message']}")

    # Verify state
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/state")
    response.raise_for_status()
    state = response.json()
    print(f"    Current state: {'ON' if state['is_on'] else 'OFF'}")

    # 8. Configure multiple parameters at once
    print(f"\nConfiguring multiple parameters at once for Laser {LASER_NUMBER}...")
    full_config = {
        "wavelength_nm": 1550.12,
        "power_dbm": 4.5,
        "power_state": True  # Turn on
    }

    response = requests.post(
        f"{API_BASE}/rlaser/{LASER_NUMBER}/config",
        json=full_config
    )
    response.raise_for_status()
    print(f"  {response.json()['message']}")

    # Verify final configuration
    response = requests.get(f"{API_BASE}/rlaser/{LASER_NUMBER}/config")
    response.raise_for_status()
    final_config = response.json()
    print(f"\nFinal Laser {LASER_NUMBER} Configuration:")
    print(f"  Wavelength: {final_config['wavelength_nm']:.4f} nm")
    print(f"  Power: {final_config['power_dbm']:.2f} dBm")
    print(f"  State: {'ON' if final_config['is_on'] else 'OFF'}")

    # 9. Example: Query multiple lasers
    print("\nQuerying multiple reference lasers (1-3)...")
    for laser_num in range(1, 4):
        try:
            response = requests.get(f"{API_BASE}/rlaser/{laser_num}/config")
            response.raise_for_status()
            config = response.json()
            print(f"  Laser {laser_num}: {config['wavelength_nm']:.2f} nm, "
                  f"{config['power_dbm']:.2f} dBm, "
                  f"{'ON' if config['is_on'] else 'OFF'}")
        except Exception as e:
            print(f"  Laser {laser_num}: Error - {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
