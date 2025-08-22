#!/usr/bin/env python3
"""Test script for ChatGLM integration with the API"""

import requests
import json
import time

# Test configuration
API_URL = "http://localhost:8000/v1/chat/completions"
TEST_MODELS = ["glm-4.5", "glm-4.5-Air", "glm-4.5V", "glm-4-32B"]

def test_non_streaming(model):
    """Test non-streaming response"""
    print(f"\n=== Testing non-streaming with {model} ===")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'Hello from ChatGLM!' in 10 words or less."}],
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            print(f"✓ Success: {content[:100]}...")
            return True
        else:
            print(f"✗ Failed: Invalid response structure")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        return False

def test_streaming(model):
    """Test streaming response"""
    print(f"\n=== Testing streaming with {model} ===")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Count from 1 to 5."}],
        "stream": True
    }
    
    try:
        response = requests.post(API_URL, json=payload, stream=True, timeout=30)
        response.raise_for_status()
        
        full_text = ""
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                full_text += delta["content"]
                                chunk_count += 1
                    except json.JSONDecodeError:
                        pass
        
        if full_text and chunk_count > 0:
            print(f"✓ Success: Received {chunk_count} chunks")
            print(f"  Response: {full_text[:100]}...")
            return True
        else:
            print(f"✗ Failed: No content received")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ChatGLM Integration Test Suite")
    print("=" * 60)
    
    # Test if API is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("✗ API is not running. Please start it with: uvicorn app.main:app")
            return
    except:
        print("✗ API is not running. Please start it with: uvicorn app.main:app")
        return
    
    results = {}
    
    # Test each model
    for model in TEST_MODELS:
        print(f"\n{'=' * 60}")
        print(f"Testing model: {model}")
        print(f"{'=' * 60}")
        
        # Test non-streaming
        non_stream_result = test_non_streaming(model)
        time.sleep(1)  # Small delay between tests
        
        # Test streaming
        stream_result = test_streaming(model)
        time.sleep(1)  # Small delay between tests
        
        results[model] = {
            "non_streaming": non_stream_result,
            "streaming": stream_result
        }
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
    
    for model, result in results.items():
        status = "✓ PASS" if all(result.values()) else "✗ FAIL"
        print(f"{model}: {status}")
        print(f"  - Non-streaming: {'✓' if result['non_streaming'] else '✗'}")
        print(f"  - Streaming: {'✓' if result['streaming'] else '✗'}")
    
    # Overall result
    all_passed = all(all(r.values()) for r in results.values())
    print(f"\n{'=' * 60}")
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()