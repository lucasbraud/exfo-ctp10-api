#!/usr/bin/env python3
"""
Example script to demonstrate EXFO CTP10 detector wavelength configuration.

This shows how to:
1. Read current detector wavelength
2. Set detector wavelength for O-band (1310 nm) or C-band (1550 nm)
3. Verify the wavelength was set correctly

The detector wavelength setting affects power measurement calibration.
"""

import requests

# Configuration
EXFO_API_BASE_URL = "http://127.0.0.1:8002"
MODULE = 4  # Detector module number
CHANNEL = 1  # Channel 1 (on IL RL OPM2, this applies to all channels)

def get_detector_wavelength():
    """Get current detector wavelength."""
    response = requests.get(
        f"{EXFO_API_BASE_URL}/detector/wavelength",
        params={"module": MODULE, "channel": CHANNEL}
    )
    response.raise_for_status()
    return response.json()

def set_detector_wavelength(wavelength_nm: float):
    """Set detector wavelength."""
    response = requests.post(
        f"{EXFO_API_BASE_URL}/detector/wavelength",
        params={
            "module": MODULE,
            "channel": CHANNEL,
            "wavelength_nm": wavelength_nm
        }
    )
    response.raise_for_status()
    return response.json()

def main():
    print("EXFO CTP10 Detector Wavelength Configuration Example")
    print("=" * 60)

    # Read current wavelength
    print("\n1. Reading current detector wavelength...")
    current = get_detector_wavelength()
    print(f"   Module: {current['module']}, Channel: {current['channel']}")
    print(f"   Wavelength: {current['wavelength_nm']:.3f} nm")
    print(f"   Frequency: {current['frequency_thz']:.4f} THz")

    # Set to O-band wavelength (1310 nm)
    print("\n2. Setting wavelength to O-band (1310 nm)...")
    result = set_detector_wavelength(1310.0)
    print(f"   ✓ Set to {result['wavelength_nm']:.3f} nm")

    # Verify
    print("\n3. Verifying wavelength was set...")
    verify = get_detector_wavelength()
    print(f"   Current: {verify['wavelength_nm']:.3f} nm")

    # Set to C-band wavelength (1550 nm)
    print("\n4. Setting wavelength to C-band (1550 nm)...")
    result = set_detector_wavelength(1550.0)
    print(f"   ✓ Set to {result['wavelength_nm']:.3f} nm")

    # Verify
    print("\n5. Verifying wavelength was set...")
    verify = get_detector_wavelength()
    print(f"   Current: {verify['wavelength_nm']:.3f} nm")

    print("\n" + "=" * 60)
    print("Done!")
    print("\nNote: On IL RL OPM2 modules, setting wavelength on one channel")
    print("      (TLS IN, Out to SCAN SYNC, or Out to DUT) applies to all channels.")

if __name__ == "__main__":
    main()
