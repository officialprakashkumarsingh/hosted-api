#!/usr/bin/env python3
"""
Real API Test - Test actual DeepInfra API calls
This script tests if the models actually work without an API key
"""

import sys
import time
import traceback

# We need to create a version that uses real HTTP requests
import json
import uuid
from typing import List, Dict, Optional, Union, Generator, Any

# Try to use urllib instead of requests to avoid dependency issues
try:
    import urllib.request
    import urllib.parse
    import urllib.error
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

class SimpleHTTPClient:
    """Simple HTTP client using urllib"""
    
    def __init__(self):
        self.headers = {}
    
    def post(self, url, headers=None, data=None, stream=False, timeout=30):
        """Make a POST request"""
        if not URLLIB_AVAILABLE:
            raise Exception("urllib not available")
        
        # Prepare request
        if data:
            data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        
        # Add headers
        all_headers = self.headers.copy()
        if headers:
            all_headers.update(headers)
        
        for key, value in all_headers.items():
            req.add_header(key, value)
        
        try:
            response = urllib.request.urlopen(req, timeout=timeout)
            response_data = response.read().decode('utf-8')
            
            if stream:
                return StreamResponse(response_data)
            else:
                return JSONResponse(json.loads(response_data), response.status)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return JSONResponse({"error": error_body}, e.code)
        except Exception as e:
            return JSONResponse({"error": str(e)}, 500)

class JSONResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
    
    def json(self):
        return self.data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}: {self.data}")

class StreamResponse:
    def __init__(self, data):
        self.data = data
    
    def iter_lines(self, decode_unicode=True):
        lines = self.data.split('\n')
        for line in lines:
            if line.strip():
                yield line

class RealDeepInfraTest:
    """Test actual DeepInfra API calls"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.client = SimpleHTTPClient()
        
        # Set headers similar to the original implementation
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://deepinfra.com",
            "Pragma": "no-cache",
            "Referer": "https://deepinfra.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Deepinfra-Source": "web-embed",
            "Sec-CH-UA": '"Not)A;Brand";v="99", "Chrome";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        self.client.headers.update(self.headers)
    
    def test_model(self, model_name, prompt="Hello, how are you?", max_tokens=50):
        """Test a specific model"""
        print(f"\n🧪 Testing model: {model_name}")
        print(f"📝 Prompt: {prompt}")
        print(f"🔑 API Key: {'Yes' if self.api_key else 'No'}")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": False,
            "temperature": 0.7
        }
        
        try:
            start_time = time.time()
            response = self.client.post(
                self.base_url,
                headers=self.headers,
                data=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    if content:
                        print(f"✅ SUCCESS ({response_time:.2f}s)")
                        print(f"📤 Response: {content[:100]}...")
                        if 'usage' in data:
                            usage = data['usage']
                            print(f"📊 Usage: {usage.get('total_tokens', 'N/A')} tokens")
                        return True, content
                    else:
                        print(f"❌ FAILED: Empty response content")
                        return False, "Empty content"
                else:
                    print(f"❌ FAILED: Invalid response structure")
                    print(f"📄 Response: {data}")
                    return False, "Invalid structure"
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                error_data = response.json()
                print(f"📄 Error: {error_data}")
                return False, f"HTTP {response.status_code}: {error_data}"
                
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            return False, str(e)
    
    def test_streaming(self, model_name, prompt="Count from 1 to 5"):
        """Test streaming response"""
        print(f"\n🌊 Testing streaming with: {model_name}")
        print(f"📝 Prompt: {prompt}")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 50,
            "stream": True,
            "temperature": 0.7
        }
        
        try:
            start_time = time.time()
            response = self.client.post(
                self.base_url,
                headers=self.headers,
                data=payload,
                stream=True,
                timeout=30
            )
            
            print("📤 Streaming response: ", end="", flush=True)
            chunks_received = 0
            content_received = ""
            
            for line in response.iter_lines():
                if line.startswith("data: "):
                    chunk_data = line[6:]
                    if chunk_data == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(chunk_data)
                        if 'choices' in chunk_json:
                            delta = chunk_json['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                content = delta['content']
                                print(content, end="", flush=True)
                                content_received += content
                                chunks_received += 1
                    except json.JSONDecodeError:
                        continue
            
            response_time = time.time() - start_time
            print(f"\n✅ Streaming SUCCESS ({response_time:.2f}s, {chunks_received} chunks)")
            return True, content_received
            
        except Exception as e:
            print(f"\n❌ Streaming FAILED: {str(e)}")
            return False, str(e)

def main():
    """Main testing function"""
    print("🔬 Real DeepInfra API Test")
    print("=" * 50)
    print("This script tests actual API calls to DeepInfra")
    
    if not URLLIB_AVAILABLE:
        print("❌ urllib not available - cannot make HTTP requests")
        return
    
    # Check for API key
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"🔑 Using provided API key: {api_key[:10]}...")
    else:
        print("🔓 No API key provided - testing free access")
    
    print("=" * 50)
    
    tester = RealDeepInfraTest(api_key)
    
    # Test popular free models first
    free_models = [
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "microsoft/phi-4",
        "Qwen/Qwen2.5-7B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "openai/gpt-oss-20b"
    ]
    
    # Test premium models (likely require API key)
    premium_models = [
        "deepseek-ai/DeepSeek-R1-0528",
        "anthropic/claude-4-sonnet",
        "google/gemini-2.5-flash"
    ]
    
    successful_tests = 0
    total_tests = 0
    
    print("\n🆓 Testing Free Models:")
    print("-" * 30)
    
    for model in free_models:
        total_tests += 1
        success, _ = tester.test_model(model, "What is 2+2?")
        if success:
            successful_tests += 1
        time.sleep(2)  # Rate limiting
    
    print(f"\n💎 Testing Premium Models:")
    print("-" * 30)
    
    for model in premium_models:
        total_tests += 1
        success, _ = tester.test_model(model, "Hello!")
        if success:
            successful_tests += 1
        time.sleep(2)  # Rate limiting
    
    # Test streaming on a working model
    if successful_tests > 0:
        print(f"\n🌊 Testing Streaming:")
        print("-" * 30)
        tester.test_streaming(free_models[0], "Count from 1 to 3")
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"📈 Success Rate: {(successful_tests/total_tests*100):.1f}%")
    
    if successful_tests == 0:
        print("\n⚠️  No models responded successfully.")
        print("This could mean:")
        print("- API key is required for all models")
        print("- DeepInfra API has changed")
        print("- Rate limiting or temporary issues")
        print("- Authentication headers need adjustment")
    elif successful_tests < total_tests:
        print(f"\n💡 {total_tests - successful_tests} models failed.")
        print("Some models may require an API key or have different requirements.")
    else:
        print(f"\n🎉 All models working {'with' if api_key else 'without'} API key!")

if __name__ == "__main__":
    main()