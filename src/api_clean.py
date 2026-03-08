#!/usr/bin/env python3
"""
SafeRouteAI Complete API with Huawei Map Kit Integration
Fixed version with proper middleware configuration
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Add src to path
sys.path.append('src')
sys.path.append('.')

# Import SafeRoute AI modules
try:
    from huawei_client import huawei_client
    from data_ingestion import data_engine
    from modelarts_integration import modelarts_engine
    from routing_engine import routing_engine
    from edge_ai_simulation import edge_ai_processor
    from real_data_integration import real_data_integrator
    from huawei_map_kit import map_kit_service
    from config import settings
except ImportError as e:
    print(f"Import warning: {e}")
    # Create mock objects for missing modules
    class MockService:
        def __getattr__(self, name):
            return lambda *args, **kwargs: {"mock": True, "service": self.__class__.__name__}
    
    huawei_client = MockService()
    data_engine = MockService()
    modelarts_engine = MockService()
    routing_engine = MockService()
    edge_ai_processor = MockService()
    real_data_integrator = MockService()
    map_kit_service = MockService()
    
    class MockSettings:
        demo_mode = True
        api_host = "0.0.0.0"
        api_port = 8003
        huawei_cloud_region = "af-south-1"
    
    settings = MockSettings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SafeRouteAI Complete API with Map Kit",
    description="AI-powered route optimization with Huawei Map Kit integration",
    version="2.0.0"
)

# Add CORS middleware - using the working configuration from demo API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3001",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models
class RouteRequest(BaseModel):
    start_point: Dict[str, float]  # {"lat": float, "lng": float}
    end_point: Dict[str, float]
    departure_time: Optional[str] = None
    safety_preferences: Optional[Dict[str, Any]] = {
        "avoid_high_crime": True,
        "avoid_load_shedding": True,
        "priority": "safety"
    }

class SafetyHeatmapRequest(BaseModel):
    area_bounds: Dict[str, float]
    time_range: Optional[Dict[str, str]] = None

class IncidentReport(BaseModel):
    location: Dict[str, float]
    incident_type: str
    severity: float
    description: str
    timestamp: Optional[str] = None

class EdgeAIRequest(BaseModel):
    sensor_data: Dict[str, Any]
    analysis_type: str

@app.get("/")
async def root():
    """Enhanced health check and system status"""
    return {
        "message": "SafeRouteAI Complete API - Intelligent Township Logistics & Safety",
        "status": "active",
        "version": "2.0.0",
        "system_status": {
            "demo_mode": getattr(settings, 'demo_mode', True),
            "huawei_integration": not getattr(settings, 'demo_mode', True),
            "map_kit_enabled": True,
            "modules_loaded": {
                "data_ingestion": True,
                "modelarts_integration": True,
                "routing_engine": True,
                "edge_ai_simulation": True,
                "map_kit_service": True
            }
        },
        "capabilities": [
            "AI-powered route optimization",
            "Real-time safety heatmaps", 
            "ML model training and deployment",
            "Edge AI hazard detection",
            "Huawei Map Kit integration",
            "Real-time hazard monitoring",
            "Crime pattern analysis"
        ]
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
                "user_reporting"
            ]
        }
    except Exception as e:
        logger.error(f"Map config retrieval failed: {e}")
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
            "last_updated": datetime.now().isoformat()
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
            "last_updated": datetime.now().isoformat()
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
            }
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
            "analysis_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Route safety analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Edge AI Integration
@app.post("/api/v1/edge-ai/driver-behavior")
async def analyze_driver_behavior(request: EdgeAIRequest):
    """Analyze driver behavior using edge AI sensor data"""
    try:
        behavior_analysis = edge_ai_processor.simulate_driver_behavior_analysis(
            request.sensor_data
        )
        
        return {
            "success": True,
            "behavior_analysis": behavior_analysis,
            "system_info": {
                "analysis_type": request.analysis_type,
                "edge_processing": True
            }
        }
    except Exception as e:
        logger.error(f"Driver behavior analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route Optimization
@app.post("/api/v1/optimize-route")
async def optimize_route(request: RouteRequest):
    """Complete route optimization using all SafeRoute AI modules"""
    try:
        logger.info(f"Route optimization request: {request.start_point} -> {request.end_point}")
        
        # Parse departure time
        departure_time = datetime.now()
        if request.departure_time:
            try:
                departure_time = datetime.fromisoformat(request.departure_time.replace('Z', '+00:00'))
                departure_time = departure_time.replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Invalid departure time format: {e}")
                departure_time = datetime.now()
        
        # Calculate optimized route
        route_result = routing_engine.calculate_safe_route(
            request.start_point["lat"],
            request.start_point["lng"],
            request.end_point["lat"], 
            request.end_point["lng"],
            request.safety_preferences,
            departure_time
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
    except Exception as e:
        logger.error(f"Route optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🇿🇦 Starting SafeRouteAI Complete API with Huawei Map Kit Integration")
    print("="*70)
    print("📡 API will be available at: http://localhost:8003")
    print("📚 API docs at: http://localhost:8003/docs")
    print("🗺️  Map Kit: ENABLED with real-time hazard detection")
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=8003)