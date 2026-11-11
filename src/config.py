"""Configuration management for SafeRouteAI (Huawei-free field-test build).

Runtime needs: Neon PostgreSQL, JWT auth, public OSRM + Nominatim, local ML.
No Huawei Cloud credentials are required or read.
"""
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = logging.getLogger(__name__)

STELLENBOSCH_CENTER_LAT = -33.9321
STELLENBOSCH_CENTER_LNG = 18.8602


class Settings(BaseSettings):
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Demo / production flag. DEMO_MODE=false for the field test.
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    # Database (Neon PostgreSQL)
    database_url: Optional[str] = os.getenv("DATABASE_URL")

    # JWT authentication
    jwt_secret: str = os.getenv("JWT_SECRET", "default-secret-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Open-source routing / geocoding (no API keys required)
    osrm_base_url: str = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
    nominatim_base_url: str = os.getenv(
        "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
    )
    osrm_timeout_seconds: int = int(os.getenv("OSRM_TIMEOUT_SECONDS", "15"))
    nominatim_timeout_seconds: int = int(os.getenv("NOMINATIM_TIMEOUT_SECONDS", "10"))
    map_user_agent: str = os.getenv(
        "MAP_USER_AGENT", "SafeRouteAI/1.0 (field-test; Stellenbosch)"
    )

    # Map defaults (Stellenbosch field-test area)
    map_center_lat: float = float(os.getenv("MAP_CENTER_LAT", str(STELLENBOSCH_CENTER_LAT)))
    map_center_lng: float = float(os.getenv("MAP_CENTER_LNG", str(STELLENBOSCH_CENTER_LNG)))
    map_default_zoom: int = int(os.getenv("MAP_DEFAULT_ZOOM", "13"))

    # Optional external data
    eskom_se_push_key: Optional[str] = os.getenv("ESKOM_SE_PUSH_KEY")

    @property
    def production_mode(self) -> bool:
        return not self.demo_mode

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_map_defaults(self) -> Dict[str, Any]:
        """Map centre used by Leaflet and by the API fallbacks."""
        return {
            "center": {"lat": self.map_center_lat, "lng": self.map_center_lng},
            "zoom": self.map_default_zoom,
        }

    def is_eskom_integration_ready(self) -> bool:
        """Check if EskomSePush integration is configured."""
        return bool(self.eskom_se_push_key)

    def validate_runtime_config(self) -> List[str]:
        """Return a list of non-fatal configuration warnings."""
        warnings: List[str] = []
        if not self.database_url:
            warnings.append(
                "DATABASE_URL is not set — auth and journey history are disabled"
            )
        if self.jwt_secret == "default-secret-change-in-production":
            warnings.append("JWT_SECRET is using the insecure default value")
        return warnings

    def log_configuration_status(self) -> None:
        """Log a Huawei-free runtime summary at startup."""
        logger.info(f"SafeRouteAI configuration — mode: {'demo' if self.demo_mode else 'live'}")
        logger.info(f"OSRM: {self.osrm_base_url}")
        logger.info(f"Nominatim: {self.nominatim_base_url}")
        logger.info(
            "Map centre: %s,%s (zoom %s)",
            self.map_center_lat,
            self.map_center_lng,
            self.map_default_zoom,
        )
        logger.info(f"Neon database: {'configured' if self.database_url else 'not configured'}")
        for warning in self.validate_runtime_config():
            logger.warning(warning)


settings = Settings()
settings.log_configuration_status()
