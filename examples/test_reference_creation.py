#!/usr/bin/env python3
"""
EXFO CTP10 API - Reference Trace Creation Example

This script demonstrates how to:
1. Retrieve the current reference trace from the detector (without sweeping)
2. Prompt the user to create a new reference trace
3. Display the newly created reference trace

The create_reference endpoint uses the CTP10's built-in reference creation
procedure (:REFerence:SENSe{module}:CHANnel{channel}:INITiate) which
internally performs a scan and stores the result as the reference trace.

Author: API Example
Date: November 28, 2025
"""
import requests
import numpy as np
import matplotlib.pyplot as plt
import io
import time

# API Configuration
API_BASE = "http://localhost:8002"
MODULE = 4  # Module number (SENSe[1-20])
CHANNEL = 1  # Detector channel (CHANnel[1-6])


def get_reference_trace():
    """
    Retrieve the current reference trace from the detector.

    This reads the existing reference trace stored in the instrument
    without performing any sweep or measurement.

    Returns:
        dict: Reference trace data with 'wavelengths' and 'values' keys
    """
    print(f"\nRetrieving current reference trace (Module {MODULE}, Channel {CHANNEL})...")

    try:
        response = requests.get(
            f"{API_BASE}/detector/trace/binary",
            params={
                "module": MODULE,
                "channel": CHANNEL,
                "trace_type": 12  # Raw reference trace
            },
            timeout=120
        )
        response.raise_for_status()

        # Load NPY data
        buffer = io.BytesIO(response.content)
        data = np.load(buffer)

        trace = {
            "wavelengths": data['wavelengths'],
            "values": data['values']
        }

        print(f"  Retrieved reference trace: {len(trace['wavelengths'])} points")
        print(f"  Wavelength range: {trace['wavelengths'][0]:.4f} - {trace['wavelengths'][-1]:.4f} nm")
        print(f"  Power range: {trace['values'].min():.2f} to {trace['values'].max():.2f} dB")

        return trace

    except Exception as e:
        print(f"  ERROR: Failed to retrieve reference trace: {e}")
        return None


def create_reference():
    """
    Create a new reference trace using the CTP10's reference creation function.

    This endpoint triggers the instrument's :REFerence:SENSe{module}:CHANnel{channel}:INITiate
    command, which:
    1. Performs an internal scan using current TLS settings
    2. Stores the result as the reference trace
    3. The reference is used for calculating TF (Transmission Function) traces

    Note: This is different from a regular measurement sweep. The reference creation
    uses the instrument's built-in reference procedure.
    """
    print(f"\nCreating new reference trace (Module {MODULE}, Channel {CHANNEL})...")
    print("  This will trigger an internal scan on the EXFO CTP10...")
    print("  Please ensure:")
    print("    - Reference fiber is connected (bypassing DUT)")
    print("    - Optical connections are clean and secure")
    print("    - TLS is configured with correct wavelength range")

    try:
        response = requests.post(
            f"{API_BASE}/detector/reference",
            params={
                "module": MODULE,
                "channel": CHANNEL
            },
            timeout=300  # Reference creation can take time
        )
        response.raise_for_status()
        result = response.json()

        print(f"  SUCCESS: {result.get('message', 'Reference created')}")
        return True

    except Exception as e:
        print(f"  ERROR: Failed to create reference: {e}")
        return False


