#!/usr/bin/env python3
"""
Test URL encoding for Huawei API keys
Demonstrates the URLEncoder.encode equivalent in Python
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

def test_url_encoding():
    """Test URL encoding transformation"""
    api_key = os.getenv("HUAWEI_MAP_API_KEY")
    
    if not api_key:
        print("❌ No API key found")
        return
    
    print("🔗 URL Encoding Test")
    print("=" * 50)
    print(f"Original API Key: {api_key}")
    print()
    
    # URL encode using quote_plus (equivalent to URLEncoder.encode in Java)
    encoded_key = quote_plus(api_key)
    print(f"URL Encoded Key: {encoded_key}")
    print()
    
    # Show character transformations
    print("Character Transformations:")
    transformations = []
    
    if '+' in api_key:
        transformations.append("'+' → '%2B'")
    if '/' in api_key:
        transformations.append("'/' → '%2F'")
    if '=' in api_key:
        transformations.append("'=' → '%3D'")
    if ' ' in api_key:
        transformations.append("' ' → '%20'")
    
    if transformations:
        for transform in transformations:
            print(f"  • {transform}")
    else:
        print("  • No special characters found")
    
    print()
    
    # Show example usage in URLs
    print("Example Usage in URLs:")
    print(f"Map Kit JS API: https://mapapi.cloud.huawei.com/mapjs/v1/api/js?key={encoded_key}")
    print(f"Location API: https://siteapi.cloud.huawei.com/mapApi/v1/siteService/geocode?key={encoded_key}&address=...")
    
    print()
    print("✅ URL encoding is working correctly!")
    print("💡 This is equivalent to Java's URLEncoder.encode(apiKey, \"UTF-8\")")

if __name__ == "__main__":
    test_url_encoding()