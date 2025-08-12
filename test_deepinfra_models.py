#!/usr/bin/env python3
"""
Test DeepInfra models on the deployed OpenAI-compatible endpoint
https://gpt-oss-openai-proxy.onrender.com/

Testing the DeepInfra models that were previously removed to see if they work now.
"""

import requests
import json
import time

BASE_URL = "https://gpt-oss-openai-proxy.onrender.com"

# DeepInfra models that were previously in the system
DEEPINFRA_MODELS = [
    # Meta LLaMA Models
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct", 
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "meta-llama/Llama-3.2-90B-Vision-Instruct",
    
    # Mistral Models
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mistralai/Mistral-Nemo-Instruct-2407",
    
    # Microsoft Models
    "microsoft/WizardLM-2-8x22B",
    "microsoft/Phi-3-medium-4k-instruct",
    
    # Qwen Models
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/QwQ-32B-Preview",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    
    # Google Models
    "google/gemma-2-27b-it",
    "google/gemma-2-9b-it",
    
    # Other Models
    "cognitivecomputations/dolphin-2.6-mixtral-8x7b",
    "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    "openchat/openchat-3.6-8b",
    "teknium/OpenHermes-2.5-Mistral-7B",
    
    # DeepSeek Models
    "deepseek-ai/deepseek-llm-67b-chat",
    "deepseek-ai/DeepSeek-V2.5",
    
    # Anthropic-style Models
    "lizpreciatior/lzlv_70b_fp16_hf",
    "Gryphe/MythoMax-L13B",
    
    # Code Models
    "codellama/CodeLlama-34b-Instruct-hf",
    "WizardLM/WizardCoder-Python-34B-V1.0",
    
    # Recent additions
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    "Nexusflow/Starling-LM-7B-beta",
]

def test_deepinfra_model(model_name, timeout=90):
    """Test a specific DeepInfra model with both streaming and non-streaming"""
    print(f"\n🧪 Testing DeepInfra model: {model_name}")
    
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
            if response.status_code == 403:
                print("     403 Forbidden - API access denied")
            elif response.status_code == 404:
                print("     404 Not Found - Model not available")
            elif response.status_code == 502:
                print("     502 Bad Gateway - Backend error")
            else:
                print(f"     Error: {response.text[:200]}")
            non_streaming_works = False
            
    except Exception as e:
        print(f"  ❌ Non-streaming error: {e}")
        non_streaming_works = False
    
    # Only test streaming if non-streaming works
    if not non_streaming_works:
        return False, False
    
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

def test_if_deepinfra_models_exist():
    """First check if any DeepInfra models are in the models list"""
    print("🔍 Checking if DeepInfra models are in the models endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=30)
        if response.status_code != 200:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return []
            
        data = response.json()
        available_models = [model["id"] for model in data["data"]]
        
        # Check which DeepInfra models are available
        found_deepinfra = []
        for model in DEEPINFRA_MODELS:
            if model in available_models:
                found_deepinfra.append(model)
        
        print(f"✅ Found {len(found_deepinfra)} DeepInfra models in endpoint")
        return found_deepinfra
        
    except Exception as e:
        print(f"❌ Error checking models endpoint: {e}")
        return []

def main():
    """Run DeepInfra models test"""
    print("🚀 DEEPINFRA MODELS TEST - Deployed Endpoint")
    print("🔗 URL: https://gpt-oss-openai-proxy.onrender.com/")
    print("=" * 70)
    
    # First check if DeepInfra models are available
    available_deepinfra = test_if_deepinfra_models_exist()
    
    if not available_deepinfra:
        print("\n❌ No DeepInfra models found in the models endpoint.")
        print("💡 This suggests DeepInfra models are not currently integrated.")
        return
    
    print(f"\n🎯 Testing {len(available_deepinfra)} available DeepInfra models...")
    
    # Test results tracking
    working_models = []
    failed_models = []
    
    for model in available_deepinfra:
        non_streaming_ok, streaming_ok = test_deepinfra_model(model)
        
        if non_streaming_ok and streaming_ok:
            working_models.append(model)
        else:
            failed_models.append(model)
        
        # Small delay between tests
        time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 DEEPINFRA TEST RESULTS")
    print("=" * 70)
    
    total_tested = len(available_deepinfra)
    working_count = len(working_models)
    
    print(f"📊 Total DeepInfra Models Tested: {total_tested}")
    print(f"✅ Working Models: {working_count}/{total_tested} ({round((working_count/total_tested)*100, 1) if total_tested > 0 else 0}%)")
    
    if working_models:
        print(f"\n✅ WORKING DEEPINFRA MODELS ({len(working_models)}):")
        for model in working_models:
            print(f"   - {model}")
    
    if failed_models:
        print(f"\n❌ FAILED DEEPINFRA MODELS ({len(failed_models)}):")
        for model in failed_models:
            print(f"   - {model}")
    
    if working_count == 0:
        print(f"\n⚠️  NO DEEPINFRA MODELS WORKING")
        print("💡 DeepInfra models may still have API restrictions or rate limits.")
    elif working_count == total_tested:
        print(f"\n🎉 ALL DEEPINFRA MODELS WORKING! 🎉")
    else:
        print(f"\n🔥 PARTIAL SUCCESS: {working_count} out of {total_tested} working!")

if __name__ == "__main__":
    main()