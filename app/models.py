"""Pydantic models for EXFO CTP10 API requests and responses."""

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Connection Models
# ============================================================================


class ConnectionStatus(BaseModel):
    """Status response for CTP10 connection."""

    connected: bool
    instrument_id: Optional[str] = None
    address: str


class ConnectRequest(BaseModel):
    """Optional request to override connection address."""

    address: Optional[str] = Field(
        None, description="VISA address (e.g., 'TCPIP::192.168.1.37::5025::SOCKET')"
    )
    timeout_ms: Optional[int] = Field(
        None, ge=1000, le=300000, description="Connection timeout in milliseconds"
    )


class ConditionRegister(BaseModel):
    """Condition register status with decoded bits."""

    register_value: int = Field(description="Raw register value (0-65535)")
    is_idle: bool = Field(description="True if register is 0 (idle state)")
    bits: dict[str, bool] = Field(description="Decoded status bits")


# ============================================================================
# TLS Models
# ============================================================================


class TLSConfig(BaseModel):
    """TLS channel configuration."""

    start_wavelength_nm: Optional[float] = Field(None, ge=1460.0, le=1640.0)
    stop_wavelength_nm: Optional[float] = Field(None, ge=1460.0, le=1640.0)
    sweep_speed_nmps: Optional[int] = Field(None, ge=5, le=200)
    laser_power_dbm: Optional[float] = Field(None, ge=-10.0, le=10.0)
    trigin: Optional[int] = Field(None, ge=0, le=8, description="Trigger input (0=none, 1-8=TRIG IN port)")


# ============================================================================
# RLaser Models
# ============================================================================


class RLaserConfig(BaseModel):
    """Reference laser configuration."""

    power_dbm: Optional[float] = None
    wavelength_nm: Optional[float] = None
    power_state: Optional[bool] = None


class RLaserStatus(BaseModel):
    """Reference laser status."""

    laser_number: int
    id: str
    power_dbm: float
    wavelength_nm: float
    is_on: bool


# ============================================================================
# Detector Models
# ============================================================================


class DetectorSnapshot(BaseModel):
    """
    Snapshot of all 4 detector channels at a single point in time.

    Represents the state of an IL RL OPM2 detector module with channels:
    - Channel 1: IN1
    - Channel 2: IN2
    - Channel 3: TLS IN
    - Channel 4: OUT TO DUT
    """

    timestamp: float = Field(description="Unix timestamp when readings were taken")
    module: int = Field(description="Detector module number (1-20)")
    wavelength_nm: float = Field(description="Module wavelength (shared by all channels)")
    unit: str = Field(description="Power unit: 'dBm' or 'mW'")

    # Individual channel powers
    ch1_power: float = Field(description="Channel 1 (IN1) power")
    ch2_power: float = Field(description="Channel 2 (IN2) power")
    ch3_power: float = Field(description="Channel 3 (TLS IN) power")
    ch4_power: float = Field(description="Channel 4 (OUT TO DUT) power")


class DetectorConfig(BaseModel):
    """Detector configuration."""

    power_unit: Optional[str] = Field(None, description="'DBM' or 'MW'")
    spectral_unit: Optional[str] = Field(None, description="'WAV' (nm) or 'FREQ' (THz)")


class TraceMetadata(BaseModel):
    """Metadata for trace data."""

    module: int
    channel: int
    trace_type: int = Field(description="1=TF live, 11=Raw live, 12=Raw ref, 13=Quick ref")
    num_points: int
    sampling_pm: float = Field(description="Resolution in picometers")
    start_wavelength_nm: float
    unit: str = Field(description="'dBm' or 'mW'")


class TraceDataResponse(BaseModel):
    """Response containing trace data (JSON format)."""

    metadata: TraceMetadata
    wavelengths: list[float] = Field(description="Wavelength array in nm")
    values: list[float] = Field(description="Power/transmission values")


# ============================================================================
# Measurement/Sweep Models
# ============================================================================


class SweepConfig(BaseModel):
    """Global sweep configuration."""

    resolution_pm: Optional[float] = Field(
        None,
        description="Wavelength sampling resolution (pm). Standard: 1-250, High-res: 0.02-0.5"
    )
    stabilization_output: Optional[bool] = Field(
        None, description="Laser output after scan (False=OFF, True=ON)"
    )
    stabilization_duration: Optional[float] = Field(
        None, ge=0.0, le=60.0, description="Stabilization time in seconds"
    )


class SweepStatus(BaseModel):
    """Sweep status response."""

    is_sweeping: bool = Field(description="True if scan is running")
    is_complete: bool = Field(description="True if scan completed")
    condition_register: int = Field(description="Raw condition register value")
