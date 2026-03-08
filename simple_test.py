#!/usr/bin/env python3
"""Simple test to check if the server is working"""

import requests
import json

def test_basic_endpoint():
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

def test_map_config():
    try:
        response = requests.get("http://localhost:8000/api/v1/map/config")
        print(f"Map config status: {response.status_code}")
        if response.status_code == 200:
            print("Map config loaded successfully!")
            data = response.json()
            print(f"Features: {data.get('features_enabled', [])}")
        else:
            print("Error response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing SafeRouteAI backend...")
    test_basic_endpoint()
    test_map_config()