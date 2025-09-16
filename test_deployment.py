#!/usr/bin/env python3
"""
Test script to verify the deployed application is working correctly
"""
import requests
import json
import time

BASE_URL = "https://multi-model-chatbot-api.onrender.com"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_home_endpoint():
    """Test the home endpoint"""
    try:
        print("\n🔍 Testing home endpoint...")
        response = requests.get(f"{BASE_URL}/", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Home endpoint working!")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Home endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Home endpoint error: {e}")
        return False

def test_providers_endpoint():
    """Test the providers endpoint"""
    try:
        print("\n🔍 Testing providers endpoint...")
        response = requests.get(f"{BASE_URL}/api/providers", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Providers endpoint working!")
            providers = data.get('providers', {})
            print(f"   Available providers: {len(providers)}")
            for name, info in providers.items():
                status = "✅" if info['available'] else "❌"
                print(f"   {status} {info['name']}: {', '.join(info['models'])}")
            return True
        else:
            print(f"❌ Providers endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Providers endpoint error: {e}")
        return False

def test_longcat_chat():
    """Test the Longcat chat endpoint"""
    try:
        print("\n🔍 Testing Longcat chat endpoint...")
        payload = {
            "message": "Hello! Can you say hi back?"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/longcat", 
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Longcat chat working!")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Longcat chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Longcat chat error: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 TESTING RENDER DEPLOYMENT")
    print("=" * 50)
    print(f"Testing: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_home_endpoint,
        test_providers_endpoint,
        test_longcat_chat
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(2)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is working perfectly!")
    elif passed > 0:
        print("⚠️  Some tests passed. Deployment is partially working.")
    else:
        print("❌ All tests failed. Deployment may have issues.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()