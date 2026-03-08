#!/usr/bin/env python3
"""Quick status check for SafeRouteAI backend"""
import requests
import json

try:
    # Get training jobs
    response = requests.get('http://localhost:8003/training/jobs', timeout=5)
    jobs = response.json()['jobs']
    
    print(f"📊 Training Jobs: {len(jobs)} total")
    print("Recent jobs:")
    for job in jobs[-5:]:
        print(f"  - {job['job_name']} ({job['status']}) - {job['progress']}%")
    
    # Get service status
    response = requests.get('http://localhost:8003/status', timeout=5)
    status = response.json()
    
    print(f"\n🔧 Service Status:")
    print(f"  - OBS Storage: {status['obs_storage']['buckets_count']} buckets")
    print(f"  - ModelArts: {status['modelarts_training']['total_jobs']} jobs")
    print(f"  - Inference: {status['inference_service']['endpoints_count']} endpoints")
    print(f"  - Mode: {'Mock' if status['mock_mode'] else 'Production'}")
    
except Exception as e:
    print(f"❌ Error: {e}")