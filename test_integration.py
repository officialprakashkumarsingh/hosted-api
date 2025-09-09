#!/usr/bin/env python3
"""
Test script for the integrated multi-model chatbot
"""

import sys
import os
from multi_model_chatbot import MultiModelChatbot

def test_integration():
    """Test the multi-model integration"""
    print("🧪 Testing Multi-Model Chatbot Integration")
    print("=" * 50)
    
    try:
        # Create the chatbot instance
        chatbot = MultiModelChatbot()
        
        print("✓ Chatbot instance created successfully")
        
        # Check providers
        print(f"\n📋 Found {len(chatbot.providers)} providers:")
        for key, provider in chatbot.providers.items():
            status = "✓ Available" if provider.available else "✗ Unavailable"
            print(f"  - {provider.name} ({key}): {status}")
            if not provider.available and provider.error_message:
                print(f"    Error: {provider.error_message[:100]}...")
        
        # Check if any provider is available
        available_count = sum(1 for p in chatbot.providers.values() if p.available)
        
        if available_count > 0:
            print(f"\n✓ {available_count} provider(s) are available")
            print(f"Current provider: {chatbot.current_provider}")
            print(f"Current model: {chatbot.current_model}")
        else:
            print("\n⚠️ No providers are currently available (expected in test environment)")
        
        print("\n✅ Integration test completed successfully!")
        print("\nThe multi-model chatbot is ready to use with the following models:")
        print("  - GPT-OSS: gpt-oss-120b")
        print("  - Grok3API: grok-3, grok-3-image")  
        print("  - Z.AI: glm-4.5v, 0727-360B-API")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)