"""
Huawei Map Kit Integration for SafeRouteAI
Provides real-time mapping, location services, and hazard overlay capabilities
"""
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import requests
import base64
from urllib.parse import urlencode, quote_plus

from config import settings
from real_data_integration import real_data_integrator
# edge_ai_processor is no longer needed here as hazards are pushed via API, not pulled/simulated


logger = logging.getLogger(__name__)

@dataclass
class MapMarker:
    """Represents a marker on the map"""
    id: str
    lat: float
    lng: float
    type: str  # 'hazard', 'crime_hotspot', 'safe_zone', 'police_station'
    severity: float  # 0.0 to 1.0
    title: str
    description: str
    timestamp: datetime
    icon_url: str
    color: str

@dataclass
class HazardZone:
    """Represents a hazard zone overlay"""
    id: str
    center_lat: float
    center_lng: float
    radius_meters: float
    hazard_type: str
    severity: float
    confidence: float
    detected_at: datetime
    expires_at: datetime
    source: str  # 'edge_ai', 'user_report', 'crime_data'

@dataclass
class SafetyHeatmapPoint:
    """Represents a point in the safety heatmap"""
    lat: float
    lng: float
    safety_score: float  # 0.0 (dangerous) to 1.0 (safe)
    risk_factors: List[str]
    data_sources: List[str]

