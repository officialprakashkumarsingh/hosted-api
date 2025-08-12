#!/usr/bin/env python3
"""
Direct test of DeepInfra models through the deployed proxy
Even though they're not in the models list, let's test a few directly
"""

import requests
import json

BASE_URL = "https://gpt-oss-openai-proxy.onrender.com"

# Test a few popular DeepInfra models
TEST_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct", 
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
    "google/gemma-2-9b-it"
]

def test_deepinfra_direct(model_name):
    """Test a DeepInfra model directly"""
    print(f"\n🧪 Direct test: {model_name}")
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
        "stream": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=60)
        
        print(f"  📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  ✅ SUCCESS: {content[:100]}")
            return True
        elif response.status_code == 403:
            print(f"  ❌ 403 Forbidden - API access denied")
        elif response.status_code == 404:
            print(f"  ❌ 404 Not Found - Model not recognized")
        elif response.status_code == 502:
            print(f"  ❌ 502 Bad Gateway - Backend error")
            try:
                error_data = response.json()
                print(f"     Error: {error_data}")
            except:
                print(f"     Raw error: {response.text[:200]}")
        else:
            print(f"  ❌ Error {response.status_code}")
            print(f"     Response: {response.text[:200]}")
        
        return False
        
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def main():
    print("🚀 DEEPINFRA DIRECT TEST")
    print("🔗 Testing DeepInfra models directly through proxy")
    print("=" * 60)
    
    working = 0
    for model in TEST_MODELS:
        if test_deepinfra_direct(model):
            working += 1
    
    print(f"\n🎯 RESULTS: {working}/{len(TEST_MODELS)} DeepInfra models working")
    
    if working == 0:
        print("❌ No DeepInfra models working - API access likely blocked")
    elif working == len(TEST_MODELS):
        print("🎉 All tested DeepInfra models working!")
    else:
        print("🔥 Some DeepInfra models working!")

if __name__ == "__main__":
    main()