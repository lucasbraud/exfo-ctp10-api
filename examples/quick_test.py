#!/usr/bin/env python3
"""
Quick Test Script for EXFO CTP10 API

This script performs a quick sanity check of all major API endpoints.
Use this to verify the refactored API is working correctly.

Author: API Testing
Date: November 10, 2025
"""
import requests
import sys

# API Configuration
API_BASE = "http://localhost:8000"

# Test configuration
MODULE = 4
CHANNEL = 1
TLS_CHANNEL = 1
RLASER_NUMBER = 2  # Using laser 2 (O-band) - laser 1 may not be present


def test_health():
    """Test health and root endpoints."""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)

    try:
        # Test root endpoint
        response = requests.get(f"{API_BASE}/")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Root endpoint: {data['service']}")

        # Test health endpoint
        response = requests.get(f"{API_BASE}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Health endpoint: {data['status']}")
        print(f"  Connected: {data['connected']}")

        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_connection():
    """Test connection endpoints."""
    print("\n" + "=" * 60)
    print("TEST 2: Connection")
    print("=" * 60)

    try:
        # Check connection status
        response = requests.get(f"{API_BASE}/connection/status")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Connection status: {data['connected']}")

        if data['connected']:
            print(f"  Instrument: {data['instrument_id']}")
            print(f"  Address: {data['address']}")
        else:
            # Try to connect
            print("  Not connected, attempting connection...")
            response = requests.post(f"{API_BASE}/connection/connect")
            response.raise_for_status()
            data = response.json()
            print(f"✓ Connected: {data['instrument_id']}")

        # Check condition register
        response = requests.get(f"{API_BASE}/connection/condition")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Condition register: {data['register_value']}")
        print(f"  Is idle: {data['is_idle']}")

        return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


