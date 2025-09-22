#!/usr/bin/env python3
"""
Test script for the File Logger Service
Run this to verify the file logger is working properly
"""

import requests
import json
from datetime import datetime

# Configuration
FILE_LOGGER_URL = "http://127.0.0.1:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{FILE_LOGGER_URL}/health")
        print("✅ Health check:", response.json())
        return True
    except Exception as e:
        print("❌ Health check failed:", e)
        return False

def test_weather2_logging():
    """Test logging weather2 data"""
    test_data = {
        "city": "New York",
        "weather2_data": {
            "temperature": 70,
            "conditions": "cloudy",
            "pressure": 1013,
            "visibility": 10,
            "source": "NationalWeatherService",
            "test_timestamp": datetime.now().isoformat()
        }
    }

    try:
        response = requests.post(f"{FILE_LOGGER_URL}/log/weather2", json=test_data)
        result = response.json()
        print("✅ Weather2 logging:", result)
        return result.get("filename")
    except Exception as e:
        print("❌ Weather2 logging failed:", e)
        return None

def test_generic_logging():
    """Test generic logging"""
    test_data = {
        "category": "test_logs",
        "data": {
            "test": "This is a test log entry",
            "timestamp": datetime.now().isoformat(),
            "value": 42
        }
    }

    try:
        response = requests.post(f"{FILE_LOGGER_URL}/log/generic", json=test_data)
        result = response.json()
        print("✅ Generic logging:", result)
        return True
    except Exception as e:
        print("❌ Generic logging failed:", e)
        return False

def test_list_logs():
    """Test listing logs"""
    try:
        response = requests.get(f"{FILE_LOGGER_URL}/logs/list/weather_responses")
        result = response.json()
        print(f"✅ List logs: Found {result.get('count', 0)} weather response files")
        if result.get('files'):
            print(f"   Most recent: {result['files'][0]['filename']}")
        return True
    except Exception as e:
        print("❌ List logs failed:", e)
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{FILE_LOGGER_URL}/logs/stats")
        result = response.json()
        print("✅ Stats:")
        print(f"   Total files: {result.get('total_files', 0)}")
        print(f"   Total size: {result.get('total_size_bytes', 0)} bytes")
        print(f"   Log directory: {result.get('log_directory', 'unknown')}")
        return True
    except Exception as e:
        print("❌ Stats failed:", e)
        return False

def main():
    print("=" * 60)
    print("Testing File Logger Service")
    print(f"URL: {FILE_LOGGER_URL}")
    print("=" * 60)

    # Run tests
    if not test_health():
        print("\n⚠️  File Logger Service is not running!")
        print("Please start it first with: python file_logger_service.py")
        return

    print("\nRunning tests...")
    test_weather2_logging()
    test_generic_logging()
    test_list_logs()
    test_stats()

    print("\n✅ All tests completed!")
    print("\nYou can now:")
    print("1. Check the mcp_logs directory for saved files")
    print("2. Use the weather1 MCP server - it will automatically log to this service")
    print("3. View logs at: http://127.0.0.1:5000/logs/list/weather_responses")

if __name__ == "__main__":
    main()