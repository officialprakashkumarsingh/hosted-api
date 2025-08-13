#!/usr/bin/env python3
"""
Comprehensive test of ALL DeepInfra models through the deployed proxy
Testing all DeepInfra models to see which ones work
"""

import requests
import json
import time

BASE_URL = "https://gpt-oss-openai-proxy.onrender.com"

# Comprehensive list of DeepInfra models
ALL_DEEPINFRA_MODELS = [
    # Meta LLaMA Models
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct", 
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "meta-llama/Llama-3.2-90B-Vision-Instruct",
    "meta-llama/Llama-2-7b-chat-hf",
    "meta-llama/Llama-2-13b-chat-hf",
    "meta-llama/Llama-2-70b-chat-hf",
    
    # Mistral Models
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mistralai/Mistral-Nemo-Instruct-2407",
    "mistralai/Pixtral-12B-2409",
    
    # Microsoft Models
    "microsoft/WizardLM-2-8x22B",
    "microsoft/Phi-3-medium-4k-instruct",
    "microsoft/Phi-3-mini-4k-instruct",
    
    # Qwen Models
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/QwQ-32B-Preview",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2-72B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    
    # Google Models
    "google/gemma-2-27b-it",
    "google/gemma-2-9b-it",
    "google/gemma-2-2b-it",
    
    # Other Popular Models
    "cognitivecomputations/dolphin-2.6-mixtral-8x7b",
    "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    "openchat/openchat-3.6-8b",
    "teknium/OpenHermes-2.5-Mistral-7B",
    "NousResearch/Nous-Hermes-2-Yi-34B",
    
    # DeepSeek Models
    "deepseek-ai/deepseek-llm-67b-chat",
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/deepseek-coder-33b-instruct",
    
    # Anthropic-style Models
    "lizpreciatior/lzlv_70b_fp16_hf",
    "Gryphe/MythoMax-L13B",
    "Undi95/ReMM-SLERP-L2-13B",
    
    # Code Models
    "codellama/CodeLlama-34b-Instruct-hf",
    "codellama/CodeLlama-13b-Instruct-hf",
    "codellama/CodeLlama-7b-Instruct-hf",
    "WizardLM/WizardCoder-Python-34B-V1.0",
    "WizardLM/WizardCoder-15B-V1.0",
    
    # NVIDIA Models
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    
    # Other Specialized Models
    "Nexusflow/Starling-LM-7B-beta",
    "togethercomputer/RedPajama-INCITE-7B-Chat",
    "garage-bAInd/Platypus2-70B-instruct",
    "upstage/SOLAR-10.7B-Instruct-v1.0",
    "01-ai/Yi-34B-Chat",
    "01-ai/Yi-6B-Chat",
    
    # Hugging Face Models
    "HuggingFaceH4/zephyr-7b-beta",
    "huggingfaceh4/zephyr-7b-alpha",
    
    # Stability AI
    "stabilityai/StableBeluga2-70B",
    "stabilityai/StableBeluga-13B",
    
    # Recent Popular Models
    "databricks/dbrx-instruct",
    "allenai/tulu-2-dpo-70b",
    "jondurbin/airoboros-l2-70b-gpt4-1.4.1",
    "Open-Orca/Mistral-7B-OpenOrca",
]

def test_deepinfra_model(model_name, timeout=90):
    """Test a specific DeepInfra model"""
    print(f"\n🧪 Testing: {model_name}")
    
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
            print(f"  ✅ SUCCESS: {content[:80]}")
            return True, "working"
        elif response.status_code == 403:
            print(f"  ❌ 403 Forbidden")
            return False, "forbidden"
        elif response.status_code == 404:
            print(f"  ❌ 404 Not Found")
            return False, "not_found"
        elif response.status_code == 502:
            print(f"  ❌ 502 Bad Gateway")
            return False, "bad_gateway"
        else:
            print(f"  ❌ Error {response.status_code}")
            return False, f"error_{response.status_code}"
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:80]}")
        return False, "exception"

