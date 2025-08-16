#!/usr/bin/env python3
"""
Test script to verify Refact models integration in the FastAPI app
"""
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_MODELS = [
    "gpt-4o",
    "claude-opus-4.1", 
    "gpt-5",
    "gemini-2.5-pro"
]

def test_models_list():
    """Test if Refact models are listed in /v1/models endpoint"""
    print("🔍 Testing /v1/models endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = [model["id"] for model in data["data"]]
        
        print(f"✅ Found {len(models)} total models")
        
        refact_models_found = [model for model in models if model in [
            "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
            "gpt-5", "gpt-5-mini", "gpt-5-nano", 
            "claude-sonnet-4", "claude-opus-4", "claude-opus-4.1",
            "gemini-2.5-pro", "gemini-2.5-pro-preview"
        ]]
        
        print(f"🟢 Refact models found: {len(refact_models_found)}")
        for model in refact_models_found:
            print(f"  ✓ {model}")
        
        return len(refact_models_found) > 0
        
    except Exception as e:
        print(f"❌ Error testing models list: {e}")
        return False

def test_model_streaming(model: str):
    """Test streaming response for a specific model"""
    print(f"\n🔄 Testing streaming for model: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello and tell me your name in one sentence."}],
        "stream": True,
        "max_tokens": 100
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=15
        )
        response.raise_for_status()
        
        content_received = ""
        chunk_count = 0
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            content_received += content
                            print(content, end='', flush=True)
                            chunk_count += 1
                except json.JSONDecodeError:
                    continue
        
        elapsed = time.time() - start_time
        print(f"\n✅ SUCCESS: {chunk_count} chunks, {len(content_received)} chars, {elapsed:.2f}s")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False

def test_model_non_streaming(model: str):
    """Test non-streaming response for a specific model"""
    print(f"\n🔄 Testing non-streaming for model: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello in one sentence."}],
        "stream": False,
        "max_tokens": 50
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        elapsed = time.time() - start_time
        
        print(f"✅ SUCCESS: {elapsed:.2f}s")
        print(f"📝 Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("🚀 TESTING REFACT INTEGRATION IN FASTAPI APP")
    print("=" * 60)
    
    # Test if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding correctly")
            return
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        return
    
    print("✅ Server is running")
    
    # Test models list
    if not test_models_list():
        print("❌ Models list test failed")
        return
    
    # Test streaming and non-streaming for selected models
    working_models = []
    failed_models = []
    
    for model in TEST_MODELS:
        print(f"\n{'='*50}")
        print(f"Testing model: {model}")
        print('='*50)
        
        # Test streaming
        streaming_success = test_model_streaming(model)
        
        # Test non-streaming
        non_streaming_success = test_model_non_streaming(model)
        
        if streaming_success and non_streaming_success:
            working_models.append(model)
        else:
            failed_models.append(model)
        
        time.sleep(1)  # Rate limiting
    
    # Final report
    print(f"\n{'='*60}")
    print("📈 FINAL TEST REPORT")
    print('='*60)
    print(f"✅ Working models: {len(working_models)}/{len(TEST_MODELS)}")
    print(f"❌ Failed models: {len(failed_models)}/{len(TEST_MODELS)}")
    
    if working_models:
        print(f"\n🟢 WORKING MODELS:")
        for model in working_models:
            print(f"  ✓ {model}")
    
    if failed_models:
        print(f"\n🔴 FAILED MODELS:")
        for model in failed_models:
            print(f"  ✗ {model}")
    
    if len(working_models) == len(TEST_MODELS):
        print(f"\n🎉 ALL TESTS PASSED! Refact integration is working perfectly!")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()