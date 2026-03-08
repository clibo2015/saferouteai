#!/usr/bin/env python3
"""
Mock Huawei Cloud Services for SafeRouteAI Development
Simulates ModelArts, OBS, and other Huawei services locally
"""
import os
import json
import time
import uuid
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

class MockOBSClient:
    """Mock Object Storage Service (OBS) Client"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, server: str):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.server = server
        self.mock_storage_path = Path("mock_obs_storage")
        self.mock_storage_path.mkdir(exist_ok=True)
        
        # Initialize mock buckets metadata
        self.buckets_file = self.mock_storage_path / "buckets.json"
        if not self.buckets_file.exists():
            self._save_buckets({})
    
    def _load_buckets(self) -> Dict:
        """Load buckets metadata"""
        try:
            with open(self.buckets_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_buckets(self, buckets: Dict):
        """Save buckets metadata"""
        with open(self.buckets_file, 'w') as f:
            json.dump(buckets, f, indent=2)
    
    def listBuckets(self):
        """List all buckets"""
        buckets = self._load_buckets()
        
        class MockResponse:
            def __init__(self, buckets_data):
                self.status = 200
                self.reason = "OK"
                self.body = MockBody(buckets_data)
        
        class MockBody:
            def __init__(self, buckets_data):
                self.buckets = [MockBucket(name, data) for name, data in buckets_data.items()]
        
        class MockBucket:
            def __init__(self, name, data):
                self.name = name
                self.creation_date = data.get('creation_date', datetime.now().isoformat())
                self.location = data.get('location', 'af-south-1')
        
        return MockResponse(buckets)
    
    def createBucket(self, bucket_name: str, location: str = 'af-south-1'):
        """Create a new bucket"""
        buckets = self._load_buckets()
        
        if bucket_name in buckets:
            class MockResponse:
                def __init__(self):
                    self.status = 409
                    self.reason = "Bucket already exists"
            return MockResponse()
        
        # Create bucket directory
        bucket_path = self.mock_storage_path / bucket_name
        bucket_path.mkdir(exist_ok=True)
        
        # Save bucket metadata
        buckets[bucket_name] = {
            'creation_date': datetime.now().isoformat(),
            'location': location,
            'objects': {}
        }
        self._save_buckets(buckets)
        
        class MockResponse:
            def __init__(self):
                self.status = 200
                self.reason = "OK"
        
        return MockResponse()
    
    def putFile(self, bucket_name: str, object_key: str, file_path: str):
        """Upload a file to bucket"""
        buckets = self._load_buckets()
        
        if bucket_name not in buckets:
            class MockResponse:
                def __init__(self):
                    self.status = 404
                    self.reason = "Bucket not found"
            return MockResponse()
        
        # Copy file to mock storage
        bucket_path = self.mock_storage_path / bucket_name
        object_path = bucket_path / object_key.replace('/', '_')
        object_path.parent.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(file_path):
            shutil.copy2(file_path, object_path)
            
            # Update metadata
            buckets[bucket_name]['objects'][object_key] = {
                'size': os.path.getsize(file_path),
                'last_modified': datetime.now().isoformat(),
                'local_path': str(object_path)
            }
            self._save_buckets(buckets)
        
        class MockResponse:
            def __init__(self):
                self.status = 200
                self.reason = "OK"
        
        return MockResponse()
    
    def getObject(self, bucket_name: str, object_key: str):
        """Download object from bucket"""
        buckets = self._load_buckets()
        
        if bucket_name not in buckets or object_key not in buckets[bucket_name]['objects']:
            class MockResponse:
                def __init__(self):
                    self.status = 404
                    self.reason = "Object not found"
            return MockResponse()
        
        object_info = buckets[bucket_name]['objects'][object_key]
        
        class MockResponse:
            def __init__(self, local_path):
                self.status = 200
                self.reason = "OK"
                self.body = MockObjectBody(local_path)
        
        class MockObjectBody:
            def __init__(self, local_path):
                self.local_path = local_path
            
            def read(self):
                with open(self.local_path, 'rb') as f:
                    return f.read()
        
        return MockResponse(object_info['local_path'])

class MockModelArtsTrainingJob:
    """Mock ModelArts Training Job"""
    
    def __init__(self, job_config: Dict):
        self.job_id = f"mock-job-{uuid.uuid4().hex[:8]}"
        self.job_name = job_config.get('job_name', f'saferoute-training-{int(time.time())}')
        self.status = "RUNNING"
        self.config = job_config
        self.created_time = datetime.now()
        self.start_time = datetime.now()
        self.end_time = None
        self.progress = 0
        self.logs = []
        self.model_path = None
        
    def update_progress(self):
        """Simulate training progress"""
        if self.status == "RUNNING":
            self.progress = min(100, self.progress + np.random.randint(5, 15))
            
            if self.progress >= 100:
                self.status = "COMPLETED"
                self.end_time = datetime.now()
                self._generate_mock_model()
            
            # Add mock logs
            self.logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': f'Training progress: {self.progress}%'
            })
    
    def _generate_mock_model(self):
        """Generate a mock trained model"""
        # Create mock model directory
        model_dir = Path("mock_obs_storage") / "saferoute-ai-data" / "models" / self.job_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Train a simple model with mock data
        np.random.seed(42)
        X = np.random.rand(1000, 8)  # 8 features
        y = np.random.rand(1000) * 10  # Risk scores 0-10
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        # Save model
        model_path = model_dir / "saferoute_risk_model.joblib"
        joblib.dump(model, model_path)
        
        # Save model metadata
        metadata = {
            'model_type': 'RandomForestRegressor',
            'features': ['latitude', 'longitude', 'hour', 'day_of_week', 
                        'crime_density', 'population_density', 'economic_index', 'road_type'],
            'target': 'risk_score',
            'accuracy_metrics': {
                'mse': 0.85,
                'r2_score': 0.92,
                'training_samples': 1000
            },
            'created_at': datetime.now().isoformat(),
            'job_id': self.job_id
        }
        
        with open(model_dir / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.model_path = str(model_path)
        
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': f'Model saved to: {self.model_path}'
        })

class MockModelArtsClient:
    """Mock ModelArts Client"""
    
    def __init__(self):
        self.jobs: Dict[str, MockModelArtsTrainingJob] = {}
        self.jobs_file = Path("mock_obs_storage") / "training_jobs.json"
        self._load_jobs()
    
    def _load_jobs(self):
        """Load existing jobs"""
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                    for job_id, job_data in jobs_data.items():
                        job = MockModelArtsTrainingJob(job_data['config'])
                        job.job_id = job_id
                        job.status = job_data['status']
                        job.progress = job_data['progress']
                        job.logs = job_data.get('logs', [])
                        self.jobs[job_id] = job
            except:
                pass
    
    def _save_jobs(self):
        """Save jobs to file"""
        jobs_data = {}
        for job_id, job in self.jobs.items():
            jobs_data[job_id] = {
                'config': job.config,
                'status': job.status,
                'progress': job.progress,
                'logs': job.logs,
                'created_time': job.created_time.isoformat(),
                'model_path': job.model_path
            }
        
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs_data, f, indent=2)
    
    def create_training_job(self, job_config: Dict) -> str:
        """Create a new training job"""
        job = MockModelArtsTrainingJob(job_config)
        self.jobs[job.job_id] = job
        self._save_jobs()
        
        print(f"✅ Mock Training Job Created: {job.job_id}")
        print(f"   Job Name: {job.job_name}")
        print(f"   Status: {job.status}")
        
        return job.job_id
    
    def get_training_job(self, job_id: str) -> Optional[MockModelArtsTrainingJob]:
        """Get training job by ID"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.update_progress()  # Simulate progress
            self._save_jobs()
            return job
        return None
    
    def list_training_jobs(self) -> List[MockModelArtsTrainingJob]:
        """List all training jobs"""
        # Update progress for running jobs
        for job in self.jobs.values():
            if job.status == "RUNNING":
                job.update_progress()
        
        self._save_jobs()
        return list(self.jobs.values())
    
    def delete_training_job(self, job_id: str) -> bool:
        """Delete a training job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            return True
        return False

class MockModelArtsInference:
    """Mock ModelArts Inference Service"""
    
    def __init__(self):
        self.endpoints = {}
        self.endpoints_file = Path("mock_obs_storage") / "inference_endpoints.json"
        self._load_endpoints()
    
    def _load_endpoints(self):
        """Load existing endpoints"""
        if self.endpoints_file.exists():
            try:
                with open(self.endpoints_file, 'r') as f:
                    self.endpoints = json.load(f)
            except:
                pass
    
    def _save_endpoints(self):
        """Save endpoints to file"""
        self.endpoints_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.endpoints_file, 'w') as f:
            json.dump(self.endpoints, f, indent=2)
    
    def create_endpoint(self, model_path: str, endpoint_name: str) -> str:
        """Create inference endpoint"""
        endpoint_id = f"mock-endpoint-{uuid.uuid4().hex[:8]}"
        
        self.endpoints[endpoint_id] = {
            'name': endpoint_name,
            'model_path': model_path,
            'status': 'RUNNING',
            'created_at': datetime.now().isoformat(),
            'url': f"https://mock-inference.af-south-1.myhuaweicloud.com/{endpoint_id}"
        }
        
        self._save_endpoints()
        
        print(f"✅ Mock Inference Endpoint Created: {endpoint_id}")
        print(f"   Name: {endpoint_name}")
        print(f"   URL: {self.endpoints[endpoint_id]['url']}")
        
        return endpoint_id
    
    def predict(self, endpoint_id: str, input_data: Dict) -> Dict:
        """Make prediction using endpoint"""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        # Mock prediction logic
        features = input_data.get('features', [])
        
        if len(features) >= 2:  # lat, lon at minimum
            lat, lon = features[0], features[1]
            
            # Simple risk calculation based on location
            base_risk = abs(lat * lon) % 10
            
            # Add some randomness and other factors
            if len(features) > 2:
                hour = features[2] if len(features) > 2 else 12
                day_of_week = features[3] if len(features) > 3 else 1
                
                # Higher risk at night and weekends
                time_factor = 1.5 if hour < 6 or hour > 22 else 1.0
                weekend_factor = 1.3 if day_of_week >= 5 else 1.0
                
                base_risk *= time_factor * weekend_factor
            
            risk_score = min(10.0, max(0.0, base_risk))
        else:
            risk_score = 5.0  # Default medium risk
        
        return {
            'prediction': risk_score,
            'confidence': 0.85 + np.random.random() * 0.1,
            'risk_level': 'LOW' if risk_score < 3 else 'MEDIUM' if risk_score < 7 else 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'endpoint_id': endpoint_id
        }

class MockHuaweiCloudService:
    """Main Mock Huawei Cloud Service Manager"""
    
    def __init__(self):
        self.obs_client = None
        self.modelarts_client = MockModelArtsClient()
        self.inference_service = MockModelArtsInference()
        self.mock_enabled = True
        
        print("🔧 Mock Huawei Cloud Services Initialized")
        print("   📦 OBS Storage: Ready")
        print("   🧠 ModelArts Training: Ready")
        print("   🚀 Inference Service: Ready")
    
    def get_obs_client(self, access_key_id: str = "mock_ak", 
                      secret_access_key: str = "mock_sk", 
                      server: str = "https://obs.af-south-1.myhuaweicloud.com") -> MockOBSClient:
        """Get mock OBS client"""
        if not self.obs_client:
            self.obs_client = MockOBSClient(access_key_id, secret_access_key, server)
        return self.obs_client
    
    def get_modelarts_client(self) -> MockModelArtsClient:
        """Get mock ModelArts client"""
        return self.modelarts_client
    
    def get_inference_service(self) -> MockModelArtsInference:
        """Get mock inference service"""
        return self.inference_service
    
    def upload_saferoute_data(self, bucket_name: str = "saferoute-ai-data") -> List[str]:
        """Upload SafeRouteAI data to mock OBS"""
        obs = self.get_obs_client()
        
        # Create bucket
        obs.createBucket(bucket_name, "af-south-1")
        
        # Upload data files
        data_files = [
            "data/saps_crime_data_national_with_real_csv.csv",
            "data/real_crime_hotspots_analysis.csv",
            "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis.csv",
            "South Africa Crime Hotspots Analysis - South Africa Crime Hotspots Analysis (1).csv"
        ]
        
        uploaded_files = []
        for file_path in data_files:
            if os.path.exists(file_path):
                object_key = f"saferoute-data/{os.path.basename(file_path)}"
                response = obs.putFile(bucket_name, object_key, file_path)
                if response.status == 200:
                    uploaded_files.append(object_key)
                    print(f"✅ Uploaded: {file_path} -> {object_key}")
                else:
                    print(f"❌ Failed to upload: {file_path}")
            else:
                print(f"⚠️  File not found: {file_path}")
        
        return uploaded_files
    
    def start_training_job(self, job_config: Dict) -> str:
        """Start a mock training job"""
        return self.modelarts_client.create_training_job(job_config)
    
    def deploy_model(self, model_path: str, endpoint_name: str = "saferoute-inference") -> str:
        """Deploy model to mock inference endpoint"""
        return self.inference_service.create_endpoint(model_path, endpoint_name)
    
    def predict_risk(self, endpoint_id: str, latitude: float, longitude: float, 
                    hour: int = 12, day_of_week: int = 1, **kwargs) -> Dict:
        """Predict risk using mock inference"""
        input_data = {
            'features': [latitude, longitude, hour, day_of_week]
        }
        
        # Add additional features if provided
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                input_data['features'].append(value)
        
        return self.inference_service.predict(endpoint_id, input_data)
    
    def get_service_status(self) -> Dict:
        """Get status of all mock services"""
        obs = self.get_obs_client()
        buckets = obs.listBuckets()
        training_jobs = self.modelarts_client.list_training_jobs()
        
        return {
            'obs_storage': {
                'status': 'RUNNING',
                'buckets_count': len(buckets.body.buckets) if buckets.body.buckets else 0,
                'storage_path': str(obs.mock_storage_path)
            },
            'modelarts_training': {
                'status': 'RUNNING',
                'total_jobs': len(training_jobs),
                'running_jobs': len([j for j in training_jobs if j.status == 'RUNNING']),
                'completed_jobs': len([j for j in training_jobs if j.status == 'COMPLETED'])
            },
            'inference_service': {
                'status': 'RUNNING',
                'endpoints_count': len(self.inference_service.endpoints)
            },
            'mock_mode': True,
            'region': 'af-south-1'
        }

# Global mock service instance
mock_huawei_service = MockHuaweiCloudService()

def get_mock_service() -> MockHuaweiCloudService:
    """Get the global mock service instance"""
    return mock_huawei_service