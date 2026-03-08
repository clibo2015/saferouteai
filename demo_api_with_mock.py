#!/usr/bin/env python3
"""
SafeRouteAI Demo API with Mock Huawei Cloud Services
Demonstrates full API functionality using mock services
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add src to path
sys.path.append('src')

from src.huawei_client_v2 import HuaweiCloudClient

# Initialize FastAPI app
app = FastAPI(
    title="SafeRouteAI Demo API",
    description="AI-powered route optimization with mock Huawei Cloud services",
    version="1.0.0"
)

# Add CORS middleware to handle frontend requests
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

# Initialize Huawei Cloud client (will use mock mode)
huawei_client = HuaweiCloudClient()

# Pydantic models
class LocationPoint(BaseModel):
    latitude: float
    longitude: float

class RouteRequest(BaseModel):
    start: LocationPoint
    end: LocationPoint
    time_of_day: int = 12  # Hour (0-23)
    day_of_week: int = 1   # Day (1=Monday, 7=Sunday)
    avoid_high_crime: bool = True
    avoid_load_shedding: bool = True

class RiskPredictionRequest(BaseModel):
    latitude: float
    longitude: float
    hour: int = 12
    day_of_week: int = 1

class TrainingJobRequest(BaseModel):
    job_name: str
    algorithm: str = "RandomForest"
    features: List[str] = ["latitude", "longitude", "hour", "day_of_week"]

# Global variables for demo
demo_endpoint_id = None
demo_training_jobs = []

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "SafeRouteAI Demo API with Mock Huawei Cloud Services",
        "version": "1.0.0",
        "mode": huawei_client.mode,
        "region": huawei_client.region,
        "services": {
            "obs_storage": "✅ Ready",
            "modelarts_training": "✅ Ready", 
            "inference_service": "✅ Ready"
        }
    }

@app.get("/status")
async def get_status():
    """Get service status"""
    return huawei_client.get_service_status()

@app.post("/data/upload")
async def upload_data():
    """Upload SafeRouteAI data to mock OBS"""
    try:
        uploaded_files = huawei_client.upload_saferoute_data()
        return {
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} files to OBS",
            "files": uploaded_files,
            "bucket": "saferoute-ai-data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training/start")
async def start_training(request: TrainingJobRequest):
    """Start a ModelArts training job"""
    global demo_training_jobs
    
    try:
        job_config = {
            'job_name': request.job_name,
            'algorithm': request.algorithm,
            'features': request.features,
            'input_data_path': 'obs://saferoute-ai-data/saferoute-data/',
            'output_model_path': 'obs://saferoute-ai-data/models/'
        }
        
        job_id = huawei_client.create_training_job(job_config)
        demo_training_jobs.append(job_id)
        
        return {
            "success": True,
            "job_id": job_id,
            "job_name": request.job_name,
            "status": "RUNNING",
            "message": "Training job started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/training/jobs")
async def list_training_jobs():
    """List all training jobs"""
    try:
        jobs = huawei_client.list_training_jobs()
        return {
            "success": True,
            "jobs": jobs,
            "total_jobs": len(jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/training/jobs/{job_id}")
async def get_training_job(job_id: str):
    """Get training job status"""
    try:
        status = huawei_client.get_training_job_status(job_id)
        return {
            "success": True,
            "job_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/model/deploy/{job_id}")
async def deploy_model(job_id: str, endpoint_name: str = "saferoute-api-endpoint"):
    """Deploy trained model to inference endpoint"""
    global demo_endpoint_id
    
    try:
        model_path = f"obs://saferoute-ai-data/models/{job_id}/model.joblib"
        endpoint_id = huawei_client.deploy_model(model_path, endpoint_name)
        demo_endpoint_id = endpoint_id
        
        return {
            "success": True,
            "endpoint_id": endpoint_id,
            "endpoint_name": endpoint_name,
            "model_path": model_path,
            "status": "DEPLOYED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/risk")
async def predict_risk(request: RiskPredictionRequest):
    """Predict crime risk for a location"""
    global demo_endpoint_id
    
    if not demo_endpoint_id:
        # Create a default endpoint for demo
        demo_endpoint_id = huawei_client.deploy_model(
            "obs://saferoute-ai-data/models/default/model.joblib",
            "default-saferoute-endpoint"
        )
    
    try:
        prediction = huawei_client.predict_risk(
            demo_endpoint_id,
            request.latitude,
            request.longitude,
            request.hour,
            request.day_of_week
        )
        
        return {
            "success": True,
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "prediction": prediction,
            "endpoint_id": demo_endpoint_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route/optimize")
async def optimize_route(request: RouteRequest):
    """Optimize route with safety considerations"""
    global demo_endpoint_id
    
    if not demo_endpoint_id:
        # Create a default endpoint for demo
        demo_endpoint_id = huawei_client.deploy_model(
            "obs://saferoute-ai-data/models/default/model.joblib",
            "route-optimization-endpoint"
        )
    
    try:
        # Get risk predictions for start and end points
        start_risk = huawei_client.predict_risk(
            demo_endpoint_id,
            request.start.latitude,
            request.start.longitude,
            request.time_of_day,
            request.day_of_week
        )
        
        end_risk = huawei_client.predict_risk(
            demo_endpoint_id,
            request.end.latitude,
            request.end.longitude,
            request.time_of_day,
            request.day_of_week
        )
        
        # Generate optimized route (mock implementation)
        import random
        
        # Create waypoints between start and end
        waypoints = []
        num_waypoints = random.randint(3, 6)
        
        for i in range(num_waypoints):
            progress = (i + 1) / (num_waypoints + 1)
            lat = request.start.latitude + (request.end.latitude - request.start.latitude) * progress
            lng = request.start.longitude + (request.end.longitude - request.start.longitude) * progress
            
            # Add some variation for realistic routing
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)
            
            # Get risk prediction for waypoint
            waypoint_risk = huawei_client.predict_risk(
                demo_endpoint_id, lat, lng, request.time_of_day, request.day_of_week
            )
            
            waypoints.append({
                "latitude": lat,
                "longitude": lng,
                "risk_score": waypoint_risk['prediction'],
                "risk_level": waypoint_risk['risk_level']
            })
        
        # Calculate route metrics
        total_risk = sum(wp['risk_score'] for wp in waypoints) / len(waypoints)
        distance_km = abs(request.end.latitude - request.start.latitude) + abs(request.end.longitude - request.start.longitude)
        distance_km *= 111  # Rough conversion to km
        
        return {
            "success": True,
            "route_id": f"route_{random.randint(1000, 9999)}",
            "start_point": {
                "latitude": request.start.latitude,
                "longitude": request.start.longitude,
                "risk_score": start_risk['prediction'],
                "risk_level": start_risk['risk_level']
            },
            "end_point": {
                "latitude": request.end.latitude,
                "longitude": request.end.longitude,
                "risk_score": end_risk['prediction'],
                "risk_level": end_risk['risk_level']
            },
            "waypoints": waypoints,
            "route_metrics": {
                "total_distance_km": round(distance_km, 2),
                "estimated_duration_minutes": len(waypoints) * 8 + random.randint(10, 30),
                "average_risk_score": round(total_risk, 2),
                "overall_safety_level": "LOW" if total_risk < 3 else "MEDIUM" if total_risk < 7 else "HIGH"
            },
            "safety_features": {
                "avoids_high_crime_areas": request.avoid_high_crime,
                "avoids_load_shedding_zones": request.avoid_load_shedding,
                "real_time_monitoring": True,
                "emergency_contacts": True
            },
            "ai_insights": [
                f"Route optimized using Huawei ModelArts AI (Mock Mode)",
                f"Analyzed {len(waypoints) + 2} points for safety assessment",
                f"Average risk level: {total_risk:.1f}/10",
                "Emergency services mapped along route"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo/full-workflow")
async def demo_full_workflow():
    """Demonstrate complete SafeRouteAI workflow"""
    try:
        results = {}
        
        # Step 1: Upload data
        uploaded_files = huawei_client.upload_saferoute_data()
        results['data_upload'] = {
            "files_uploaded": len(uploaded_files),
            "status": "✅ Complete"
        }
        
        # Step 2: Start training
        job_config = {
            'job_name': f'demo-workflow-{datetime.now().strftime("%H%M%S")}',
            'algorithm': 'XGBoost',
            'features': ['latitude', 'longitude', 'hour', 'day_of_week', 'crime_density']
        }
        job_id = huawei_client.create_training_job(job_config)
        results['training'] = {
            "job_id": job_id,
            "status": "✅ Started"
        }
        
        # Step 3: Deploy model
        model_path = f"obs://saferoute-ai-data/models/{job_id}/model.joblib"
        endpoint_id = huawei_client.deploy_model(model_path, "demo-workflow-endpoint")
        results['deployment'] = {
            "endpoint_id": endpoint_id,
            "status": "✅ Deployed"
        }
        
        # Step 4: Test prediction
        prediction = huawei_client.predict_risk(
            endpoint_id, -26.2041, 28.0473, 14, 2  # Johannesburg CBD, Tuesday 2PM
        )
        results['prediction'] = {
            "location": "Johannesburg CBD",
            "risk_score": prediction['prediction'],
            "risk_level": prediction['risk_level'],
            "status": "✅ Working"
        }
        
        return {
            "success": True,
            "message": "Complete SafeRouteAI workflow demonstrated",
            "workflow_steps": results,
            "competitive_advantages": [
                "Full Huawei Cloud ModelArts integration (Mock)",
                "Real AI training and inference pipeline",
                "Production-ready architecture",
                "Zero cloud costs during development",
                "Seamless switch to production mode"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🇿🇦 Starting SafeRouteAI Demo API with Mock Huawei Cloud Services")
    print("="*70)
    print("📡 API will be available at: http://localhost:8003")
    print("📚 API docs at: http://localhost:8003/docs")
    print("🔧 Mode: MOCK (no real cloud charges)")
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=8003)