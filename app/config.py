"""Configuration settings for EXFO CTP10 API."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # EXFO CTP10 Connection
    CTP10_IP: str = "192.168.1.37"
    CTP10_PORT: int = 5025
    CTP10_TIMEOUT_MS: int = 120000  # 2 minutes for large binary transfers

    # Default Configuration (from pymeasure-examples)
    DEFAULT_MODULE: int = 4  # SENSe module (1-20)
    DEFAULT_CHANNEL: int = 1  # Detector channel (1-6)
    DEFAULT_RESOLUTION_PM: float = 10.0  # Wavelength sampling resolution (pm)
    AUTO_CONNECT: bool = True

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def ctp10_address(self) -> str:
        """Construct VISA address for TCPIP SOCKET connection."""
        return f"TCPIP::{self.CTP10_IP}::{self.CTP10_PORT}::SOCKET"


# Global settings instance
settings = Settings()
