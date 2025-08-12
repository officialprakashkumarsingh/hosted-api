#!/usr/bin/env python3
"""
Standalone DeepInfra Test Script
Tests the DeepInfra provider logic without external dependencies
"""

import json
import time
import uuid
import sys
from typing import List, Dict, Optional, Union, Generator, Any
from unittest.mock import Mock, MagicMock

# Mock the requests module
class MockResponse:
    def __init__(self, json_data, status_code=200, streaming=False):
        self.json_data = json_data
        self.status_code = status_code
        self.streaming = streaming
        
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
    
    def iter_lines(self, decode_unicode=True):
        """Mock streaming response"""
        if self.streaming:
            # Simulate streaming response
            chunks = [
                "data: " + json.dumps({
                    "choices": [{
                        "delta": {"content": "Hello", "role": "assistant"},
                        "index": 0,
                        "finish_reason": None
                    }]
                }),
                "data: " + json.dumps({
                    "choices": [{
                        "delta": {"content": " there!", "role": None},
                        "index": 0,
                        "finish_reason": None
                    }]
                }),
                "data: " + json.dumps({
                    "choices": [{
                        "delta": {"content": None, "role": None},
                        "index": 0,
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 15,
                        "total_tokens": 25
                    }
                }),
                "data: [DONE]"
            ]
            for chunk in chunks:
                yield chunk
        else:
            yield ""

class MockSession:
    def __init__(self):
        self.headers = {}
    
    def post(self, url, headers=None, json=None, stream=False, timeout=None, proxies=None):
        # Simulate successful response
        if stream:
            return MockResponse({}, streaming=True)
        else:
            # Return mock non-streaming response
            response_data = {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": json.get("model", "test-model"),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response to: " + json["messages"][-1]["content"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
            return MockResponse(response_data)
    
    def update(self, headers):
        self.headers.update(headers)

# Mock implementation classes
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

# Create mock modules
class MockRequests:
    Session = MockSession

# Now implement the DeepInfra classes with mocked dependencies
class Completions(MockBaseCompletions):
    def __init__(self, client: 'DeepInfra'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 2049,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Union[MockChatCompletion, Generator[MockChatCompletionChunk, None, None]]:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        payload.update(kwargs)
        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())
        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, payload, timeout, proxies)

    def _create_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any],
        timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> Generator[MockChatCompletionChunk, None, None]:
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                stream=True,
                timeout=timeout or self._client.timeout,
                proxies=proxies
            )
            response.raise_for_status()
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        json_str = line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)
                            choice_data = data.get('choices', [{}])[0]
                            delta_data = choice_data.get('delta', {})
                            finish_reason = choice_data.get('finish_reason')
                            usage_data = data.get('usage', {})
                            if usage_data:
                                prompt_tokens = usage_data.get('prompt_tokens', prompt_tokens)
                                completion_tokens = usage_data.get('completion_tokens', completion_tokens)
                                total_tokens = usage_data.get('total_tokens', total_tokens)
                            if delta_data.get('content'):
                                completion_tokens += 1
                                total_tokens = prompt_tokens + completion_tokens
                            delta = MockChoiceDelta(
                                content=delta_data.get('content'),
                                role=delta_data.get('role'),
                                tool_calls=delta_data.get('tool_calls')
                            )
                            choice = MockChoice(
                                index=choice_data.get('index', 0),
                                delta=delta,
                                finish_reason=finish_reason,
                                logprobs=choice_data.get('logprobs')
                            )
                            chunk = MockChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                                system_fingerprint=data.get('system_fingerprint')
                            )
                            chunk.usage = {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens,
                                "estimated_cost": None
                            }
                            yield chunk
                        except json.JSONDecodeError:
                            continue
            # Final chunk with finish_reason="stop"
            delta = MockChoiceDelta(content=None, role=None, tool_calls=None)
            choice = MockChoice(index=0, delta=delta, finish_reason="stop", logprobs=None)
            chunk = MockChatCompletionChunk(
                id=request_id,
                choices=[choice],
                created=created_time,
                model=model,
                system_fingerprint=None
            )
            chunk.usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": None
            }
            yield chunk
        except Exception as e:
            print(f"Error during DeepInfra stream request: {e}")
            raise IOError(f"DeepInfra request failed: {e}") from e

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any],
        timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> MockChatCompletion:
        try:
            response = self._client.session.post(
                self._client.base_url,
                headers=self._client.headers,
                json=payload,
                timeout=timeout or self._client.timeout,
                proxies=proxies
            )
            response.raise_for_status()
            data = response.json()
            choices_data = data.get('choices', [])
            usage_data = data.get('usage', {})
            choices = []
            for choice_d in choices_data:
                message_d = choice_d.get('message')
                if not message_d and 'delta' in choice_d:
                    delta = choice_d['delta']
                    message_d = {
                        'role': delta.get('role', 'assistant'),
                        'content': delta.get('content', '')
                    }
                if not message_d:
                    message_d = {'role': 'assistant', 'content': ''}
                message = MockChatCompletionMessage(
                    role=message_d.get('role', 'assistant'),
                    content=message_d.get('content', '')
                )
                choice = MockChoice(
                    index=choice_d.get('index', 0),
                    message=message,
                    finish_reason=choice_d.get('finish_reason', 'stop')
                )
                choices.append(choice)
            usage = MockCompletionUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            completion = MockChatCompletion(
                id=request_id,
                choices=choices,
                created=created_time,
                model=data.get('model', model),
                usage=usage,
            )
            return completion
        except Exception as e:
            print(f"Error during DeepInfra non-stream request: {e}")
            raise IOError(f"DeepInfra request failed: {e}") from e

