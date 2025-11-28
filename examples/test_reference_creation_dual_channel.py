#!/usr/bin/env python3
"""
EXFO CTP10 API - Dual Channel Reference Creation Example

This script mimics the pymeasure example (exfo_ctp10_reference_example.py) using the REST API.

It demonstrates how to:
1. Configure sweep parameters
2. Check for existing references on both channels
3. Create references on channels 1 and 2 independently
4. Monitor referencing progress
5. Verify reference creation
6. Read and plot reference trace data for both channels

Channel mapping (IL RL OPM2 module):
- Channel 1 (IN1): Transmission measurement
- Channel 2 (IN2): Back-reflection measurement

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
CHANNEL_1 = 1  # IN1 - Transmission
CHANNEL_2 = 2  # IN2 - Back-reflection


def connect_to_ctp10():
    """Connect to CTP10 via API."""
    print("\n--- Connecting to CTP10 ---")
    try:
        response = requests.post(f"{API_BASE}/connection/connect", timeout=10)
        response.raise_for_status()
        instrument_id = response.json()['instrument_id']
        print(f"Connected: {instrument_id}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        print("\nPlease ensure:")
        print("  - EXFO CTP10 API is running (port 8002)")
        print("  - The instrument is powered on and connected")
        return False


def get_sweep_configuration():
    """Get and display current sweep configuration."""
    print("\n--- Sweep Configuration ---")
    try:
        # Get resolution
        response = requests.get(f"{API_BASE}/detector/config", params={"module": MODULE, "channel": 1})
        response.raise_for_status()
        config = response.json()
        print(f"Resolution: {config.get('resolution_pm', 'N/A'):.2f} pm")

        # Get sweep wavelengths
        response = requests.get(f"{API_BASE}/measurement/sweep/wavelengths")
        response.raise_for_status()
        sweep = response.json()
        print(f"Start: {sweep['start_wavelength_nm']:.2f} nm")
        print(f"Stop: {sweep['stop_wavelength_nm']:.2f} nm")

        # Get TLS1 configuration
        response = requests.get(f"{API_BASE}/tls/1/config")
        response.raise_for_status()
        tls = response.json()
        print(f"TLS1 Speed: {tls.get('sweep_speed_nmps', 'N/A')} nm/s")

        return True
    except Exception as e:
        print(f"WARNING: Could not get sweep configuration: {e}")
        return False


def set_sweep_wavelengths(start_nm, stop_nm):
    """Configure sweep parameters."""
    print(f"\n--- Configuring Sweep Parameters ---")
    try:
        response = requests.post(
            f"{API_BASE}/measurement/sweep/wavelengths",
            json={
                "start_wavelength_nm": start_nm,
                "stop_wavelength_nm": stop_nm
            }
        )
        response.raise_for_status()
        result = response.json()
        print(f"Set Start: {result['start_wavelength_nm']:.2f} nm")
        print(f"Set Stop: {result['stop_wavelength_nm']:.2f} nm")
        return True
    except Exception as e:
        print(f"ERROR: Failed to set sweep wavelengths: {e}")
        return False


def check_existing_reference(channel):
    """Check if there's an existing reference on the channel."""
    try:
        response = requests.get(
            f"{API_BASE}/detector/reference/result",
            params={"module": MODULE, "channel": channel}
        )
        response.raise_for_status()
        result = response.json()

        print(f"\nChannel {channel}:")
        if result['state'] == 1:
            print("  ✓ Valid reference found:")
            type_desc = 'TF (1 sweep)' if result['type'] == 0 else 'TF/PDL (4 sweeps)'
            print(f"    Type: {result['type']} ({type_desc})")
            print(f"    Date: {result['date']}")
            print(f"    Time: {result['time']}")

            # Format timestamp
            if result['date'] and result['time']:
                date_str = result['date']
                time_str = result['time']
                formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                formatted_time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                print(f"    Timestamp: {formatted_date} {formatted_time}")
        else:
            print("  ✗ No valid reference found")

        return result
    except Exception as e:
        print(f"  ERROR: Failed to check reference: {e}")
        return None


def create_reference_for_channel(channel):
    """
    Create a new reference on the specified channel and wait for completion.

    This uses the wait=true parameter which blocks until the referencing operation
    completes, matching the logic from the pymeasure example.

    Returns:
        bool: True if successful, False otherwise
    """
    channel_name = "IN1 (Transmission)" if channel == 1 else "IN2 (Back-reflection)"
    print(f"\n--- Creating Reference for Channel {channel} ({channel_name}) ---")

    try:
        # Create reference with wait=true (blocks until complete)
        print("Initiating reference creation (will wait for completion)...")
        response = requests.post(
            f"{API_BASE}/detector/reference",
            params={
                "module": MODULE,
                "channel": channel,
                "wait": True  # IMPORTANT: Wait for completion
            },
            timeout=90  # Allow up to 90 seconds for reference to complete
        )
        response.raise_for_status()
        result = response.json()

        if result.get('is_complete'):
            print(f"✓ Reference operation completed!")

            # Display result details
            ref_result = result.get('result', {})
            if ref_result:
                type_desc = ref_result.get('type_description', 'Unknown')
                print(f"  Type: {ref_result.get('type')} ({type_desc})")
                print(f"  Date: {ref_result.get('date')}")
                print(f"  Time: {ref_result.get('time')}")

                # Format timestamp
                if ref_result.get('date') and ref_result.get('time'):
                    date_str = ref_result['date']
                    time_str = ref_result['time']
                    formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    formatted_time = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                    print(f"  Timestamp: {formatted_date} {formatted_time}")

            print(f"\n  ✓ Reference created successfully for Channel {channel}!")
            return True
        else:
            print(f"  ✗ Reference creation did not complete for Channel {channel}")
            return False

    except requests.exceptions.Timeout:
        print(f"✗ Timeout: Reference operation did not complete within 90 seconds")
        return False
    except Exception as e:
        print(f"ERROR during reference creation: {e}")
        return False


