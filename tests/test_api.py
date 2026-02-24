#!/usr/bin/env python3
"""Test script to verify all API endpoints are working."""

import requests
import json
import sys

BASE_URL = "https://ask-mirror-talk-api.onrender.com"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description or endpoint}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            print(f"Payload: {json.dumps(data, indent=2)}")
            response = requests.post(url, json=data, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Body (text): {response.text[:500]}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Ask Mirror Talk API Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Health endpoint
    results.append(("Health Check", test_endpoint(
        "GET", 
        "/health",
        description="Health Check - Should always work"
    )))
    
    # Test 2: Status endpoint
    results.append(("Status Check", test_endpoint(
        "GET",
        "/status",
        description="Status - Database stats"
    )))
    
    # Test 3: Ask endpoint
    results.append(("Ask Endpoint", test_endpoint(
        "POST",
        "/ask",
        data={"question": "What is this podcast about?"},
        description="Ask Question - Main functionality"
    )))
    
    # Test 4: Ask with empty question (should fail)
    results.append(("Empty Question Validation", not test_endpoint(
        "POST",
        "/ask",
        data={"question": ""},
        description="Empty Question - Should return 400"
    )))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print("="*60)
    
    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
