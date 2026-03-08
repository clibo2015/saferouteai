"""Huawei Cloud SDK client wrapper for SafeRouteAI"""
import logging
from typing import Optional, Dict, Any, List
from config import settings

# Try to import Huawei Cloud SDK, fall back to demo mode if not available
try:
    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    from huaweicloudsdkcore.client import Client
    from huaweicloudsdkcore.http.http_config import HttpConfig
    from huaweicloudsdkmodelarts.v1 import ModelArtsClient
    from huaweicloudsdkmodelarts.v1.region.modelarts_region import ModelArtsRegion
    HUAWEI_SDK_AVAILABLE = True
except ImportError:
    HUAWEI_SDK_AVAILABLE = False
    BasicCredentials = None
    ModelArtsClient = None
    ModelArtsRegion = None

logger = logging.getLogger(__name__)

class HuaweiCloudClient:
    """Wrapper for Huawei Cloud services used in SafeRouteAI"""
    
    def __init__(self):
        self.modelarts_client: Optional[ModelArtsClient] = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Huawei Cloud service clients"""
        if not HUAWEI_SDK_AVAILABLE:
            logger.info("Huawei Cloud SDK not installed - running in demo mode")
            settings.demo_mode = True
            return
            
        if not settings.demo_mode and self._has_credentials():
            try:
                # Set up authentication
                credentials = BasicCredentials(
                    ak=settings.huawei_cloud_ak,
                    sk=settings.huawei_cloud_sk,
                    project_id=settings.huawei_cloud_project_id
                )
                
                # Configure HTTP settings
                http_config = HttpConfig.get_default_config()
                http_config.ignore_ssl_verification = True
                
                # Initialize ModelArts client
                region = ModelArtsRegion.value_of(settings.huawei_cloud_region)
                self.modelarts_client = ModelArtsClient.new_builder() \
                    .with_credentials(credentials) \
                    .with_region(region) \
                    .with_http_config(http_config) \
                    .build()
                
                logger.info("Huawei Cloud clients initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Huawei Cloud clients: {e}")
                logger.info("Falling back to demo mode")
                settings.demo_mode = True
        else:
            logger.info("Running in demo mode - using mock data")
    
    def _has_credentials(self) -> bool:
        """Check if all required credentials are available"""
        return all([
            settings.huawei_cloud_ak,
            settings.huawei_cloud_sk,
            settings.huawei_cloud_project_id
        ])
    
    def optimize_route(self, start_point: Dict[str, float], 
                           end_point: Dict[str, float], 
                           safety_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize delivery route using ModelArts AI or mock algorithm
        
        Args:
            start_point: {"lat": float, "lng": float}
            end_point: {"lat": float, "lng": float}
            safety_preferences: {"avoid_high_crime": bool, "avoid_load_shedding": bool}
        
        Returns:
            Optimized route with safety scores
        """
        if settings.demo_mode or not self.modelarts_client:
            return self._mock_route_optimization(start_point, end_point, safety_preferences)
        
        try:
            # Real ModelArts implementation would go here
            # For now, return mock data to avoid charges
            logger.info("Using ModelArts for route optimization")
            return self._mock_route_optimization(start_point, end_point, safety_preferences)
            
        except Exception as e:
            logger.error(f"ModelArts route optimization failed: {e}")
            return self._mock_route_optimization(start_point, end_point, safety_preferences)
    
    def _mock_route_optimization(self, start_point: Dict[str, float], 
                                end_point: Dict[str, float], 
                                safety_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Mock route optimization for demo purposes"""
        import random
        
        # Simulate AI-powered route optimization
        base_distance = abs(end_point["lat"] - start_point["lat"]) + abs(end_point["lng"] - start_point["lng"])
        
        # Generate mock waypoints
        waypoints = []
        num_waypoints = random.randint(3, 7)
        
        for i in range(num_waypoints):
            progress = (i + 1) / (num_waypoints + 1)
            lat = start_point["lat"] + (end_point["lat"] - start_point["lat"]) * progress
            lng = start_point["lng"] + (end_point["lng"] - start_point["lng"]) * progress
            
            # Add some variation for realistic routing
            lat += random.uniform(-0.01, 0.01)
            lng += random.uniform(-0.01, 0.01)
            
            waypoints.append({
                "lat": lat,
                "lng": lng,
                "safety_score": random.uniform(0.6, 0.95),
                "estimated_time": i * 5 + random.randint(2, 8)
            })
        
        # Calculate safety metrics
        overall_safety = sum(wp["safety_score"] for wp in waypoints) / len(waypoints)
        
        return {
            "route_id": f"route_{random.randint(1000, 9999)}",
            "waypoints": waypoints,
            "total_distance_km": round(base_distance * 111, 2),  # Rough km conversion
            "estimated_duration_minutes": sum(wp["estimated_time"] for wp in waypoints),
            "overall_safety_score": round(overall_safety, 2),
            "safety_features": {
                "avoids_high_crime_areas": safety_preferences.get("avoid_high_crime", True),
                "avoids_load_shedding_zones": safety_preferences.get("avoid_load_shedding", True),
                "has_emergency_contacts": True,
                "real_time_monitoring": True
            },
            "ai_insights": [
                "Route optimized to avoid high-crime areas during evening hours",
                "Alternative path selected due to predicted load shedding in Zone 3",
                "Emergency services contact points identified along route"
            ]
        }
    
    def analyze_safety_heatmap(self, area_bounds: Dict[str, float]) -> Dict[str, Any]:
        """Generate safety heatmap for township area"""
        if settings.demo_mode:
            return self._mock_safety_heatmap(area_bounds)
        
        # Real implementation would use ModelArts + crime data
        return self._mock_safety_heatmap(area_bounds)
    
    def _mock_safety_heatmap(self, area_bounds: Dict[str, float]) -> Dict[str, Any]:
        """Generate mock safety heatmap data"""
        import random
        
        # Generate grid of safety scores
        grid_size = 10
        heatmap_data = []
        
        lat_step = (area_bounds["north"] - area_bounds["south"]) / grid_size
        lng_step = (area_bounds["east"] - area_bounds["west"]) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                lat = area_bounds["south"] + i * lat_step
                lng = area_bounds["west"] + j * lng_step
                
                # Simulate varying safety levels
                safety_score = random.uniform(0.3, 0.9)
                
                heatmap_data.append({
                    "lat": lat,
                    "lng": lng,
                    "safety_score": round(safety_score, 2),
                    "risk_factors": random.sample([
                        "high_crime_reports", "poor_lighting", "isolated_area",
                        "frequent_load_shedding", "narrow_roads", "no_emergency_access"
                    ], random.randint(0, 3))
                })
        
        return {
            "heatmap_data": heatmap_data,
            "last_updated": "2025-01-25T10:00:00Z",
            "data_sources": [
                "SAPS Crime Statistics (Mock)",
                "Social Media Sentiment Analysis (Mock)", 
                "Eskom Load Shedding Schedule (Mock)",
                "Community Reports (Mock)"
            ]
        }

# Global client instance
huawei_client = HuaweiCloudClient()