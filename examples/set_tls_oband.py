#!/usr/bin/env python3
"""
Set TLS1 to O-band Configuration (Corrected Order)

This script configures TLS1 for O-band operation by setting parameters in the correct order:
1. Set identifier first (which may reset wavelengths to defaults)
2. Set trigin
3. Set other parameters (speed, power)
4. Set wavelengths last to override defaults

Author: API Testing
Date: November 21, 2025
"""
import requests
import sys
import time

# API Configuration
API_BASE = "http://localhost:8002"
TLS_CHANNEL = 1  # TLS1

# O-band Configuration
OBAND_CONFIG = {
    "identifier": 2,  # Set first - O-band laser
    "trigin": 2,  # TRIG IN port 2 for O-band
    "sweep_speed_nmps": 20,
    "laser_power_dbm": 10.0,
    "start_wavelength_nm": 1262.5,  # Set last to override defaults
    "stop_wavelength_nm": 1355.0,   # Set last to override defaults
}


def check_api_server():
    """Check if API server is running."""
    try:
        requests.get(f"{API_BASE}/", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        print(f"✗ ERROR: Cannot connect to API server at {API_BASE}")
        print("  Make sure the API server is running:")
        print("  → fastapi dev app/main.py --port=8002")
        return False


def read_tls_config():
    """Read and display TLS1 configuration."""
    try:
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/config")
        response.raise_for_status()
        config = response.json()

        print(f"Channel:                 {config['channel']}")
        print(f"Start Wavelength:        {config['start_wavelength_nm']:.4f} nm")
        print(f"Stop Wavelength:         {config['stop_wavelength_nm']:.4f} nm")
        print(f"Wavelength Range:        {config['stop_wavelength_nm'] - config['start_wavelength_nm']:.4f} nm")
        print(f"Sweep Speed:             {config['sweep_speed_nmps']} nm/s")
        print(f"Laser Power:             {config['laser_power_dbm']:.2f} dBm")
        print(f"Trigger Input (trigin):  {config['trigin']}")
        
        # Decode trigin
        if config['trigin'] == 0:
            trigger_desc = "Software trigger"
        else:
            trigger_desc = f"TRIG IN port {config['trigin']}"
        print(f"Trigger Description:     {trigger_desc}")
        
        print(f"Identifier:              {config['identifier']}")
        
        # Decode identifier (laser reference)
        if config['identifier'] == 1:
            laser_desc = "C-band laser (1502-1627 nm)"
        elif config['identifier'] == 2:
            laser_desc = "O-band laser (1262.5-1355 nm)"
        else:
            laser_desc = f"Unknown/Other (ID {config['identifier']})"
        print(f"Reference Laser:         {laser_desc}")
        
        # Calculate sweep duration
        wavelength_range = config['stop_wavelength_nm'] - config['start_wavelength_nm']
        sweep_duration_sec = wavelength_range / config['sweep_speed_nmps']
        print(f"\nEstimated Sweep Duration: {sweep_duration_sec:.2f} seconds")
        
        return config

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        if e.response is not None:
            print(f"  Status Code: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"  Detail: {error_detail.get('detail', 'No detail available')}")
            except:
                print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def set_config_parameter(param_dict, description):
    """Set TLS configuration parameter(s) via /config endpoint."""
    try:
        response = requests.post(
            f"{API_BASE}/tls/{TLS_CHANNEL}/config",
            json=param_dict
        )
        response.raise_for_status()
        result = response.json()
        print(f"  ✓ {description}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 70)
    print("TLS1 O-band Configuration Script (Corrected Order)")
    print("=" * 70)
    print(f"API Base URL: {API_BASE}\n")

    # Check if API server is running
    if not check_api_server():
        sys.exit(1)

    # Read current configuration
    print("=" * 70)
    print("CURRENT TLS1 CONFIGURATION (BEFORE)")
    print("=" * 70)
    current_config = read_tls_config()
    if current_config is None:
        sys.exit(1)
    print("=" * 70)

    # Display new O-band configuration
    print("\n" + "=" * 70)
    print("APPLYING O-BAND CONFIGURATION (IN CORRECT ORDER)")
    print("=" * 70)
    print("Order matters: identifier & trigin first, wavelengths last")
    print()

    # Step 1: Set identifier (may reset wavelengths to defaults)
    print("Step 1: Set identifier to O-band laser...")
    if not set_config_parameter(
        {"identifier": OBAND_CONFIG["identifier"]},
        f"Set identifier = {OBAND_CONFIG['identifier']} (O-band laser)"
    ):
        sys.exit(1)
    time.sleep(0.2)

    # Step 2: Set trigin
    print("\nStep 2: Set trigger input...")
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/trigger",
        params={"trigin": OBAND_CONFIG["trigin"]}
    )
    if response.status_code == 200:
        print(f"  ✓ Set trigin = {OBAND_CONFIG['trigin']} (TRIG IN port {OBAND_CONFIG['trigin']})")
    else:
        print(f"  ✗ Failed to set trigin")
        sys.exit(1)
    time.sleep(0.2)

    # Step 3: Set sweep speed
    print("\nStep 3: Set sweep speed...")
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/speed",
        params={"speed_nmps": OBAND_CONFIG["sweep_speed_nmps"]}
    )
    if response.status_code == 200:
        print(f"  ✓ Set sweep_speed = {OBAND_CONFIG['sweep_speed_nmps']} nm/s")
    else:
        print(f"  ✗ Failed to set sweep speed")
        sys.exit(1)
    time.sleep(0.2)

    # Step 4: Set laser power
    print("\nStep 4: Set laser power...")
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/power",
        params={"power_dbm": OBAND_CONFIG["laser_power_dbm"]}
    )
    if response.status_code == 200:
        print(f"  ✓ Set laser_power = {OBAND_CONFIG['laser_power_dbm']} dBm")
    else:
        print(f"  ✗ Failed to set laser power")
        sys.exit(1)
    time.sleep(0.2)

    # Step 5: Set wavelength range (LAST to override defaults from identifier change)
    print("\nStep 5: Set wavelength range (overrides defaults)...")
    response = requests.post(
        f"{API_BASE}/tls/{TLS_CHANNEL}/wavelength",
        params={
            "start_nm": OBAND_CONFIG["start_wavelength_nm"],
            "stop_nm": OBAND_CONFIG["stop_wavelength_nm"]
        }
    )
    if response.status_code == 200:
        print(f"  ✓ Set start_wavelength = {OBAND_CONFIG['start_wavelength_nm']} nm")
        print(f"  ✓ Set stop_wavelength = {OBAND_CONFIG['stop_wavelength_nm']} nm")
    else:
        print(f"  ✗ Failed to set wavelength range")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✓ All parameters applied successfully!")
    print("=" * 70)

    # Wait a moment for settings to take effect
    time.sleep(0.5)

    # Read back configuration to verify
    print("\n" + "=" * 70)
    print("TLS1 CONFIGURATION (AFTER) - VERIFICATION")
    print("=" * 70)
    new_config = read_tls_config()
    if new_config is None:
        sys.exit(1)
    print("=" * 70)

    # Verify changes
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_correct = True
    checks = [
        ("Start Wavelength", new_config['start_wavelength_nm'], OBAND_CONFIG['start_wavelength_nm'], "nm"),
        ("Stop Wavelength", new_config['stop_wavelength_nm'], OBAND_CONFIG['stop_wavelength_nm'], "nm"),
        ("Sweep Speed", new_config['sweep_speed_nmps'], OBAND_CONFIG['sweep_speed_nmps'], "nm/s"),
        ("Laser Power", new_config['laser_power_dbm'], OBAND_CONFIG['laser_power_dbm'], "dBm"),
        ("Trigger Input", new_config['trigin'], OBAND_CONFIG['trigin'], ""),
        ("Identifier", new_config['identifier'], OBAND_CONFIG['identifier'], ""),
    ]
    
    for name, actual, expected, unit in checks:
        if abs(actual - expected) < 0.01:  # Small tolerance for floating point
            status = "✓"
        else:
            status = "✗"
            all_correct = False
        
        unit_str = f" {unit}" if unit else ""
        print(f"{status} {name:20} Expected: {expected}{unit_str:8}  Actual: {actual}{unit_str}")
    
    print("=" * 70)
    
    if all_correct:
        print("\n✓ SUCCESS: All O-band configuration parameters verified!")
    else:
        print("\n✗ WARNING: Some parameters may not match expected values")
    
    print("\n✓ Configuration complete!")


if __name__ == "__main__":
    main()
