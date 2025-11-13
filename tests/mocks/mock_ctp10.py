"""Mock CTP10 instrument for testing without hardware."""

import numpy as np
from typing import Optional
import time


class FakeDetector:
    """Mock detector channel for CTP10."""

    def __init__(self, module: int, channel: int, ctp10_instance=None):
        self.module = module
        self.channel = channel
        self.ctp10 = ctp10_instance  # Reference to parent CTP10 instance
        self._wavelength_nm = 1310.0
        self._power = -15.5 + (channel * 2.3)  # Varied power per channel
        self._power_unit = "dBm"
        self._spectral_unit = "nm"
        self._trace_data = {}  # Store trace data by type

    @property
    def wavelength_nm(self) -> float:
        """Get detector wavelength."""
        return self._wavelength_nm

    @wavelength_nm.setter
    def wavelength_nm(self, value: float):
        """Set detector wavelength."""
        self._wavelength_nm = value

    @property
    def power(self) -> float:
        """Get detector power reading."""
        # Add small random variation to simulate real readings
        return self._power + (np.random.random() * 0.1 - 0.05)

    @property
    def power_unit(self) -> str:
        """Get power unit."""
        return self._power_unit

    @power_unit.setter
    def power_unit(self, value: str):
        """Set power unit."""
        self._power_unit = value

    @property
    def spectral_unit(self) -> str:
        """Get spectral unit."""
        return self._spectral_unit

    @spectral_unit.setter
    def spectral_unit(self, value: str):
        """Set spectral unit."""
        self._spectral_unit = value

    def create_reference(self):
        """Create reference trace."""
        # Simulate reference creation
        pass

    def length(self, trace_type: int = 1) -> int:
        """Get trace length."""
        return 100000  # Simulated trace length

    def sampling_pm(self, trace_type: int = 1) -> float:
        """Get sampling resolution in picometers."""
        return 10.0

    def start_wavelength_nm(self, trace_type: int = 1) -> float:
        """Get trace start wavelength."""
        # Use TLS1 start wavelength if available
        if self.ctp10 and hasattr(self.ctp10, 'tls1'):
            return self.ctp10.tls1.start_wavelength_nm
        return 1460.0

    def get_data_x(self, trace_type: int = 1, unit: str = 'M', format: str = 'BIN') -> np.ndarray:
        """Get wavelength data."""
        # Generate mock wavelength array using TLS configuration
        num_points = self.length(trace_type)
        
        # Get start/stop from TLS1 if available
        if self.ctp10 and hasattr(self.ctp10, 'tls1'):
            start_nm = self.ctp10.tls1.start_wavelength_nm
            stop_nm = self.ctp10.tls1.stop_wavelength_nm
        else:
            start_nm = 1460.0
            stop_nm = 1640.0
        
        start_m = start_nm * 1e-9  # Convert to meters
        stop_m = stop_nm * 1e-9
        return np.linspace(start_m, stop_m, num_points)

    def get_data_y(self, trace_type: int = 1, unit: str = 'DB', format: str = 'BIN') -> np.ndarray:
        """Get power/transmission data."""
        # Generate mock power array with some noise
        num_points = self.length(trace_type)
        base_power = -20.0
        noise = np.random.randn(num_points) * 0.5
        return np.full(num_points, base_power) + noise


class FakeTLS:
    """Mock TLS (Tunable Laser Source) channel."""

    def __init__(self, channel: int):
        self.channel = channel
        self._start_wavelength_nm = 1500.0
        self._stop_wavelength_nm = 1600.0
        self._sweep_speed_nmps = 50
        self._laser_power_dbm = 5.0
        self._trigin = 0
        self._identifier = 1  # Default to C-band

    @property
    def start_wavelength_nm(self) -> float:
        return self._start_wavelength_nm

    @start_wavelength_nm.setter
    def start_wavelength_nm(self, value: float):
        self._start_wavelength_nm = value

    @property
    def stop_wavelength_nm(self) -> float:
        return self._stop_wavelength_nm

    @stop_wavelength_nm.setter
    def stop_wavelength_nm(self, value: float):
        self._stop_wavelength_nm = value

    @property
    def sweep_speed_nmps(self) -> int:
        return self._sweep_speed_nmps

    @sweep_speed_nmps.setter
    def sweep_speed_nmps(self, value: int):
        self._sweep_speed_nmps = value

    @property
    def laser_power_dbm(self) -> float:
        return self._laser_power_dbm

    @laser_power_dbm.setter
    def laser_power_dbm(self, value: float):
        self._laser_power_dbm = value

    @property
    def trigin(self) -> int:
        return self._trigin

    @trigin.setter
    def trigin(self, value: int):
        self._trigin = value

    @property
    def identifier(self) -> int:
        return self._identifier

    @identifier.setter
    def identifier(self, value: int):
        self._identifier = value


