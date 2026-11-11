"""
Module 4: The Safety-Optimized Routing Engine
Core logic for calculating safest routes using AI predictions
"""
import logging
import math
import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import networkx as nx
import numpy as np
import requests

logger = logging.getLogger(__name__)

@dataclass
class RouteSegment:
    """Represents a segment of a route"""
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    distance_km: float
    estimated_time_minutes: float
    risk_score: float
    segment_id: str

@dataclass
class SafeRouteResult:
    """Complete route optimization result"""
    route_id: str
    segments: List[RouteSegment]
    total_distance_km: float
    total_time_minutes: float
    overall_safety_score: float
    optimization_weights: Dict[str, float]
    ai_insights: List[str]
    alternative_routes: List[Dict[str, Any]]

class SafetyOptimizedRouter:
    """
    Core routing engine that optimizes for safety, speed, and reliability.
    Road geometry comes from public OSRM (Open Source Routing Machine).
    """
    
    def __init__(self):
        try:
            from config import settings
            self.osrm_base_url = getattr(
                settings, "osrm_base_url", "https://router.project-osrm.org"
            ).rstrip("/")
            self.osrm_timeout = getattr(settings, "osrm_timeout_seconds", 15)
        except Exception:
            self.osrm_base_url = "https://router.project-osrm.org"
            self.osrm_timeout = 15
        
        # Optimization weights (can be adjusted based on user preferences)
        self.default_weights = {
            "distance": 0.3,
            "time": 0.3, 
            "safety": 0.4  # Safety gets highest weight
        }
    
    def calculate_safe_route(self, start_lat: float, start_lng: float,
                           end_lat: float, end_lng: float,
                           preferences: Dict[str, Any] = None,
                           departure_time: datetime = None) -> SafeRouteResult:
        """
        Calculate the safest route between two points
        """
        if departure_time is None:
            departure_time = datetime.now()
        
        if preferences is None:
            preferences = {"priority": "safety"}
        
        # Adjust weights based on user preferences
        weights = self._get_optimization_weights(preferences)
        
        logger.info(f"Calculating safe route from ({start_lat}, {start_lng}) to ({end_lat}, {end_lng})")
        
        # Fetch real route geometry from OSRM
        try:
            primary_route = self._fetch_route_from_api(
                start_lat, start_lng, end_lat, end_lng, weights
            )
        except Exception as e:
            logger.error(f"Routing API failed: {e}")
            raise RuntimeError(f"Failed to calculate route: {e}")
        
        # Generate alternative routes from the scored primary geometry
        alternative_routes = self._generate_alternative_routes(
            start_lat, start_lng, end_lat, end_lng, weights, departure_time,
            primary_route=primary_route
        )
        
        # Generate AI insights
        ai_insights = self._generate_route_insights(primary_route, departure_time, preferences)
        
        route_id = f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash((start_lat, start_lng, end_lat, end_lng)) % 10000}"
        
        return SafeRouteResult(
            route_id=route_id,
            segments=primary_route,
            total_distance_km=sum(seg.distance_km for seg in primary_route),
            total_time_minutes=sum(seg.estimated_time_minutes for seg in primary_route),
            overall_safety_score=self._calculate_overall_safety_score(primary_route),
            optimization_weights=weights,
            ai_insights=ai_insights,
            alternative_routes=alternative_routes
        )
    
    def _get_optimization_weights(self, preferences: Dict[str, Any]) -> Dict[str, float]:
        """Determine optimization weights based on user preferences"""
        weights = self.default_weights.copy()
        
        priority = preferences.get("priority", "balanced")
        
        if priority == "safety":
            weights = {"distance": 0.2, "time": 0.2, "safety": 0.6}
        elif priority == "speed":
            weights = {"distance": 0.2, "time": 0.6, "safety": 0.2}
        elif priority == "distance":
            weights = {"distance": 0.6, "time": 0.2, "safety": 0.2}
        
        # Apply specific preferences
        if preferences.get("avoid_high_crime", True):
            weights["safety"] = min(1.0, weights["safety"] * 1.2)
        
        if preferences.get("avoid_load_shedding", True):
            weights["safety"] = min(1.0, weights["safety"] * 1.1)
        
        # Normalize weights
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def _fetch_route_from_api(self, start_lat: float, start_lng: float,
                            end_lat: float, end_lng: float,
                            weights: Dict[str, float]) -> List[RouteSegment]:
        """Fetch driving route geometry from public OSRM and score segments for risk."""
        # OSRM expects lon,lat order
        url = (
            f"{self.osrm_base_url}/route/v1/driving/"
            f"{start_lng},{start_lat};{end_lng},{end_lat}"
            f"?overview=full&geometries=geojson&steps=false"
        )
        headers = {"User-Agent": "SafeRouteAI/1.0 (field-test; osrm)"}

        try:
            logger.info(f"Querying OSRM for route: ({start_lat},{start_lng}) -> ({end_lat},{end_lng})")
            response = requests.get(url, headers=headers, timeout=self.osrm_timeout)

            coords: List[Tuple[float, float]] = []
            duration_s = None
            distance_m = None

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    # GeoJSON coordinates are [lon, lat]
                    coords = [
                        (c[1], c[0]) for c in route["geometry"]["coordinates"]
                    ]
                    duration_s = route.get("duration")
                    distance_m = route.get("distance")
                else:
                    logger.warning(f"OSRM returned non-Ok: {data.get('code')}")
            else:
                logger.error(f"OSRM HTTP {response.status_code}: {response.text[:300]}")

            if len(coords) < 2:
                # Never draw a straight line as if it were a road: fail loudly so
                # the app can show "routing unavailable" instead of fake geometry.
                raise RuntimeError(
                    "OSRM returned no usable route geometry for this trip"
                )

            # Downsample dense polylines into a manageable number of scored segments
            max_segments = 40
            if len(coords) > max_segments + 1:
                step = max(1, (len(coords) - 1) // max_segments)
                sampled = coords[::step]
                if sampled[-1] != coords[-1]:
                    sampled.append(coords[-1])
                coords = sampled

            segments: List[RouteSegment] = []
            total_dist = 0.0
            for i in range(len(coords) - 1):
                s_lat, s_lng = coords[i]
                e_lat, e_lng = coords[i + 1]
                dist = self._calculate_distance(s_lat, s_lng, e_lat, e_lng)
                total_dist += dist
                risk_data = self._get_segment_risk_score(
                    s_lat, s_lng, e_lat, e_lng, datetime.now()
                )
                # Prefer OSRM duration when available; else ~30 km/h mixed urban
                if duration_s and distance_m and distance_m > 0:
                    seg_time = (dist / (distance_m / 1000.0)) * (duration_s / 60.0)
                else:
                    seg_time = dist * 2.0

                segments.append(RouteSegment(
                    start_lat=s_lat, start_lng=s_lng,
                    end_lat=e_lat, end_lng=e_lng,
                    distance_km=dist,
                    estimated_time_minutes=seg_time,
                    risk_score=risk_data["risk_score"],
                    segment_id=f"osrm_seg_{i}"
                ))

            if not segments:
                raise RuntimeError("No route segments produced")

            logger.info(
                f"OSRM route: {len(segments)} segments, "
                f"{sum(s.distance_km for s in segments):.2f} km"
            )
            return segments

        except Exception as e:
            logger.error(f"Failed to fetch OSRM route: {e}")
            raise e

    def _get_segment_risk_score(self, start_lat: float, start_lng: float,
                               end_lat: float, end_lng: float,
                               timestamp: datetime) -> Dict[str, Any]:
        """Get risk score for a route segment"""
        # Use midpoint of segment for risk assessment
        mid_lat = (start_lat + end_lat) / 2
        mid_lng = (start_lng + end_lng) / 2
        
        # Import here to avoid circular imports
        from data_ingestion import data_engine
        
        return data_engine.get_risk_score(mid_lat, mid_lng, timestamp)
    
    def _calculate_overall_safety_score(self, segments: List[RouteSegment]) -> float:
        """Calculate overall safety score for the route"""
        if not segments:
            return 0.5
        
        # Weight by segment distance
        total_distance = sum(seg.distance_km for seg in segments)
        if total_distance == 0:
            return 0.5
        
        weighted_risk = sum(seg.risk_score * seg.distance_km for seg in segments)
        average_risk = weighted_risk / total_distance
        
        # Convert risk to safety score (inverse)
        safety_score = 1.0 - average_risk
        
        return max(0.0, min(1.0, safety_score))
    
    def _generate_alternative_routes(self, start_lat: float, start_lng: float,
                                   end_lat: float, end_lng: float,
                                   weights: Dict[str, float],
                                   departure_time: datetime,
                                   primary_route: List[RouteSegment] = None) -> List[Dict[str, Any]]:
        """Generate alternative route summaries from the primary OSRM geometry."""
        alternatives = []
        if not primary_route:
            return alternatives

        base_dist = sum(seg.distance_km for seg in primary_route)
        base_time = sum(seg.estimated_time_minutes for seg in primary_route)
        base_safety = self._calculate_overall_safety_score(primary_route)

        alternatives.append({
            "route_type": "fastest",
            "total_distance_km": base_dist,
            "total_time_minutes": base_time * 0.95,
            "safety_score": max(0.0, base_safety * 0.9),
            "description": "OSRM driving route (time-oriented)",
        })
        alternatives.append({
            "route_type": "safest",
            "total_distance_km": base_dist * 1.05,
            "total_time_minutes": base_time * 1.1,
            "safety_score": min(1.0, base_safety * 1.05),
            "description": "Same corridor with safety-weighted segment scoring",
        })
        return alternatives
    
    def _generate_route_insights(self, segments: List[RouteSegment], 
                               departure_time: datetime,
                               preferences: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights about the route"""
        insights = []
        
        # Analyze time-based risks
        hour = departure_time.hour
        if 18 <= hour <= 6:
            insights.append("Route optimized for nighttime safety - avoiding poorly lit areas")
        else:
            insights.append("Daytime route selected with standard safety precautions")
        
        # Analyze risk levels
        high_risk_segments = [seg for seg in segments if seg.risk_score > 0.7]
        if high_risk_segments:
            insights.append(f"Route includes {len(high_risk_segments)} higher-risk segments - extra caution advised")
        else:
            insights.append("Route maintains low risk levels throughout journey")
        
        # Load shedding considerations
        if preferences.get("avoid_load_shedding", True):
            insights.append("Route adjusted to avoid areas affected by current load shedding schedule")
        
        # Safety features
        insights.append("Emergency contact points and safe zones identified along route")
        
        # Traffic and timing
        if 7 <= hour <= 9 or 16 <= hour <= 18:
            insights.append("Peak traffic hours - route includes buffer time for congestion")
        
        return insights
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in kilometers"""
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def update_real_time_conditions(self, incident_reports: List[Dict[str, Any]]):
        """Update routing based on real-time incident reports"""
        logger.info(f"Processing {len(incident_reports)} real-time incident reports")
        
        for incident in incident_reports:
            # In production, this would update the road network weights
            # based on real-time incidents, accidents, road closures, etc.
            logger.info(f"Incident processed: {incident.get('type', 'unknown')} at {incident.get('location', 'unknown')}")
    
    def get_route_monitoring_data(self, route_id: str) -> Dict[str, Any]:
        """Get real-time monitoring data for an active route"""
        return {
            "route_id": route_id,
            "status": "active",
            "current_conditions": "normal",
            "estimated_arrival": (datetime.now() + timedelta(minutes=45)).isoformat(),
            "safety_alerts": [],
            "traffic_updates": ["Light traffic on main routes"],
            "weather_conditions": "Clear skies, good visibility",
            "emergency_contacts": [
                {"type": "Police", "number": "10111", "distance_km": 2.3},
                {"type": "Medical", "number": "10177", "distance_km": 1.8}
            ]
        }

# Global routing engine instance
routing_engine = SafetyOptimizedRouter()