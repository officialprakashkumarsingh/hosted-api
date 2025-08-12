#!/usr/bin/env python3
"""
Simple DeepInfra Usage Example
Demonstrates basic usage of the DeepInfra provider
"""

import sys
import os

# Add current directory to path to import our deepinfra_provider
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock webscout dependencies for the example
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

# Mock the webscout modules
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

# Now we can import our DeepInfra provider
try:
    from deepinfra_provider import DeepInfra
    PROVIDER_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Could not import DeepInfra provider: {e}")
    PROVIDER_AVAILABLE = False

def demonstrate_basic_usage():
    """Demonstrate basic usage of DeepInfra provider"""
    print("🚀 DeepInfra Provider Basic Usage Example")
    print("=" * 50)
    
    if not PROVIDER_AVAILABLE:
        print("❌ DeepInfra provider not available")
        return
    
    try:
        # Initialize the client
        client = DeepInfra()
        print("✅ DeepInfra client initialized successfully")
        
        # List available models
        print("\n📋 Available Models (first 10):")
        models = client.models.list()
        for i, model in enumerate(models[:10]):
            print(f"   {i+1}. {model}")
        print(f"   ... and {len(models)-10} more models")
        
        # Example 1: Basic non-streaming completion
        print("\n💬 Example 1: Basic Chat Completion")
        print("-" * 30)
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {"role": "user", "content": "Explain quantum computing in simple terms"}
            ],
            max_tokens=150,
            temperature=0.7,
            stream=False
        )
        
        print(f"Model: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage.total_tokens} total tokens")
        
        # Example 2: Streaming completion
        print("\n🌊 Example 2: Streaming Chat Completion")
        print("-" * 30)
        
        print("Assistant: ", end="", flush=True)
        stream = client.chat.completions.create(
            model="microsoft/phi-4",
            messages=[
                {"role": "user", "content": "Write a haiku about programming"}
            ],
            max_tokens=100,
            temperature=0.8,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()  # New line after streaming
        
        # Example 3: Multi-turn conversation
        print("\n💭 Example 3: Multi-turn Conversation")
        print("-" * 30)
        
        conversation = [
            {"role": "user", "content": "What is the capital of France?"}
        ]
        
        # First turn
        response1 = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=conversation,
            max_tokens=50,
            stream=False
        )
        
        conversation.append({
            "role": "assistant", 
            "content": response1.choices[0].message.content
        })
        conversation.append({
            "role": "user", 
            "content": "What is its population approximately?"
        })
        
        print(f"User: {conversation[0]['content']}")
        print(f"Assistant: {conversation[1]['content']}")
        
        # Second turn
        response2 = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=conversation,
            max_tokens=50,
            stream=False
        )
        
        print(f"User: {conversation[2]['content']}")
        print(f"Assistant: {response2.choices[0].message.content}")
        
        # Example 4: Different models comparison
        print("\n🔄 Example 4: Comparing Different Models")
        print("-" * 30)
        
        prompt = "What is artificial intelligence?"
        test_models = [
            "deepseek-ai/DeepSeek-R1-0528",
            "microsoft/phi-4", 
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        ]
        
        for model in test_models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                    temperature=0.5,
                    stream=False
                )
                
                print(f"\n{model}:")
                print(f"   {response.choices[0].message.content[:100]}...")
                
            except Exception as e:
                print(f"\n{model}: Error - {e}")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_advanced_features():
    """Demonstrate advanced features"""
    print("\n🔧 Advanced Features")
    print("=" * 30)
    
    if not PROVIDER_AVAILABLE:
        return
    
    try:
        client = DeepInfra()
        
        # Custom parameters
        print("🎛️ Testing custom parameters...")
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[{"role": "user", "content": "Be creative and tell me a joke"}],
            max_tokens=100,
            temperature=0.9,  # High creativity
            top_p=0.95,
            stream=False
        )
        
        print(f"High temperature response: {response.choices[0].message.content}")
        
        # Low temperature for consistency
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[{"role": "user", "content": "What is 2+2?"}],
            max_tokens=50,
            temperature=0.1,  # Low for consistency
            stream=False
        )
        
        print(f"Low temperature response: {response.choices[0].message.content}")
        
        print("✅ Advanced features demonstration completed!")
        
    except Exception as e:
        print(f"❌ Error in advanced features: {e}")

def main():
    """Main function"""
    print("DeepInfra Provider Usage Examples")
    print("This demonstrates the usage of the DeepInfra provider")
    print("Note: This example uses mocked HTTP requests for demonstration")
    print()
    
    # Check for API key
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"🔑 Using API key: {api_key[:10]}...")
    else:
        print("ℹ️ No API key provided. Using default configuration.")
        print("   For real usage, provide an API key as the first argument.")
    
    print()
    
    # Run demonstrations
    demonstrate_basic_usage()
    demonstrate_advanced_features()
    
    print("\n" + "=" * 50)
    print("💡 Usage Tips:")
    print("1. Always check response.choices[0].message.content for the actual response")
    print("2. Use streaming for real-time applications")
    print("3. Adjust temperature for creativity vs consistency")
    print("4. Use conversation history for multi-turn chats")
    print("5. Different models have different strengths - experiment!")
    print("=" * 50)

if __name__ == "__main__":
    main()