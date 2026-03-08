#!/usr/bin/env python3
"""
SafeRouteAI API with Huawei Map Kit Integration
Extended from working demo API with Map Kit endpoints
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Add src to path
sys.path.append('src')

# Import Map Kit service
try:
    from huawei_map_kit import map_kit_service
    from edge_ai_simulation import edge_ai_processor
    from huawei_client import huawei_client
    from data_ingestion import data_engine
    from modelarts_integration import modelarts_engine
    from routing_engine import routing_engine
    from real_data_integration import real_data_integrator
    from config import settings
    
    # Check if Map Kit is in production mode
    MAP_KIT_AVAILABLE = True
    MAP_KIT_PRODUCTION = settings.is_map_kit_production_ready()
    
except ImportError as e:
    print(f"Import warning: {e}")
    MAP_KIT_AVAILABLE = False
    MAP_KIT_PRODUCTION = False
    
    # Create mock service
    class MockMapKitService:
        def get_map_config(self):
            return {
                "api_key": "mock_key", 
                "region": "af-south-1",
                "js_api_url": "https://mapapi.cloud.huawei.com/mapjs/v1/api/js",
                "map_options": {
                    "center": {"lat": -26.2041, "lng": 28.0473},
                    "zoom": 10,
                    "mapTypeId": "roadmap"
                },
                "south_africa_bounds": {
                    "north": -22.0,
                    "south": -35.0,
                    "east": 33.0,
                    "west": 16.0
                }
            }
        
        def get_real_time_markers(self, bounds=None):
            return [
                {
                    "id": "marker_1",
                    "position": {"lat": -26.2041, "lng": 28.0473},
                    "title": "Crime Hotspot",
                    "description": "High crime area - exercise caution",
                    "type": "crime_hotspot", 
                    "severity": 0.8
                },
                {
                    "id": "marker_2",
                    "position": {"lat": -26.2678, "lng": 27.8546},
                    "title": "Road Hazard",
                    "description": "Construction zone ahead",
                    "type": "hazard", 
                    "severity": 0.6
                }
            ]
        
        def get_hazard_zones(self, bounds=None):
            return [
                {
                    "id": "zone_1",
                    "center": {"lat": -26.2041, "lng": 28.0473}, 
                    "radius": 500, 
                    "type": "high_crime",
                    "severity": 0.8,
                    "confidence": 0.9
                }
            ]
        
        def get_safety_heatmap_data(self, bounds=None):
            return [
                {
                    "location": {"lat": -26.2041, "lng": 28.0473},
                    "weight": 0.8,
                    "safety_score": 0.3,
                    "risk_factors": ["high_crime", "poor_lighting"]
                },
                {
                    "location": {"lat": -26.2678, "lng": 27.8546},
                    "weight": 0.4,
                    "safety_score": 0.7,
                    "risk_factors": ["moderate_traffic"]
                }
            ]
        
        def report_user_hazard(self, lat, lng, hazard_type, description, severity):
            return f"hazard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        def get_route_safety_analysis(self, waypoints):
            return {
                "overall_safety_score": 0.6,
                "average_risk": 0.4,
                "high_risk_segments": [
                    {"start": waypoints[0], "end": waypoints[1], "risk_level": 0.8}
                ],
                "hazards_along_route": [
                    {"location": waypoints[0], "type": "crime_hotspot", "severity": 0.7}
                ],
                "safety_rating": "Fair",
                "recommendations": ["Avoid area around waypoint 2"]
            }
    
    class MockEdgeAI:
        def simulate_driver_behavior_analysis(self, sensor_data):
            return {
                "driver_behavior_score": 0.8,
                "speed_assessment": "NORMAL",
                "driving_style": "CAUTIOUS",
                "alerts": [],
                "recommendations": ["Maintain current driving pattern"]
            }
    
    map_kit_service = MockMapKitService()
    edge_ai_processor = MockEdgeAI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SafeRouteAI API with Map Kit",
    description="AI-powered route optimization with Huawei Map Kit integration",
    version="2.0.0"
)

# Add CORS middleware - using exact same config as working demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models
class LocationPoint(BaseModel):
    latitude: float
    longitude: float

@app.get("/")
async def root():
    """API root endpoint"""
    map_status = "🗺️ Production Ready" if MAP_KIT_PRODUCTION else ("✅ Ready" if MAP_KIT_AVAILABLE else "🔄 Mock Mode")
    
    return {
        "message": "SafeRouteAI API with Huawei Map Kit Integration",
        "version": "2.0.0",
        "map_kit_available": MAP_KIT_AVAILABLE,
        "map_kit_production": MAP_KIT_PRODUCTION,
        "services": {
            "map_kit": map_status,
            "edge_ai": "✅ Ready",
            "real_time_hazards": "✅ Ready"
        },
        "capabilities": [
            "Real-time hazard detection",
            "Crime hotspot mapping", 
            "Safety heatmap generation",
            "Route safety analysis",
            "User hazard reporting",
            "Interactive map rendering" if MAP_KIT_PRODUCTION else "Mock map rendering",
            "Real GPS coordinates" if MAP_KIT_PRODUCTION else "Simulated GPS coordinates"
        ],
        "production_features": {
            "real_gps_handling": MAP_KIT_PRODUCTION,
            "interactive_maps": MAP_KIT_PRODUCTION,
            "offline_caching": MAP_KIT_PRODUCTION and settings.map_kit_cache_enabled,
            "turn_by_turn_navigation": MAP_KIT_PRODUCTION
        }
    }

# Map Kit Endpoints
@app.get("/api/v1/map/config")
async def get_map_config():
    """Get Huawei Map Kit configuration for frontend"""
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
                "user_reporting",
                "interactive_maps" if MAP_KIT_PRODUCTION else "mock_maps",
                "real_gps" if MAP_KIT_PRODUCTION else "simulated_gps"
            ],
            "map_kit_available": MAP_KIT_AVAILABLE,
            "map_kit_production": MAP_KIT_PRODUCTION,
            "production_status": map_kit_service.get_production_status() if MAP_KIT_AVAILABLE else None
        }
    except Exception as e:
        logger.error(f"Map config retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/map/status")
async def get_map_kit_status():
    """Get detailed Map Kit production status"""
    try:
        if MAP_KIT_AVAILABLE:
            status = map_kit_service.get_production_status()
            config_status = settings.get_map_kit_status()
            
            return {
                "success": True,
                "map_kit_status": status,
                "configuration_status": config_status,
                "transition_ready": status["production_mode"],
                "issues": config_status.get("configuration_issues", [])
            }
        else:
            return {
                "success": False,
                "error": "Map Kit service not available",
                "map_kit_status": {"production_mode": False}
            }
    except Exception as e:
        logger.error(f"Map Kit status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/geocode")
async def geocode_address(request: Dict[str, Any]):
    """Get GPS coordinates for an address using real Huawei Location Kit"""
    try:
        address = request.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="Address required")
        
        coordinates = map_kit_service.get_real_gps_coordinates(address)
        
        if coordinates:
            return {
                "success": True,
                "coordinates": coordinates,
                "address": address,
                "production_mode": MAP_KIT_PRODUCTION,
                "data_source": "Huawei Location Kit" if MAP_KIT_PRODUCTION else "Mock Geocoding"
            }
        else:
            raise HTTPException(status_code=404, detail="Address not found")
            
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/render")
async def render_interactive_map(request: Dict[str, Any]):
    """Render interactive map with real map tiles"""
    try:
        center_lat = request.get("center_lat", -26.2041)
        center_lng = request.get("center_lng", 28.0473)
        zoom = request.get("zoom", 10)
        
        map_result = map_kit_service.render_interactive_map(center_lat, center_lng, zoom)
        
        return {
            "success": True,
            "map_rendering": map_result,
            "production_mode": MAP_KIT_PRODUCTION,
            "interactive": MAP_KIT_PRODUCTION
        }
        
    except Exception as e:
        logger.error(f"Map rendering failed: {e}")
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
            "data_source": "Real-time SAPS + Edge AI" if MAP_KIT_AVAILABLE else "Mock Data"
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
            "coverage": "All of South Africa" if MAP_KIT_AVAILABLE else "Mock Coverage"
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
async def report_hazard(request: Dict[str, Any]):
    """Report a user-submitted hazard"""
    try:
        lat = request.get("latitude")
        lng = request.get("longitude") 
        hazard_type = request.get("hazard_type", "unknown")
        description = request.get("description", "")
        severity = request.get("severity", 0.5)
        
        if not lat or not lng:
            raise HTTPException(status_code=400, detail="Latitude and longitude required")
        
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
            "processing_mode": "Real-time" if MAP_KIT_AVAILABLE else "Mock Mode"
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
            "analysis_method": "AI + Real Data" if MAP_KIT_AVAILABLE else "Mock Analysis"
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
        
        behavior_analysis = edge_ai_processor.simulate_driver_behavior_analysis(sensor_data)
        
        return {
            "success": True,
            "behavior_analysis": behavior_analysis,
            "system_info": {
                "analysis_type": analysis_type,
                "edge_processing": True,
                "real_time": MAP_KIT_AVAILABLE
            }
        }
    except Exception as e:
        logger.error(f"Driver behavior analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Optimization
@app.post("/api/v1/optimize-route")
async def optimize_route(request: Dict[str, Any]):
    """Complete route optimization using all SafeRoute AI modules"""
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
        
        if MAP_KIT_AVAILABLE:
            # Calculate optimized route using real services
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
                    "optimization_weights": route_result.optimization_weights
                },
                "system_info": {
                    "demo_mode": getattr(settings, 'demo_mode', True),
                    "processing_time": datetime.now().isoformat(),
                    "huawei_services_used": ["ModelArts", "GaussDB", "Pangu_Models", "Map_Kit"]
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
                    "huawei_services_used": ["Mock_Services"]
                }
            }
            
    except Exception as e:
        logger.error(f"Route optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🇿🇦 Starting SafeRouteAI API with Huawei Map Kit Integration")
    print("="*70)
    print("📡 API will be available at: http://localhost:8003")
    print("📚 API docs at: http://localhost:8003/docs")
    
    if MAP_KIT_PRODUCTION:
        print("🗺️  Map Kit: PRODUCTION MODE - Real Huawei Map Kit Integration")
        print("✅ Features: Real GPS, Interactive Maps, Offline Caching")
    elif MAP_KIT_AVAILABLE:
        print("🔧 Map Kit: DEMO MODE - Mock Map Integration")
        print("⚠️  To enable production mode:")
        print("   1. Set HUAWEI_MAP_API_KEY in .env")
        print("   2. Set MAP_KIT_PRODUCTION_MODE=true")
        print("   3. Ensure DEMO_MODE=false")
    else:
        print("❌ Map Kit: UNAVAILABLE - Service Import Failed")
    
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=8003)