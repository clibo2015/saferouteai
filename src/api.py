#!/usr/bin/env python3
"""
SafeRouteAI API — open-source maps (OSRM/Nominatim/Leaflet) + Neon Database
Huawei-free runtime for Stellenbosch field testing
"""
import sys
import os

# Set writable config dir for Ultralytics/YOLO before any imports
os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/Ultralytics")
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Add src to path
sys.path.append('src')

# Import services
edge_ai_processor = None  # lazy-loaded in startup_event
MAP_SERVICES_AVAILABLE = False
NEON_AVAILABLE = False
routing_engine = None
settings = None
neon_db = None
User = None
Journey = None
HazardReport = None
auth_service = None
get_current_user = None
get_current_user_optional = None
map_kit_service = None

try:
    from opensource_maps import map_service as map_kit_service
    from routing_engine import routing_engine
    from config import settings
    from ai_copilot import ai_copilot
    MAP_SERVICES_AVAILABLE = True
    print("OK: Open-source map services (OSRM/Nominatim) loaded")
except Exception as e:
    print(f"ERROR: Map/routing import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from neon_database import neon_db, User, Journey, HazardReport
    from neon_auth import auth_service, get_current_user, get_current_user_optional
    NEON_AVAILABLE = True
    print("OK: Neon database + auth loaded")
except Exception as e:
    print(f"ERROR: Neon import error: {e}")
    import traceback
    traceback.print_exc()

# Optional legacy modules — never required to boot
try:
    from data_ingestion import data_engine  # noqa: F401
except ImportError:
    data_engine = None
try:
    from real_data_integration import real_data_integrator  # noqa: F401
except ImportError:
    real_data_integrator = None

if map_kit_service is None:
    class MockMapService:
        def get_map_config(self):
            return {
                "provider": "leaflet_osm",
                "map_options": {
                    "center": {"lat": -33.9321, "lng": 18.8602},
                    "zoom": 13,
                    "mapTypeId": "roadmap",
                },
                "south_africa_bounds": {
                    "north": -22.0, "south": -35.0, "east": 33.0, "west": 16.0
                },
            }

        def get_real_gps_coordinates(self, address):
            return {"lat": -33.9321, "lng": 18.8602}

        def get_real_time_markers(self, bounds=None):
            return []

        def get_hazard_zones(self, bounds=None):
            return []

        def get_safety_heatmap_data(self, bounds=None):
            return []

        def report_user_hazard(self, lat, lng, hazard_type, description, severity):
            return f"hazard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        def get_route_safety_analysis(self, waypoints):
            return {
                "overall_safety_score": 0.6,
                "average_risk": 0.4,
                "high_risk_segments": [],
                "hazards_along_route": [],
                "safety_rating": "Fair",
                "recommendations": ["Mock analysis — map services unavailable"],
            }

    map_kit_service = MockMapService()

if not NEON_AVAILABLE:
    class _AnonUser:
        id = "anonymous"

    async def get_current_user_optional():
        return None

    async def get_current_user():
        raise HTTPException(status_code=503, detail="Auth unavailable — Neon not configured")

def _database_ready() -> bool:
    """True only when Neon is configured (DATABASE_URL present)."""
    return bool(NEON_AVAILABLE and neon_db and getattr(neon_db, "database_url", None))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SafeRouteAI API",
    description="AI-powered route optimization with OSRM, Nominatim, Leaflet/OSM, and Neon PostgreSQL",
    version="4.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # JWT authentication doesn't need credentials/cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LocationPoint(BaseModel):
    latitude: float
    longitude: float

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str

class JourneyRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    route_data: Dict[str, Any]
    safety_score: float
    distance_km: float
    duration_minutes: float

class HazardReportRequest(BaseModel):
    lat: float
    lng: float
    hazard_type: str
    description: str
    severity: float

def _get_edge_ai_processor():
    """Import/construct Edge AI on first use (keeps Render boot fast)."""
    global edge_ai_processor
    if edge_ai_processor is None:
        from edge_ai_processor import EdgeAIProcessor

        edge_ai_processor = EdgeAIProcessor()
    return edge_ai_processor


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup.

    Edge AI (YOLO) is deliberately NOT imported here: it pulls in torch/cv2
    and would slow down or time out Render's free-tier boot.
    """
    if NEON_AVAILABLE:
        try:
            await neon_db.connect()
            logger.info("Neon database connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neon database: {e}")
    logger.info("Edge AI will load lazily on first request")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    if NEON_AVAILABLE:
        await neon_db.disconnect()

@app.get("/")
async def root():
    """API root endpoint"""
    # NEON_AVAILABLE only means the modules imported; the pool may still be down.
    neon_connected = bool(NEON_AVAILABLE and neon_db and getattr(neon_db, "connected", False))
    return {
        "message": "SafeRouteAI API — Huawei-free (OSRM + Nominatim + Neon)",
        "version": "4.0.0",
        "map_services_available": MAP_SERVICES_AVAILABLE,
        "neon_database": neon_connected,
        "field_test_area": "Stellenbosch",
        "services": {
            "routing": "✅ OSRM" if MAP_SERVICES_AVAILABLE else "🔄 Mock Mode",
            "geocoding": "✅ Nominatim" if MAP_SERVICES_AVAILABLE else "🔄 Mock Mode",
            "maps": "✅ Leaflet/OSM",
            "ai_copilot": f"✅ APInex ({ai_copilot.model})" if (ai_copilot and ai_copilot.is_configured()) else "🔄 Heuristic Fallback",
            "edge_ai": "✅ Ready (lazy)",
            "neon_database": "✅ Connected" if neon_connected else "❌ Offline",
            "authentication": "✅ Enabled" if neon_connected else "❌ Disabled"
        },
        "capabilities": [
            "Real-time hazard detection",
            "Crime hotspot mapping", 
            "Safety heatmap generation",
            "Route safety analysis",
            "User hazard reporting",
            "User authentication",
            "Journey history",
            "Personalized preferences"
        ]
    }

# Authentication Endpoints
@app.post("/api/v1/auth/register")
async def register_user(request: RegisterRequest):
    """Register a new user"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        user_data = await auth_service.register_user(
            email=request.email,
            name=request.name,
            password=request.password
        )
        
        # Create access token
        access_token = auth_service.create_access_token(user_data)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data["name"]
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/auth/login")
async def login_user(request: LoginRequest):
    """Authenticate user and return access token"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        user_data = await auth_service.authenticate_with_neon(
            email=request.email,
            password=request.password
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(user_data)
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "preferences": user_data["preferences"]
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/v1/auth/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    try:
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name
        }
        
        new_token = auth_service.create_access_token(user_data)
        
        return {
            "success": True,
            "access_token": new_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "preferences": current_user.preferences,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login,
            "is_active": current_user.is_active
        }
    }

@app.put("/api/v1/auth/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        success = await auth_service.update_user_preferences(current_user.id, preferences)
        
        if success:
            return {
                "success": True,
                "message": "Preferences updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
            
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# Map / geocode endpoints (OSRM + Nominatim + Leaflet)
@app.get("/api/v1/map/config")
async def get_map_config():
    """Get Leaflet/OSM map configuration for frontend"""
    try:
        config = map_kit_service.get_map_config()
        return {
            "success": True,
            "map_config": config,
            "features_enabled": [
                "real_time_hazards",
                "crime_hotspots", 
                "safety_heatmap",
                "edge_ai_detection",
                "user_reporting"
            ],
            "map_services_available": MAP_SERVICES_AVAILABLE,
            "provider": "leaflet_osm_osrm_nominatim"
        }
    except Exception as e:
        logger.error(f"Map config retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/geocode")
async def geocode_address(request: Dict[str, Any]):
    """Geocode an address string to GPS coordinates via Nominatim"""
    try:
        address = request.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="Address required")
            
        location = map_kit_service.get_real_gps_coordinates(address)
        
        if location:
            return {
                "success": True,
                "location": location,
                "address": address,
                "provider": "nominatim"
            }
        else:
            # Stellenbosch fallback when geocoding fails
            return {
                "success": True,
                "location": {"lat": -33.9321, "lng": 18.8602},
                "address": address,
                "is_fallback": True,
                "provider": "stellenbosch_fallback"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/map/markers")
async def get_map_markers(
    north: float = None,
    south: float = None, 
    east: float = None,
    west: float = None
):
    """Get real-time markers for map display"""
    try:
        bounds = None
        if all(coord is not None for coord in [north, south, east, west]):
            bounds = {"north": north, "south": south, "east": east, "west": west}
        
        markers = map_kit_service.get_real_time_markers(bounds)
        
        return {
            "success": True,
            "markers": markers,
            "total_markers": len(markers),
            "bounds": bounds,
            "last_updated": datetime.now().isoformat(),
            "data_source": "Stellenbosch hotspots + Edge AI" if MAP_SERVICES_AVAILABLE else "Mock Data"
        }
    except Exception as e:
        logger.error(f"Map markers retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/map/hazard-zones")
async def get_hazard_zones(
    north: float = None,
    south: float = None,
    east: float = None, 
    west: float = None
):
    """Get active hazard zones for map overlay"""
    try:
        bounds = None
        if all(coord is not None for coord in [north, south, east, west]):
            bounds = {"north": north, "south": south, "east": east, "west": west}
        
        zones = map_kit_service.get_hazard_zones(bounds)
        
        return {
            "success": True,
            "hazard_zones": zones,
            "total_zones": len(zones),
            "bounds": bounds,
            "last_updated": datetime.now().isoformat(),
            "coverage": "Stellenbosch & surrounds" if MAP_SERVICES_AVAILABLE else "Mock Coverage"
        }
    except Exception as e:
        logger.error(f"Hazard zones retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/map/safety-heatmap")
async def get_safety_heatmap(
    north: float = None,
    south: float = None,
    east: float = None,
    west: float = None
):
    """Get safety heatmap data for visualization"""
    try:
        bounds = None
        if all(coord is not None for coord in [north, south, east, west]):
            bounds = {"north": north, "south": south, "east": east, "west": west}
        
        heatmap_data = map_kit_service.get_safety_heatmap_data(bounds)
        
        return {
            "success": True,
            "heatmap_data": heatmap_data,
            "total_points": len(heatmap_data),
            "bounds": bounds,
            "data_sources": ["SAPS Crime Data", "EskomSePush", "Edge AI Detection", "User Reports"],
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Safety heatmap retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/report-hazard")
async def report_hazard(
    request: Dict[str, Any],
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Report a user-submitted hazard"""
    try:
        lat = request.get("latitude")
        lng = request.get("longitude") 
        hazard_type = request.get("hazard_type", "unknown")
        description = request.get("description", "")
        severity = request.get("severity", 0.5)
        
        if not lat or not lng:
            raise HTTPException(status_code=400, detail="Latitude and longitude required")
        
        if NEON_AVAILABLE and current_user:
            # Store in database with user association
            from datetime import timedelta
            hazard = HazardReport(
                id="",  # Will be generated by database
                user_id=current_user.id,
                lat=lat,
                lng=lng,
                hazard_type=hazard_type,
                description=description,
                severity=severity,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
            hazard_id = await neon_db.create_hazard_report(hazard)
        else:
            # Fallback to map kit service
            hazard_id = map_kit_service.report_user_hazard(lat, lng, hazard_type, description, severity)
        
        return {
            "success": True,
            "hazard_id": hazard_id,
            "message": "Hazard reported successfully",
            "estimated_impact": {
                "radius_meters": 100,
                "duration_minutes": 120,
                "affected_users": "nearby_drivers"
            },
            "processing_mode": "Database" if NEON_AVAILABLE and current_user else "Local"
        }
    except Exception as e:
        logger.error(f"Hazard reporting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/analyze-route-safety")
async def analyze_route_safety(request: Dict[str, Any]):
    """Analyze safety along a specific route"""
    try:
        waypoints = request.get("waypoints", [])
        
        if not waypoints:
            raise HTTPException(status_code=400, detail="Waypoints required")
        
        # Convert waypoints to tuples
        waypoint_tuples = [(wp["lat"], wp["lng"]) for wp in waypoints]
        
        safety_analysis = map_kit_service.get_route_safety_analysis(waypoint_tuples)
        
        return {
            "success": True,
            "safety_analysis": safety_analysis,
            "route_length_km": len(waypoints) * 5,  # Approximate
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_method": "AI + Open Data" if MAP_SERVICES_AVAILABLE else "Mock Analysis"
        }
    except Exception as e:
        logger.error(f"Route safety analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Edge AI Integration
@app.post("/api/v1/edge-ai/driver-behavior")
async def analyze_driver_behavior(request: Dict[str, Any]):
    """Analyze driver behavior using edge AI sensor data"""
    try:
        sensor_data = request.get("sensor_data", {})
        analysis_type = request.get("analysis_type", "behavior")

        try:
            processor = _get_edge_ai_processor()
        except Exception as e:
            logger.warning(f"Edge AI unavailable: {e}")
            raise HTTPException(status_code=503, detail="Edge AI unavailable on this server")

        behavior_analysis = processor.analyze_driver_behavior(sensor_data)
        
        return {
            "success": True,
            "behavior_analysis": behavior_analysis,
            "system_info": {
                "analysis_type": analysis_type,
                "edge_processing": True,
                "real_time": MAP_SERVICES_AVAILABLE
            }
        }
    except Exception as e:
        logger.error(f"Driver behavior analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Safety Copilot (APInex)
@app.post("/api/v1/ai/briefing")
async def get_ai_safety_briefing(request: Dict[str, Any]):
    """Generate dynamic AI safety briefing via APInex Gateway"""
    try:
        route_summary = request.get("route_summary", {})
        hazards = request.get("hazards", [])
        departure_time = request.get("departure_time")

        dep_dt = datetime.now()
        if departure_time:
            try:
                dep_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00')).replace(tzinfo=None)
            except Exception:
                pass

        briefing = ai_copilot.generate_safety_briefing(route_summary, hazards, dep_dt)
        return {
            "success": True,
            "briefing": briefing,
            "provider": f"APInex ({ai_copilot.model})" if ai_copilot.is_configured() else "Local Heuristics",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"AI briefing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Optimization
@app.post("/api/v1/optimize-route")
async def optimize_route(request: Dict[str, Any]):
    """Complete route optimization using OSRM + local risk scoring"""
    try:
        start_point = request.get("start_point", {})
        end_point = request.get("end_point", {})
        departure_time = request.get("departure_time")
        safety_preferences = request.get("safety_preferences", {})
        
        logger.info(f"Route optimization request: {start_point} -> {end_point}")
        
        # Parse departure time
        departure_dt = datetime.now()
        if departure_time:
            try:
                departure_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
                departure_dt = departure_dt.replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Invalid departure time format: {e}")
                departure_dt = datetime.now()
        
        if MAP_SERVICES_AVAILABLE and routing_engine is not None:
            route_result = routing_engine.calculate_safe_route(
                start_point["lat"],
                start_point["lng"],
                end_point["lat"], 
                end_point["lng"],
                safety_preferences,
                departure_dt
            )
            
            return {
                "success": True,
                "route_data": {
                    "route_id": route_result.route_id,
                    "segments": [
                        {
                            "segment_id": seg.segment_id,
                            "start_point": {"lat": seg.start_lat, "lng": seg.start_lng},
                            "end_point": {"lat": seg.end_lat, "lng": seg.end_lng},
                            "distance_km": seg.distance_km,
                            "estimated_time_minutes": seg.estimated_time_minutes,
                            "risk_score": seg.risk_score
                        } for seg in route_result.segments
                    ],
                    "total_distance_km": route_result.total_distance_km,
                    "total_time_minutes": route_result.total_time_minutes,
                    "overall_safety_score": route_result.overall_safety_score,
                    "optimization_weights": route_result.optimization_weights,
                    "ai_insights": route_result.ai_insights,
                    "alternative_routes": route_result.alternative_routes,
                },
                "system_info": {
                    "demo_mode": getattr(settings, 'demo_mode', False) if settings else False,
                    "processing_time": datetime.now().isoformat(),
                    "services_used": ["OSRM", "Nominatim", "LocalRiskModel", "Neon"]
                }
            }
        else:
            # Mock route optimization
            import random
            route_id = f"route_{random.randint(1000, 9999)}"
            
            # Generate mock waypoints
            waypoints = []
            num_waypoints = random.randint(3, 6)
            
            for i in range(num_waypoints):
                progress = (i + 1) / (num_waypoints + 1)
                lat = start_point["lat"] + (end_point["lat"] - start_point["lat"]) * progress
                lng = start_point["lng"] + (end_point["lng"] - start_point["lng"]) * progress
                
                # Add some variation
                lat += random.uniform(-0.005, 0.005)
                lng += random.uniform(-0.005, 0.005)
                
                waypoints.append({
                    "segment_id": f"seg_{i}",
                    "start_point": {"lat": lat, "lng": lng},
                    "end_point": {"lat": lat + 0.001, "lng": lng + 0.001},
                    "distance_km": random.uniform(2, 8),
                    "estimated_time_minutes": random.randint(5, 15),
                    "risk_score": random.uniform(0.1, 0.8)
                })
            
            total_distance = sum(wp["distance_km"] for wp in waypoints)
            total_time = sum(wp["estimated_time_minutes"] for wp in waypoints)
            avg_risk = sum(wp["risk_score"] for wp in waypoints) / len(waypoints)
            
            return {
                "success": True,
                "route_data": {
                    "route_id": route_id,
                    "segments": waypoints,
                    "total_distance_km": round(total_distance, 2),
                    "total_time_minutes": total_time,
                    "overall_safety_score": round(1.0 - avg_risk, 2),
                    "optimization_weights": safety_preferences
                },
                "system_info": {
                    "demo_mode": True,
                    "processing_time": datetime.now().isoformat(),
                    "services_used": ["Mock_Services"]
                }
            }
            
    except Exception as e:
        logger.error(f"Route optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Journey Management Endpoints
@app.post("/api/v1/journeys")
async def save_journey(
    request: JourneyRequest,
    current_user: User = Depends(get_current_user)
):
    """Save a completed journey"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        journey = Journey(
            id="",  # Will be generated by database
            user_id=current_user.id,
            start_lat=request.start_lat,
            start_lng=request.start_lng,
            end_lat=request.end_lat,
            end_lng=request.end_lng,
            route_data=request.route_data,
            safety_score=request.safety_score,
            distance_km=request.distance_km,
            duration_minutes=request.duration_minutes,
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        journey_id = await neon_db.save_journey(journey)
        
        return {
            "success": True,
            "journey_id": journey_id,
            "message": "Journey saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save journey: {e}")
        raise HTTPException(status_code=500, detail="Failed to save journey")

@app.get("/api/v1/journeys")
async def get_user_journeys(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get user's journey history"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        journeys = await neon_db.get_user_journeys(current_user.id, limit)
        
        journey_list = []
        for journey in journeys:
            # Extract destination name from route_data if available
            destination_name = "Unknown Destination"
            if isinstance(journey.route_data, dict):
                destination_name = journey.route_data.get("query", "Unknown Destination")
            elif isinstance(journey.route_data, str):
                try:
                    import json
                    parsed_route = json.loads(journey.route_data)
                    destination_name = parsed_route.get("query", "Unknown Destination")
                except:
                    pass
                
            journey_list.append({
                "id": journey.id,
                "name": destination_name,
                "start_location": {"lat": journey.start_lat, "lng": journey.start_lng},
                "end_location": {"lat": journey.end_lat, "lng": journey.end_lng},
                "safety_score": journey.safety_score,
                "distance_km": journey.distance_km,
                "duration_minutes": journey.duration_minutes,
                "created_at": journey.created_at,
                "completed_at": journey.completed_at
            })
        
        return {
            "success": True,
            "journeys": journey_list,
            "total": len(journey_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get journeys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get journeys")

@app.get("/api/v1/hazards")
async def get_user_hazard_reports(
    current_user: User = Depends(get_current_user)
):
    """Get user's hazard reports"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get all active hazards (could be filtered by user in the future)
        hazards = await neon_db.get_active_hazards()
        
        hazard_list = []
        for hazard in hazards:
            hazard_list.append({
                "id": hazard.id,
                "location": {"lat": hazard.lat, "lng": hazard.lng},
                "hazard_type": hazard.hazard_type,
                "description": hazard.description,
                "severity": hazard.severity,
                "verified": hazard.verified,
                "created_at": hazard.created_at,
                "expires_at": hazard.expires_at
            })
        
        return {
            "success": True,
            "hazards": hazard_list,
            "total": len(hazard_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get hazard reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to get hazard reports")

# Database Statistics Endpoint
@app.get("/api/v1/stats")
async def get_database_stats(current_user: User = Depends(get_current_user)):
    """Get database statistics (admin only in production)"""
    if not _database_ready():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        stats = await neon_db.get_database_stats()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    # Render injects PORT; local runs default to 8004.
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", "8004")))
    print("=" * 70)
    print("Starting SafeRouteAI API (OSRM + Nominatim + Neon, no Huawei)")
    print(f"API available at: http://localhost:{port}")
    print(f"API docs at: http://localhost:{port}/docs")
    print(f"Maps: {'OSRM + Nominatim' if MAP_SERVICES_AVAILABLE else 'MOCK MODE'}")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=port)