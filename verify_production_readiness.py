import os
import sys
import logging
import asyncio
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Verification")
logging.getLogger("src.modelarts_integration").setLevel(logging.DEBUG)
logging.getLogger("src.obs_manager").setLevel(logging.DEBUG)

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

def verify_system():
    print("="*60)
    print(f"SafeRouteAI - Final Production Verification | CWD: {os.getcwd()}")
    print("="*60)
    
    # Check model file exists
    print(f"Checking for saferoute_model.pkl in {os.getcwd()}...")
    if os.path.exists("saferoute_model.pkl"):
        print("   -> Found saferoute_model.pkl")
        try:
            import joblib
            m = joblib.load("saferoute_model.pkl")
            print("   -> Manual joblib.load() SUCCESS")
        except Exception as e:
            print(f"   -> Manual joblib.load() FAILED: {e}")
    else:
        print("   -> saferoute_model.pkl NOT FOUND in root")
    
    results = {}

    # 1. Configuration
    print("\n[1] Verifying Configuration...")
    try:
        from src.config import settings
        status = settings.get_production_status()
        print(f"   Mode: {'Production' if status['production_mode'] else 'Demo'}")
        print(f"   Credentials Present: {status['has_credentials']}")
        print(f"   Region: {status['region']}")
        
        results['config'] = 'PASS' if status['production_mode'] and status['has_credentials'] else 'FAIL'
        
        if not settings.eskom_se_push_key:
             print("   ! WARNING: ESKOM_SE_PUSH_KEY is missing. Load shedding data will be unavailable.")
             results['eskom_key'] = 'MISSING'
        else:
             results['eskom_key'] = 'PRESENT'

    except Exception as e:
        print(f"   ! CRITICAL ERROR: {e}")
        results['config'] = 'CRITICAL'
        return results

    # 2. OBS Connectivity
    print("\n[2] Verifying OBS Connectivity...")
    try:
        from src.obs_manager import obs_manager
        if obs_manager.client:
            print(f"   OBS Client Initialized: Yes")
            resp = obs_manager.client.listBuckets()
            if resp.status < 300 and resp.body.buckets:
                print(f"   Success: Listed {len(resp.body.buckets)} buckets.")
                print(f"   Target Bucket '{settings.obs_bucket_name}' found: {any(b.name == settings.obs_bucket_name for b in resp.body.buckets)}")
                results['obs'] = 'PASS'
            else:
                 print(f"   Warning: List buckets failed or empty. Status: {resp.status}")
                 results['obs'] = 'WARNING'
        else:
            print("   Failure: OBS Client not initialized (check credentials).")
            results['obs'] = 'FAIL'
    except Exception as e:
        print(f"   ! OBS ERROR: {e}")
        results['obs'] = 'FAIL'

    # 3. Model Loading
    print("\n[3] Verifying AI Model...")
    try:
        from src.modelarts_integration import modelarts_engine
        # Check if local model is loaded/trained
        if modelarts_engine.local_model.is_trained:
            print("   Success: Local SafeRoute model is loaded/trained.")
            results['model'] = 'PASS'
        else:
            print("   Failure: Model not loaded.")
            print(f"   Debug: Search paths were {[p for p in ['saferoute_model.pkl', 'models/saferoute_model.pkl', 'data/saferoute_model.pkl']]}")
            results['model'] = 'FAIL'
    except Exception as e:
        print(f"   ! MODEL ERROR: {e}")
        results['model'] = 'FAIL'

    # 4. Edge AI Object Detection
    print("\n[4] Verifying Edge AI (YOLOv8)...")
    try:
        from src.edge_ai_processor import EdgeAIProcessor
        import numpy as np
        import cv2
        
        processor = EdgeAIProcessor()
        # Create a dummy black image
        dummy_frame = np.array(np.zeros((640, 640, 3), dtype=np.uint8))
        _, buffer = cv2.imencode('.jpg', dummy_frame)
        
        result = processor.process_frame(buffer.tobytes())
        hazards = result.get("hazards", [])
        
        print("   Success: YOLOv8 initialized and processed frame.")
        print(f"   Inference Hazards Detected: {len(hazards)} (Expected 0 for blank image)")
        
        if result.get("error"):
             print(f"   ! Edge AI Warning: {result.get('error')}")
             results['edge_ai'] = 'WARNING'
        else:
             results['edge_ai'] = 'PASS'

    except ImportError:
        print("   ! Failure: ultraalytics or opencv not installed.")
        results['edge_ai'] = 'FAIL'
    except Exception as e:
        print(f"   ! EDGE AI ERROR: {e}")
        results['edge_ai'] = 'FAIL'

    # 5. Real Data Integration (Map Kit & Eskom)
    print("\n[5] Verifying Data Integration...")
    try:
        from src.real_data_integration import RealDataIntegrator
        integrator = RealDataIntegrator()
        
        # Test Eskom
        print("   Testing Eskom API Connection...")
        eskom_data = integrator.get_eskom_load_shedding_data()
        print(f"   Eskom Status: {eskom_data.get('status', 'unknown')}")
        if eskom_data.get('status') == 'no_key':
            print("   -> Confirmed implementation handles missing key gracefully.")
            results['eskom_api'] = 'SKIPPED (No Key)'
        elif eskom_data.get('error'):
             print(f"   -> API Error: {eskom_data.get('error')}")
             results['eskom_api'] = 'FAIL'
        else:
             results['eskom_api'] = 'PASS'
             
    except Exception as e:
        print(f"   ! INTEGRATION ERROR: {e}")
        results['data_integration'] = 'FAIL'
        
    # 6. Routing Engine (Map Kit)
    print("\n[6] Verifying Routing Engine (Huawei Map Kit)...")
    try:
        from src.routing_engine import SafetyOptimizedRouter
        engine = SafetyOptimizedRouter()
        # Verify it has the API key
        if settings.huawei_map_api_key and settings.huawei_map_api_key != "demo_map_key":
             print("   Success: Real Map Kit API Key configured.")
             results['map_kit'] = 'PASS (Configured)'
        else:
             print("   Failure: Using demo/invalid Map Kit key.")
             results['map_kit'] = 'FAIL'
             
    except Exception as e:
        print(f"   ! ROUTING ERROR: {e}")
        results['map_kit'] = 'FAIL'

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for k, v in results.items():
        print(f"{k.upper():<20}: {v}")
    
    print("-" * 30)
    print("MANUAL CHECKS")
    if os.path.exists("saferoute_model.pkl"):
         try:
             import joblib
             joblib.load("saferoute_model.pkl")
             print("MANUAL_MODEL_LOAD   : PASS")
         except Exception as e:
             print(f"MANUAL_MODEL_LOAD   : FAIL ({e})")
    else:
         print("MANUAL_MODEL_LOAD   : FILE_MISSING")

    return results

if __name__ == "__main__":
    verify_system()
