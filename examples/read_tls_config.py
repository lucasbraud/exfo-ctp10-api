#!/usr/bin/env python3
"""
Read TLS Configuration Script for EXFO CTP10 API

This script reads the current configuration of TLS1 (Tunable Laser Source)
including wavelength range, sweep speed, laser power, identifier, and trigger settings.

Author: API Testing
Date: November 21, 2025
"""
import requests
import sys

# API Configuration
API_BASE = "http://localhost:8002"
TLS_CHANNEL = 1  # TLS1


def read_tls_config():
    """Read complete TLS1 configuration."""
    print("=" * 70)
    print(f"TLS{TLS_CHANNEL} Configuration Reader")
    print("=" * 70)
    print(f"API Base URL: {API_BASE}\n")

    try:
        # Check if API server is running
        try:
            requests.get(f"{API_BASE}/", timeout=2)
        except requests.exceptions.ConnectionError:
            print(f"✗ ERROR: Cannot connect to API server at {API_BASE}")
            print("  Make sure the API server is running:")
            print("  → fastapi dev app/main.py --port=8002")
            sys.exit(1)

        # Get complete TLS configuration
        print(f"Reading TLS{TLS_CHANNEL} configuration...\n")
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/config")
        response.raise_for_status()
        config = response.json()

        # Display configuration
        print("=" * 70)
        print("CURRENT TLS1 CONFIGURATION")
        print("=" * 70)
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
        
        print("=" * 70)
        
        # Calculate sweep duration
        wavelength_range = config['stop_wavelength_nm'] - config['start_wavelength_nm']
        sweep_duration_sec = wavelength_range / config['sweep_speed_nmps']
        print(f"\nEstimated Sweep Duration: {sweep_duration_sec:.2f} seconds")
        print("=" * 70)

        return config

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        if e.response is not None:
            print(f"  Status Code: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"  Detail: {error_detail.get('detail', 'No detail available')}")
            except:
                print(f"  Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


def read_individual_parameters():
    """Read individual TLS parameters using specific endpoints."""
    print("\n" + "=" * 70)
    print("READING INDIVIDUAL PARAMETERS (verification)")
    print("=" * 70)
    
    try:
        # Wavelength range
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/wavelength")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Wavelength: {data['start_wavelength_nm']:.4f} - {data['stop_wavelength_nm']:.4f} nm")

        # Power
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/power")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Power:      {data['laser_power_dbm']:.2f} dBm")

        # Speed
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/speed")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Speed:      {data['sweep_speed_nmps']} nm/s")

        # Trigger
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/trigger")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Trigger:    {data['trigin']} ({data['description']})")

        print("=" * 70)
        print("\n✓ All parameters read successfully!")
        
    except Exception as e:
        print(f"\n✗ Error reading individual parameters: {e}")


def main():
    """Main entry point."""
    # Read complete configuration
    config = read_tls_config()
    
    # Optionally read individual parameters for verification
    # Uncomment the line below to verify using individual endpoints
    # read_individual_parameters()
    
    print("\n✓ Configuration read complete!")


if __name__ == "__main__":
    main()
