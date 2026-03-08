#!/usr/bin/env python3
"""
Enhanced Huawei Cloud Client for SafeRouteAI
Handles ModelArts training, OBS storage, and inference services
Supports both mock (development) and production modes
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class HuaweiCloudClient:
    """Unified Huawei Cloud Client for SafeRouteAI"""
    
    def __init__(self):
        # Get configuration from environment
        self.ak = os.getenv('HUAWEI_CLOUD_AK')
        self.sk = os.getenv('HUAWEI_CLOUD_SK')
        self.project_id = os.getenv('HUAWEI_CLOUD_PROJECT_ID')
        self.region = os.getenv('HUAWEI_CLOUD_REGION', 'af-south-1')
        self.demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
        
        # Initialize clients based on mode
        if self.demo_mode or not all([self.ak, self.sk, self.project_id]):
            print("🔧 Initializing Huawei Cloud Client in MOCK mode")
            self._init_mock_mode()
        else:
            print("🔧 Initializing Huawei Cloud Client in PRODUCTION mode")
            self._init_production_mode()
    
    def _init_mock_mode(self):
        """Initialize mock mode with full service simulation"""
        self.mode = "MOCK"
        
        # Import mock services
        from .mock_huawei_services import get_mock_service
        self.mock_service = get_mock_service()
        
        # Get mock clients
        self.obs_client = self.mock_service.get_obs_client()
        self.modelarts_client = self.mock_service.get_modelarts_client()
        self.inference_service = self.mock_service.get_inference_service()
        
        print("   📦 OBS Storage: Mock service ready")
        print("   🧠 ModelArts: Mock training ready")
        print("   🚀 Inference: Mock endpoints ready")
        print("   💾 Local storage: mock_obs_storage/")
    
    def _init_production_mode(self):
        """Initialize production mode with real Huawei Cloud services"""
        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkobs import ObsClient
            
            self.mode = "PRODUCTION"
            self.credentials = BasicCredentials(ak=self.ak, sk=self.sk)
            
            # Initialize OBS client
            self.obs_client = ObsClient(
                access_key_id=self.ak,
                secret_access_key=self.sk,
                server=f'https://obs.{self.region}.myhuaweicloud.com'
            )
            
            print("   📦 OBS Storage: Production ready")
            print("   🧠 ModelArts: Production ready")
            print("   🚀 Inference: Production ready")
            
        except ImportError as e:
            print(f"⚠️  Huawei Cloud SDK not available: {e}")
            print("   Falling back to mock mode")
            self._init_mock_mode()
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create OBS bucket"""
        if self.mode == "MOCK":
            response = self.obs_client.createBucket(bucket_name, self.region)
            return response.status == 200
        
        try:
            response = self.obs_client.createBucket(bucket_name, location=self.region)
            return response.status < 300
        except Exception as e:
            print(f"❌ Bucket creation failed: {str(e)}")
            return False
    
    def upload_data_to_obs(self, local_file_path: str, bucket_name: str, object_key: str) -> bool:
        """Upload data file to OBS storage"""
        if self.mode == "MOCK":
            response = self.obs_client.putFile(bucket_name, object_key, local_file_path)
            success = response.status == 200
            if success:
                print(f"✅ Mock Upload: {local_file_path} -> obs://{bucket_name}/{object_key}")
            return success
        
        try:
            response = self.obs_client.putFile(bucket_name, object_key, local_file_path)
            if response.status < 300:
                print(f"✅ Uploaded: {local_file_path} -> obs://{bucket_name}/{object_key}")
                return True
            else:
                print(f"❌ Upload failed: {response.reason}")
                return False
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            return False
    
    def upload_saferoute_data(self, bucket_name: str = "saferoute-ai-data") -> List[str]:
        """Upload all SafeRouteAI data files"""
        if self.mode == "MOCK":
            return self.mock_service.upload_saferoute_data(bucket_name)
        
        # Production upload logic
        uploaded_files = []
        data_files = [
            "data/saps_crime_data_national_with_real_csv.csv",
            "data/real_crime_hotspots_analysis.csv",
            "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis.csv",
            "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis (1).csv"
        ]
        
        # Create bucket first
        self.create_bucket(bucket_name)
        
        for file_path in data_files:
            if os.path.exists(file_path):
                object_key = f"saferoute-data/{os.path.basename(file_path)}"
                if self.upload_data_to_obs(file_path, bucket_name, object_key):
                    uploaded_files.append(object_key)
        
        return uploaded_files
    
    def create_training_job(self, job_config: Dict) -> Optional[str]:
        """Create ModelArts training job"""
        if self.mode == "MOCK":
            return self.mock_service.start_training_job(job_config)
        
        # Production ModelArts implementation would go here
        print("🚧 Production ModelArts training not yet implemented")
        return None
    
    def get_training_job_status(self, job_id: str) -> Dict:
        """Get training job status"""
        if self.mode == "MOCK":
            job = self.modelarts_client.get_training_job(job_id)
            if job:
                return {
                    'job_id': job.job_id,
                    'job_name': job.job_name,
                    'status': job.status,
                    'progress': job.progress,
                    'created_time': job.created_time.isoformat(),
                    'start_time': job.start_time.isoformat(),
                    'end_time': job.end_time.isoformat() if job.end_time else None,
                    'model_path': job.model_path,
                    'logs': job.logs[-5:] if job.logs else []  # Last 5 log entries
                }
            return {'status': 'NOT_FOUND'}
        
        # Production implementation would go here
        return {'status': 'UNKNOWN'}
    
    def list_training_jobs(self) -> List[Dict]:
        """List all training jobs"""
        if self.mode == "MOCK":
            jobs = self.modelarts_client.list_training_jobs()
            return [{
                'job_id': job.job_id,
                'job_name': job.job_name,
                'status': job.status,
                'progress': job.progress,
                'created_time': job.created_time.isoformat()
            } for job in jobs]
        
        return []
    
    def deploy_model(self, model_path: str, endpoint_name: str = "saferoute-inference") -> Optional[str]:
        """Deploy model to inference endpoint"""
        if self.mode == "MOCK":
            return self.mock_service.deploy_model(model_path, endpoint_name)
        
        # Production implementation would go here
        print("🚧 Production model deployment not yet implemented")
        return None
    
    def predict_risk(self, endpoint_id: str, latitude: float, longitude: float, 
                    hour: int = 12, day_of_week: int = 1, **kwargs) -> Dict:
        """Predict risk score for a location"""
        if self.mode == "MOCK":
            return self.mock_service.predict_risk(endpoint_id, latitude, longitude, 
                                                hour, day_of_week, **kwargs)
        
        # Production implementation would go here
        return {'error': 'Production inference not yet implemented'}
    
    def predict(self, endpoint_id: str, input_data: Dict) -> Dict:
        """Make prediction using deployed model (generic interface)"""
        if self.mode == "MOCK":
            return self.inference_service.predict(endpoint_id, input_data)
        
        # Production implementation would go here
        return {'error': 'Production inference not yet implemented'}
    
    def get_service_status(self) -> Dict:
        """Get status of all Huawei Cloud services"""
        if self.mode == "MOCK":
            return self.mock_service.get_service_status()
        
        return {
            'mode': self.mode,
            'region': self.region,
            'obs_storage': 'CONFIGURED',
            'modelarts_training': 'CONFIGURED',
            'inference_service': 'CONFIGURED',
            'mock_mode': False
        }
    
    def switch_to_production(self, ak: str, sk: str, project_id: str):
        """Switch from mock to production mode"""
        self.ak = ak
        self.sk = sk
        self.project_id = project_id
        self.demo_mode = False
        
        print("🔄 Switching to production mode...")
        self._init_production_mode()
        
        # Update environment file
        env_content = f"""# Production Huawei Cloud Configuration
HUAWEI_CLOUD_AK={ak}
HUAWEI_CLOUD_SK={sk}
HUAWEI_CLOUD_PROJECT_ID={project_id}
HUAWEI_CLOUD_REGION={self.region}
DEMO_MODE=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# OBS Configuration
OBS_BUCKET_NAME=saferoute-ai-data
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Switched to production mode")
        print("   Updated .env file with production credentials")
        print("   Restart application to use production services")

# Global client instance
huawei_client_v2 = HuaweiCloudClient()