#!/usr/bin/env python3
"""
Comprehensive test of all models from the deployed OpenAI-compatible endpoint
https://gpt-oss-openai-proxy.onrender.com/
"""

import requests
import json
import time

BASE_URL = "https://gpt-oss-openai-proxy.onrender.com"

def test_models_endpoint():
    """Test the /v1/models endpoint to get all available models"""
    print("🔍 Testing /v1/models endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=30)
        if response.status_code != 200:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return None
            
        data = response.json()
        models = [model["id"] for model in data["data"]]
        
        print(f"✅ Found {len(models)} total models")
        return models
        
    except Exception as e:
        print(f"❌ Error testing models endpoint: {e}")
        return None

def test_model(model_name, timeout=60):
    """Test a specific model with both streaming and non-streaming"""
    print(f"\n🧪 Testing: {model_name}")
    
    # Test non-streaming first
    print("  📝 Non-streaming test...")
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
        "stream": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  ✅ Non-streaming: {content[:100]}")
            non_streaming_works = True
        else:
            print(f"  ❌ Non-streaming failed: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            non_streaming_works = False
            
    except Exception as e:
        print(f"  ❌ Non-streaming error: {e}")
        non_streaming_works = False
    
    # Test streaming
    print("  🌊 Streaming test...")
    payload["stream"] = True
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, stream=True, timeout=timeout)
        
        if response.status_code == 200:
            content = ""
            chunk_count = 0
            
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
                                    chunk_count += 1
                        except json.JSONDecodeError:
                            continue
            
            if content.strip():
                print(f"  ✅ Streaming: {content[:100]} ({chunk_count} chunks)")
                streaming_works = True
            else:
                print("  ⚠️  Streaming: Empty response")
                streaming_works = False
        else:
            print(f"  ❌ Streaming failed: {response.status_code}")
            streaming_works = False
            
    except Exception as e:
        print(f"  ❌ Streaming error: {e}")
        streaming_works = False
    
    return non_streaming_works, streaming_works

def categorize_models(models):
    """Categorize models by provider"""
    categories = {
        "Core Models": [],
        "GPT-OSS Models": [],
        "ExaChat Models": [],
        "Flowith Models": []
    }
    
    # Define model lists
    core_models = ["gpt-4o", "gpt-4o-mini", "perplexed", "felo"]
    gpt_oss_models = ["gpt-oss-20b", "gpt-oss-120b"]
    
    # ExaChat models (curated list)
    exachat_models = [
        "exaanswer", "gemini-2.0-flash", "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-2.5-flash-lite-preview-06-17", "gemini-2.5-flash", "deepseek/deepseek-r1:free",
        "deepseek-r1-distill-llama-70b", "qwen-qwq-32b", "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-4-scout-17b-16e-instruct"
    ]
    
    # Flowith models
    flowith_models = [
        "gpt-5-nano", "gpt-5-mini", "glm-4.5", "gpt-oss-120b", "gpt-oss-20b", "kimi-k2",
        "gpt-4.1", "gpt-4.1-mini", "deepseek-chat", "deepseek-reasoner", "gemini-2.5-flash", "grok-3-mini"
    ]
    
    for model in models:
        if model in core_models:
            categories["Core Models"].append(model)
        elif model in gpt_oss_models:
            categories["GPT-OSS Models"].append(model)
        elif model in exachat_models:
            categories["ExaChat Models"].append(model)
        elif model in flowith_models:
            categories["Flowith Models"].append(model)
    
    return categories

def main():
    """Run comprehensive test of all models"""
    print("🚀 COMPREHENSIVE MODEL TEST - Deployed Endpoint")
    print("🔗 URL: https://gpt-oss-openai-proxy.onrender.com/")
    print("=" * 70)
    
    # Get all models
    models = test_models_endpoint()
    if not models:
        print("❌ Failed to get models list. Exiting.")
        return
    
    # Categorize models
    categories = categorize_models(models)
    
    # Test results tracking
    results = {
        "total_models": len(models),
        "working_non_streaming": 0,
        "working_streaming": 0,
        "fully_working": 0,
        "failed_models": [],
        "category_results": {}
    }
    
    # Test each category
    for category, model_list in categories.items():
        if not model_list:
            continue
            
        print(f"\n🏷️  TESTING {category.upper()} ({len(model_list)} models)")
        print("-" * 50)
        
        category_working = 0
        category_total = len(model_list)
        
        for model in model_list:
            non_streaming_ok, streaming_ok = test_model(model, timeout=90)
            
            if non_streaming_ok:
                results["working_non_streaming"] += 1
            if streaming_ok:
                results["working_streaming"] += 1
            if non_streaming_ok and streaming_ok:
                results["fully_working"] += 1
                category_working += 1
            elif not non_streaming_ok and not streaming_ok:
                results["failed_models"].append(model)
            
            # Small delay between tests
            time.sleep(1)
        
        results["category_results"][category] = {
            "working": category_working,
            "total": category_total,
            "percentage": round((category_working / category_total) * 100, 1) if category_total > 0 else 0
        }
        
        print(f"\n📊 {category} Results: {category_working}/{category_total} ({results['category_results'][category]['percentage']}%) working")
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 70)
    
    print(f"📊 Total Models Tested: {results['total_models']}")
    print(f"✅ Fully Working (both modes): {results['fully_working']}/{results['total_models']} ({round((results['fully_working']/results['total_models'])*100, 1)}%)")
    print(f"📝 Non-streaming Working: {results['working_non_streaming']}/{results['total_models']}")
    print(f"🌊 Streaming Working: {results['working_streaming']}/{results['total_models']}")
    
    print(f"\n🏷️  CATEGORY BREAKDOWN:")
    for category, stats in results["category_results"].items():
        print(f"   {category}: {stats['working']}/{stats['total']} ({stats['percentage']}%)")
    
    if results["failed_models"]:
        print(f"\n❌ Failed Models ({len(results['failed_models'])}):")
        for model in results["failed_models"]:
            print(f"   - {model}")
    
    if results["fully_working"] == results["total_models"]:
        print(f"\n🎉 ALL MODELS WORKING PERFECTLY! 🎉")
    elif results["fully_working"] >= results["total_models"] * 0.8:
        print(f"\n🔥 EXCELLENT! {round((results['fully_working']/results['total_models'])*100, 1)}% models working!")
    else:
        print(f"\n⚠️  Some models need attention.")

if __name__ == "__main__":
    main()