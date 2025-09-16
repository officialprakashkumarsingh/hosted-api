#!/usr/bin/env python3
"""
Enhanced Multi-Model CLI Chatbot
Supports GPT-OSS, Grok3API, Z.AI, and Longcat models
"""

import requests
import json
import uuid
import sys
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ModelProvider:
    """Model provider configuration"""
    name: str
    models: List[str]
    available: bool = False
    error_message: Optional[str] = None

class MultiModelChatbot:
    def __init__(self):
        self.providers = {}
        self.current_provider = None
        self.current_model = None
        
        # GPT-OSS configuration
        self.gpt_oss_base_url = "https://api.gpt-oss.com"
        self.gpt_oss_session = requests.Session()
        self.thread_id: Optional[str] = None
        
        # Initialize providers
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all available model providers"""
        
        # 1. GPT-OSS (original)
        try:
            self.gpt_oss_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Origin': 'https://gpt-oss.com',
                'Referer': 'https://gpt-oss.com/',
                'x-reasoning-effort': 'high',
                'x-selected-model': 'gpt-oss-120b',
                'x-show-reasoning': 'true'
            })
            self.providers['gpt-oss'] = ModelProvider(
                name="GPT-OSS",
                models=["gpt-oss-120b"],
                available=True
            )
        except Exception as e:
            self.providers['gpt-oss'] = ModelProvider(
                name="GPT-OSS", 
                models=["gpt-oss-120b"],
                available=False,
                error_message=str(e)
            )
            
        # 2. Grok3API
        try:
            from grok3api.client import GrokClient
            self.grok_client = GrokClient()
            self.providers['grok'] = ModelProvider(
                name="Grok3API",
                models=["grok-3", "grok-3-image"],
                available=True
            )
        except Exception as e:
            self.providers['grok'] = ModelProvider(
                name="Grok3API",
                models=["grok-3", "grok-3-image"], 
                available=False,
                error_message=str(e)
            )
            self.grok_client = None
            
        # 3. Z.AI Python SDK
        try:
            # Import zai modules from the downloaded files
            sys.path.insert(0, '/tmp/model_tests')
            from zai.client import ZAIClient
            self.zai_client = ZAIClient(auto_auth=True)
            self.providers['zai'] = ModelProvider(
                name="Z.AI",
                models=["glm-4.5v", "0727-360B-API"],
                available=True
            )
        except Exception as e:
            self.providers['zai'] = ModelProvider(
                name="Z.AI",
                models=["glm-4.5v", "0727-360B-API"],
                available=False,
                error_message=str(e)
            )
            self.zai_client = None
        
        # 4. Longcat
        try:
            from longcat_client import LongcatClient
            self.longcat_client = LongcatClient()
            self.providers['longcat'] = ModelProvider(
                name="Longcat",
                models=["longcat-chat"],
                available=True
            )
        except Exception as e:
            self.providers['longcat'] = ModelProvider(
                name="Longcat",
                models=["longcat-chat"],
                available=False,
                error_message=str(e)
            )
            self.longcat_client = None
            
        # Set default provider to the first available one
        for provider_key, provider in self.providers.items():
            if provider.available:
                self.current_provider = provider_key
                self.current_model = provider.models[0]
                break
    
    def list_providers(self):
        """List all available providers and their models"""
        print("\n📋 Available Model Providers:")
        print("=" * 50)
        
        for key, provider in self.providers.items():
            status = "✓ Available" if provider.available else f"✗ Unavailable ({provider.error_message})"
            print(f"{provider.name}: {status}")
            for model in provider.models:
                marker = "→" if (key == self.current_provider and model == self.current_model) else " "
                print(f"  {marker} {model}")
        
        if self.current_provider:
            current = self.providers[self.current_provider]
            print(f"\nCurrent: {current.name} - {self.current_model}")
        else:
            print("\n⚠️ No providers available!")
    
    def select_model(self, provider_key: str, model_name: str) -> bool:
        """Select a specific model from a provider"""
        if provider_key not in self.providers:
            print(f"❌ Provider '{provider_key}' not found")
            return False
            
        provider = self.providers[provider_key]
        if not provider.available:
            print(f"❌ Provider '{provider.name}' is not available: {provider.error_message}")
            return False
            
        if model_name not in provider.models:
            print(f"❌ Model '{model_name}' not found in {provider.name}")
            return False
            
        self.current_provider = provider_key
        self.current_model = model_name
        print(f"✓ Switched to {provider.name} - {model_name}")
        return True
    
    def create_thread(self) -> str:
        """Create a new conversation thread (for GPT-OSS)"""
        thread_id = f"thr_{uuid.uuid4().hex[:8]}"
        self.thread_id = thread_id
        return thread_id
    
    def send_message_gpt_oss(self, message: str) -> None:
        """Send message via GPT-OSS API"""
        if not self.thread_id:
            self.create_thread()
        
        payload = {
            "op": "threads.addMessage",
            "params": {
                "input": {
                    "text": message,
                    "content": [{"type": "input_text", "text": message}],
                    "quoted_text": "",
                    "attachments": []
                },
                "threadId": self.thread_id
            }
        }
        
        try:
            response = self.gpt_oss_session.post(
                f"{self.gpt_oss_base_url}/chatkit",
                json=payload,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            self._process_gpt_oss_stream(response)
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error communicating with GPT-OSS API: {e}")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
    
    def send_message_grok(self, message: str) -> None:
        """Send message via Grok3API"""
        if not self.grok_client:
            print("❌ Grok client not available")
            return
            
        try:
            print("\n🤖 Grok:", end=" ", flush=True)
            result = self.grok_client.ask(message)
            
            if result and result.modelResponse and result.modelResponse.message:
                print(result.modelResponse.message)
                
                # Check for generated images
                if result.modelResponse.generatedImages:
                    print(f"\n🎨 Generated {len(result.modelResponse.generatedImages)} image(s)")
                    for i, img in enumerate(result.modelResponse.generatedImages):
                        filename = f"grok_image_{int(time.time())}_{i}.jpg"
                        try:
                            img.save_to(filename)
                            print(f"   Saved: {filename}")
                        except Exception as e:
                            print(f"   Failed to save image {i}: {e}")
            else:
                print("No response received")
                
        except Exception as e:
            print(f"\n❌ Error with Grok API: {e}")
    
    def send_message_zai(self, message: str) -> None:
        """Send message via Z.AI API"""
        if not self.zai_client:
            print("❌ Z.AI client not available")
            return
            
        try:
            print("\n🤖 Z.AI:", end=" ", flush=True)
            response = self.zai_client.simple_chat(
                message=message,
                model=self.current_model,
                enable_thinking=True,
                temperature=0.7,
                max_tokens=500
            )
            
            if response.content:
                print(response.content)
                
                if response.thinking:
                    print(f"\n💭 Thinking: {response.thinking}")
                    
            else:
                print("No response received")
                
        except Exception as e:
            print(f"\n❌ Error with Z.AI API: {e}")
    
    def send_message_longcat(self, message: str) -> None:
        """Send message via Longcat API (streaming)."""
        if not getattr(self, 'longcat_client', None):
            print("❌ Longcat client not available")
            return
        try:
            print("\n🐱 Longcat:", end=" ", flush=True)
            for chunk in self.longcat_client.stream(message):
                if chunk:
                    print(chunk, end='', flush=True)
            print("")
        except Exception as e:
            print(f"\n❌ Error with Longcat API: {e}")
    
    def _process_gpt_oss_stream(self, response: requests.Response) -> None:
        """Process GPT-OSS streaming response"""
        assistant_response = ""
        reasoning_shown = False
        
        print("\n🤖 GPT-OSS:", end=" ", flush=True)
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data: '):
                continue
            
            try:
                data_str = line[6:]
                if data_str.strip() == '':
                    continue
                    
                data = json.loads(data_str)
                
                if data.get('type') == 'thread.item_updated':
                    update = data.get('update', {})
                    
                    # Handle reasoning
                    if update.get('type') == 'cot.entry_added' and not reasoning_shown:
                        entry = update.get('entry', {})
                        if entry.get('type') == 'thought':
                            content = entry.get('content', '')
                            if content and len(content) > 50:
                                print(f"\n💭 Reasoning: {content[:100]}..." if len(content) > 100 else f"\n💭 Reasoning: {content}")
                                reasoning_shown = True
                    
                    # Handle text deltas
                    elif update.get('type') == 'assistant_message.content_part.text_delta':
                        delta = update.get('delta', '')
                        assistant_response += delta
                        print(delta, end='', flush=True)
                
                elif data.get('type') == 'thread.item_done':
                    item = data.get('item', {})
                    if item.get('type') == 'assistant_message':
                        break
                        
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"\n⚠️ Error processing stream: {e}")
                continue
        
        print("\n")
    
    def send_message(self, message: str) -> None:
        """Send message using current provider"""
        if not self.current_provider:
            print("❌ No provider selected")
            return
            
        provider = self.providers[self.current_provider]
        if not provider.available:
            print(f"❌ Current provider {provider.name} is not available")
            return
        
        print(f"Using {provider.name} - {self.current_model}")
        
        if self.current_provider == 'gpt-oss':
            self.send_message_gpt_oss(message)
        elif self.current_provider == 'grok':
            self.send_message_grok(message)
        elif self.current_provider == 'zai':
            self.send_message_zai(message)
        elif self.current_provider == 'longcat':
            self.send_message_longcat(message)
        else:
            print(f"❌ Unknown provider: {self.current_provider}")
    
    def run(self) -> None:
        """Main chat loop"""
        print("🚀 Multi-Model CLI Chatbot")
        print("=" * 50)
        print("Available commands:")
        print("  'quit', 'exit', 'q' - End conversation")
        print("  'providers' - List all providers and models")
        print("  'switch <provider> <model>' - Switch provider/model")
        print("  'new' - Start new conversation thread")
        print("=" * 50)
        
        self.list_providers()
        
        if self.current_provider and self.thread_id is None:
            self.create_thread()
            print(f"\n📝 Started new conversation")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    sys.exit(0)
                elif user_input.lower() == 'providers':
                    self.list_providers()
                    continue
                elif user_input.lower().startswith('switch '):
                    parts = user_input.split()
                    if len(parts) >= 3:
                        provider_key = parts[1]
                        model_name = parts[2]
                        self.select_model(provider_key, model_name)
                    else:
                        print("Usage: switch <provider> <model>")
                        print("Example: switch grok grok-3")
                    continue
                elif user_input.lower() in ['new', 'restart']:
                    if self.current_provider == 'gpt-oss':
                        self.create_thread()
                        print(f"\n📝 Started new conversation thread")
                    else:
                        print(f"\n📝 New conversation (provider: {self.providers[self.current_provider].name})")
                    continue
                elif not user_input:
                    continue
                
                # Send message
                self.send_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 Goodbye!")
                sys.exit(0)

def main():
    """Entry point for the multi-model CLI chatbot"""
    chatbot = MultiModelChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()