def categorize_models(models):
    """Categorize models by provider/type"""
    categories = {
        "Meta LLaMA": [],
        "Mistral": [],
        "Microsoft": [],
        "Qwen": [],
        "Google": [],
        "DeepSeek": [],
        "Code Models": [],
        "NVIDIA": [],
        "Other": []
    }
    
    for model in models:
        if "meta-llama" in model.lower():
            categories["Meta LLaMA"].append(model)
        elif "mistral" in model.lower():
            categories["Mistral"].append(model)
        elif "microsoft" in model.lower():
            categories["Microsoft"].append(model)
        elif "qwen" in model.lower():
            categories["Qwen"].append(model)
        elif "google" in model.lower():
            categories["Google"].append(model)
        elif "deepseek" in model.lower():
            categories["DeepSeek"].append(model)
        elif any(x in model.lower() for x in ["code", "wizard"]):
            categories["Code Models"].append(model)
        elif "nvidia" in model.lower():
            categories["NVIDIA"].append(model)
        else:
            categories["Other"].append(model)
    
    return categories

def main():
    """Run comprehensive DeepInfra test"""
    print("🚀 COMPREHENSIVE DEEPINFRA MODELS TEST")
    print("🔗 URL: https://gpt-oss-openai-proxy.onrender.com/")
    print(f"🎯 Testing {len(ALL_DEEPINFRA_MODELS)} DeepInfra models")
    print("=" * 70)
    
    # Categorize models
    categories = categorize_models(ALL_DEEPINFRA_MODELS)
    
    # Test results tracking
    results = {
        "total": len(ALL_DEEPINFRA_MODELS),
        "working": [],
        "forbidden": [],
        "not_found": [],
        "bad_gateway": [],
        "errors": [],
        "category_results": {}
    }
    
    # Test each category
    for category, model_list in categories.items():
        if not model_list:
            continue
            
        print(f"\n🏷️  TESTING {category.upper()} ({len(model_list)} models)")
        print("-" * 50)
        
        category_working = 0
        
        for model in model_list:
            success, status = test_deepinfra_model(model, timeout=60)
            
            if success:
                results["working"].append(model)
                category_working += 1
            else:
                if status == "forbidden":
                    results["forbidden"].append(model)
                elif status == "not_found":
                    results["not_found"].append(model)
                elif status == "bad_gateway":
                    results["bad_gateway"].append(model)
                else:
                    results["errors"].append(model)
            
            # Small delay between tests
            time.sleep(0.5)
        
        results["category_results"][category] = {
            "working": category_working,
            "total": len(model_list),
            "percentage": round((category_working / len(model_list)) * 100, 1) if len(model_list) > 0 else 0
        }
        
        print(f"\n📊 {category} Results: {category_working}/{len(model_list)} ({results['category_results'][category]['percentage']}%) working")
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE DEEPINFRA TEST RESULTS")
    print("=" * 70)
    
    working_count = len(results["working"])
    total_count = results["total"]
    
    print(f"📊 Total Models Tested: {total_count}")
    print(f"✅ Working Models: {working_count}/{total_count} ({round((working_count/total_count)*100, 1)}%)")
    print(f"❌ Forbidden (403): {len(results['forbidden'])}")
    print(f"❌ Not Found (404): {len(results['not_found'])}")
    print(f"❌ Bad Gateway (502): {len(results['bad_gateway'])}")
    print(f"❌ Other Errors: {len(results['errors'])}")
    
    print(f"\n🏷️  CATEGORY BREAKDOWN:")
    for category, stats in results["category_results"].items():
        if stats["total"] > 0:
            print(f"   {category}: {stats['working']}/{stats['total']} ({stats['percentage']}%)")
    
    if working_count > 0:
        print(f"\n✅ WORKING DEEPINFRA MODELS ({working_count}):")
        for i, model in enumerate(results["working"][:20], 1):  # Show first 20
            print(f"   {i:2d}. {model}")
        if len(results["working"]) > 20:
            print(f"   ... and {len(results['working']) - 20} more")
    
    if working_count == 0:
        print(f"\n❌ NO DEEPINFRA MODELS WORKING")
    elif working_count == total_count:
        print(f"\n🎉 ALL DEEPINFRA MODELS WORKING! 🎉")
    elif working_count >= total_count * 0.8:
        print(f"\n🔥 EXCELLENT! {round((working_count/total_count)*100, 1)}% of DeepInfra models working!")
    else:
        print(f"\n🎯 PARTIAL SUCCESS: {working_count} DeepInfra models working")

if __name__ == "__main__":
    main()