def get_reference_trace(channel):
    """Retrieve reference trace data for a channel."""
    try:
        response = requests.get(
            f"{API_BASE}/detector/trace/binary",
            params={
                "module": MODULE,
                "channel": channel,
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

        return trace
    except Exception as e:
        print(f"ERROR: Failed to get reference trace for channel {channel}: {e}")
        return None


def plot_reference_traces(trace_ch1, trace_ch2):
    """Plot reference traces for both channels."""
    print("\n--- Reading and Plotting Reference Trace Data ---")

    # Create subplots for both channels
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    for idx, (channel, trace, ax, name) in enumerate([
        (CHANNEL_1, trace_ch1, ax1, "IN1 (Transmission)"),
        (CHANNEL_2, trace_ch2, ax2, "IN2 (Back-reflection)")
    ]):
        if trace is None:
            print(f"\nChannel {channel}: No trace data available")
            ax.text(0.5, 0.5, f'No trace data for Channel {channel}',
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
            continue

        wavelengths_nm = trace["wavelengths"]
        ref_powers = trace["values"]

        print(f"\nChannel {channel} ({name}):")
        print(f"  Reference trace length: {len(wavelengths_nm)} points")
        print(f"  Reference power range: {ref_powers.min():.2f} to {ref_powers.max():.2f} dB")
        print(f"  Reference mean power: {ref_powers.mean():.2f} dB")
        print(f"  Wavelength range: {wavelengths_nm[0]:.2f} to {wavelengths_nm[-1]:.2f} nm")

        # Plot the reference trace
        ax.plot(wavelengths_nm, ref_powers, linewidth=0.8, color='blue', label='Reference Trace')
        ax.set_xlabel('Wavelength (nm)', fontsize=11)
        ax.set_ylabel('Power (dB)', fontsize=11)
        ax.set_title(f'Channel {channel} ({name}) - Reference Trace', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

    plt.suptitle(f'EXFO CTP10 Reference Traces - Module {MODULE}', fontsize=14, y=0.995)
    plt.tight_layout()
    plt.show()


def main():
    """Main execution flow."""
    print("=" * 70)
    print("EXFO CTP10 - Dual Channel Reference Creation Example")
    print("=" * 70)

    # Step 1: Connect
    if not connect_to_ctp10():
        return

    # Step 2: Get configuration
    get_sweep_configuration()

    # Step 3: Configure sweep parameters (optional - uncomment to set)
    # set_sweep_wavelengths(start_nm=1262.5, stop_nm=1355.0)

    # Step 4: Check existing references
    print("\n--- Checking Existing References ---")
    check_existing_reference(CHANNEL_1)
    check_existing_reference(CHANNEL_2)

    # Step 5: Ask user if they want to create new references
    print("\n" + "=" * 70)
    print("REFERENCE TRACE CREATION")
    print("=" * 70)
    print("\nYou can now create NEW reference traces for both channels.")
    print("\nBefore proceeding, please ensure:")
    print("  1. Remove any DUT from the setup")
    print("  2. Connect the reference fiber (bypassing the DUT)")
    print("  3. Ensure good optical connections (clean connectors)")
    print("  4. TLS is configured with the desired wavelength range")
    print("=" * 70)

    response = input("\nDo you want to create new reference traces? (y/n): ").strip().lower()

    if response != 'y':
        print("\nReference creation cancelled by user.")
        print("\n--- Retrieving and plotting existing references ---")
        trace_ch1 = get_reference_trace(CHANNEL_1)
        trace_ch2 = get_reference_trace(CHANNEL_2)
        if trace_ch1 or trace_ch2:
            plot_reference_traces(trace_ch1, trace_ch2)
        print("\nExiting...")
        return

    # Step 6: Create references for both channels (decoupled, independent)
    print("\n--- Creating New References ---")
    print("Starting reference acquisition on both channels (independently)...")

    success_ch1 = create_reference_for_channel(CHANNEL_1)
    success_ch2 = create_reference_for_channel(CHANNEL_2)

    if not success_ch1 or not success_ch2:
        print("\n⚠ Warning: One or more reference creations failed")
        print("Continuing to plot available references...")

    # Step 7: Retrieve and plot reference traces
    time.sleep(1)  # Brief delay to ensure data is available

    trace_ch1 = get_reference_trace(CHANNEL_1)
    trace_ch2 = get_reference_trace(CHANNEL_2)

    if trace_ch1 or trace_ch2:
        plot_reference_traces(trace_ch1, trace_ch2)
    else:
        print("\nERROR: Could not retrieve reference traces")

    # Summary
    print("\n--- Reference Example Complete ---")
    print("\nNext steps:")
    print("1. Perform a sweep to acquire live trace data")
    print("2. Read the TF trace (TYPE1) to see the transmission function")
    print("3. The TF trace shows the difference between live and reference measurements")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
