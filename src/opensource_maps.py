"""
Open-source maps service: OSRM routing + Nominatim geocoding + Leaflet config.
Replaces Huawei Map Kit / Site Kit for field testing.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import requests

try:
    from config import settings
except ImportError:
    from src.config import settings

logger = logging.getLogger(__name__)

STELLENBOSCH_CENTER = {"lat": -33.9321, "lng": 18.8602}


class OpenSourceMapService:
    """Leaflet/OSM config, Nominatim geocode, local hotspot helpers."""

    def __init__(self):
        self.osrm_base = settings.osrm_base_url.rstrip("/")
        self.nominatim_base = settings.nominatim_base_url.rstrip("/")
        self.user_agent = settings.map_user_agent
        self.map_defaults = settings.get_map_defaults()

    def get_map_config(self) -> Dict[str, Any]:
        return {
            "provider": "leaflet_osm",
            "tile_url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            "tile_attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
            "routing_provider": "osrm",
            "routing_url": f"{self.osrm_base}/route/v1/driving",
            "geocoding_provider": "nominatim",
            "geocoding_url": f"{self.nominatim_base}/search",
            "map_options": {
                "center": dict(self.map_defaults["center"]),
                "zoom": self.map_defaults["zoom"],
                "mapTypeId": "roadmap",
            },
            "south_africa_bounds": {
                "north": -22.0,
                "south": -35.0,
                "east": 33.0,
                "west": 16.0,
            },
            "field_test_area": "Stellenbosch",
        }

    def get_real_gps_coordinates(self, address: str) -> Optional[Dict[str, float]]:
        """Geocode via Nominatim (OpenStreetMap)."""
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
                "countrycodes": "za",
            }
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(
                f"{self.nominatim_base}/search",
                params=params,
                headers=headers,
                timeout=settings.nominatim_timeout_seconds,
            )
            if resp.status_code != 200:
                logger.error(f"Nominatim error {resp.status_code}: {resp.text[:200]}")
                return None
            results = resp.json()
            if not results:
                return None
            return {
                "lat": float(results[0]["lat"]),
                "lng": float(results[0]["lon"]),
            }
        except Exception as e:
            logger.error(f"Nominatim geocode failed: {e}")
            return None

    def get_real_time_markers(self, bounds: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Stellenbosch-area sample markers for field testing."""
        markers = [
            {
                "id": "wc_stb",
                "position": {"lat": -33.9358, "lng": 18.8601},
                "title": "Stellenbosch SAPS",
                "description": "Vehicle break-ins & mugging awareness",
                "type": "crime_hotspot",
                "severity": 0.65,
            },
            {
                "id": "wc_stb_kay1",
                "position": {"lat": -33.9180, "lng": 18.8350},
                "title": "Kayamandi Entrance",
                "description": "High robbery — commuter route",
                "type": "crime_hotspot",
                "severity": 0.78,
            },
            {
                "id": "wc_stb_clo1",
                "position": {"lat": -33.9454, "lng": 18.8556},
                "title": "Cloetesville",
                "description": "Residential robbery awareness",
                "type": "crime_hotspot",
                "severity": 0.70,
            },
            {
                "id": "wc_stb_s3",
                "position": {"lat": -33.9395, "lng": 18.8514},
                "title": "Merriman Ave (R44)",
                "description": "R44 approach carjacking awareness",
                "type": "hazard",
                "severity": 0.63,
            },
        ]
        if not bounds:
            return markers
        return [
            m
            for m in markers
            if bounds["south"] <= m["position"]["lat"] <= bounds["north"]
            and bounds["west"] <= m["position"]["lng"] <= bounds["east"]
        ]

    def get_hazard_zones(self, bounds: Optional[Dict] = None) -> List[Dict[str, Any]]:
        zones = [
            {
                "id": "zone_kayamandi",
                "center": {"lat": -33.9180, "lng": 18.8350},
                "radius": 800,
                "type": "high_crime",
                "severity": 0.78,
                "confidence": 0.85,
            },
            {
                "id": "zone_cloetesville",
                "center": {"lat": -33.9454, "lng": 18.8556},
                "radius": 600,
                "type": "moderate_crime",
                "severity": 0.70,
                "confidence": 0.8,
            },
        ]
        if not bounds:
            return zones
        return [
            z
            for z in zones
            if bounds["south"] <= z["center"]["lat"] <= bounds["north"]
            and bounds["west"] <= z["center"]["lng"] <= bounds["east"]
        ]

    def get_safety_heatmap_data(self, bounds: Optional[Dict] = None) -> List[Dict[str, Any]]:
        points = [
            {
                "location": {"lat": -33.9358, "lng": 18.8601},
                "weight": 0.55,
                "safety_score": 0.45,
                "risk_factors": ["vehicle_breakins", "evening_mugging"],
            },
            {
                "location": {"lat": -33.9180, "lng": 18.8350},
                "weight": 0.78,
                "safety_score": 0.22,
                "risk_factors": ["high_robbery", "commuter_route"],
            },
            {
                "location": {"lat": -33.9454, "lng": 18.8556},
                "weight": 0.70,
                "safety_score": 0.30,
                "risk_factors": ["residential_robbery"],
            },
            {
                "location": {"lat": -33.9321, "lng": 18.8602},
                "weight": 0.35,
                "safety_score": 0.65,
                "risk_factors": ["tourist_area"],
            },
        ]
        if not bounds:
            return points
        return [
            p
            for p in points
            if bounds["south"] <= p["location"]["lat"] <= bounds["north"]
            and bounds["west"] <= p["location"]["lng"] <= bounds["east"]
        ]

    def report_user_hazard(
        self, lat: float, lng: float, hazard_type: str, description: str, severity: float
    ) -> str:
        return f"hazard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def get_route_safety_analysis(
        self, waypoints: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        if len(waypoints) < 2:
            return {
                "overall_safety_score": 0.7,
                "average_risk": 0.3,
                "high_risk_segments": [],
                "hazards_along_route": [],
                "safety_rating": "Good",
                "recommendations": ["Insufficient waypoints for detailed analysis"],
            }
        try:
            from data_ingestion import data_engine

            risks = []
            for lat, lng in waypoints:
                risks.append(data_engine.get_risk_score(lat, lng, datetime.now())["risk_score"])
            avg_risk = sum(risks) / len(risks)
            safety = max(0.0, min(1.0, 1.0 - avg_risk))
            rating = (
                "Excellent"
                if safety >= 0.8
                else "Good"
                if safety >= 0.6
                else "Fair"
                if safety >= 0.4
                else "Poor"
            )
            return {
                "overall_safety_score": safety,
                "average_risk": avg_risk,
                "high_risk_segments": [],
                "hazards_along_route": [],
                "safety_rating": rating,
                "recommendations": [
                    "Prefer well-lit main roads after dark",
                    "Watch R44 and Kayamandi approach junctions",
                ],
            }
        except Exception as e:
            logger.warning(f"Route safety analysis fallback: {e}")
            return {
                "overall_safety_score": 0.6,
                "average_risk": 0.4,
                "high_risk_segments": [],
                "hazards_along_route": [],
                "safety_rating": "Fair",
                "recommendations": ["Drive cautiously; verify local conditions"],
            }


map_service = OpenSourceMapService()
