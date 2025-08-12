#!/usr/bin/env python3
"""
Test script for Flowith integration in the FastAPI proxy
Tests models endpoint and a few Flowith models with both streaming and non-streaming
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_models_endpoint():
    """Test that all models are available via /v1/models"""
    print("🔍 Testing /v1/models endpoint...")
    
    response = requests.get(f"{BASE_URL}/v1/models")
    if response.status_code != 200:
        print(f"❌ Models endpoint failed: {response.status_code}")
        return False
        
    data = response.json()
    models = [model["id"] for model in data["data"]]
    
    # Check for Flowith models
    flowith_models = [
        "gpt-5-nano", "gpt-5-mini", "glm-4.5", 
        "gpt-oss-120b", "gpt-oss-20b", "kimi-k2",
        "gpt-4.1", "gpt-4.1-mini", "deepseek-chat", 
        "deepseek-reasoner", "gemini-2.5-flash", "grok-3-mini"
    ]
    
    found_models = []
    missing_models = []
    
    for model in flowith_models:
        if model in models:
            found_models.append(model)
        else:
            missing_models.append(model)
    
    print(f"✅ Found {len(found_models)}/12 Flowith models")
    print(f"📊 Total models available: {len(models)}")
    
    if missing_models:
        print(f"⚠️  Missing models: {missing_models}")
        return False
    
    return True

def test_flowith_model(model_name, test_streaming=True):
    """Test a specific Flowith model"""
    print(f"\n🧪 Testing model: {model_name}")
    
    # Test non-streaming
    print("  📝 Testing non-streaming...")
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
        "stream": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"  ✅ Non-streaming: {content[:50]}...")
        else:
            print(f"  ❌ Non-streaming failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ Non-streaming error: {e}")
        return False
    
    if not test_streaming:
        return True
    
    # Test streaming
    print("  🌊 Testing streaming...")
    payload["stream"] = True
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, stream=True, timeout=30)
        if response.status_code == 200:
            content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: ') and not line_str.endswith('[DONE]'):
                        try:
                            chunk_data = json.loads(line_str[6:])  # Remove 'data: '
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content += delta["content"]
                        except json.JSONDecodeError:
                            continue
            
            if content.strip():
                print(f"  ✅ Streaming: {content[:50]}...")
            else:
                print("  ⚠️  Streaming: Empty response")
                return False
        else:
            print(f"  ❌ Streaming failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Streaming error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Flowith Integration Test Suite")
    print("=" * 50)
    
    # Test models endpoint
    if not test_models_endpoint():
        print("\n❌ Models endpoint test failed!")
        return
    
    # Test a few key Flowith models
    test_models = [
        "gpt-5-nano",      # GPT-5 model
        "deepseek-chat",   # DeepSeek model  
        "gemini-2.5-flash" # Gemini model
    ]
    
    success_count = 0
    for model in test_models:
        if test_flowith_model(model):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {success_count}/{len(test_models)} models working")
    
    if success_count == len(test_models):
        print("🎉 All Flowith integration tests PASSED!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()