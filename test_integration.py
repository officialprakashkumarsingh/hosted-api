#!/usr/bin/env python3
"""
Test script for the new ExaChat integration in the FastAPI proxy
"""

import requests
import json
import time

def test_models_endpoint():
    """Test that the /v1/models endpoint includes ExaChat models"""
    print("🔍 Testing /v1/models endpoint...")
    try:
        response = requests.get("http://localhost:8000/v1/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model["id"] for model in data["data"]]
            
            # Check for ExaChat models
            exachat_models = [m for m in models if any(x in m for x in [
                "exaanswer", "grok-3", "gemini-2", "deepseek/", "meta-llama/", 
                "llama-3", "qwen-", "gemma"
            ])]
            
            print(f"✅ Total models: {len(models)}")
            print(f"✅ ExaChat models found: {len(exachat_models)}")
            
            # Print first few ExaChat models
            print("📝 Sample ExaChat models:")
            for model in exachat_models[:5]:
                print(f"  - {model}")
            
            return True, exachat_models[:3]  # Return first 3 for testing
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False, []

def test_exachat_model(model):
    """Test a specific ExaChat model"""
    print(f"\n🧪 Testing {model}...")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "stream": False,
        "max_tokens": 50
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/v1/chat/completions", 
            json=payload, 
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"✅ SUCCESS ({response_time:.2f}s): {content.strip()[:50]}...")
                return True
            else:
                print(f"❌ Invalid response format: {data}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_streaming(model):
    """Test streaming with an ExaChat model"""
    print(f"\n🌊 Testing streaming with {model}...")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Count from 1 to 3"}],
        "stream": True,
        "max_tokens": 50
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/v1/chat/completions", 
            json=payload, 
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            chunks_received = 0
            content_received = ""
            
            print("📤 Streaming: ", end="", flush=True)
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
                                
                                if chunks_received > 20:  # Limit for test
                                    break
                    except json.JSONDecodeError:
                        continue
            
            response_time = time.time() - start_time
            print(f"\n✅ Streaming SUCCESS ({response_time:.2f}s, {chunks_received} chunks)")
            return True
        else:
            print(f"❌ Streaming failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streaming ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ExaChat Integration Test")
    print("=" * 60)
    print("Testing the new ExaChat models integration...")
    print("Make sure the FastAPI server is running on localhost:8000")
    print("=" * 60)
    
    # Test models endpoint
    success, test_models = test_models_endpoint()
    if not success:
        print("❌ Cannot proceed - models endpoint failed")
        return
    
    if not test_models:
        print("❌ No ExaChat models found to test")
        return
    
    # Test individual models
    successful_tests = 0
    total_tests = 0
    
    for model in test_models:
        # Test non-streaming
        total_tests += 1
        if test_exachat_model(model):
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
        print("🎉 All tests passed! ExaChat integration is working perfectly!")
    elif successful_tests > 0:
        print("⚠️ Some tests failed, but basic functionality is working")
    else:
        print("❌ All tests failed - check your server and ExaChat integration")

if __name__ == "__main__":
    main()