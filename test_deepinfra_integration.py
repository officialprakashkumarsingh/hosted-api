#!/usr/bin/env python3
"""
Test script for DeepInfra integration in FastAPI app
Tests both streaming and non-streaming requests
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:3000"

def test_models_endpoint():
    """Test the /v1/models endpoint"""
    print("🔍 Testing /v1/models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            data = response.json()
            models = [model["id"] for model in data["data"]]
            deepinfra_models = [m for m in models if "/" in m and any(provider in m for provider in ["deepseek", "Qwen", "meta-llama", "microsoft", "google", "mistral"])]
            print(f"✅ Models endpoint working - {len(models)} total models")
            print(f"🎯 DeepInfra models found: {len(deepinfra_models)}")
            return True, deepinfra_models[:5]  # Return first 5 for testing
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False, []

def test_non_streaming(model):
    """Test non-streaming chat completion"""
    print(f"\n📝 Testing non-streaming with {model}...")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hello in one sentence"}],
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ Non-streaming SUCCESS ({response_time:.2f}s)")
            print(f"📤 Response: {content[:80]}...")
            return True
        else:
            print(f"❌ Non-streaming FAILED: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Non-streaming ERROR: {e}")
        return False

def test_streaming(model):
    """Test streaming chat completion"""
    print(f"\n🌊 Testing streaming with {model}...")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Count from 1 to 3"}],
            "stream": True
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, stream=True, timeout=30)
        
        if response.status_code == 200:
            chunks_received = 0
            content_received = ""
            
            print("📤 Streaming response: ", end="", flush=True)
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    chunk_data = line[6:]
                    if chunk_data == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(chunk_data)
                        if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                            delta = chunk_json["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content = delta["content"]
                                print(content, end="", flush=True)
                                content_received += content
                                chunks_received += 1
                    except json.JSONDecodeError:
                        continue
            
            response_time = time.time() - start_time
            print(f"\n✅ Streaming SUCCESS ({response_time:.2f}s, {chunks_received} chunks)")
            return True
        else:
            print(f"❌ Streaming FAILED: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Streaming ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 DeepInfra Integration Test")
    print("=" * 50)
    print("Make sure your FastAPI server is running on localhost:3000")
    print("Run: uvicorn app.main:app --host 0.0.0.0 --port 3000")
    print("=" * 50)
    
    # Test models endpoint
    success, test_models = test_models_endpoint()
    if not success or not test_models:
        print("❌ Cannot proceed - models endpoint failed")
        return
    
    # Test a few models
    successful_tests = 0
    total_tests = 0
    
    for model in test_models:
        print(f"\n🎯 Testing model: {model}")
        print("-" * 40)
        
        # Test non-streaming
        total_tests += 1
        if test_non_streaming(model):
            successful_tests += 1
        
        # Test streaming
        total_tests += 1
        if test_streaming(model):
            successful_tests += 1
        
        time.sleep(1)  # Rate limiting
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"📈 Success Rate: {(successful_tests/total_tests*100):.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! DeepInfra integration is working perfectly!")
    elif successful_tests > 0:
        print("⚠️ Some tests failed, but basic functionality is working")
    else:
        print("❌ All tests failed - check your server and configuration")

if __name__ == "__main__":
    main()