def test_detector():
    """Test detector endpoints."""
    print("\n" + "=" * 60)
    print("TEST 3: Detector")
    print("=" * 60)

    try:
        # Get detector configuration
        response = requests.get(
            f"{API_BASE}/detector/config",
            params={"module": MODULE, "channel": CHANNEL}
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Detector config (Module {MODULE}, Channel {CHANNEL}):")
        print(f"  Power unit: {data['power_unit']}")
        print(f"  Spectral unit: {data['spectral_unit']}")

        # Get 4-channel snapshot
        response = requests.get(
            f"{API_BASE}/detector/snapshot",
            params={"module": MODULE}
        )
        response.raise_for_status()
        snapshot = response.json()
        print(f"✓ Detector snapshot (4 channels):")
        print(f"  CH1: {snapshot['ch1_power']:.3f} {snapshot['unit']}")
        print(f"  CH2: {snapshot['ch2_power']:.3f} {snapshot['unit']}")
        print(f"  CH3: {snapshot['ch3_power']:.3f} {snapshot['unit']}")
        print(f"  CH4: {snapshot['ch4_power']:.3f} {snapshot['unit']}")
        print(f"  Wavelength: {snapshot['wavelength_nm']:.4f} nm")

        return True
    except Exception as e:
        print(f"✗ Detector test failed: {e}")
        return False


def test_tls():
    """Test TLS endpoints."""
    print("\n" + "=" * 60)
    print("TEST 4: TLS")
    print("=" * 60)

    try:
        # Get TLS configuration
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/config")
        response.raise_for_status()
        data = response.json()
        print(f"✓ TLS{TLS_CHANNEL} configuration:")
        print(f"  Start wavelength: {data['start_wavelength_nm']:.2f} nm")
        print(f"  Stop wavelength: {data['stop_wavelength_nm']:.2f} nm")
        print(f"  Sweep speed: {data['sweep_speed_nmps']} nm/s")
        print(f"  Laser power: {data['laser_power_dbm']:.2f} dBm")
        print(f"  Trigger: {data['trigin']}")

        # Get individual parameters
        response = requests.get(f"{API_BASE}/tls/{TLS_CHANNEL}/power")
        response.raise_for_status()
        data = response.json()
        print(f"✓ TLS{TLS_CHANNEL} power: {data['laser_power_dbm']:.2f} dBm")

        return True
    except Exception as e:
        print(f"✗ TLS test failed: {e}")
        return False


def test_rlaser():
    """Test RLaser endpoints."""
    print("\n" + "=" * 60)
    print("TEST 5: Reference Laser")
    print("=" * 60)

    try:
        # Test both laser 1 and laser 2 (C-band and O-band)
        for laser_num in [1, 2]:
            laser_type = "C-band" if laser_num == 1 else "O-band"

            # Get RLaser ID
            response = requests.get(f"{API_BASE}/rlaser/{laser_num}/id")
            response.raise_for_status()
            data = response.json()
            print(f"✓ RLaser{laser_num} ({laser_type}) ID:")
            print(f"  Manufacturer: {data['manufacturer']}")
            print(f"  Model: {data['model']}")
            print(f"  Firmware: {data['firmware']}")

            # Get RLaser state
            response = requests.get(f"{API_BASE}/rlaser/{laser_num}/state")
            response.raise_for_status()
            data = response.json()
            print(f"  State: {'ON' if data['is_on'] else 'OFF'}")

        # Get RLaser configuration for primary laser (laser 2)
        response = requests.get(f"{API_BASE}/rlaser/{RLASER_NUMBER}/config")
        response.raise_for_status()
        data = response.json()
        print(f"\n✓ RLaser{RLASER_NUMBER} configuration:")
        print(f"  Wavelength: {data['wavelength_nm']:.2f} nm")
        print(f"  Power: {data['power_dbm']:.2f} dBm")

        return True
    except Exception as e:
        print(f"✗ RLaser test failed: {e}")
        return False


def test_measurement():
    """Test measurement endpoints."""
    print("\n" + "=" * 60)
    print("TEST 6: Measurement")
    print("=" * 60)

    try:
        # Get sweep configuration
        response = requests.get(f"{API_BASE}/measurement/config")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Sweep configuration:")
        print(f"  Resolution: {data['resolution_pm']:.2f} pm")
        print(f"  Stabilization output: {data['stabilization_output']}")
        print(f"  Stabilization duration: {data['stabilization_duration']} s")

        # Get sweep status
        response = requests.get(f"{API_BASE}/measurement/sweep/status")
        response.raise_for_status()
        data = response.json()
        print(f"✓ Sweep status:")
        print(f"  Is sweeping: {data['is_sweeping']}")
        print(f"  Is complete: {data['is_complete']}")
        print(f"  Condition register: {data['condition_register']}")

        return True
    except Exception as e:
        print(f"✗ Measurement test failed: {e}")
        return False


def test_trace_metadata():
    """Test trace metadata endpoint (quick test without downloading data)."""
    print("\n" + "=" * 60)
    print("TEST 7: Trace Metadata")
    print("=" * 60)

    try:
        # Get trace metadata
        response = requests.get(
            f"{API_BASE}/detector/trace/metadata",
            params={
                "module": MODULE,
                "channel": CHANNEL,
                "trace_type": 1  # TF live
            }
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Trace metadata (Module {MODULE}, Channel {CHANNEL}, Type 1):")
        print(f"  Number of points: {data['num_points']}")
        print(f"  Sampling: {data['sampling_pm']:.2f} pm")
        print(f"  Start wavelength: {data['start_wavelength_nm']:.4f} nm")
        print(f"  Unit: {data['unit']}")

        return True
    except Exception as e:
        print(f"✗ Trace metadata test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EXFO CTP10 API - Quick Test")
    print("=" * 60)
    print(f"API Base URL: {API_BASE}")
    print(f"Test Configuration:")
    print(f"  Module: {MODULE}")
    print(f"  Channel: {CHANNEL}")
    print(f"  TLS Channel: {TLS_CHANNEL}")
    print(f"  RLaser Number: {RLASER_NUMBER}")
    print()

    # Check if API server is running
    try:
        requests.get(f"{API_BASE}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"✗ ERROR: Cannot connect to API server at {API_BASE}")
        print("  Make sure the API server is running:")
        print("  → fastapi dev app/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ ERROR: Unexpected error: {e}")
        sys.exit(1)

    # Run all tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Connection", test_connection()))
    results.append(("Detector", test_detector()))
    results.append(("TLS", test_tls()))
    results.append(("RLaser", test_rlaser()))
    results.append(("Measurement", test_measurement()))
    results.append(("Trace Metadata", test_trace_metadata()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