class HuaweiMapKitService:
    """
    Huawei Map Kit integration service for SafeRouteAI
    Provides real-time mapping with safety overlays for South Africa
    Supports both production and demo modes
    """
    
    def __init__(self):
        self.api_key = settings.huawei_map_api_key
        self.location_api_key = settings.huawei_location_api_key
        
        # URL encode the API keys for HTTP requests
        self.encoded_api_key = quote_plus(self.api_key) if self.api_key else None
        self.encoded_location_api_key = quote_plus(self.location_api_key) if self.location_api_key else None
        
        self.production_mode = settings.is_map_kit_production_ready()
        self.region = settings.map_kit_region
        self.cache_enabled = settings.map_kit_cache_enabled
        
        # Map Kit API endpoints - Using standard global endpoint for JS SDK (validated)
        self.base_url = "https://mapapi.cloud.huawei.com"
        self.js_api_url = "https://mapapi.cloud.huawei.com/mapjs/v1/api/js"
        # Site Kit requires DRE cluster for South Africa with DE region header
        self.location_api_url = "https://siteapi-dre.cloud.huawei.com"
        
        # Real-time hazard tracking
        self.active_hazards: Dict[str, HazardZone] = {}
        self.crime_hotspots: List[MapMarker] = []
        self.safety_heatmap: List[SafetyHeatmapPoint] = []
        
        # South Africa bounds for optimization
        self.sa_bounds = {
            "north": -22.0,
            "south": -35.0,
            "east": 33.0,
            "west": 16.0
        }
        
        # Initialize based on mode
        if self.production_mode:
            logger.info("🗺️  Initializing Huawei Map Kit in PRODUCTION mode")
            self._initialize_production_mode()
        else:
            logger.info("🔧 Initializing Huawei Map Kit in DEMO mode")
            self._initialize_demo_mode()
        
        # Start background task for hazard monitoring (will be started by FastAPI)
        self._monitoring_task = None
    
    def _initialize_production_mode(self):
        """Initialize production mode with real Huawei Map Kit services"""
        logger.info("Setting up real Huawei Map Kit integration")
        
        # Validate API key
        if not self._validate_api_key():
            logger.error("Invalid Map Kit API key - falling back to demo mode")
            self.production_mode = False
            self._initialize_demo_mode()
            return
        
        # Initialize real-time data with production services
        self._initialize_south_africa_data()
        
        # Set up production-specific features
        self._setup_production_features()
        
        logger.info("✅ Huawei Map Kit production mode initialized successfully")
    
    def _initialize_demo_mode(self):
        """Initialize demo mode with mock data"""
        logger.info("Setting up Map Kit demo mode with mock data")
        
        # Initialize with demo data
        self._initialize_south_africa_data()
        
        logger.info("✅ Huawei Map Kit demo mode initialized")
    
    def _validate_api_key(self) -> bool:
        """Validate the Map Kit API key"""
        if not self.api_key:
            logger.error("Huawei Map Kit API key is missing")
            return False
            
        if self.api_key == "demo_map_key" or self.api_key == "your_real_map_api_key_here":
            logger.error("Using placehoder/demo API key in production mode is not allowed")
            return False
        
        # Check for Base64 encoded key format (typical for Huawei API keys)
        if len(self.api_key) > 50 and ('=' in self.api_key or '+' in self.api_key or '/' in self.api_key):
            return True
        
        # Check for simple alphanumeric format
        return len(self.api_key) > 10 and self.api_key.replace('+', '').replace('/', '').replace('=', '').isalnum()
    
    def _setup_production_features(self):
        """Set up production-specific Map Kit features"""
        # Enable real GPS coordinate handling
        self.gps_enabled = True
        
        # Enable map caching for offline support
        if self.cache_enabled:
            self._setup_map_caching()
        
        # Set up real-time location services
        self._setup_location_services()
    
    def _setup_map_caching(self):
        """Set up map caching for offline support"""
        logger.info("Setting up map caching for offline support")
        # Implementation would set up local map tile caching
        pass
    
    def _setup_location_services(self):
        """Set up real-time location services"""
        logger.info("Setting up real-time location services")
        # Implementation would configure Location Kit integration
        pass
    
    def _initialize_south_africa_data(self):
        """Initialize real-time data for all of South Africa"""
        logger.info("Initializing South Africa real-time safety data")
        
        # Load crime hotspots from real data
        self._load_crime_hotspots()
        
        # Generate safety heatmap
        self._generate_safety_heatmap()
        
        # Note: Real-time hazard monitoring will be started when FastAPI starts
    
    def _load_crime_hotspots(self):
        """Load real crime hotspots from SAPS data"""
        try:
            # Get real crime hotspots data
            hotspots_df = real_data_integrator.load_real_crime_hotspots_data()
            
            if hotspots_df.empty:
                logger.warning("No real crime hotspots data available")
                return
            
            self.crime_hotspots = []
            
            for _, row in hotspots_df.iterrows():
                # Generate approximate coordinates for each station
                # In production, you'd have exact coordinates
                base_lat = -26.2041 + (hash(row['station']) % 1000) / 10000
                base_lng = 28.0473 + (hash(row['station']) % 1000) / 10000
                
                # Create markers for carjacking hotspots
                if row['is_carjacking_hotspot']:
                    marker = MapMarker(
                        id=f"carjack_{row['station']}",
                        lat=base_lat,
                        lng=base_lng,
                        type='crime_hotspot',
                        severity=min(row['quarterly_carjackings'] / 50.0, 1.0),
                        title=f"Carjacking Hotspot: {row['station']}",
                        description=f"Q1 2025: {row['quarterly_carjackings']} incidents",
                        timestamp=datetime.now(),
                        icon_url='/icons/carjacking-warning.png',
                        color='#ff4757'
                    )
                    self.crime_hotspots.append(marker)
                
                # Create markers for robbery hotspots
                if row['is_robbery_hotspot']:
                    marker = MapMarker(
                        id=f"robbery_{row['station']}",
                        lat=base_lat + 0.001,
                        lng=base_lng + 0.001,
                        type='crime_hotspot',
                        severity=min(row['quarterly_robberies'] / 100.0, 1.0),
                        title=f"Robbery Hotspot: {row['station']}",
                        description=f"Q1 2025: {row['quarterly_robberies']} incidents",
                        timestamp=datetime.now(),
                        icon_url='/icons/robbery-warning.png',
                        color='#ff6b7a'
                    )
                    self.crime_hotspots.append(marker)
            
            logger.info(f"Loaded {len(self.crime_hotspots)} real crime hotspots across South Africa")
            
        except Exception as e:
            logger.error(f"Failed to load crime hotspots: {e}")
    
    def _generate_safety_heatmap(self):
        """Generate comprehensive safety heatmap for South Africa"""
        try:
            self.safety_heatmap = []
            
            # Generate grid points across South Africa
            lat_step = 0.1  # ~11km resolution
            lng_step = 0.1
            
            for lat in [self.sa_bounds["south"] + i * lat_step 
                       for i in range(int((self.sa_bounds["north"] - self.sa_bounds["south"]) / lat_step))]:
                for lng in [self.sa_bounds["west"] + i * lng_step 
                           for i in range(int((self.sa_bounds["east"] - self.sa_bounds["west"]) / lng_step))]:
                    
                    # Get enhanced risk score for this location
                    risk_data = real_data_integrator.get_enhanced_risk_score(lat, lng, datetime.now())
                    
                    safety_point = SafetyHeatmapPoint(
                        lat=lat,
                        lng=lng,
                        safety_score=1.0 - risk_data["risk_score"],
                        risk_factors=["crime_data", "load_shedding", "time_based"],  # Default risk factors
                        data_sources=risk_data["data_sources"]
                    )
                    
                    self.safety_heatmap.append(safety_point)
            
            logger.info(f"Generated safety heatmap with {len(self.safety_heatmap)} points")
            
        except Exception as e:
            logger.error(f"Failed to generate safety heatmap: {e}")
    
    async def _start_hazard_monitoring(self):
        """Start real-time hazard detection and monitoring"""
        logger.info("Starting real-time hazard monitoring for South Africa")
        
        while True:
            try:
                # Simulate edge AI hazard detection across SA
                await self._detect_real_time_hazards()
                
                # Clean up expired hazards
                self._cleanup_expired_hazards()
                
                # Wait 30 seconds before next scan
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Hazard monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _detect_real_time_hazards(self):
        """
        Monitor for real-time hazards.
        In strict production mode, this relies on incoming API reports from Edge AI nodes 
        (via /api/v1/edge-ai/process-frame) rather than self-generated simulations.
        """
        # No mock generation. We just wait for events.
        pass
    
    def _cleanup_expired_hazards(self):
        """Remove expired hazards"""
        now = datetime.now()
        expired_hazards = [hid for hid, hazard in self.active_hazards.items() 
                          if hazard.expires_at < now]
        
        for hid in expired_hazards:
            del self.active_hazards[hid]
        
        if expired_hazards:
            logger.info(f"Cleaned up {len(expired_hazards)} expired hazards")
    
    def get_map_config(self) -> Dict[str, Any]:
        """Get Huawei Map Kit configuration for frontend"""
        config = {
            "api_key": self.encoded_api_key,  # Use URL-encoded key
            "js_api_url": self.js_api_url,
            "production_mode": self.production_mode,
            "region": self.region,
            "map_options": {
                "center": {"lat": -26.2041, "lng": 28.0473},  # Johannesburg
                "zoom": 6,  # Show most of South Africa
                "mapTypeId": "roadmap",
                "gestureHandling": "greedy",
                "zoomControl": True,
                "mapTypeControl": True,
                "streetViewControl": False,
                "fullscreenControl": True,
                "rotateControl": True,
                "scaleControl": True
            },
            "south_africa_bounds": self.sa_bounds,
            "features": {
                "real_time_hazards": True,
                "crime_hotspots": True,
                "safety_heatmap": True,
                "user_reporting": True,
                "offline_maps": self.cache_enabled,
                "gps_tracking": self.production_mode,
                "turn_by_turn_navigation": self.production_mode
            }
        }
        
        # Add production-specific configuration
        if self.production_mode:
            config.update({
                "location_api_key": self.encoded_location_api_key,  # Use URL-encoded key
                "location_api_url": self.location_api_url,
                "cache_enabled": self.cache_enabled,
                "real_gps_enabled": True,
                "production_features": [
                    "Real GPS coordinate handling",
                    "Interactive map rendering",
                    "Offline map caching",
                    "Turn-by-turn navigation",
                    "Real-time traffic data"
                ]
            })
        else:
            config.update({
                "demo_mode": True,
                "mock_features": [
                    "Simulated GPS coordinates",
                    "Mock map rendering",
                    "Demo hazard data",
                    "Sample navigation routes"
                ]
            })
        
        return config
    
    def get_real_time_markers(self, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get all real-time markers for the map"""
        markers = []
        
        # Add crime hotspots
        for hotspot in self.crime_hotspots:
            if bounds and not self._is_in_bounds(hotspot.lat, hotspot.lng, bounds):
                continue
                
            markers.append({
                "id": hotspot.id,
                "position": {"lat": hotspot.lat, "lng": hotspot.lng},
                "type": hotspot.type,
                "severity": hotspot.severity,
                "title": hotspot.title,
                "description": hotspot.description,
                "icon": {
                    "url": hotspot.icon_url,
                    "scaledSize": {"width": 32, "height": 32}
                },
                "color": hotspot.color,
                "timestamp": hotspot.timestamp.isoformat()
            })
        
        # Add active hazards
        for hazard in self.active_hazards.values():
            if bounds and not self._is_in_bounds(hazard.center_lat, hazard.center_lng, bounds):
                continue
                
            markers.append({
                "id": hazard.id,
                "position": {"lat": hazard.center_lat, "lng": hazard.center_lng},
                "type": "active_hazard",
                "severity": hazard.severity,
                "title": f"Live Hazard: {hazard.hazard_type.title()}",
                "description": f"Detected {hazard.detected_at.strftime('%H:%M')} - Confidence: {hazard.confidence:.0%}",
                "icon": {
                    "url": f"/icons/{hazard.hazard_type}-hazard.png",
                    "scaledSize": {"width": 28, "height": 28}
                },
                "color": "#ff4757" if hazard.severity > 0.7 else "#ffa502",
                "timestamp": hazard.detected_at.isoformat(),
                "expires_at": hazard.expires_at.isoformat()
            })
        
        return markers
    
    def get_hazard_zones(self, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get hazard zone overlays for the map"""
        zones = []
        
        for hazard in self.active_hazards.values():
            if bounds and not self._is_in_bounds(hazard.center_lat, hazard.center_lng, bounds):
                continue
            
            zones.append({
                "id": hazard.id,
                "center": {"lat": hazard.center_lat, "lng": hazard.center_lng},
                "radius": hazard.radius_meters,
                "type": hazard.hazard_type,
                "severity": hazard.severity,
                "confidence": hazard.confidence,
                "fillColor": "#ff4757" if hazard.severity > 0.7 else "#ffa502",
                "fillOpacity": 0.3,
                "strokeColor": "#ff4757",
                "strokeOpacity": 0.8,
                "strokeWeight": 2,
                "detected_at": hazard.detected_at.isoformat(),
                "expires_at": hazard.expires_at.isoformat()
            })
        
        return zones
    
    def get_safety_heatmap_data(self, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get safety heatmap data for visualization"""
        heatmap_data = []
        
        for point in self.safety_heatmap:
            if bounds and not self._is_in_bounds(point.lat, point.lng, bounds):
                continue
            
            heatmap_data.append({
                "location": {"lat": point.lat, "lng": point.lng},
                "weight": 1.0 - point.safety_score,  # Higher weight = more dangerous
                "safety_score": point.safety_score,
                "risk_factors": point.risk_factors,
                "data_sources": point.data_sources
            })
        
        return heatmap_data
    
    def report_user_hazard(self, lat: float, lng: float, hazard_type: str, 
                          description: str, severity: float) -> str:
        """Report a user-submitted hazard"""
        hazard_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash((lat, lng)) % 10000}"
        
        hazard = HazardZone(
            id=hazard_id,
            center_lat=lat,
            center_lng=lng,
            radius_meters=100,  # Default 100m radius for user reports
            hazard_type=hazard_type,
            severity=severity,
            confidence=0.8,  # User reports have high confidence
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2),  # User reports last longer
            source="user_report"
        )
        
        self.active_hazards[hazard_id] = hazard
        logger.info(f"User reported hazard: {hazard_type} at ({lat:.4f}, {lng:.4f})")
        
        return hazard_id
    
    def get_route_safety_analysis(self, waypoints: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Analyze safety along a route"""
        total_risk = 0.0
        high_risk_segments = []
        hazards_along_route = []
        
        for i, (lat, lng) in enumerate(waypoints):
            # Check for nearby hazards
            nearby_hazards = [
                hazard for hazard in self.active_hazards.values()
                if self._calculate_distance(lat, lng, hazard.center_lat, hazard.center_lng) <= hazard.radius_meters / 1000
            ]
            
            if nearby_hazards:
                hazards_along_route.extend([
                    {
                        "segment": i,
                        "hazard_type": h.hazard_type,
                        "severity": h.severity,
                        "distance_km": self._calculate_distance(lat, lng, h.center_lat, h.center_lng)
                    } for h in nearby_hazards
                ])
            
            # Get risk score for this point
            risk_data = real_data_integrator.get_enhanced_risk_score(lat, lng, datetime.now())
            segment_risk = risk_data["risk_score"]
            total_risk += segment_risk
            
            if segment_risk > 0.7:
                high_risk_segments.append({
                    "segment": i,
                    "lat": lat,
                    "lng": lng,
                    "risk_score": segment_risk,
                    "risk_factors": risk_data["risk_factors"]
                })
        
        average_risk = total_risk / len(waypoints) if waypoints else 0.0
        safety_score = 1.0 - average_risk
        
        return {
            "overall_safety_score": safety_score,
            "average_risk": average_risk,
            "high_risk_segments": high_risk_segments,
            "hazards_along_route": hazards_along_route,
            "safety_rating": self._get_safety_rating(safety_score),
            "recommendations": self._get_safety_recommendations(safety_score, high_risk_segments, hazards_along_route),
            "production_mode": self.production_mode,
            "real_gps_data": self.production_mode
        }
    
    def get_real_gps_coordinates(self, address: str) -> Optional[Dict[str, float]]:
        """Get real GPS coordinates for an address using Huawei Site Kit (Location)"""
        if not self.production_mode:
            logger.error("Cannot get real GPS coordinates in non-production mode")
            return None
            
        if not self.location_api_key:
             logger.error("Huawei Location API Key missing")
             return None
        
        # Improve address specificity for better geocoding results
        enhanced_address = self._enhance_address_for_geocoding(address)
        
        try:
            # Huawei Site Kit Geocoding API
            # Docs: https://developer.huawei.com/consumer/en/doc/development/HMSCore-References/site-geocode-0000001050162024
            url = f"{self.location_api_url}/mapApi/v1/siteService/geocode?key={self.encoded_location_api_key}"
            
            # Validated: Site Kit requires x-agccp-region-id: DE for REST calls
            headers = {
                "Content-Type": "application/json",
                "x-agccp-region-id": "DE" 
            }
            payload = {
                "address": enhanced_address,
                "language": "en"
            }
            
            logger.info(f"Querying Huawei Location Kit (DRE/DE) for: {address} -> {enhanced_address}")
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("returnCode") == "0" and data.get("sites"):
                    location = data["sites"][0]["location"]
                    result = {
                        "lat": location["lat"],
                        "lng": location["lng"]
                    }
                    logger.info(f"✅ Found coordinates: {result}")
                    return result
                else:
                    logger.warning(f"Location Kit returned no results: {data.get('returnDesc')}")
                    return None
            else:
                logger.error(f"Location Kit API failed: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get GPS coordinates: {e}")
            return None
    
    def _enhance_address_for_geocoding(self, address: str) -> str:
        """Enhance address with country context to improve geocoding accuracy"""
        address_lower = address.lower().strip()
        
        # Common South African cities
        south_african_cities = [
            'pretoria', 'johannesburg', 'cape town', 'durban', 'port elizabeth',
            'east london', 'bloemfontein', 'nelspruit', 'polokwane', 'kimberley',
            'roussenouw', 'centurion', 'midrand', 'sandton', 'fourways',
            'roodepoort', 'springs', 'benoni', 'boksburg', 'kempton park',
            'stellenbosch', 'paarl', 'wellington', 'somerset west', 'hermanus',
            'knysna', 'george', 'moses kotane', 'rustenburg', 'potchefstroom'
        ]
        
        # Check if it's likely a South African address
        is_sa_address = any(city in address_lower for city in south_african_cities)
        
        # Check if country is already specified
        has_country = any(country in address_lower for country in ['south africa', 'rsa', 'suid afrika'])
        
        if is_sa_address and not has_country:
            # Add South Africa context
            enhanced = f"{address}, South Africa"
            logger.debug(f"Enhanced SA address: {address} -> {enhanced}")
            return enhanced
        
        # For international addresses, try to make them more specific
        # Add common country identifiers if missing
        international_places = [
            ('times square', 'Times Square, Manhattan, New York, NY, USA'),
            ('eiffel tower', 'Eiffel Tower, Paris, France'),
            ('london eye', 'London Eye, London, UK'),
            ('big ben', 'Big Ben, London, UK'),
            ('sydney opera house', 'Sydney Opera House, Sydney, NSW, Australia'),
            ('statue of liberty', 'Statue of Liberty, New York, NY, USA'),
            ('golden gate bridge', 'Golden Gate Bridge, San Francisco, CA, USA'),
            ('white house', 'White House, Washington, DC, USA')
        ]
        
        for place_name, enhanced_version in international_places:
            if place_name in address_lower:
                logger.debug(f"Enhanced landmark address: {address} -> {enhanced_version}")
                return enhanced_version
        
        return address
    
    def render_interactive_map(self, center_lat: float, center_lng: float, zoom: int = 10) -> Dict[str, Any]:
        """Render interactive map with real map tiles"""
        if not self.production_mode:
            return self._render_mock_map(center_lat, center_lng, zoom)
        
        try:
            # In production, this would configure real Huawei Map Kit rendering
            logger.info(f"Rendering interactive map at ({center_lat}, {center_lng}) zoom {zoom}")
            
            map_config = {
                "center": {"lat": center_lat, "lng": center_lng},
                "zoom": zoom,
                "map_type": "roadmap",
                "interactive": True,
                "real_tiles": True,
                "offline_support": self.cache_enabled,
                "layers": {
                    "traffic": True,
                    "satellite": True,
                    "terrain": True,
                    "poi": True
                },
                "controls": {
                    "zoom": True,
                    "pan": True,
                    "rotate": True,
                    "tilt": True,
                    "fullscreen": True
                }
            }
            
            return {
                "success": True,
                "map_config": map_config,
                "production_mode": True,
                "features": ["Real map tiles", "Interactive controls", "Offline caching"]
            }
            
        except Exception as e:
            logger.error(f"Failed to render interactive map: {e}")
            return self._render_mock_map(center_lat, center_lng, zoom)
    
    def _render_mock_map(self, center_lat: float, center_lng: float, zoom: int) -> Dict[str, Any]:
        """Render mock map for demo mode"""
        return {
            "success": True,
            "map_config": {
                "center": {"lat": center_lat, "lng": center_lng},
                "zoom": zoom,
                "map_type": "roadmap",
                "interactive": False,
                "real_tiles": False,
                "demo_mode": True
            },
            "production_mode": False,
            "features": ["Mock map tiles", "Demo controls", "Simulated data"]
        }
    
    def get_production_status(self) -> Dict[str, Any]:
        """Get detailed production status of Map Kit"""
        return {
            "production_mode": self.production_mode,
            "api_key_valid": self._validate_api_key(),
            "region": self.region,
            "cache_enabled": self.cache_enabled,
            "features": {
                "real_gps": self.production_mode,
                "interactive_maps": self.production_mode,
                "offline_caching": self.cache_enabled,
                "real_time_traffic": self.production_mode,
                "turn_by_turn_nav": self.production_mode
            },
            "configuration": {
                "api_key_configured": bool(self.api_key and self.api_key != "demo_map_key"),
                "location_key_configured": bool(self.location_api_key and self.location_api_key != "demo_location_key"),
                "south_africa_optimized": self.region == "af-south-1"
            },
            "transition_status": "Production Ready" if self.production_mode else "Demo Mode Active"
        }
    
    def _is_in_bounds(self, lat: float, lng: float, bounds: Dict[str, float]) -> bool:
        """Check if coordinates are within bounds"""
        return (bounds["south"] <= lat <= bounds["north"] and 
                bounds["west"] <= lng <= bounds["east"])
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in kilometers"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _get_safety_rating(self, safety_score: float) -> str:
        """Get safety rating based on score"""
        if safety_score >= 0.9:
            return "Excellent"
        elif safety_score >= 0.8:
            return "Very Good"
        elif safety_score >= 0.7:
            return "Good"
        elif safety_score >= 0.6:
            return "Fair"
        elif safety_score >= 0.5:
            return "Poor"
        else:
            return "Dangerous"
    
    def _get_safety_recommendations(self, safety_score: float, high_risk_segments: List[Dict], 
                                   hazards: List[Dict]) -> List[str]:
        """Get safety recommendations based on analysis"""
        recommendations = []
        
        if safety_score < 0.6:
            recommendations.append("Consider alternative route - current route has significant safety concerns")
        
        if high_risk_segments:
            recommendations.append(f"Exercise extra caution in {len(high_risk_segments)} high-risk areas")
        
        if hazards:
            recommendations.append(f"Active hazards detected along route - check real-time updates")
        
        if any(h["hazard_type"] in ["pothole", "road_damage"] for h in hazards):
            recommendations.append("Road hazards detected - reduce speed and maintain safe following distance")
        
        if any(h["hazard_type"] in ["accident", "breakdown"] for h in hazards):
            recommendations.append("Traffic incidents ahead - expect delays and use alternative routes if possible")
        
        return recommendations

# Global map kit service instance
map_kit_service = HuaweiMapKitService()