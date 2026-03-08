#!/usr/bin/env python3
"""
Test script to verify OBS bucket access and trained model functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_obs_connection():
    """Test OBS bucket connection and list contents."""
    print("\n" + "="*60)
    print("TEST 1: OBS Bucket Connection")
    print("="*60)
    
    # Patch for Python 3.12+ compatibility with esdk-obs-python
    import ssl
    import sys
    import http.client
    
    if sys.version_info >= (3, 12):
        if not hasattr(ssl, 'WRAP_SOCKET'):
            ssl.WRAP_SOCKET = 1
            
        # Monkey patch HTTPSConnection
        _orig_init = http.client.HTTPSConnection.__init__
        
        def patched_init(self, host, port=None, key_file=None, cert_file=None,
                         timeout=http.client._CS_REQ_SENT,
                         source_address=None, *, context=None,
                         check_hostname=None, blocksize=8192):
            _orig_init(self, host, port=port, timeout=timeout,
                       source_address=source_address, context=context,
                       blocksize=blocksize)
                       
        http.client.HTTPSConnection.__init__ = patched_init
        
    try:
        from obs import ObsClient
        
        # Get credentials and config
        ak = os.getenv('HUAWEI_CLOUD_AK')
        sk = os.getenv('HUAWEI_CLOUD_SK')
        # Use env vars for bucket and region, matching .env updates
        bucket_name = os.getenv('OBS_BUCKET_NAME', 'saferoute-data')
        region = os.getenv('HUAWEI_CLOUD_REGION', 'ap-southeast-1')
        
        print(f"Connecting to OBS bucket: {bucket_name}")
        print(f"Region: {region}")
        
        # Create OBS client
        obs_client = ObsClient(
            access_key_id=ak,
            secret_access_key=sk,
            server=f'https://obs.{region}.myhuaweicloud.com'
        )
        
        # List bucket contents
        print("\nListing bucket contents...")
        resp = obs_client.listObjects(bucket_name, max_keys=20)
        
        if resp.status < 300:
            print("✅ OBS Connection Successful!")
            
            if resp.body.contents:
                print(f"\nFound {len(resp.body.contents)} objects:")
                for obj in resp.body.contents:
                    size_kb = obj.size / 1024
                    print(f"  - {obj.key} ({size_kb:.2f} KB)")
            else:
                print("\nBucket is empty (no objects found)")
            
            return True
        else:
            print(f"❌ OBS Error: {resp.errorCode} - {resp.errorMessage}")
            return False
            
    except ImportError:
        print("❌ OBS SDK not installed")
        print("Install with: pip install esdk-obs-python")
        return False
    except TypeError as e:
        if "check_hostname" in str(e):
            print(f"❌ OBS SDK Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        else:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

def test_trained_model():
    """Test loading and using the trained model."""
    print("\n" + "="*60)
    print("TEST 2: Trained Model Loading and Prediction")
    print("="*60)
    
    try:
        import joblib
        import numpy as np
        from pathlib import Path
        
        # Find the model file
        model_paths = [
            'saferoute_model.pkl',
            'models/saferoute_model.pkl',
            'data/saferoute_model.pkl',
            'src/saferoute_model.pkl'
        ]
        
        model_path = None
        for path in model_paths:
            if Path(path).exists():
                model_path = path
                break
        
        if not model_path:
            print("❌ Model file not found!")
            print("Searched in:")
            for path in model_paths:
                print(f"  - {path}")
            print("\nPlease ensure saferoute_model.pkl is in the project directory")
            return False
        
        print(f"Loading model from: {model_path}")
        
        # Load model
        model_artifacts = joblib.load(model_path)
        
        print("✅ Model loaded successfully!")
        print(f"\nModel Information:")
        print(f"  Version: {model_artifacts.get('model_version', 'N/A')}")
        print(f"  Framework: {model_artifacts.get('framework', 'N/A')}")
        print(f"  Features: {len(model_artifacts.get('feature_columns', []))}")
        
        # Display metrics
        metrics = model_artifacts.get('metrics', {})
        if metrics:
            print(f"\nModel Performance:")
            print(f"  R² Score: {metrics.get('r2_score', 'N/A'):.4f}")
            print(f"  MSE: {metrics.get('mse', 'N/A'):.4f}")
        
        # Test prediction
        print("\n" + "-"*60)
        print("Testing Model Prediction")
        print("-"*60)
        
        model = model_artifacts['model']
        scaler = model_artifacts['scaler']
        feature_columns = model_artifacts['feature_columns']
        
        # Create sample input (Johannesburg coordinates)
        sample_data = np.array([[
            -26.2041,  # lat (Johannesburg)
            28.0473,   # lng (Johannesburg)
            20,        # hour (8 PM)
            5,         # day_of_week (Friday)
            2,         # month (February)
            0,         # is_weekend
            1,         # is_night
            3,         # num_risk_factors
            1,         # has_gang_activity
            1,         # has_poor_lighting
            1          # has_theft_reports
        ]])
        
        print("\nSample Input (Johannesburg at 8 PM):")
        for i, col in enumerate(feature_columns):
            print(f"  {col}: {sample_data[0][i]}")
        
        # Make prediction
        sample_scaled = scaler.transform(sample_data)
        prediction = model.predict(sample_scaled)[0]
        
        print(f"\n✅ Prediction Successful!")
        print(f"Risk Level: {prediction:.4f} (0 = safe, 1 = dangerous)")
        
        # Interpret risk level
        if prediction < 0.3:
            risk_category = "LOW"
        elif prediction < 0.6:
            risk_category = "MEDIUM"
        else:
            risk_category = "HIGH"
        
        print(f"Risk Category: {risk_category}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install joblib scikit-learn numpy")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_model_integration():
    """Test model integration with application."""
    print("\n" + "="*60)
    print("TEST 3: Model Integration Test")
    print("="*60)
    
    try:
        import joblib
        import numpy as np
        from pathlib import Path
        
        # Find model
        model_paths = ['saferoute_model.pkl', 'models/saferoute_model.pkl', 'data/saferoute_model.pkl']
        model_path = next((p for p in model_paths if Path(p).exists()), None)
        
        if not model_path:
            print("⚠️  Model not found, skipping integration test")
            return None
        
        # Load model
        model_artifacts = joblib.load(model_path)
        model = model_artifacts['model']
        scaler = model_artifacts['scaler']
        
        # Test multiple locations
        test_locations = [
            {"name": "Johannesburg CBD (Night)", "lat": -26.2041, "lng": 28.0473, "hour": 22, "night": 1},
            {"name": "Sandton (Day)", "lat": -26.1076, "lng": 28.0567, "hour": 14, "night": 0},
            {"name": "Soweto (Evening)", "lat": -26.2678, "lng": 27.8546, "hour": 19, "night": 1},
        ]
        
        print("\nTesting predictions for multiple locations:")
        print("-"*60)
        
        for loc in test_locations:
            sample = np.array([[
                loc['lat'], loc['lng'], loc['hour'], 5, 2, 0, loc['night'], 2, 1, 1, 0
            ]])
            
            sample_scaled = scaler.transform(sample)
            prediction = model.predict(sample_scaled)[0]
            
            risk = "HIGH" if prediction > 0.6 else "MEDIUM" if prediction > 0.3 else "LOW"
            print(f"\n{loc['name']}:")
            print(f"  Coordinates: ({loc['lat']:.4f}, {loc['lng']:.4f})")
            print(f"  Risk Score: {prediction:.4f}")
            print(f"  Risk Level: {risk}")
        
        print("\n✅ Integration test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n🚀 SafeRoute AI - OBS & Model Verification")
    print("="*60)
    
    results = {
        'obs': test_obs_connection(),
        'model': test_trained_model(),
        'integration': test_model_integration()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result == "skipped":
            status = "⚠️  SKIPPED (Python 3.12 compatibility)"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        
        print(f"{test_name.upper()}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    total = len([r for r in results.values() if r is not None])
    
    print("\n" + "="*60)
    if passed == total and total > 0:
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Your OBS bucket is accessible")
        print("✅ Your trained model works correctly")
        print("✅ Model integration is functional")
        print("\nYour SafeRoute AI application is ready to use!")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("="*60)
        print("\nPlease review the errors above and:")
        print("1. Ensure OBS SDK is installed: pip install esdk-obs-python")
        print("2. Ensure ML libraries are installed: pip install joblib scikit-learn")
        print("3. Ensure saferoute_model.pkl is in the project directory")
        print("4. Check your .env file has correct credentials")
    
    print("\n" + "="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