def plot_reference_trace(trace_data, title="Reference Trace"):
    """
    Plot the reference trace.

    Args:
        trace_data: Dictionary with 'wavelengths' and 'values' keys
        title: Plot title
    """
    wavelengths = trace_data["wavelengths"]
    values = trace_data["values"]

    plt.figure(figsize=(12, 6))
    plt.plot(wavelengths, values, linewidth=0.8, color='red', label='Reference Trace')

    plt.xlabel('Wavelength (nm)', fontsize=12)
    plt.ylabel('Power (dB)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()

    # Print statistics
    print(f"\n  Trace Statistics:")
    print(f"    Number of points: {len(wavelengths)}")
    print(f"    Wavelength range: {wavelengths[0]:.4f} - {wavelengths[-1]:.4f} nm")
    print(f"    Power range: {values.min():.2f} to {values.max():.2f} dB")
    print(f"    Mean power: {values.mean():.2f} dB")
    print(f"    Std deviation: {values.std():.2f} dB")

    plt.show()


def main():
    """Main execution flow."""

    print("=" * 70)
    print("EXFO CTP10 - Reference Trace Creation Example")
    print("=" * 70)

    # Step 1: Connect to CTP10
    print("\n[Step 1] Connecting to CTP10 via API...")
    try:
        response = requests.post(f"{API_BASE}/connection/connect", timeout=10)
        response.raise_for_status()
        print(f"  Connected: {response.json()['instrument_id']}")
    except Exception as e:
        print(f"  ERROR: Failed to connect: {e}")
        print("\nPlease ensure:")
        print("  - EXFO CTP10 API is running (usually on port 8002)")
        print("  - The instrument is powered on and connected")
        return

    # Step 2: Read current TLS configuration
    print("\n[Step 2] Reading current TLS configuration...")
    try:
        response = requests.get(f"{API_BASE}/tls/1/config", timeout=5)
        response.raise_for_status()
        tls_config = response.json()

        laser_type = 'C-band' if tls_config['identifier'] == 1 else 'O-band' if tls_config['identifier'] == 2 else 'Unknown'
        print(f"  TLS Identifier: {tls_config['identifier']} ({laser_type})")
        print(f"  Wavelength range: {tls_config['start_wavelength_nm']:.2f} - {tls_config['stop_wavelength_nm']:.2f} nm")
        print(f"  Sweep speed: {tls_config['sweep_speed_nmps']} nm/s")
        print(f"  Laser power: {tls_config['laser_power_dbm']:.2f} dBm")
    except Exception as e:
        print(f"  WARNING: Could not read TLS config: {e}")

    # Step 3: Retrieve current reference trace
    print("\n[Step 3] Retrieving current reference trace...")
    current_reference = get_reference_trace()

    if current_reference:
        print("\n  Displaying current reference trace...")
        plot_reference_trace(current_reference, title="Current Reference Trace")
    else:
        print("  No valid reference trace found or retrieval failed.")

    # Step 4: Prompt user to create new reference
    print("\n" + "=" * 70)
    print("REFERENCE TRACE CREATION")
    print("=" * 70)
    print("\nYou can now create a NEW reference trace.")
    print("\nBefore proceeding, please ensure:")
    print("  1. Remove any DUT from the setup")
    print("  2. Connect the reference fiber (bypassing the DUT)")
    print("  3. Ensure good optical connection (clean connectors)")
    print("  4. TLS is configured with the desired wavelength range")
    print("=" * 70)

    response = input("\nDo you want to create a new reference trace? (y/n): ").strip().lower()

    if response != 'y':
        print("\nReference creation cancelled by user.")
        print("Exiting...")
        return

    # Step 5: Create reference
    print("\n[Step 4] Creating reference trace...")
    success = create_reference()

    if not success:
        print("\nReference creation failed. Exiting...")
        return

    # Step 6: Wait a moment for the reference to be stored
    print("\nWaiting for reference to be stored in instrument...")
    time.sleep(2)

    # Step 7: Retrieve and display new reference trace
    print("\n[Step 5] Retrieving newly created reference trace...")
    new_reference = get_reference_trace()

    if new_reference:
        print("\n  Displaying newly created reference trace...")
        plot_reference_trace(new_reference, title="Newly Created Reference Trace")

        # Compare with previous reference if available
        if current_reference:
            print("\n[Comparison] Old vs New Reference:")
            old_wl_range = f"{current_reference['wavelengths'][0]:.4f} - {current_reference['wavelengths'][-1]:.4f} nm"
            new_wl_range = f"{new_reference['wavelengths'][0]:.4f} - {new_reference['wavelengths'][-1]:.4f} nm"
            old_power_range = f"{current_reference['values'].min():.2f} to {current_reference['values'].max():.2f} dB"
            new_power_range = f"{new_reference['values'].min():.2f} to {new_reference['values'].max():.2f} dB"

            print(f"  Old wavelength range: {old_wl_range}")
            print(f"  New wavelength range: {new_wl_range}")
            print(f"  Old power range: {old_power_range}")
            print(f"  New power range: {new_power_range}")

            # Check if wavelength ranges are similar
            wl_match = abs(current_reference['wavelengths'][0] - new_reference['wavelengths'][0]) < 1.0
            if wl_match:
                print("\n  ✓ Wavelength ranges are consistent")
            else:
                print("\n  ⚠ Wavelength ranges differ - TLS configuration may have changed")
    else:
        print("\n  ERROR: Failed to retrieve new reference trace")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
