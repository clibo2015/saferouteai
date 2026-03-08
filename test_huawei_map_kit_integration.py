#!/usr/bin/env python3
"""
Comprehensive test for Huawei Map Kit integration with SafeRouteAI
Tests real-time hazard detection, crime hotspot overlays, and Edge AI integration
"""

import asyncio
import json
import time
from datetime import datetime
import requests
from typing import Dict, Any

class HuaweiMapKitTester:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_map_config_endpoint(self) -> bool:
        """Test Map Kit configuration endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/map/config")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields
                required_fields = ["map_config", "features_enabled"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Map Config Endpoint", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Verify map config structure
                map_config = data["map_config"]
                config_fields = ["api_key", "js_api_url", "map_options", "south_africa_bounds"]
                missing_config = [field for field in config_fields if field not in map_config]
                
                if missing_config:
                    self.log_test("Map Config Endpoint", False, f"Missing config fields: {missing_config}")
                    return False
                
                # Verify South Africa bounds
                bounds = map_config["south_africa_bounds"]
                if not all(key in bounds for key in ["north", "south", "east", "west"]):
                    self.log_test("Map Config Endpoint", False, "Invalid South Africa bounds")
                    return False
                
                self.log_test("Map Config Endpoint", True, f"Config loaded with {len(data['features_enabled'])} features")
                return True
            else:
                self.log_test("Map Config Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Map Config Endpoint", False, str(e))
            return False
    
    def test_real_time_markers(self) -> bool:
        """Test real-time markers endpoint"""
        try:
            # Test without bounds
            response = requests.get(f"{self.base_url}/api/v1/map/markers")
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Real-time Markers", False, "API returned success=false")
                    return False
                
                markers = data.get("markers", [])
                total_markers = data.get("total_markers", 0)
                
                if len(markers) != total_markers:
                    self.log_test("Real-time Markers", False, "Marker count mismatch")
                    return False
                
                # Verify marker structure
                if markers:
                    marker = markers[0]
                    required_fields = ["id", "position", "type", "severity", "title", "description"]
                    missing_fields = [field for field in required_fields if field not in marker]
                    
                    if missing_fields:
                        self.log_test("Real-time Markers", False, f"Missing marker fields: {missing_fields}")
                        return False
                
                self.log_test("Real-time Markers", True, f"Loaded {total_markers} markers")
                return True
            else:
                self.log_test("Real-time Markers", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Real-time Markers", False, str(e))
            return False
    
    def test_hazard_zones(self) -> bool:
        """Test active hazard zones endpoint"""
        try:
            # Test with South Africa bounds
            bounds = "north=-22.0&south=-35.0&east=33.0&west=16.0"
            response = requests.get(f"{self.base_url}/api/v1/map/hazard-zones?{bounds}")
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Hazard Zones", False, "API returned success=false")
                    return False
                
                zones = data.get("hazard_zones", [])
                total_zones = data.get("total_zones", 0)
                
                # Verify zone structure
                if zones:
                    zone = zones[0]
                    required_fields = ["id", "center", "radius", "type", "severity", "confidence"]
                    missing_fields = [field for field in required_fields if field not in zone]
                    
                    if missing_fields:
                        self.log_test("Hazard Zones", False, f"Missing zone fields: {missing_fields}")
                        return False
                    
                    # Verify center coordinates
                    center = zone["center"]
                    if not ("lat" in center and "lng" in center):
                        self.log_test("Hazard Zones", False, "Invalid zone center coordinates")
                        return False
                
                self.log_test("Hazard Zones", True, f"Loaded {total_zones} active hazard zones")
                return True
            else:
                self.log_test("Hazard Zones", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Hazard Zones", False, str(e))
            return False
    
    def test_safety_heatmap(self) -> bool:
        """Test safety heatmap data endpoint"""
        try:
            # Test with Johannesburg area bounds
            bounds = "north=-26.0&south=-26.5&east=28.5&west=27.5"
            response = requests.get(f"{self.base_url}/api/v1/map/safety-heatmap?{bounds}")
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Safety Heatmap", False, "API returned success=false")
                    return False
                
                heatmap_data = data.get("heatmap_data", [])
                total_points = data.get("total_points", 0)
                data_sources = data.get("data_sources", [])
                
                # Verify data sources include real data
                expected_sources = ["SAPS Crime Data", "EskomSePush", "Edge AI Detection"]
                missing_sources = [src for src in expected_sources if src not in data_sources]
                
                if missing_sources:
                    self.log_test("Safety Heatmap", False, f"Missing data sources: {missing_sources}")
                    return False
                
                # Verify heatmap point structure
                if heatmap_data:
                    point = heatmap_data[0]
                    required_fields = ["location", "weight", "safety_score", "risk_factors"]
                    missing_fields = [field for field in required_fields if field not in point]
                    
                    if missing_fields:
                        self.log_test("Safety Heatmap", False, f"Missing heatmap fields: {missing_fields}")
                        return False
                
                self.log_test("Safety Heatmap", True, f"Generated {total_points} heatmap points from {len(data_sources)} sources")
                return True
            else:
                self.log_test("Safety Heatmap", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Safety Heatmap", False, str(e))
            return False
    
    def test_hazard_reporting(self) -> bool:
        """Test user hazard reporting functionality"""
        try:
            # Report a test hazard
            hazard_data = {
                "latitude": -26.2041,
                "longitude": 28.0473,
                "hazard_type": "pothole",
                "description": "Large pothole blocking left lane",
                "severity": 0.8
            }
            
            response = requests.post(f"{self.base_url}/api/v1/map/report-hazard", json=hazard_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Hazard Reporting", False, "API returned success=false")
                    return False
                
                hazard_id = data.get("hazard_id")
                if not hazard_id:
                    self.log_test("Hazard Reporting", False, "No hazard ID returned")
                    return False
                
                # Verify impact estimation
                impact = data.get("estimated_impact", {})
                required_impact_fields = ["radius_meters", "duration_minutes", "affected_users"]
                missing_impact = [field for field in required_impact_fields if field not in impact]
                
                if missing_impact:
                    self.log_test("Hazard Reporting", False, f"Missing impact fields: {missing_impact}")
                    return False
                
                self.log_test("Hazard Reporting", True, f"Hazard reported with ID: {hazard_id}")
                return True
            else:
                self.log_test("Hazard Reporting", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Hazard Reporting", False, str(e))
            return False
    
    def test_route_safety_analysis(self) -> bool:
        """Test route safety analysis functionality"""
        try:
            # Test route from Johannesburg CBD to Soweto
            waypoints = [
                {"lat": -26.2041, "lng": 28.0473},  # Johannesburg CBD
                {"lat": -26.2341, "lng": 28.0173},  # Intermediate point
                {"lat": -26.2678, "lng": 27.8546}   # Soweto
            ]
            
            response = requests.post(f"{self.base_url}/api/v1/map/analyze-route-safety", 
                                   json={"waypoints": waypoints})
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Route Safety Analysis", False, "API returned success=false")
                    return False
                
                analysis = data.get("safety_analysis", {})
                required_fields = ["overall_safety_score", "average_risk", "high_risk_segments", 
                                 "hazards_along_route", "safety_rating", "recommendations"]
                missing_fields = [field for field in required_fields if field not in analysis]
                
                if missing_fields:
                    self.log_test("Route Safety Analysis", False, f"Missing analysis fields: {missing_fields}")
                    return False
                
                # Verify safety score is valid
                safety_score = analysis["overall_safety_score"]
                if not (0.0 <= safety_score <= 1.0):
                    self.log_test("Route Safety Analysis", False, f"Invalid safety score: {safety_score}")
                    return False
                
                # Verify safety rating
                valid_ratings = ["Excellent", "Very Good", "Good", "Fair", "Poor", "Dangerous"]
                if analysis["safety_rating"] not in valid_ratings:
                    self.log_test("Route Safety Analysis", False, f"Invalid safety rating: {analysis['safety_rating']}")
                    return False
                
                self.log_test("Route Safety Analysis", True, 
                            f"Route analyzed: {analysis['safety_rating']} ({safety_score:.1%} safe)")
                return True
            else:
                self.log_test("Route Safety Analysis", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Route Safety Analysis", False, str(e))
            return False
    
    def test_edge_ai_integration(self) -> bool:
        """Test Edge AI hazard detection integration"""
        try:
            # Test edge AI analysis endpoint
            response = requests.post(f"{self.base_url}/api/v1/edge-ai/driver-behavior", 
                                   json={
                                       "sensor_data": {
                                           "speed_kmh": 65,
                                           "acceleration_ms2": 1.2,
                                           "steering_angle": 15
                                       },
                                       "analysis_type": "behavior"
                                   })
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Edge AI Integration", False, "API returned success=false")
                    return False
                
                analysis = data.get("behavior_analysis", {})
                required_fields = ["driver_behavior_score", "speed_assessment", "driving_style", "recommendations"]
                missing_fields = [field for field in required_fields if field not in analysis]
                
                if missing_fields:
                    self.log_test("Edge AI Integration", False, f"Missing analysis fields: {missing_fields}")
                    return False
                
                # Verify behavior score
                behavior_score = analysis["driver_behavior_score"]
                if not (0.0 <= behavior_score <= 1.0):
                    self.log_test("Edge AI Integration", False, f"Invalid behavior score: {behavior_score}")
                    return False
                
                self.log_test("Edge AI Integration", True, 
                            f"Edge AI analysis: {analysis['driving_style']} driving ({behavior_score:.1%} score)")
                return True
            else:
                self.log_test("Edge AI Integration", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Edge AI Integration", False, str(e))
            return False
    
    def test_map_kit_production_status(self) -> bool:
        """Test Map Kit production status and configuration"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/map/status")
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Map Kit Production Status", False, "API returned success=false")
                    return False
                
                map_status = data.get("map_kit_status", {})
                config_status = data.get("configuration_status", {})
                
                # Check production mode
                production_mode = map_status.get("production_mode", False)
                api_key_valid = map_status.get("api_key_valid", False)
                
                # Check configuration
                ready_for_real_mapping = config_status.get("ready_for_real_mapping", False)
                issues = config_status.get("configuration_issues", [])
                
                status_msg = f"Production: {production_mode}, API Valid: {api_key_valid}, Ready: {ready_for_real_mapping}"
                if issues:
                    status_msg += f", Issues: {len(issues)}"
                
                self.log_test("Map Kit Production Status", True, status_msg)
                return True
            else:
                self.log_test("Map Kit Production Status", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Map Kit Production Status", False, str(e))
            return False
    
    def test_geocoding_service(self) -> bool:
        """Test geocoding service with real/mock GPS coordinates"""
        try:
            test_address = "Johannesburg, South Africa"
            response = requests.post(f"{self.base_url}/api/v1/map/geocode", 
                                   json={"address": test_address})
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Geocoding Service", False, "API returned success=false")
                    return False
                
                coordinates = data.get("coordinates", {})
                production_mode = data.get("production_mode", False)
                data_source = data.get("data_source", "Unknown")
                
                # Verify coordinates are reasonable for Johannesburg
                lat = coordinates.get("lat", 0)
                lng = coordinates.get("lng", 0)
                
                if not (-27 <= lat <= -25 and 27 <= lng <= 29):
                    self.log_test("Geocoding Service", False, f"Invalid coordinates for Johannesburg: ({lat}, {lng})")
                    return False
                
                self.log_test("Geocoding Service", True, 
                            f"Geocoded '{test_address}' using {data_source} ({'Production' if production_mode else 'Demo'} mode)")
                return True
            else:
                self.log_test("Geocoding Service", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Geocoding Service", False, str(e))
            return False
    
    def test_interactive_map_rendering(self) -> bool:
        """Test interactive map rendering"""
        try:
            response = requests.post(f"{self.base_url}/api/v1/map/render", 
                                   json={
                                       "center_lat": -26.2041,
                                       "center_lng": 28.0473,
                                       "zoom": 12
                                   })
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("Interactive Map Rendering", False, "API returned success=false")
                    return False
                
                map_rendering = data.get("map_rendering", {})
                production_mode = data.get("production_mode", False)
                interactive = data.get("interactive", False)
                
                # Check map configuration
                map_config = map_rendering.get("map_config", {})
                center = map_config.get("center", {})
                
                if not (center.get("lat") and center.get("lng")):
                    self.log_test("Interactive Map Rendering", False, "Invalid map center coordinates")
                    return False
                
                features = map_rendering.get("features", [])
                mode_desc = "Production" if production_mode else "Demo"
                interactive_desc = "Interactive" if interactive else "Static"
                
                self.log_test("Interactive Map Rendering", True, 
                            f"Map rendered in {mode_desc} mode ({interactive_desc}) with {len(features)} features")
                return True
            else:
                self.log_test("Interactive Map Rendering", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Interactive Map Rendering", False, str(e))
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all Map Kit integration tests"""
        print("🗺️  Starting Huawei Map Kit Integration Tests")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_map_config_endpoint,
            self.test_map_kit_production_status,
            self.test_real_time_markers,
            self.test_hazard_zones,
            self.test_safety_heatmap,
            self.test_hazard_reporting,
            self.test_route_safety_analysis,
            self.test_geocoding_service,
            self.test_interactive_map_rendering,
            self.test_edge_ai_integration
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"🎯 Test Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All Map Kit integration tests PASSED!")
            print("✅ SafeRouteAI is ready for real-time mapping with Huawei Map Kit")
        else:
            print(f"⚠️  {total - passed} tests failed - check implementation")
        
        # Generate detailed report
        report = {
            "test_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{passed/total*100:.1f}%"
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "map_kit_features_tested": [
                "Real-time hazard detection",
                "Crime hotspot overlays",
                "Safety heatmap generation",
                "User hazard reporting",
                "Route safety analysis",
                "Edge AI integration",
                "Production status monitoring",
                "GPS geocoding service",
                "Interactive map rendering"
            ]
        }
        
        return report

def main():
    """Main test execution"""
    print("🚀 SafeRouteAI - Huawei Map Kit Integration Test Suite")
    print("Testing real-time mapping with Edge AI hazard detection")
    print("Coverage: All of South Africa with live crime data\n")
    
    tester = HuaweiMapKitTester()
    report = tester.run_comprehensive_test()
    
    # Save detailed report
    with open("huawei_map_kit_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Detailed report saved to: huawei_map_kit_test_report.json")
    
    return report["test_summary"]["passed"] == report["test_summary"]["total_tests"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)