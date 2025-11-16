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
        return 0.1  # 0.1 pm resolution

    def start_wavelength_nm(self, trace_type: int = 1) -> float:
        """Get trace start wavelength."""
        # Use TLS1 start wavelength if available (O-band by default)
        if self.ctp10 and hasattr(self.ctp10, 'tls1'):
            return self.ctp10.tls1.start_wavelength_nm
        return 1262.5  # Default to O-band start

    def get_data_x(self, trace_type: int = 1, unit: str = 'M', format: str = 'BIN') -> np.ndarray:
        """Get wavelength data."""
        # Generate mock wavelength array using TLS configuration
        num_points = self.length(trace_type)
        
        # Get start/stop from TLS1 if available (O-band by default)
        if self.ctp10 and hasattr(self.ctp10, 'tls1'):
            start_nm = self.ctp10.tls1.start_wavelength_nm
            stop_nm = self.ctp10.tls1.stop_wavelength_nm
        else:
            start_nm = 1262.5  # Default to O-band
            stop_nm = 1355.0
        
        start_m = start_nm * 1e-9  # Convert to meters
        stop_m = stop_nm * 1e-9
        return np.linspace(start_m, stop_m, num_points)

    def get_data_y(self, trace_type: int = 1, unit: str = 'DB', format: str = 'BIN') -> np.ndarray:
        """Get power/transmission data with microring resonator features.
        
        Trace types:
        - trace_type=1: TF live (Transmission Function, normalized to reference)
        - trace_type=11: Raw live (actual transmitted power)
        - trace_type=12: Raw reference (flat at -6 dBm)
        """
        num_points = self.length(trace_type)
        
        # Get wavelength array to calculate resonances
        wavelength_m = self.get_data_x(trace_type, unit='M', format='BIN')
        wavelength_nm = wavelength_m * 1e9
        
        # Raw reference trace: flat at -6 dBm with minimal noise
        if trace_type == 12:
            reference_db = np.full(num_points, -6.0)
            noise = np.random.randn(num_points) * 0.02  # Very small noise (20 mdB RMS)
            return reference_db + noise
        
        # Raw live trace: reference level with device transmission loss and resonances
        # Baseline transmission (slightly sloped, ~10 dB insertion loss from reference)
        baseline_db = -16.0 + (wavelength_nm - wavelength_nm[0]) * 0.001
        
        # Add multiple resonance dips (typical microring behavior)
        # Free Spectral Range (FSR) varies between 0.5-2.0 nm depending on ring size
        fsr_nm = 1.2  # FSR for a typical microring (~100 µm radius)
        
        # Determine wavelength range
        wl_start = wavelength_nm[0]
        wl_stop = wavelength_nm[-1]
        wl_range = wl_stop - wl_start
        
        # Calculate number of resonances in this range
        num_resonances = int(wl_range / fsr_nm) + 1
        
        # Generate resonances
        transmission_db = baseline_db.copy()
        for i in range(num_resonances):
            # Resonance wavelength
            resonance_wl = wl_start + (i + 0.3) * fsr_nm  # offset by 0.3 for variety
            
            # Lorentzian dip parameters
            extinction_ratio = 15 + np.random.rand() * 5  # 15-20 dB extinction
            linewidth_nm = 0.05 + np.random.rand() * 0.05  # 50-100 pm linewidth (Q ~ 15000-30000)
            
            # Lorentzian profile: L(λ) = -ER / (1 + 4((λ-λ0)/Δλ)²)
            detuning = (wavelength_nm - resonance_wl) / linewidth_nm
            lorentzian = -extinction_ratio / (1 + 4 * detuning**2)
            
            transmission_db += lorentzian
        
        # Add realistic noise (measurement noise)
        noise = np.random.randn(num_points) * 0.05  # 50 mdB RMS noise
        raw_live_db = transmission_db + noise
        
        # TF live trace: normalized transmission (raw_live - reference)
        # This removes the absolute power level and shows only device response
        if trace_type == 1:
            # TF = Raw Live - Raw Reference (in dB)
            # Since raw_live is ~-16 dBm and reference is -6 dBm, TF will be around -10 dB
            # TF shows transmission loss relative to reference (sits below reference visually)
            tf_db = raw_live_db - (-6.0)  # This gives ~-10 dB baseline with resonances deeper
            return tf_db
        
        # Raw live trace (trace_type == 11 or default)
        return raw_live_db


class FakeTLS:
    """Mock TLS (Tunable Laser Source) channel."""

    def __init__(self, channel: int):
        self.channel = channel
        # Default to O-band laser (identifier 2) for TLS1
        # Settings change when identifier is set to different laser
        self._identifier = 2  # Default to O-band laser
        self._update_settings_for_laser()

    def _update_settings_for_laser(self):
        """Update TLS settings based on selected laser identifier."""
        if self._identifier == 1:
            # C-band laser configuration
            self._start_wavelength_nm = 1502.0
            self._stop_wavelength_nm = 1627.0
            self._trigin = 1
            self._sweep_speed_nmps = 20
            self._laser_power_dbm = 8.0
        elif self._identifier == 2:
            # O-band laser configuration
            self._start_wavelength_nm = 1262.5
            self._stop_wavelength_nm = 1355.0
            self._trigin = 2
            self._sweep_speed_nmps = 20
            self._laser_power_dbm = 10.0
        else:
            # Default/unassigned
            self._start_wavelength_nm = 1500.0
            self._stop_wavelength_nm = 1600.0
            self._trigin = 0
            self._sweep_speed_nmps = 20
            self._laser_power_dbm = 5.0

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
        # Update all TLS settings when laser selection changes
        self._update_settings_for_laser()


class FakeRLaser:
    """Mock Reference Laser."""

    def __init__(self, laser_number: int):
        self.laser_number = laser_number
        
        # Laser 1 = C-band (T100S-HP), Laser 2 = O-band (T200S-O-M)
        if laser_number == 1:
            # C-band laser
            self._idn = ["EXFO", "T100S-HP", 0.0, 6.07]
            self._wavelength_nm = 1550.0
            self._power_dbm = 8.0
        elif laser_number == 2:
            # O-band laser
            self._idn = ["EXFO", "T200S-O-M", "EO241510155", "4.6.3.0"]
            self._wavelength_nm = 1355.0
            self._power_dbm = 10.0
        else:
            # Other lasers (not present)
            self._idn = ["EXFO", "Unknown", "0", "0.0.0"]
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
        self._resolution_pm = 0.1  # 0.1 pm resolution
        self._stabilization = (True, 0.0)  # (output_state=True, duration=0.0)
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