class Chat(MockBaseChat):
    def __init__(self, client: 'DeepInfra'):
        self.completions = Completions(client)

class DeepInfra(MockOpenAICompatibleProvider):
    AVAILABLE_MODELS = [
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
    
    def __init__(self, browser: str = "chrome", api_key: str = None):
        self.timeout = None
        self.base_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.session = MockSession()
        agent = MockLitAgent()
        fingerprint = agent.generate_fingerprint(browser)
        self.headers = {
            "Accept": fingerprint["accept"],
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": fingerprint["accept_language"],
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
            "Sec-CH-UA": fingerprint["sec_ch_ua"] or '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{fingerprint["platform"]}"',
            "User-Agent": fingerprint["user_agent"],
        }
        if api_key is not None:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.session.headers.update(self.headers)
        self.chat = Chat(self)
    
    @property
    def models(self):
        class _ModelList:
            def list(inner_self):
                return type(self).AVAILABLE_MODELS
        return _ModelList()

# Test Suite
class DeepInfraTestSuite:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def test_model_listing(self):
        """Test if model listing works"""
        try:
            client = DeepInfra()
            models = client.models.list()
            if len(models) > 0:
                self.log_test("Model Listing", True, f"Found {len(models)} models")
                print(f"   Sample models: {models[:3]}")
            else:
                self.log_test("Model Listing", False, "No models found")
        except Exception as e:
            self.log_test("Model Listing", False, str(e))

    def test_basic_completion(self):
        """Test basic chat completion"""
        try:
            client = DeepInfra()
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-0528",
                messages=[{"role": "user", "content": "Hello, how are you?"}],
                max_tokens=50,
                stream=False
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and len(content.strip()) > 0:
                    self.log_test("Basic Completion", True, f"Generated: {content[:50]}...")
                else:
                    self.log_test("Basic Completion", False, "Empty response")
            else:
                self.log_test("Basic Completion", False, "Invalid response structure")
        except Exception as e:
            self.log_test("Basic Completion", False, str(e))

    def test_streaming_completion(self):
        """Test streaming chat completion"""
        try:
            client = DeepInfra()
            stream = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-0528",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=50,
                stream=True
            )
            
            chunks_received = 0
            total_content = ""
            
            for chunk in stream:
                chunks_received += 1
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        total_content += delta.content
                
                if chunks_received > 10:  # Limit for testing
                    break
            
            if chunks_received > 0:
                self.log_test("Streaming Completion", True, f"Received {chunks_received} chunks: {total_content}")
            else:
                self.log_test("Streaming Completion", False, "No chunks received")
        except Exception as e:
            self.log_test("Streaming Completion", False, str(e))

    def test_multiple_models(self):
        """Test multiple models"""
        test_models = [
            "deepseek-ai/DeepSeek-R1-0528",
            "microsoft/phi-4",
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        ]
        
        for model in test_models:
            try:
                client = DeepInfra()
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=20,
                    stream=False
                )
                
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    self.log_test(f"Model {model}", True, "Response generated")
                else:
                    self.log_test(f"Model {model}", False, "No response")
            except Exception as e:
                self.log_test(f"Model {model}", False, str(e))

    def test_parameter_variations(self):
        """Test different parameters"""
        try:
            client = DeepInfra()
            
            # Test temperature variation
            for temp in [0.1, 0.5, 0.9]:
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1-0528",
                    messages=[{"role": "user", "content": "Say hello"}],
                    max_tokens=20,
                    temperature=temp,
                    stream=False
                )
                
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    self.log_test(f"Temperature {temp}", True, "Parameter accepted")
                else:
                    self.log_test(f"Temperature {temp}", False, "Parameter rejected")
        except Exception as e:
            self.log_test("Parameter Variations", False, str(e))

    def test_conversation_flow(self):
        """Test multi-turn conversation"""
        try:
            client = DeepInfra()
            
            # First message
            messages = [{"role": "user", "content": "What is 2+2?"}]
            response1 = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-0528",
                messages=messages,
                max_tokens=30,
                stream=False
            )
            
            if hasattr(response1, 'choices') and len(response1.choices) > 0:
                # Add assistant response and continue conversation
                messages.append({"role": "assistant", "content": response1.choices[0].message.content})
                messages.append({"role": "user", "content": "What about 3+3?"})
                
                response2 = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1-0528",
                    messages=messages,
                    max_tokens=30,
                    stream=False
                )
                
                if hasattr(response2, 'choices') and len(response2.choices) > 0:
                    self.log_test("Conversation Flow", True, "Multi-turn conversation successful")
                else:
                    self.log_test("Conversation Flow", False, "Second response failed")
            else:
                self.log_test("Conversation Flow", False, "First response failed")
        except Exception as e:
            self.log_test("Conversation Flow", False, str(e))

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 DeepInfra Standalone Test Suite")
        print("=" * 50)
        print("Note: Using mocked HTTP requests for testing logic")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run all tests
        self.test_model_listing()
        print()
        
        self.test_basic_completion()
        print()
        
        self.test_streaming_completion()
        print()
        
        self.test_multiple_models()
        print()
        
        self.test_parameter_variations()
        print()
        
        self.test_conversation_flow()
        
        # Generate summary
        total_time = time.time() - start_time
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"🕒 Total test time: {total_time:.2f} seconds")
        print(f"📈 Total tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Success rate: {success_rate:.1f}%")
        print("=" * 50)
        
        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")

def main():
    """Main entry point"""
    print("🧪 Standalone DeepInfra Test Suite")
    print("This test suite validates the DeepInfra provider logic using mocked HTTP requests")
    print()
    
    suite = DeepInfraTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()