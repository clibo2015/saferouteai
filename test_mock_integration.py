#!/usr/bin/env python3
"""
Test SafeRouteAI Mock Integration
Quick test to verify all mock services work correctly
"""
import sys
import os
import requests
import time
import json
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_mock_services():
    """Test mock services directly"""
    print("🧪 Testing Mock Services Directly")
    print("="*50)
    
    try:
        from src.mock_huawei_services import get_mock_service
        
        # Test mock service
        mock_service = get_mock_service()
        
        # Test OBS
        obs_client = mock_service.get_obs_client()
        obs_client.createBucket("test-bucket", "af-south-1")
        print("✅ OBS Mock: Bucket creation works")
        
        # Test ModelArts
        modelarts_client = mock_service.get_modelarts_client()
        job_id = modelarts_client.create_training_job({
            'job_name': 'test-job',
            'algorithm': 'TestAlgorithm'
        })
        print(f"✅ ModelArts Mock: Training job created ({job_id})")
        
        # Test Inference
        inference_service = mock_service.get_inference_service()
        endpoint_id = inference_service.create_endpoint("test-model", "test-endpoint")
        prediction = inference_service.predict(endpoint_id, {'features': [-26.2, 28.0]})
        print(f"✅ Inference Mock: Prediction works (Risk: {prediction['prediction']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock services test failed: {e}")
        return False

def test_unified_client():
    """Test unified Huawei client"""
    print("\n🧪 Testing Unified Client")
    print("="*50)
    
    try:
        from src.huawei_client_v2 import HuaweiCloudClient
        
        client = HuaweiCloudClient()
        
        # Test data upload
        uploaded = client.upload_saferoute_data()
        print(f"✅ Data Upload: {len(uploaded)} files uploaded")
        
        # Test training
        job_id = client.create_training_job({
            'job_name': 'test-unified-job',
            'algorithm': 'TestAlgorithm'
        })
        print(f"✅ Training: Job created ({job_id})")
        
        # Test deployment
        endpoint_id = client.deploy_model("test-model-path", "test-endpoint")
        print(f"✅ Deployment: Endpoint created ({endpoint_id})")
        
        # Test prediction
        prediction = client.predict_risk(endpoint_id, -26.2041, 28.0473)
        print(f"✅ Prediction: Risk score {prediction['prediction']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints (requires API to be running)"""
    print("\n🧪 Testing API Endpoints")
    print("="*50)
    
    base_url = "http://localhost:8003"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ API Root: Accessible")
        else:
            print(f"❌ API Root: Status {response.status_code}")
            return False
        
        # Test status endpoint
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Status: {status.get('mock_mode', 'Unknown')} mode")
        
        # Test data upload
        response = requests.post(f"{base_url}/data/upload", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Upload: {result.get('message', 'Success')}")
        
        # Test risk prediction
        prediction_data = {
            "latitude": -26.2041,
            "longitude": 28.0473,
            "hour": 14,
            "day_of_week": 2
        }
        response = requests.post(f"{base_url}/predict/risk", 
                               json=prediction_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            risk_score = result['prediction']['prediction']
            print(f"✅ API Prediction: Risk score {risk_score:.2f}")
        
        # Test full workflow
        response = requests.get(f"{base_url}/demo/full-workflow", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("✅ API Workflow: Complete workflow successful")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  API not running - start with: python demo_api_with_mock.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🇿🇦 SafeRouteAI Mock Integration Tests")
    print("Testing all mock services and integrations")
    print("="*60)
    
    results = []
    
    # Test mock services
    results.append(("Mock Services", test_mock_services()))
    
    # Test unified client
    results.append(("Unified Client", test_unified_client()))
    
    # Test API endpoints
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Summary
    print("\n" + "="*60)
    print("🏆 TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("   SafeRouteAI mock services are fully functional")
        print("   Ready for development and demo")
    else:
        print("\n⚠️  Some tests failed")
        print("   Check error messages above")
    
    print(f"\n💡 NEXT STEPS:")
    print("   1. Run API: python demo_api_with_mock.py")
    print("   2. Visit: http://localhost:8000/docs")
    print("   3. Test endpoints in browser")
    print("   4. When ready, get Huawei Cloud coupon")
    print("   5. Switch to production mode")

if __name__ == "__main__":
    main()