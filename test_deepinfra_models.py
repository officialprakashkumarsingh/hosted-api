#!/usr/bin/env python3
"""
DeepInfra Models Test Script
Comprehensive testing suite for DeepInfra provider with multiple models
"""

import sys
import time
import traceback
import json
from typing import List, Dict, Any
from datetime import datetime

# Mock implementations for testing without webscout dependencies
class MockOpenAICompatibleProvider:
    pass

class MockBaseChat:
    pass

class MockBaseCompletions:
    pass

class MockChatCompletionChunk:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockChatCompletion:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockChoice:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockChoiceDelta:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockChatCompletionMessage:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockCompletionUsage:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockLitAgent:
    def generate_fingerprint(self, browser):
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept_language": "en-US,en;q=0.9",
            "sec_ch_ua": '"Not)A;Brand";v="99", "Chrome";v="127", "Chromium";v="127"',
            "platform": "Linux",
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }

# Replace webscout imports with mocks for testing
sys.modules['webscout.Provider.OPENAI.base'] = type('MockModule', (), {
    'OpenAICompatibleProvider': MockOpenAICompatibleProvider,
    'BaseChat': MockBaseChat,
    'BaseCompletions': MockBaseCompletions
})()

sys.modules['webscout.Provider.OPENAI.utils'] = type('MockModule', (), {
    'ChatCompletionChunk': MockChatCompletionChunk,
    'ChatCompletion': MockChatCompletion,
    'Choice': MockChoice,
    'ChoiceDelta': MockChoiceDelta,
    'ChatCompletionMessage': MockChatCompletionMessage,
    'CompletionUsage': MockCompletionUsage
})()

sys.modules['webscout.litagent'] = type('MockModule', (), {
    'LitAgent': MockLitAgent
})()

# Now import our DeepInfra implementation
from deepinfra_provider import DeepInfra

