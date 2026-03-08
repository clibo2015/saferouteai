#!/usr/bin/env python3
"""
Install Huawei Cloud SDK components for SafeRouteAI
Run this when you're ready to use real Huawei Cloud services
"""
import subprocess
import sys

def install_huawei_sdk():
    """Install Huawei Cloud SDK packages"""
    packages = [
        "huaweicloudsdkcore>=3.1.0",
        "huaweicloudsdkmodelarts>=3.1.0", 
        "huaweicloudsdkgaussdb>=3.1.0",
        "huaweicloudsdkecs>=3.1.0"  # For compute resources
    ]
    
    print("🔧 Installing Huawei Cloud SDK packages...")
    print("This will enable real AI services integration")
    print()
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
        print()
    
    print("🎉 Huawei Cloud SDK installation completed!")
    print()
    print("Next steps:")
    print("1. Get your Huawei Cloud credentials from console.huaweicloud.com")
    print("2. Update your .env file with:")
    print("   HUAWEI_CLOUD_AK=your_access_key")
    print("   HUAWEI_CLOUD_SK=your_secret_key") 
    print("   HUAWEI_CLOUD_PROJECT_ID=your_project_id")
    print("   DEMO_MODE=false")
    print("3. Restart the API server")
    print()
    print("💡 Tip: Keep DEMO_MODE=true during development to avoid charges")
    
    return True

if __name__ == "__main__":
    install_huawei_sdk()