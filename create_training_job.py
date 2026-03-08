#!/usr/bin/env python3
"""
Script to create a ModelArts training job programmatically using REST API.
The ModelArts SDK doesn't support af-south-1 region, so we use REST API directly.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_training_job():
    """Create a ModelArts training job using REST API."""
    
    # Get credentials from environment
    access_key = os.getenv('HUAWEI_CLOUD_AK')
    secret_key = os.getenv('HUAWEI_CLOUD_SK')
    project_id = os.getenv('HUAWEI_CLOUD_PROJECT_ID')
    region = os.getenv('HUAWEI_CLOUD_REGION', 'af-south-1')
    
    if not all([access_key, secret_key, project_id]):
        raise ValueError("Missing required credentials in .env file")
    
    # Normalize region name
    region_normalized = region.lower().replace('_', '-')
    if 'johannesburg' in region_normalized:
        region_normalized = 'af-south-1'
    
    print(f"Creating training job in region: {region_normalized}")
    print(f"Project ID: {project_id}")
    print(f"Access Key: {access_key[:8]}...")
    
    # ModelArts API endpoint
    modelarts_endpoint = f"https://modelarts.{region_normalized}.myhuaweicloud.com"
    
    # Training job configuration matching your console setup
    job_config = {
        "job_name": "saferoute-training-job-sdk",
        "job_desc": "SafeRoute AI model training - created via SDK",
        "config": {
            "worker_server_num": 1,
            "app_url": "/saferoute-ai-data/training-data/",
            "boot_file_url": "/saferoute-ai-data/training-data/train.py",
            "data_url": "/saferoute-ai-data/crime-data/",
            "train_url": "/saferoute-ai-data/models/",
            "log_url": "/saferoute-ai-data/logs/",
            "engine_id": 1,  # TensorFlow
            "spec_id": 1,    # GPU instance
            "max_duration": 3600  # 1 hour auto-stop
        },
        "data_source": [
            {
                "type": "obs",
                "data_url": "/saferoute-ai-data/crime-data/"
            }
        ],
        "outputs": [
            {
                "type": "obs",
                "obs_url": "/saferoute-ai-data/models/"
            }
        ]
    }
    
    print("\n" + "="*60)
    print("Training Job Configuration:")
    print("="*60)
    print(json.dumps(job_config, indent=2))
    print("="*60 + "\n")
    
    try:
        print("Authenticating with Huawei Cloud...")
        
        # Use AK/SK authentication with signature
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdkcore.http.http_client import HttpClient
        from huaweicloudsdkcore.http.http_config import HttpConfig
        from huaweicloudsdkcore.region.region import Region
        
        # Create credentials
        credentials = BasicCredentials(access_key, secret_key, project_id)
        
        # Create HTTP config
        config = HttpConfig.get_default_config()
        config.ignore_ssl_verification = False
        
        # Create HTTP client
        http_client = HttpClient(config)
        
        print("Submitting training job to ModelArts...")
        
        # Prepare request
        url = f"{modelarts_endpoint}/v1/{project_id}/training-jobs"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Sign and send request
        from huaweicloudsdkcore.http.http_request import HttpRequest
        request = HttpRequest(
            method="POST",
            url=url,
            headers=headers,
            body=json.dumps(job_config)
        )
        
        # Add authentication
        credentials.process_auth_request(request)
        
        # Send request
        response = http_client.do_request_sync(request)
        
        if response.status_code in [200, 201]:
            job_response = json.loads(response.content)
            
            print("\n" + "="*60)
            print("✅ Training Job Created Successfully!")
            print("="*60)
            print(f"Job ID: {job_response.get('job_id', 'N/A')}")
            print(f"Job Name: {job_response.get('job_name', 'N/A')}")
            print(f"Status: {job_response.get('status', 'N/A')}")
            print("="*60 + "\n")
            
            print("📊 Monitor your job:")
            print(f"   - Console: https://console.huaweicloud.com/modelarts/?region={region_normalized}#/trainingJobs")
            print("\n⚠️  Remember:")
            print("   - Auto-stop is set to 1 hour")
            print("   - Cost: ~$4.72/hour for GPU")
            print("   - Job may queue if no GPU resources available")
            print("   - You can manually stop it anytime to save costs")
            
            return job_response
        else:
            error_msg = response.content.decode('utf-8') if response.content else 'No error details'
            raise Exception(f"API Error: {response.status_code} - {error_msg}")
        
    except ImportError as e:
        print(f"\n❌ Missing required SDK: {e}")
        print("\nPlease install: pip install huaweicloudsdkcore")
        return None
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ Error Creating Training Job")
        print("="*60)
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print("\nPossible reasons:")
        print("  1. No GPU resources available in af-south-1")
        print("  2. IAM permissions issue")
        print("  3. OBS bucket access issue")
        print("  4. Invalid API endpoint or configuration")
        print("\nTroubleshooting:")
        print("  - Check ModelArts console for more details")
        print("  - Verify IAM role has ModelArts permissions")
        print("  - The 7-hour queue suggests no resources available")
        print("="*60 + "\n")
        return None

if __name__ == "__main__":
    print("\n🚀 ModelArts Training Job Creator (REST API)")
    print("="*60 + "\n")
    
    job = create_training_job()
    
    if job:
        print("\n✅ Script completed successfully!")
    else:
        print("\n⚠️  Job creation encountered issues.")
        print("Check the error messages above for details.")
        print("\n💡 Note: The 7-hour queue you experienced suggests")
        print("   af-south-1 has no GPU resources available currently.")