class FakeRLaser:
    """Mock Reference Laser."""

    def __init__(self, laser_number: int):
        self.laser_number = laser_number
        self._idn = ["EXFO", "T100S-HP", "0", "6.06"]
        self._wavelength_nm = 1550.0
        self._power_dbm = 5.0
        self._power_state_enabled = False

    @property
    def idn(self) -> list:
        """Get laser identification."""
        return self._idn

    @property
    def wavelength_nm(self) -> float:
        return self._wavelength_nm

    @wavelength_nm.setter
    def wavelength_nm(self, value: float):
        self._wavelength_nm = value

    @property
    def power_dbm(self) -> float:
        return self._power_dbm

    @power_dbm.setter
    def power_dbm(self, value: float):
        self._power_dbm = value

    @property
    def power_state_enabled(self) -> bool:
        return self._power_state_enabled

    @power_state_enabled.setter
    def power_state_enabled(self, value: bool):
        self._power_state_enabled = value


class FakeRLaserCollection:
    """Mock RLaser collection that acts like a dictionary."""

    def __init__(self):
        self._lasers = {i: FakeRLaser(i) for i in range(1, 11)}

    def __getitem__(self, key: int) -> FakeRLaser:
        """Get laser by number."""
        if key not in self._lasers:
            raise KeyError(f"Invalid laser number: {key}")
        return self._lasers[key]


class FakeCTP10:
    """
    Mock CTP10 instrument for testing without real hardware.

    Implements the pymeasure CTP10 interface with stateful behavior.
    """

    def __init__(self, address: str = "MOCK::ADDRESS"):
        self.address = address
        self._id = "EXFO,CTP10,12345678,1.2.3"
        self._condition_register = 0  # 0 = idle
        self._resolution_pm = 10.0
        self._stabilization = (0, 0.0)  # (output, duration)
        self._sweep_in_progress = False
        self._sweep_start_time = None

        # Create TLS channels
        self.tls1 = FakeTLS(1)
        self.tls2 = FakeTLS(2)
        self.tls3 = FakeTLS(3)
        self.tls4 = FakeTLS(4)

        # Create RLaser collection
        self.rlaser = FakeRLaserCollection()

        # Mock adapter for timeout setting
        self.adapter = type('obj', (object,), {
            'connection': type('obj', (object,), {'timeout': 120000})()
        })()

    @property
    def id(self) -> str:
        """Get instrument identification."""
        return self._id

    @property
    def condition_register(self) -> int:
        """Get condition register (status bits)."""
        # Auto-clear scanning bit after simulated sweep duration
        if self._sweep_in_progress and self._sweep_start_time:
            elapsed = time.time() - self._sweep_start_time
            if elapsed > 0.5:  # Simulate 0.5 second sweep
                self._sweep_in_progress = False
                self._condition_register = 0

        return self._condition_register

    def check_errors(self):
        """Check for instrument errors."""
        # Mock - no errors
        pass

    def detector(self, module: int, channel: int) -> FakeDetector:
        """Get detector channel object."""
        return FakeDetector(module, channel, ctp10_instance=self)

    @property
    def resolution_pm(self) -> float:
        """Get sampling resolution."""
        return self._resolution_pm

    @resolution_pm.setter
    def resolution_pm(self, value: float):
        """Set sampling resolution."""
        self._resolution_pm = value

    @property
    def stabilization(self) -> tuple:
        """Get stabilization settings (output, duration)."""
        return self._stabilization

    @stabilization.setter
    def stabilization(self, value: tuple):
        """Set stabilization settings."""
        self._stabilization = value

    def initiate_sweep(self):
        """Start a sweep operation."""
        self._sweep_in_progress = True
        self._sweep_start_time = time.time()
        self._condition_register = 4  # Bit 2 = scanning

    def wait_for_sweep_complete(self):
        """Wait for sweep to complete (blocking)."""
        while self._sweep_in_progress:
            time.sleep(0.1)
            # Check condition register to update sweep status
            _ = self.condition_register

    @property
    def sweep_complete(self) -> bool:
        """Check if sweep is complete."""
        # Trigger status check
        _ = self.condition_register
        return not self._sweep_in_progress

    def write(self, command: str):
        """Write SCPI command."""
        if command == ':ABORt':
            self._sweep_in_progress = False
            self._condition_register = 0

    def shutdown(self):
        """Shutdown instrument connection."""
        # Mock - nothing to cleanup
        pass
