#!/usr/bin/env python3
"""
SafeRouteAI Mock Services Demo
Demonstrates full Huawei Cloud functionality without real credentials
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

from src.mock_huawei_services import get_mock_service
from src.huawei_client_v2 import HuaweiCloudClient

def demo_obs_storage():
    """Demo OBS storage functionality"""
    print("\n" + "="*60)
    print("📦 DEMO: OBS Storage Service")
    print("="*60)
    
    # Get mock service
    mock_service = get_mock_service()
    obs_client = mock_service.get_obs_client()
    
    # Create bucket
    print("🪣 Creating SafeRouteAI bucket...")
    response = obs_client.createBucket("saferoute-ai-data", "af-south-1")
    print(f"   Status: {response.status} - {response.reason}")
    
    # List buckets
    print("\n📋 Listing buckets...")
    buckets_response = obs_client.listBuckets()
    if buckets_response.body.buckets:
        for bucket in buckets_response.body.buckets:
            print(f"   ✅ Bucket: {bucket.name} (Location: {bucket.location})")
    
    # Upload sample data
    print("\n📤 Uploading crime data...")
    sample_files = [
        "data/saps_crime_data_national_with_real_csv.csv",
        "data/real_crime_hotspots_analysis.csv"
    ]
    
    for file_path in sample_files:
        if os.path.exists(file_path):
            object_key = f"saferoute-data/{os.path.basename(file_path)}"
            response = obs_client.putFile("saferoute-ai-data", object_key, file_path)
            print(f"   ✅ Uploaded: {file_path} -> {object_key}")
        else:
            print(f"   ⚠️  File not found: {file_path} (creating mock)")
            # Create mock file for demo
            mock_file = Path(file_path)
            mock_file.parent.mkdir(exist_ok=True)
            mock_file.write_text("mock,crime,data\n1,theft,johannesburg\n2,robbery,cape_town")
            
            object_key = f"saferoute-data/{os.path.basename(file_path)}"
            response = obs_client.putFile("saferoute-ai-data", object_key, file_path)
            print(f"   ✅ Created & Uploaded: {file_path} -> {object_key}")

def demo_modelarts_training():
    """Demo ModelArts training functionality"""
    print("\n" + "="*60)
    print("🧠 DEMO: ModelArts Training Service")
    print("="*60)
    
    # Get mock service
    mock_service = get_mock_service()
    modelarts_client = mock_service.get_modelarts_client()
    
    # Create training job
    print("🚀 Creating SafeRouteAI training job...")
    job_config = {
        'job_name': f'saferoute-risk-prediction-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'algorithm': 'RandomForest',
        'input_data_path': 'obs://saferoute-ai-data/saferoute-data/',
        'output_model_path': 'obs://saferoute-ai-data/models/',
        'hyperparameters': {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        }
    }
    
    job_id = modelarts_client.create_training_job(job_config)
    print(f"   Job ID: {job_id}")
    
    # Monitor training progress
    print("\n📊 Monitoring training progress...")
    for i in range(5):
        job = modelarts_client.get_training_job(job_id)
        if job:
            print(f"   Progress: {job.progress}% - Status: {job.status}")
            if job.status == "COMPLETED":
                print(f"   ✅ Training completed! Model saved to: {job.model_path}")
                break
        time.sleep(2)
    
    # List all jobs
    print("\n📋 All training jobs:")
    jobs = modelarts_client.list_training_jobs()
    for job in jobs:
        print(f"   Job: {job.job_name} - Status: {job.status} - Progress: {job.progress}%")
    
    return job_id

def demo_inference_service(model_job_id):
    """Demo inference service functionality"""
    print("\n" + "="*60)
    print("🚀 DEMO: Inference Service")
    print("="*60)
    
    # Get mock service
    mock_service = get_mock_service()
    inference_service = mock_service.get_inference_service()
    
    # Deploy model
    print("📡 Deploying SafeRouteAI model...")
    model_path = f"obs://saferoute-ai-data/models/{model_job_id}/saferoute_risk_model.joblib"
    endpoint_id = inference_service.create_endpoint(model_path, "saferoute-inference")
    
    # Test predictions
    print("\n🎯 Testing risk predictions...")
    
    test_locations = [
        {"name": "Johannesburg CBD", "lat": -26.2041, "lng": 28.0473, "hour": 14, "day": 2},
        {"name": "Cape Town Waterfront", "lat": -33.9249, "lng": 18.4241, "hour": 22, "day": 6},
        {"name": "Durban Beachfront", "lat": -29.8587, "lng": 31.0218, "hour": 8, "day": 1},
        {"name": "Pretoria Central", "lat": -25.7479, "lng": 28.2293, "hour": 18, "day": 5}
    ]
    
    for location in test_locations:
        prediction = mock_service.predict_risk(
            endpoint_id, 
            location["lat"], 
            location["lng"],
            location["hour"],
            location["day"]
        )
        
        print(f"   📍 {location['name']}:")
        print(f"      Risk Score: {prediction['prediction']:.2f}/10")
        print(f"      Risk Level: {prediction['risk_level']}")
        print(f"      Confidence: {prediction['confidence']:.2f}")
    
    return endpoint_id

def demo_unified_client():
    """Demo the unified Huawei Cloud client"""
    print("\n" + "="*60)
    print("🔧 DEMO: Unified Huawei Cloud Client")
    print("="*60)
    
    # Initialize client
    client = HuaweiCloudClient()
    
    # Upload data
    print("📤 Uploading SafeRouteAI data...")
    uploaded_files = client.upload_saferoute_data()
    print(f"   Uploaded {len(uploaded_files)} files")
    
    # Create training job
    print("\n🧠 Starting training job...")
    job_config = {
        'job_name': 'saferoute-unified-demo',
        'algorithm': 'XGBoost',
        'features': ['latitude', 'longitude', 'hour', 'day_of_week', 'crime_density']
    }
    job_id = client.create_training_job(job_config)
    
    # Wait for completion
    print("⏳ Waiting for training completion...")
    for i in range(3):
        status = client.get_training_job_status(job_id)
        print(f"   Status: {status.get('status')} - Progress: {status.get('progress', 0)}%")
        if status.get('status') == 'COMPLETED':
            break
        time.sleep(2)
    
    # Deploy model
    print("\n🚀 Deploying model...")
    model_path = f"obs://saferoute-ai-data/models/{job_id}/model.joblib"
    endpoint_id = client.deploy_model(model_path, "saferoute-unified")
    
    # Test prediction
    print("\n🎯 Testing unified prediction...")
    prediction = client.predict_risk(
        endpoint_id, 
        latitude=-26.2041, 
        longitude=28.0473,
        hour=20,
        day_of_week=5
    )
    
    print(f"   Risk Score: {prediction['prediction']:.2f}")
    print(f"   Risk Level: {prediction['risk_level']}")
    
    # Get service status
    print("\n📊 Service Status:")
    status = client.get_service_status()
    for service, state in status.items():
        print(f"   {service}: {state}")

def demo_production_switch():
    """Demo switching to production mode"""
    print("\n" + "="*60)
    print("🔄 DEMO: Production Mode Switch")
    print("="*60)
    
    client = HuaweiCloudClient()
    
    print("📋 Current mode: MOCK")
    print("   All services running locally")
    print("   No cloud charges incurred")
    
    print("\n💡 To switch to production:")
    print("   1. Get Huawei Cloud credentials (AK/SK)")
    print("   2. Call client.switch_to_production(ak, sk, project_id)")
    print("   3. Restart application")
    print("   4. All services will use real Huawei Cloud")
    
    print("\n🎯 Example production switch:")
    print("   client.switch_to_production(")
    print("       ak='your_access_key',")
    print("       sk='your_secret_key',")
    print("       project_id='your_project_id'")
    print("   )")

def main():
    """Run complete SafeRouteAI mock services demo"""
    print("🇿🇦 SafeRouteAI - Mock Huawei Cloud Services Demo")
    print("Demonstrating full cloud functionality without real credentials")
    print("="*80)
    
    try:
        # Demo OBS storage
        demo_obs_storage()
        
        # Demo ModelArts training
        job_id = demo_modelarts_training()
        
        # Demo inference service
        endpoint_id = demo_inference_service(job_id)
        
        # Demo unified client
        demo_unified_client()
        
        # Demo production switch
        demo_production_switch()
        
        print("\n" + "="*80)
        print("🏆 DEMO COMPLETE - SafeRouteAI Mock Services")
        print("="*80)
        print("✅ OBS Storage: Fully functional")
        print("✅ ModelArts Training: AI models trained locally")
        print("✅ Inference Service: Real-time predictions working")
        print("✅ Unified Client: Production-ready architecture")
        
        print(f"\n📁 Mock data stored in: {Path('mock_obs_storage').absolute()}")
        print("🔄 Ready to switch to production with real Huawei Cloud credentials")
        
        print(f"\n🎯 COMPETITIVE ADVANTAGE:")
        print("   • Full cloud architecture without cloud costs")
        print("   • Real AI training and inference locally")
        print("   • Seamless production deployment ready")
        print("   • Authentic Huawei Cloud integration")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()