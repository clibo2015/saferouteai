"""
Minimal SafeRouteAI API for Map Testing
Focuses only on map and geocoding functionality without heavy dependencies
"""
import os
import sys
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Import only what we need
try:
    from config import settings
    from huawei_map_kit import map_kit_service
    MAP_KIT_AVAILABLE = True
    logger.info("✅ Real Map Kit services loaded")
except ImportError as e:
    logger.error(f"❌ Failed to load real services: {e}")
    MAP_KIT_AVAILABLE = False
    
    # Create mock service
    class MockMapKitService:
        def get_real_gps_coordinates(self, address: str) -> Optional[Dict[str, float]]:
            # Return Johannesburg coordinates for any address in demo mode
            return {"lat": -26.2041, "lng": 28.0473}
        
        def get_map_config(self):
            return {
                "api_key": "mock_key",
                "js_api_url": "https://mapapi.cloud.huawei.com/mapjs/v1/api/js",
                "map_options": {
                    "center": {"lat": -26.2041, "lng": 28.0473},
                    "zoom": 10
                }
            }
    
    map_kit_service = MockMapKitService()

# Create FastAPI app
app = FastAPI(
    title="SafeRouteAI Map API",
    description="API for SafeRouteAI mapping and geocoding services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "SafeRouteAI Map API Running",
        "status": "healthy",
        "map_kit_available": MAP_KIT_AVAILABLE,
        "production_mode": getattr(map_kit_service, 'production_mode', False) if MAP_KIT_AVAILABLE else False
    }

@app.get("/api/v1/map/config")
async def get_map_config():
    """Get Huawei Map Kit configuration"""
    try:
        config = map_kit_service.get_map_config()
        return {
            "success": True,
            "map_config": config,
            "production_mode": MAP_KIT_AVAILABLE and getattr(map_kit_service, 'production_mode', False)
        }
    except Exception as e:
        logger.error(f"Map config retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/map/geocode")
async def geocode_address(request: Dict[str, Any]):
    """Geocode an address string to GPS coordinates"""
    try:
        address = request.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="Address required")
            
        logger.info(f"Geocoding address: {address}")
        location = map_kit_service.get_real_gps_coordinates(address)
        
        if location:
            logger.info(f"✅ Found coordinates: {location}")
            return {
                "success": True,
                "location": location,
                "address": address
            }
        else:
            logger.warning(f"❌ No coordinates found for: {address}")
            # Fallback for demo if geocoding fails
            if not MAP_KIT_AVAILABLE:
                return {
                    "success": True,
                    "location": {"lat": -26.2041, "lng": 28.0473},
                    "address": address,
                    "is_demo": True
                }
            raise HTTPException(status_code=404, detail="Address not found")
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/map/test-geocode")
async def test_geocode():
    """Test endpoint to verify geocoding is working"""
    test_addresses = [
        "Rosenview, Pretoria, South Africa",
        "Times Square, New York, USA", 
        "Cape Town, South Africa"
    ]
    
    results = {}
    for addr in test_addresses:
        try:
            location = map_kit_service.get_real_gps_coordinates(addr)
            results[addr] = location
        except Exception as e:
            results[addr] = f"Error: {e}"
    
    return {
        "success": True,
        "test_results": results,
        "map_kit_available": MAP_KIT_AVAILABLE
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)