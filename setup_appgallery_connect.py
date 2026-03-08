#!/usr/bin/env python3
"""
AppGallery Connect Configuration Setup for SafeRouteAI
Validates and tests the AppGallery Connect integration
"""
import os
import sys
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_section(title):
    """Print a section title"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}\n")

def validate_configuration():
    """Validate AppGallery Connect configuration"""
    print_header("AppGallery Connect Configuration Validator")
    
    # Check required environment variables
    required_vars = {
        'HUAWEI_CLOUD_AK': 'Huawei Cloud Access Key',
        'HUAWEI_CLOUD_SK': 'Huawei Cloud Secret Key',
        'HUAWEI_CLOUD_PROJECT_ID': 'Huawei Cloud Project ID',
        'HUAWEI_MAP_API_KEY': 'Map Kit API Key',
        'HUAWEI_OAUTH_CLIENT_ID': 'OAuth Client ID',
        'HUAWEI_OAUTH_CLIENT_SECRET': 'OAuth Client Secret',
        'HUAWEI_APP_ID': 'App ID',
        'DATABASE_URL': 'Neon Database URL',
        'JWT_SECRET': 'JWT Secret Key'
    }
    
    print_section("Environment Variables Check")
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'SK' in var or 'KEY' in var:
                display_value = value[:10] + '...' + value[-10:] if len(value) > 20 else '***'
            else:
                display_value = value
            print(f"✅ {description:30} : {display_value}")
        else:
            print(f"❌ {description:30} : NOT SET")
            all_present = False
    
    if not all_present:
        print("\n⚠️  Some required environment variables are missing!")
        print("Please check your .env file and ensure all variables are set.")
        return False
    
    print("\n✅ All required environment variables are present!")
    return True

def display_configuration_summary():
    """Display configuration summary"""
    print_section("Configuration Summary")
    
    config = {
        "Developer ID": "30027000029470745",
        "Project ID": os.getenv('HUAWEI_CLOUD_PROJECT_ID'),
        "App ID": os.getenv('HUAWEI_APP_ID'),
        "OAuth Client ID": os.getenv('HUAWEI_OAUTH_CLIENT_ID'),
        "Region": os.getenv('HUAWEI_CLOUD_REGION', 'AF-Johannesburg'),
        "Database": "Neon PostgreSQL (Connected)" if os.getenv('DATABASE_URL') else "Not Configured",
        "Authentication": "JWT + Neon Auth",
        "Map Kit": "Enabled" if os.getenv('HUAWEI_MAP_API_KEY') else "Not Configured"
    }
    
    for key, value in config.items():
        print(f"  {key:20} : {value}")

def display_callback_urls():
    """Display callback URLs that need to be configured"""
    print_section("Callback URLs to Configure in AppGallery Connect")
    
    print("Add these URLs in AppGallery Connect Console:")
    print("  → Build → Auth Service → Settings → OAuth 2.0 Configuration\n")
    
    callback_urls = [
        "http://localhost:3000/auth/callback",
        "http://localhost:8004/auth/callback",
        "http://127.0.0.1:3000/auth/callback",
        "http://127.0.0.1:8004/auth/callback"
    ]
    
    for url in callback_urls:
        print(f"  • {url}")
    
    print("\n📝 Production URLs (add when deploying):")
    print("  • https://your-frontend-domain.com/auth/callback")
    print("  • https://your-backend-domain.com/auth/callback")

def display_access_restrictions():
    """Display access restrictions that need to be configured"""
    print_section("Access Restrictions to Configure")
    
    print("Add these domains in AppGallery Connect Console:")
    print("  → Build → Auth Service → Settings → Access Restrictions\n")
    
    domains = [
        "http://localhost:3000",
        "http://localhost:8004",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8004"
    ]
    
    for domain in domains:
        print(f"  • {domain}")
    
    print("\n📝 Production Domains (add when deploying):")
    print("  • https://your-frontend-domain.com")
    print("  • https://your-backend-domain.com")

def display_map_kit_setup():
    """Display Map Kit setup instructions"""
    print_section("Map Kit Configuration")
    
    map_api_key = os.getenv('HUAWEI_MAP_API_KEY')
    
    if map_api_key:
        print("✅ Map Kit API Key is configured")
        print(f"   Key: {map_api_key[:20]}...{map_api_key[-20:]}")
        
        # URL encode the key
        encoded_key = quote_plus(map_api_key)
        print(f"\n📝 URL-Encoded Key (for API requests):")
        print(f"   {encoded_key[:30]}...{encoded_key[-30:]}")
    else:
        print("❌ Map Kit API Key is not configured")
    
    print("\n📋 Map Kit Services to Enable:")
    print("  1. Go to AppGallery Connect Console")
    print("  2. Navigate to Build → Map Kit")
    print("  3. Click 'Enable Now'")
    print("  4. Configure API quotas (use defaults for development)")
    print("  5. Add authorized domains (same as access restrictions)")
    print("  6. Save configuration")

def display_next_steps():
    """Display next steps"""
    print_section("Next Steps")
    
    steps = [
        {
            "step": "1. Configure AppGallery Connect",
            "actions": [
                "Add callback URLs in OAuth 2.0 settings",
                "Add access restrictions (authorized domains)",
                "Enable Map Kit service",
                "Enable Location Kit (optional)",
                "Save all changes"
            ]
        },
        {
            "step": "2. Test Backend API",
            "actions": [
                "Start backend: python src/api.py",
                "Test authentication endpoints",
                "Test Map Kit integration",
                "Verify database connection"
            ]
        },
        {
            "step": "3. Test Frontend",
            "actions": [
                "Start frontend: cd frontend && npm start",
                "Test user registration/login",
                "Test map display",
                "Test route optimization"
            ]
        },
        {
            "step": "4. Deploy to Production",
            "actions": [
                "Choose hosting platforms (Railway, Netlify, etc.)",
                "Update callback URLs with production domains",
                "Update access restrictions with production domains",
                "Configure SSL/TLS certificates",
                "Set up monitoring and logging"
            ]
        }
    ]
    
    for item in steps:
        print(f"\n{item['step']}")
        for action in item['actions']:
            print(f"  • {action}")

def generate_agconnect_config():
    """Generate AGConnect configuration snippet"""
    print_section("AGConnect Configuration Snippet")
    
    config = {
        "agcgw_all": {
            "SG": "connect-dra.dbankcloud.cn",
            "SG_back": "connect-dra.hispace.hicloud.com",
            "CN": "connect-drcn.dbankcloud.cn",
            "CN_back": "connect-drcn.hispace.hicloud.com",
            "RU": "connect-drru.hispace.dbankcloud.ru",
            "RU_back": "connect-drru.hispace.dbankcloud.cn",
            "DE": "connect-dre.dbankcloud.cn",
            "DE_back": "connect-dre.hispace.hicloud.com"
        },
        "websocketgw_all": {
            "SG": "connect-ws-dra.hispace.dbankcloud.cn",
            "SG_back": "connect-ws-dra.hispace.dbankcloud.com",
            "CN": "connect-ws-drcn.hispace.dbankcloud.cn",
            "CN_back": "connect-ws-drcn.hispace.dbankcloud.com",
            "RU": "connect-ws-drru.hispace.dbankcloud.ru",
            "RU_back": "connect-ws-drru.hispace.dbankcloud.cn",
            "DE": "connect-ws-dre.hispace.dbankcloud.cn",
            "DE_back": "connect-ws-dre.hispace.dbankcloud.com"
        },
        "client": {
            "cp_id": "30027000029470745",
            "product_id": os.getenv('HUAWEI_CLOUD_PROJECT_ID', '101653523863540321'),
            "project_id": os.getenv('HUAWEI_CLOUD_PROJECT_ID', '101653523863540321'),
            "app_id": os.getenv('HUAWEI_APP_ID', '101653523124655000')
        },
        "oauth_client": {
            "client_id": os.getenv('HUAWEI_OAUTH_CLIENT_ID', '116823677'),
            "client_type": 7
        },
        "app_info": {
            "app_id": os.getenv('HUAWEI_APP_ID', '101653523124655000')
        },
        "configuration_version": "3.0"
    }
    
    print("Add this to your frontend HTML (before </body>):\n")
    print("<script>")
    print(f"var agConnectConfig = {json.dumps(config, indent=2)};")
    print("</script>")
    
    # Save to file
    with open('frontend/public/agconnect-config.js', 'w') as f:
        f.write(f"var agConnectConfig = {json.dumps(config, indent=2)};")
    
    print("\n✅ Configuration saved to: frontend/public/agconnect-config.js")

def display_useful_links():
    """Display useful links"""
    print_section("Useful Links")
    
    links = {
        "AppGallery Connect Console": "https://developer.huawei.com/consumer/en/service/josp/agc/index.html",
        "Map Kit Documentation": "https://developer.huawei.com/consumer/en/doc/HMSCore-Guides/android-sdk-brief-introduction-0000001061991291",
        "Auth Service Documentation": "https://developer.huawei.com/consumer/en/doc/development/AppGallery-connect-Guides/agc-auth-introduction-0000001053732605",
        "Huawei Developer Forum": "https://forums.developer.huawei.com/",
        "Neon Database Console": "https://console.neon.tech/"
    }
    
    for name, url in links.items():
        print(f"  • {name}")
        print(f"    {url}\n")

def main():
    """Main function"""
    print_header("SafeRouteAI - AppGallery Connect Setup")
    
    # Validate configuration
    if not validate_configuration():
        print("\n❌ Configuration validation failed!")
        print("Please fix the issues above and run this script again.")
        sys.exit(1)
    
    # Display configuration summary
    display_configuration_summary()
    
    # Display callback URLs
    display_callback_urls()
    
    # Display access restrictions
    display_access_restrictions()
    
    # Display Map Kit setup
    display_map_kit_setup()
    
    # Generate AGConnect config
    generate_agconnect_config()
    
    # Display next steps
    display_next_steps()
    
    # Display useful links
    display_useful_links()
    
    print_header("Setup Complete!")
    print("✅ Configuration validated successfully!")
    print("✅ AGConnect configuration generated!")
    print("\n📋 Next: Configure callback URLs and access restrictions in AppGallery Connect")
    print("📖 See APPGALLERY_CONNECT_CONFIG.md for detailed instructions\n")

if __name__ == "__main__":
    main()