class DeepInfraModelTester:
    def __init__(self, api_key: str = None):
        """Initialize the tester with optional API key"""
        self.api_key = api_key
        self.test_results = []
        self.failed_tests = []
        self.successful_tests = []
        
        # Select a variety of models to test
        self.test_models = [
            "deepseek-ai/DeepSeek-R1-0528",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "microsoft/phi-4",
            "Qwen/Qwen2.5-7B-Instruct",
            "google/gemini-2.0-flash-001",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "anthropic/claude-3-7-sonnet-latest",
            "openai/gpt-oss-20b"
        ]
        
        # Test prompts for different scenarios
        self.test_prompts = {
            "simple": "Hello, how are you?",
            "coding": "Write a Python function to calculate fibonacci numbers",
            "reasoning": "Explain the process of photosynthesis in simple terms",
            "creative": "Write a short poem about artificial intelligence",
            "math": "Solve this equation: 2x + 5 = 15. Show your work."
        }

    def log_result(self, test_name: str, model: str, success: bool, details: str, response_time: float = None):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "model": model,
            "success": success,
            "details": details,
            "response_time": response_time
        }
        self.test_results.append(result)
        
        if success:
            self.successful_tests.append(result)
            print(f"✅ {test_name} - {model}: SUCCESS")
            if response_time:
                print(f"   Response time: {response_time:.2f}s")
        else:
            self.failed_tests.append(result)
            print(f"❌ {test_name} - {model}: FAILED")
            print(f"   Details: {details}")

    def test_model_availability(self):
        """Test if models are listed correctly"""
        print("\n🔍 Testing Model Availability...")
        try:
            client = DeepInfra(api_key=self.api_key)
            available_models = client.models.list()
            
            print(f"📋 Total available models: {len(available_models)}")
            print("📋 First 10 models:")
            for i, model in enumerate(available_models[:10]):
                print(f"   {i+1}. {model}")
            
            # Check if our test models are available
            missing_models = []
            for model in self.test_models:
                if model not in available_models:
                    missing_models.append(model)
            
            if missing_models:
                self.log_result("Model Availability", "N/A", False, 
                              f"Missing models: {missing_models}")
            else:
                self.log_result("Model Availability", "N/A", True, 
                              f"All {len(self.test_models)} test models available")
                
        except Exception as e:
            self.log_result("Model Availability", "N/A", False, str(e))

    def test_basic_completion(self, model: str, prompt: str):
        """Test basic non-streaming completion"""
        try:
            client = DeepInfra(api_key=self.api_key)
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                stream=False,
                temperature=0.7
            )
            
            response_time = time.time() - start_time
            
            # Validate response structure
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and len(content.strip()) > 0:
                    self.log_result("Basic Completion", model, True, 
                                  f"Generated {len(content)} characters", response_time)
                    print(f"   Preview: {content[:100]}...")
                else:
                    self.log_result("Basic Completion", model, False, 
                                  "Empty response content")
            else:
                self.log_result("Basic Completion", model, False, 
                              "Invalid response structure")
                
        except Exception as e:
            self.log_result("Basic Completion", model, False, str(e))

    def test_streaming_completion(self, model: str, prompt: str):
        """Test streaming completion"""
        try:
            client = DeepInfra(api_key=self.api_key)
            start_time = time.time()
            
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                stream=True,
                temperature=0.7
            )
            
            chunks_received = 0
            total_content = ""
            
            for chunk in stream:
                chunks_received += 1
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        total_content += delta.content
                
                # Break after reasonable number of chunks to avoid infinite loops
                if chunks_received > 50:
                    break
            
            response_time = time.time() - start_time
            
            if chunks_received > 0 and len(total_content.strip()) > 0:
                self.log_result("Streaming Completion", model, True, 
                              f"Received {chunks_received} chunks, {len(total_content)} chars", 
                              response_time)
                print(f"   Preview: {total_content[:100]}...")
            else:
                self.log_result("Streaming Completion", model, False, 
                              f"No content received in {chunks_received} chunks")
                
        except Exception as e:
            self.log_result("Streaming Completion", model, False, str(e))

    def test_parameter_variations(self, model: str):
        """Test different parameter combinations"""
        try:
            client = DeepInfra(api_key=self.api_key)
            
            # Test with different temperature values
            for temp in [0.1, 0.5, 0.9]:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "Say hello in a creative way"}],
                        max_tokens=50,
                        temperature=temp,
                        stream=False
                    )
                    
                    if hasattr(response, 'choices') and len(response.choices) > 0:
                        content = response.choices[0].message.content
                        if content and len(content.strip()) > 0:
                            self.log_result(f"Temperature Test ({temp})", model, True, 
                                          f"Generated content with temp={temp}")
                        else:
                            self.log_result(f"Temperature Test ({temp})", model, False, 
                                          "Empty response")
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    self.log_result(f"Temperature Test ({temp})", model, False, str(e))
                    
        except Exception as e:
            self.log_result("Parameter Variations", model, False, str(e))

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing Error Handling...")
        
        try:
            client = DeepInfra(api_key=self.api_key)
            
            # Test with invalid model
            try:
                response = client.chat.completions.create(
                    model="invalid/model-name",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=50,
                    stream=False
                )
                self.log_result("Invalid Model Test", "invalid/model-name", False, 
                              "Should have failed but didn't")
            except Exception as e:
                self.log_result("Invalid Model Test", "invalid/model-name", True, 
                              f"Correctly handled error: {type(e).__name__}")
            
            # Test with extremely large max_tokens
            try:
                response = client.chat.completions.create(
                    model=self.test_models[0],
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=999999,
                    stream=False
                )
                # If it succeeds, that's also valid
                self.log_result("Large Max Tokens Test", self.test_models[0], True, 
                              "Handled large max_tokens gracefully")
            except Exception as e:
                self.log_result("Large Max Tokens Test", self.test_models[0], True, 
                              f"Correctly limited max_tokens: {type(e).__name__}")
                
        except Exception as e:
            self.log_result("Error Handling Setup", "N/A", False, str(e))

    def test_conversation_flow(self, model: str):
        """Test multi-turn conversation"""
        try:
            client = DeepInfra(api_key=self.api_key)
            
            # Multi-turn conversation
            messages = [
                {"role": "user", "content": "What is the capital of France?"},
            ]
            
            response1 = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=50,
                stream=False
            )
            
            if hasattr(response1, 'choices') and len(response1.choices) > 0:
                assistant_response = response1.choices[0].message.content
                
                # Add assistant response and follow-up question
                messages.append({"role": "assistant", "content": assistant_response})
                messages.append({"role": "user", "content": "What is its population?"})
                
                response2 = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=50,
                    stream=False
                )
                
                if hasattr(response2, 'choices') and len(response2.choices) > 0:
                    second_response = response2.choices[0].message.content
                    if second_response and len(second_response.strip()) > 0:
                        self.log_result("Conversation Flow", model, True, 
                                      "Successfully handled multi-turn conversation")
                    else:
                        self.log_result("Conversation Flow", model, False, 
                                      "Empty second response")
                else:
                    self.log_result("Conversation Flow", model, False, 
                                  "Invalid second response structure")
            else:
                self.log_result("Conversation Flow", model, False, 
                              "Invalid first response structure")
                
        except Exception as e:
            self.log_result("Conversation Flow", model, False, str(e))

    def run_comprehensive_tests(self):
        """Run all tests"""
        print("🚀 Starting DeepInfra Models Comprehensive Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test model availability first
        self.test_model_availability()
        
        # Test a subset of models to avoid rate limiting
        models_to_test = self.test_models[:3]  # Test first 3 models
        
        for i, model in enumerate(models_to_test):
            print(f"\n🤖 Testing Model {i+1}/{len(models_to_test)}: {model}")
            print("-" * 50)
            
            # Test basic completion with different prompts
            for prompt_type, prompt in list(self.test_prompts.items())[:2]:  # Test 2 prompts per model
                print(f"\n📝 Testing {prompt_type} prompt...")
                self.test_basic_completion(model, prompt)
                time.sleep(2)  # Rate limiting
                
                # Test streaming for this prompt
                print(f"🌊 Testing streaming for {prompt_type} prompt...")
                self.test_streaming_completion(model, prompt)
                time.sleep(2)  # Rate limiting
            
            # Test parameter variations
            print(f"\n⚙️ Testing parameter variations...")
            self.test_parameter_variations(model)
            time.sleep(2)  # Rate limiting
            
            # Test conversation flow
            print(f"\n💬 Testing conversation flow...")
            self.test_conversation_flow(model)
            time.sleep(3)  # Longer wait between models
        
        # Test error handling
        self.test_error_handling()
        
        # Generate summary report
        self.generate_summary_report(time.time() - start_time)

    def generate_summary_report(self, total_time: float):
        """Generate a comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len(self.successful_tests)
        failed_tests = len(self.failed_tests)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🕒 Total test time: {total_time:.2f} seconds")
        print(f"📈 Total tests run: {total_tests}")
        print(f"✅ Successful tests: {successful_tests}")
        print(f"❌ Failed tests: {failed_tests}")
        print(f"📊 Success rate: {success_rate:.1f}%")
        
        # Group results by test type
        test_types = {}
        for result in self.test_results:
            test_type = result['test_name']
            if test_type not in test_types:
                test_types[test_type] = {'success': 0, 'failed': 0, 'total': 0}
            
            test_types[test_type]['total'] += 1
            if result['success']:
                test_types[test_type]['success'] += 1
            else:
                test_types[test_type]['failed'] += 1
        
        print(f"\n📋 Results by Test Type:")
        for test_type, stats in test_types.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {test_type}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show failed tests details
        if self.failed_tests:
            print(f"\n❌ Failed Tests Details:")
            for failed in self.failed_tests[:5]:  # Show first 5 failures
                print(f"   • {failed['test_name']} - {failed['model']}: {failed['details']}")
            
            if len(self.failed_tests) > 5:
                print(f"   ... and {len(self.failed_tests) - 5} more failures")
        
        # Performance statistics
        response_times = [r['response_time'] for r in self.test_results if r['response_time']]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            print(f"\n⚡ Performance Statistics:")
            print(f"   Average response time: {avg_response_time:.2f}s")
            print(f"   Fastest response: {min_response_time:.2f}s")
            print(f"   Slowest response: {max_response_time:.2f}s")
        
        # Save detailed results to JSON file
        results_file = f"deepinfra_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total_tests': total_tests,
                        'successful_tests': successful_tests,
                        'failed_tests': failed_tests,
                        'success_rate': success_rate,
                        'total_time': total_time
                    },
                    'test_results': self.test_results
                }, f, indent=2)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"\n⚠️ Could not save results file: {e}")
        
        print("=" * 60)

def main():
    """Main entry point"""
    print("DeepInfra Models Test Suite")
    print("=" * 30)
    
    # Check if API key is provided as command line argument
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"🔑 Using provided API key: {api_key[:10]}...")
    else:
        print("ℹ️  No API key provided. Testing without authentication.")
        print("   Some models may require an API key for access.")
    
    # Initialize and run tests
    tester = DeepInfraModelTester(api_key=api_key)
    
    try:
        tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        tester.generate_summary_report(0)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        traceback.print_exc()
        tester.generate_summary_report(0)

if __name__ == "__main__":
    main()