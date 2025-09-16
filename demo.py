#!/usr/bin/env python3
"""
Demo script showing multi-model chatbot capabilities
"""

from multi_model_chatbot import MultiModelChatbot

def demo():
    """Demonstrate multi-model functionality"""
    print("🎮 Multi-Model Chatbot Demo")
    print("=" * 50)
    
    # Create chatbot instance
    chatbot = MultiModelChatbot()
    
    # Show available providers
    print("\n1. Available Providers:")
    chatbot.list_providers()
    
    # Demo commands
    print("\n2. Available Commands:")
    commands = [
        ("providers", "List all providers and models"),
        ("switch <provider> <model>", "Switch to specific model"),
        ("new", "Start new conversation"),
        ("quit/exit", "End session")
    ]
    
    for command, description in commands:
        print(f"   {command:25} - {description}")
    
    # Show example usage
    print("\n3. Example Usage:")
    print("   👤 You: providers")
    print("   📋 Shows all available models...")
    print("")
    print("   👤 You: switch grok grok-3")
    print("   ✓ Switched to Grok3API - grok-3")
    print("")
    print("   👤 You: Hello!")
    print("   🤖 Grok: Hello! How can I help you today?")
    print("")
    print("   👤 You: switch zai glm-4.5v")
    print("   ✓ Switched to Z.AI - glm-4.5v")
    print("")
    print("   👤 You: What is AI?")
    print("   🤖 Z.AI: Artificial Intelligence is...")
    
    # Show model capabilities
    print("\n4. Model Capabilities:")
    capabilities = [
        ("GPT-OSS (gpt-oss-120b)", "Advanced reasoning, streaming responses"),
        ("Grok3API (grok-3)", "Text generation, reasoning"),
        ("Grok3API (grok-3-image)", "Text + image generation"),
        ("Z.AI (glm-4.5v)", "Visual understanding, analysis"),
        ("Z.AI (0727-360B-API)", "Advanced coding, tool use"),
        ("Longcat (longcat-chat)", "General conversation, streaming responses")
    ]
    
    for model, capability in capabilities:
        print(f"   {model:30} - {capability}")
    
    print("\n5. Integration Status:")
    available_providers = [p for p in chatbot.providers.values() if p.available]
    unavailable_providers = [p for p in chatbot.providers.values() if not p.available]
    
    print(f"   ✓ {len(available_providers)} provider(s) available")
    print(f"   ⚠ {len(unavailable_providers)} provider(s) unavailable (expected in test environment)")
    
    print("\n🚀 Ready to start chatting!")
    print("   Run: python3 multi_model_chatbot.py")

if __name__ == "__main__":
    demo()