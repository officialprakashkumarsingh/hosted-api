#!/usr/bin/env python3
"""
Test All Free DeepInfra Models
This script tests all 67 available models to identify which ones work without an API key
"""

import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

class DeepInfraFreeTester:
    """Test all DeepInfra models for free access"""
    
    def __init__(self):
        self.base_url = "https://api.deepinfra.com/v1/openai/chat/completions"
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
        
        # All available models from the DeepInfra provider
        self.all_models = [
            "anthropic/claude-4-opus",
            "moonshotai/Kimi-K2-Instruct",
            "anthropic/claude-4-sonnet",
            "deepseek-ai/DeepSeek-R1-0528-Turbo",
            "Qwen/Qwen3-235B-A22B-Thinking-2507",
            "Qwen/Qwen3-Coder-480B-A35B-Instruct",
            "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
            "Qwen/Qwen3-235B-A22B-Instruct-2507",
            "Qwen/Qwen3-235B-A22B",
            "Qwen/Qwen3-30B-A3B",
            "Qwen/Qwen3-32B",
            "Qwen/Qwen3-14B",
            "deepseek-ai/DeepSeek-V3-0324-Turbo",
            "deepseek-ai/DeepSeek-Prover-V2-671B",
            "meta-llama/Llama-4-Maverick-17B-128E-Instruct-Turbo",
            "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "meta-llama/Llama-4-Scout-17B-16E-Instruct",
            "deepseek-ai/DeepSeek-R1-0528",
            "deepseek-ai/DeepSeek-V3-0324",
            "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
            "microsoft/phi-4-reasoning-plus",
            "Qwen/QwQ-32B",
            "google/gemini-2.5-flash",
            "google/gemini-2.5-pro",
            "google/gemma-3-27b-it",
            "google/gemma-3-12b-it",
            "google/gemma-3-4b-it",
            "microsoft/Phi-4-multimodal-instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "deepseek-ai/DeepSeek-V3",
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Llama-3.3-70B-Instruct",
            "microsoft/phi-4",
            "Gryphe/MythoMax-L2-13b",
            "NousResearch/Hermes-3-Llama-3.1-405B",
            "NousResearch/Hermes-3-Llama-3.1-70B",
            "NovaSky-AI/Sky-T1-32B-Preview",
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Sao10K/L3-8B-Lunaris-v1-Turbo",
            "Sao10K/L3.1-70B-Euryale-v2.2",
            "Sao10K/L3.3-70B-Euryale-v2.3",
            "anthropic/claude-3-7-sonnet-latest",
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "deepseek-ai/DeepSeek-R1-Turbo",
            "google/gemini-2.0-flash-001",
            "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "meta-llama/Llama-3.2-1B-Instruct",
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Llama-3.2-90B-Vision-Instruct",
            "meta-llama/Meta-Llama-3-70B-Instruct",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "microsoft/WizardLM-2-8x22B",
            "mistralai/Devstral-Small-2505",
            "mistralai/Devstral-Small-2507",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "mistralai/Mistral-Nemo-Instruct-2407",
            "mistralai/Mistral-Small-24B-Instruct-2501",
            "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "nvidia/Llama-3.1-Nemotron-70B-Instruct",
            "zai-org/GLM-4.5-Air",
            "zai-org/GLM-4.5",
            "zai-org/GLM-4.5V",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "allenai/olmOCR-7B-0725-FP8",
        ]
        
        self.free_models = []
        self.paid_models = []
        self.error_models = []
        self.test_results = []
    
    def test_model(self, model_name, timeout=15):
        """Test a single model with a simple prompt"""
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
            "stream": False,
            "temperature": 0.5
        }
        
        try:
            # Prepare request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.base_url, data=data, method='POST')
            
            # Add headers
            for key, value in self.headers.items():
                req.add_header(key, value)
            
            start_time = time.time()
            
            # Make request
            response = urllib.request.urlopen(req, timeout=timeout)
            response_time = time.time() - start_time
            response_data = response.read().decode('utf-8')
            
            if response.status == 200:
                data = json.loads(response_data)
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    if content:
                        self.free_models.append(model_name)
                        result = {
                            'model': model_name,
                            'status': 'FREE',
                            'response_time': response_time,
                            'content': content[:50] + '...' if len(content) > 50 else content,
                            'tokens': data.get('usage', {}).get('total_tokens', 'N/A')
                        }
                        self.test_results.append(result)
                        return True, f"SUCCESS ({response_time:.2f}s): {content[:30]}..."
                    else:
                        self.error_models.append(model_name)
                        result = {
                            'model': model_name,
                            'status': 'ERROR',
                            'response_time': response_time,
                            'error': 'Empty content'
                        }
                        self.test_results.append(result)
                        return False, "Empty response content"
                else:
                    self.error_models.append(model_name)
                    result = {
                        'model': model_name,
                        'status': 'ERROR',
                        'response_time': response_time,
                        'error': 'Invalid response structure'
                    }
                    self.test_results.append(result)
                    return False, "Invalid response structure"
            else:
                self.error_models.append(model_name)
                result = {
                    'model': model_name,
                    'status': 'ERROR',
                    'response_time': response_time,
                    'error': f'HTTP {response.status}'
                }
                self.test_results.append(result)
                return False, f"HTTP {response.status}"
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.paid_models.append(model_name)
                result = {
                    'model': model_name,
                    'status': 'PAID',
                    'error': 'Authentication required'
                }
                self.test_results.append(result)
                return False, "Requires API key"
            else:
                self.error_models.append(model_name)
                error_body = e.read().decode('utf-8') if e.fp else str(e)
                result = {
                    'model': model_name,
                    'status': 'ERROR',
                    'error': f'HTTP {e.code}: {error_body[:100]}'
                }
                self.test_results.append(result)
                return False, f"HTTP {e.code}"
        except Exception as e:
            self.error_models.append(model_name)
            result = {
                'model': model_name,
                'status': 'ERROR',
                'error': str(e)[:100]
            }
            self.test_results.append(result)
            return False, str(e)
    
    def test_all_models(self):
        """Test all models systematically"""
        print("🚀 Testing All DeepInfra Models for Free Access")
        print("=" * 60)
        print(f"📋 Total models to test: {len(self.all_models)}")
        print(f"⏱️  Estimated time: {len(self.all_models) * 2 / 60:.1f} minutes")
        print("=" * 60)
        
        start_time = time.time()
        
        for i, model in enumerate(self.all_models):
            print(f"\n[{i+1:2d}/{len(self.all_models)}] 🧪 {model}")
            
            success, message = self.test_model(model)
            
            if success:
                print(f"         ✅ FREE: {message}")
            elif "API key" in message:
                print(f"         🔐 PAID: {message}")
            else:
                print(f"         ❌ ERROR: {message}")
            
            # Rate limiting - wait between requests
            if i < len(self.all_models) - 1:  # Don't wait after last request
                time.sleep(2)  # 2 second delay between requests
        
        total_time = time.time() - start_time
        self.generate_comprehensive_report(total_time)
    
    def generate_comprehensive_report(self, total_time):
        """Generate detailed report of all findings"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DEEPINFRA FREE MODEL REPORT")
        print("=" * 60)
        
        # Summary statistics
        total_models = len(self.all_models)
        free_count = len(self.free_models)
        paid_count = len(self.paid_models)
        error_count = len(self.error_models)
        
        print(f"🕒 Total test time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"📈 Total models tested: {total_models}")
        print(f"🆓 Free models found: {free_count} ({free_count/total_models*100:.1f}%)")
        print(f"🔐 Paid models: {paid_count} ({paid_count/total_models*100:.1f}%)")
        print(f"❌ Error/Unknown: {error_count} ({error_count/total_models*100:.1f}%)")
        
        # Free models section
        if self.free_models:
            print(f"\n🆓 FREE MODELS ({len(self.free_models)} total):")
            print("-" * 40)
            
            # Group by provider for better organization
            providers = {}
            for model in self.free_models:
                provider = model.split('/')[0]
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(model)
            
            for provider, models in providers.items():
                print(f"\n📦 {provider.upper()} ({len(models)} models):")
                for model in models:
                    # Find response details
                    result = next((r for r in self.test_results if r['model'] == model), {})
                    response_time = result.get('response_time', 0)
                    content_preview = result.get('content', '')
                    tokens = result.get('tokens', 'N/A')
                    print(f"   ✅ {model}")
                    print(f"      ⏱️  {response_time:.2f}s | 🎯 {tokens} tokens | 💬 {content_preview}")
        
        # Paid models section (condensed)
        if self.paid_models:
            print(f"\n🔐 PAID MODELS (Require API Key) - {len(self.paid_models)} total:")
            print("-" * 40)
            
            # Group by provider
            paid_providers = {}
            for model in self.paid_models:
                provider = model.split('/')[0]
                if provider not in paid_providers:
                    paid_providers[provider] = []
                paid_providers[provider].append(model.split('/')[1])
            
            for provider, models in paid_providers.items():
                models_str = ', '.join(models[:3])  # Show first 3
                if len(models) > 3:
                    models_str += f" (+{len(models)-3} more)"
                print(f"   🔐 {provider}: {models_str}")
        
        # Error models (if any)
        if self.error_models:
            print(f"\n❌ MODELS WITH ERRORS - {len(self.error_models)} total:")
            print("-" * 40)
            for model in self.error_models[:5]:  # Show first 5 errors
                result = next((r for r in self.test_results if r['model'] == model), {})
                error = result.get('error', 'Unknown error')
                print(f"   ❌ {model}: {error}")
            if len(self.error_models) > 5:
                print(f"   ... and {len(self.error_models) - 5} more errors")
        
        # Performance analysis
        successful_results = [r for r in self.test_results if r['status'] == 'FREE']
        if successful_results:
            response_times = [r['response_time'] for r in successful_results]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n⚡ PERFORMANCE ANALYSIS:")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Fastest model: {min_time:.2f}s")
            print(f"   Slowest model: {max_time:.2f}s")
            
            # Find fastest and slowest
            fastest = min(successful_results, key=lambda x: x['response_time'])
            slowest = max(successful_results, key=lambda x: x['response_time'])
            print(f"   🏃 Fastest: {fastest['model']} ({fastest['response_time']:.2f}s)")
            print(f"   🐌 Slowest: {slowest['model']} ({slowest['response_time']:.2f}s)")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deepinfra_free_models_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'summary': {
                        'total_models': total_models,
                        'free_models': free_count,
                        'paid_models': paid_count,
                        'error_models': error_count,
                        'test_time': total_time,
                        'success_rate': free_count / total_models * 100
                    },
                    'free_models': self.free_models,
                    'paid_models': self.paid_models,
                    'error_models': self.error_models,
                    'detailed_results': self.test_results
                }, f, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save results: {e}")
        
        # Final recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.free_models:
            print(f"✅ {len(self.free_models)} models are available for FREE without API key")
            print("🎯 Best free models to try:")
            
            # Highlight some of the best free models
            recommended = []
            for model in self.free_models:
                if any(keyword in model.lower() for keyword in ['deepseek', 'phi', 'gpt-oss']):
                    recommended.append(model)
            
            for model in recommended[:5]:  # Top 5 recommendations
                print(f"   🌟 {model}")
        else:
            print("❌ No free models found - all models may require API key")
        
        print("=" * 60)

def main():
    """Main execution"""
    print("🔬 DeepInfra Free Models Discovery")
    print("This script will test all 67 models to find which work without API key")
    print()
    
    # Confirm before starting
    response = input("⚠️  This will make 67 API calls and take ~3-4 minutes. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Test cancelled")
        return
    
    print("\n🚀 Starting comprehensive test...")
    
    tester = DeepInfraFreeTester()
    tester.test_all_models()

if __name__ == "__main__":
    main()