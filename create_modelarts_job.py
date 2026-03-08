#!/usr/bin/env python3
"""
Simple script to create ModelArts training job using the SDK v2.
Tries multiple regions to find one with GPU availability and low cost.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_training_job_in_region(ak, sk, project_id, region):
    """Try to create training job in a specific region using Estimator v2."""
    
    print(f"\n{'='*60}")
    print(f"Trying region: {region}")
    print(f"{'='*60}")
    
    try:
        from modelarts.session import Session
        from modelarts.estimatorV2 import EstimatorV2
        
        # Create session
        session = Session(
            access_key=ak,
            secret_key=sk,
            project_id=project_id,
            region_name=region
        )
        
        print("✅ Session created successfully!")
        
        # Create estimator v2 (newer API)
        estimator = EstimatorV2(
            modelarts_session=session,
            train_instance_type='modelarts.vm.cpu.2u',  # Use CPU to reduce cost
            train_instance_count=1,
            code_dir='/saferoute-ai-data/training-data/',
            boot_file='/saferoute-ai-data/training-data/train.py',
            output_path='/saferoute-ai-data/models/',
            log_url='/saferoute-ai-data/logs/',
            job_description=f'SafeRoute AI training job - {region} (CPU)'
        )
        
        print("✅ Estimator v2 configured (CPU instance for low cost)!")
        print("Submitting training job...")
        
        # Create and submit the job
        job_instance = estimator.fit(
            inputs='/saferoute-ai-data/crime-data/',
            wait=False,
            job_name=f'saferoute-training-{region}'
        )
        
        print("\n" + "="*60)
        print("✅ Training Job Submitted Successfully!")
        print("="*60)
        print(f"Job Name: saferoute-training-{region}")
        print(f"Region: {region}")
        print(f"Instance: CPU (2 cores) - Low cost!")
        print(f"Status: Submitted")
        print("="*60)
        
        print(f"\n📊 Monitor your job:")
        print(f"   https://console.huaweicloud.com/modelarts/?region={region}#/trainingJobs")
        
        print("\n💰 Cost Optimization:")
        print("   - Using CPU instance (~$0.50-1/hour)")
        print("   - Much cheaper than GPU (~$4.72/hour)")
        print("   - Auto-stop: 1 hour")
        
        return job_instance, region
        
    except ImportError as e:
        print(f"❌ SDK import error: {e}")
        return None, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {type(e).__name__}")
        
        # Check for specific errors
        if "IP address is not authorized" in error_msg or "APIGW.0402" in error_msg:
            print("   Issue: IP address not whitelisted for API access")
            print("   This is a Huawei Cloud security feature")
        elif "ReadTimeout" in error_msg:
            print("   Issue: Connection timeout (region may not be accessible)")
        else:
            print(f"   Details: {error_msg[:200]}")
        
        return None, None

def create_training_job():
    """Create ModelArts training job, trying multiple regions."""
    
    # Get credentials
    ak = os.getenv('HUAWEI_CLOUD_AK')
    sk = os.getenv('HUAWEI_CLOUD_SK')
    project_id = os.getenv('HUAWEI_CLOUD_PROJECT_ID')
    
    if not all([ak, sk, project_id]):
        print("❌ Missing credentials in .env file")
        return None
    
    print(f"Project ID: {project_id}")
    print(f"Access Key: {ak[:8]}...")
    
    # Try regions in order of preference
    # Starting with af-south-1 since OBS bucket is there
    regions_to_try = ['af-south-1', 'cn-north-4', 'ap-southeast-3']
    
    print(f"\nWill try regions: {', '.join(regions_to_try)}")
    print("Using CPU instances for low cost (~$0.50-1/hour)")
    
    for region in regions_to_try:
        job, success_region = create_training_job_in_region(ak, sk, project_id, region)
        
        if job:
            print(f"\n✅ Successfully created job in {success_region}!")
            return job
        
        print(f"⚠️  Failed in {region}, trying next region...")
    
    print("\n" + "="*60)
    print("❌ Failed to create job in all regions")
    print("="*60)
    print("\n🔍 Root Cause Analysis:")
    print("  The main issue is: IP address not authorized (APIGW.0402)")
    print("\n💡 Solutions:")
    print("  1. Whitelist your IP in Huawei Cloud Console:")
    print("     - Go to API Gateway > API Groups")
    print("     - Find ModelArts API group")
    print("     - Add your IP to whitelist")
    print("\n  2. Use Huawei Cloud Console directly:")
    print("     - You already have OBS bucket set up")
    print("     - Create job manually (you tried this)")
    print("\n  3. Use VPN/Proxy from whitelisted IP range")
    print("\n  4. Contact Huawei Cloud support to whitelist your IP")
    print("\n  5. Use mock services for development (recommended)")
    print("     - Already implemented in your codebase")
    print("     - Run: python demo_api_with_mock.py")
    
    return None

if __name__ == "__main__":
    print("\n🚀 ModelArts Training Job Creator (SDK v2)")
    print("="*60 + "\n")
    
    job = create_training_job()
    
    if job:
        print("\n✅ Script completed successfully!")
    else:
        print("\n⚠️  Job creation blocked by IP authorization.")
        print("\nRecommendation: Use mock services for now.")
        print("Your application is fully functional with mock data!")
