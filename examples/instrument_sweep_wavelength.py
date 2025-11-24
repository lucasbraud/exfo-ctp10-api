#!/usr/bin/env python3
"""Example: Get and set instrument-level sweep wavelengths on EXFO CTP10 API.

This demonstrates the new /measurement/sweep/wavelengths endpoints which expose
CTP10 global sweep start/stop wavelength (distinct from TLS channel settings).

Prerequisites:
  1. Run the FastAPI server for exfo-ctp10-api (e.g. `uvicorn app.main:app --reload`)
  2. Ensure the server has connected to the instrument (see connection endpoints)
  3. PyMeasure installed from dev-all-instruments branch so CTP10 has properties:
     start_wavelength_nm, stop_wavelength_nm

Usage:
  python examples/instrument_sweep_wavelength.py --host http://localhost:8000 \
      --start 1525 --stop 1565

If only --start is given, only start updates. Same for --stop.

Note: The instrument may auto-adjust one limit when the other changes; the
returned values reflect effective configuration after firmware normalization.
"""

import argparse
import sys
import requests


def get_wavelengths(base_url: str) -> dict:
    r = requests.get(f"{base_url}/measurement/sweep/wavelengths", timeout=10)
    r.raise_for_status()
    return r.json()


def set_wavelengths(base_url: str, start: float | None, stop: float | None) -> dict:
    payload = {"start_wavelength_nm": start, "stop_wavelength_nm": stop}
    # Remove None entries to avoid 400 on validation
    payload = {k: v for k, v in payload.items() if v is not None}
    r = requests.post(f"{base_url}/measurement/sweep/wavelengths", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Instrument-level sweep wavelength control example")
    parser.add_argument("--host", default="http://localhost:8002", help="Base URL of API server")
    parser.add_argument("--start", type=float, default=None, help="New start wavelength (nm)")
    parser.add_argument("--stop", type=float, default=None, help="New stop wavelength (nm)")
    args = parser.parse_args()

    base_url = args.host.rstrip('/')

    print("Current sweep wavelengths (instrument-level):")
    current = get_wavelengths(base_url)
    print(f"  Start: {current.get('start_wavelength_nm')} nm")
    print(f"  Stop : {current.get('stop_wavelength_nm')} nm")

    if args.start is None and args.stop is None:
        print("No new values provided; exiting.")
        return

    print("\nSetting sweep wavelengths...")
    updated = set_wavelengths(base_url, args.start, args.stop)
    print("Effective values returned by instrument:")
    print(f"  Start: {updated.get('start_wavelength_nm')} nm")
    print(f"  Stop : {updated.get('stop_wavelength_nm')} nm")

    print("\nRe-query to confirm:")
    confirmed = get_wavelengths(base_url)
    print(f"  Start: {confirmed.get('start_wavelength_nm')} nm")
    print(f"  Stop : {confirmed.get('stop_wavelength_nm')} nm")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"HTTP error: {e.response.status_code} {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)
