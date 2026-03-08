#!/usr/bin/env python3
"""
Helper script to open the right Huawei Cloud console pages in your browser.
"""

import webbrowser
import time

def open_console_pages():
    """Open relevant Huawei Cloud console pages."""
    
    print("\n🌐 Opening Huawei Cloud Console Pages")
    print("="*60)
    
    pages = [
        {
            "name": "API Gateway Console",
            "url": "https://console.huaweicloud.com/apigateway",
            "purpose": "To whitelist your IP address"
        },
        {
            "name": "ModelArts Training Jobs",
            "url": "https://console.huaweicloud.com/modelarts/?region=af-south-1#/trainingJobs",
            "purpose": "To create training jobs manually"
        },
        {
            "name": "Support Tickets",
            "url": "https://console.huaweicloud.com/ticket",
            "purpose": "To request IP whitelisting from support"
        },
        {
            "name": "IAM Policies",
            "url": "https://console.huaweicloud.com/iam/#/iam/policies",
            "purpose": "To check your permissions"
        }
    ]
    
    print("\nYour IP Address: 192.143.129.78")
    print("Project ID: 4b96831b25094c25993949bab01aa216")
    print("\n" + "="*60)
    
    print("\nI will open these pages in your browser:\n")
    
    for i, page in enumerate(pages, 1):
        print(f"{i}. {page['name']}")
        print(f"   Purpose: {page['purpose']}")
        print(f"   URL: {page['url']}\n")
    
    response = input("Open these pages? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n📂 Opening pages...")
        for page in pages:
            print(f"  → Opening {page['name']}...")
            webbrowser.open(page['url'])
            time.sleep(2)  # Wait 2 seconds between opens
        
        print("\n✅ All pages opened!")
        print("\n" + "="*60)
        print("📋 What to Do Next:")
        print("="*60)
        print("\n1. In API Gateway:")
        print("   - Look for 'Access Control' or 'IP Whitelist'")
        print("   - Add IP: 192.143.129.78")
        print("   - Save changes")
        
        print("\n2. If you can't find API Gateway settings:")
        print("   - Go to Support Tickets page")
        print("   - Create ticket requesting IP whitelist")
        print("   - Copy message from QUICK_FIX_GUIDE.md")
        
        print("\n3. Alternative - Create job manually:")
        print("   - Go to ModelArts Training Jobs page")
        print("   - Click 'Create Training Job'")
        print("   - Use CPU instance (cheaper!)")
        
        print("\n4. Check permissions:")
        print("   - Go to IAM Policies page")
        print("   - Ensure you have ModelArts FullAccess")
        
        print("\n" + "="*60)
        print("\n💡 While waiting, use mock services:")
        print("   python demo_api_with_mock.py")
        print("\n" + "="*60)
        
    else:
        print("\n❌ Cancelled. No pages opened.")
        print("\nYou can manually visit:")
        print("  - API Gateway: https://console.huaweicloud.com/apigateway")
        print("  - Support: https://console.huaweicloud.com/ticket")

if __name__ == "__main__":
    print("\n🚀 Huawei Cloud Console Helper")
    print("="*60)
    print("\nThis script will open the console pages you need")
    print("to fix the IP authorization issue.")
    print("\n" + "="*60)
    
    try:
        open_console_pages()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease manually visit:")
        print("  https://console.huaweicloud.com/apigateway")
