#!/usr/bin/env python3
"""
SafeRouteAI Production Deployment Script
Executes complete transition from demo to production with cost optimization
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from production_orchestrator import production_orchestrator
from config import settings

def setup_logging():
    """Set up logging for deployment"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f"data/deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def print_banner():
    """Print deployment banner"""
    print("=" * 80)
    print("🚀 SafeRouteAI - Production Deployment")
    print("💰 Cost-Optimized Huawei Cloud Setup")
    print("🌍 AF-Johannesburg Region")
    print("=" * 80)
    print()

def print_pre_deployment_info():
    """Print pre-deployment information"""
    print("📋 Pre-Deployment Information")
    print("-" * 40)
    
    env_summary = settings.get_environment_summary()
    
    print(f"Current Mode: {env_summary['mode']}")
    print(f"Region: {env_summary['region']}")
    print(f"Budget Limit: ${env_summary['cost_management']['budget_limit']}")
    print(f"Auto-scaling: {'Enabled' if env_summary['cost_management']['auto_scaling'] else 'Disabled'}")
    print(f"Credentials: {'✅ Configured' if env_summary['credentials_configured'] else '❌ Missing'}")
    print()
    
    if not env_summary['credentials_configured']:
        print("⚠️  WARNING: Huawei Cloud credentials not configured!")
        print("   Please run: python setup_huawei_cloud.py")
        print("   Or manually configure credentials in .env file")
        print()
        return False
    
    return True

def print_deployment_summary(summary):
    """Print deployment summary"""
    print("=" * 80)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 80)
    
    status_icon = "✅" if summary["status"] == "success" else "❌"
    print(f"{status_icon} Status: {summary['status'].upper()}")
    print(f"⏱️  Duration: {summary['deployment_time_minutes']:.1f} minutes")
    print(f"📈 Success Rate: {summary['steps_summary']['success_rate']:.1f}%")
    print()
    
    # Steps summary
    print("📋 Deployment Steps:")
    for step in summary["deployment_steps"]:
        step_icon = "✅" if step["status"] == "completed" else "❌" if step["status"] == "failed" else "⏳"
        print(f"   {step_icon} {step['name']} ({step['duration_seconds']:.1f}s)")
        if step["error_message"]:
            print(f"      Error: {step['error_message']}")
    print()
    
    # Production status
    prod_status = summary["production_status"]
    print("🏭 Production Status:")
    print(f"   Mode: {'Production' if prod_status['production_mode'] else 'Demo'}")
    print(f"   Region: {prod_status['region']}")
    print(f"   Cost Controls: {'✅ Active' if prod_status['cost_controls_enabled'] else '❌ Inactive'}")
    print(f"   Competition Ready: {'✅ Yes' if prod_status['competition_ready'] else '❌ No'}")
    print()
    
    # Cost summary
    cost_summary = summary["cost_summary"]
    print("💰 Cost Summary:")
    print(f"   Current Spend: ${cost_summary['current_spend']:.2f}")
    print(f"   Budget Usage: {cost_summary['usage_percentage']:.1f}%")
    print(f"   Remaining: ${cost_summary['remaining_budget']:.2f}")
    print(f"   Daily Rate: ${cost_summary['daily_burn_rate']:.2f}")
    print(f"   Days Remaining: {cost_summary['days_remaining']}")
    print()
    
    # Next steps
    print("🎯 Next Steps:")
    for step in summary["next_steps"]:
        print(f"   {step}")
    print()
    
    # Monitoring URLs
    print("🔗 Monitoring URLs:")
    for name, url in summary["monitoring_urls"].items():
        print(f"   {name.replace('_', ' ').title()}: {url}")
    print()

def main():
    """Main deployment function"""
    setup_logging()
    print_banner()
    
    # Pre-deployment checks
    if not print_pre_deployment_info():
        print("❌ Pre-deployment checks failed. Please configure credentials first.")
        return 1
    
    # Confirm deployment
    print("🤔 Ready to deploy SafeRouteAI to production?")
    print("   This will:")
    print("   • Configure Huawei Cloud services (ModelArts, OBS)")
    print("   • Set up cost monitoring and auto-scaling")
    print("   • Migrate data to cloud storage")
    print("   • Transition from demo to production mode")
    print("   • Run comprehensive validation tests")
    print()
    
    confirm = input("Continue with deployment? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Deployment cancelled by user")
        return 0
    
    print("\n🚀 Starting production deployment...")
    print("   This may take 5-10 minutes depending on data size")
    print("   Please wait...\n")
    
    try:
        # Execute full production deployment
        deployment_summary = production_orchestrator.execute_full_production_deployment()
        
        # Print results
        print_deployment_summary(deployment_summary)
        
        # Return appropriate exit code
        return 0 if deployment_summary["status"] == "success" else 1
        
    except KeyboardInterrupt:
        print("\n❌ Deployment interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        logging.error(f"Deployment failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())