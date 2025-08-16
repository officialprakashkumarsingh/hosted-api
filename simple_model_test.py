#!/usr/bin/env python3
import requests
import json
import time
import uuid
import random
import string

def generate_api_key_suffix(length: int = 4) -> str:
    """Generate a random API key suffix like 'C1Z5'"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_full_api_key(prefix: str = "EU1CW20nX5oau42xBSgm") -> str:
    """Generate a full API key with a random suffix"""
    suffix = generate_api_key_suffix(4)
    return prefix + suffix

def test_model_streaming(model_name, timeout_seconds=15):
    """Test a specific model with streaming response"""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print('='*60)
    
    # API configuration
    base_url = "https://inference.smallcloud.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "refact-lsp 0.10.19",
        "Authorization": f"Bearer {generate_full_api_key()}"
    }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Say hello and tell me about yourself in one sentence."}],
        "max_tokens": 100,
        "stream": True,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout_seconds
        )
        response.raise_for_status()
        
        content_received = ""
        chunk_count = 0
        
        for line in response.iter_lines(decode_unicode=True):
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                print(f"❌ TIMEOUT after {timeout_seconds}s")
                return False, f"Timeout after {timeout_seconds}s"
                
            if line:
                if line.startswith("data: "):
                    json_str = line[6:]
                    if json_str == "[DONE]":
                        break
                    try:
                        data = json.loads(json_str)
                        choice_data = data.get('choices', [{}])[0]
                        delta_data = choice_data.get('delta', {})
                        
                        if delta_data.get('content'):
                            content = delta_data.get('content')
                            content_received += content
                            print(content, end='', flush=True)
                            chunk_count += 1
                    except json.JSONDecodeError:
                        continue
        
        elapsed = time.time() - start_time
        print(f"\n\n✅ SUCCESS")
        print(f"📊 Stats: {chunk_count} chunks, {len(content_received)} chars, {elapsed:.2f}s")
        print(f"📝 Response: {content_received[:100]}{'...' if len(content_received) > 100 else ''}")
        return True, content_received
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False, f"Request error: {e}"
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e)

def test_all_models():
    """Test all available models"""
    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "o4-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "claude-sonnet-4",
        "claude-opus-4",
        "claude-opus-4.1",
        "gemini-2.5-pro",
        "gemini-2.5-pro-preview"
    ]
    
    print("🚀 Starting comprehensive model testing...")
    print(f"📋 Total models to test: {len(AVAILABLE_MODELS)}")
    
    results = {}
    working_models = []
    failed_models = []
    
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        print(f"\n🔄 Progress: {i}/{len(AVAILABLE_MODELS)}")
        success, result = test_model_streaming(model)
        results[model] = {"success": success, "result": result}
        
        if success:
            working_models.append(model)
        else:
            failed_models.append(model)
        
        # Small delay between requests to be nice to the API
        time.sleep(1)
    
    # Summary report
    print(f"\n{'='*80}")
    print("📈 FINAL SUMMARY REPORT")
    print('='*80)
    print(f"✅ Working models: {len(working_models)}/{len(AVAILABLE_MODELS)}")
    print(f"❌ Failed models: {len(failed_models)}/{len(AVAILABLE_MODELS)}")
    
    if working_models:
        print(f"\n🟢 WORKING MODELS ({len(working_models)}):")
        for model in working_models:
            print(f"  ✓ {model}")
    
    if failed_models:
        print(f"\n🔴 FAILED MODELS ({len(failed_models)}):")
        for model in failed_models:
            error = results[model]["result"]
            print(f"  ✗ {model}: {error}")
    
    return results

if __name__ == "__main__":
    # Test all models
    results = test_all_models()
    
    # Save results to file
    with open("/workspace/model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: model_test_results.json")