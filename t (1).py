#!/usr/bin/env python3
"""
GPT-OSS CLI Chatbot
A simple command-line chatbot that interfaces with the GPT-OSS API
"""

import requests
import json
import uuid
import sys
import time
from typing import Optional, Dict, Any

class GPTOSSChatbot:
    def __init__(self):
        self.base_url = "https://api.gpt-oss.com"
        self.session = requests.Session()
        self.thread_id: Optional[str] = None
        self.user_id: Optional[str] = None
        
        # Set up session headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Origin': 'https://gpt-oss.com',
            'Referer': 'https://gpt-oss.com/',
            'x-reasoning-effort': 'high',
            'x-selected-model': 'gpt-oss-120b',
            'x-show-reasoning': 'true'
        })
    
    def create_thread(self) -> str:
        """Create a new conversation thread"""
        thread_id = f"thr_{uuid.uuid4().hex[:8]}"
        self.thread_id = thread_id
        return thread_id
    
    def send_message(self, message: str) -> None:
        """Send a message to the chatbot and stream the response"""
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
            response = self.session.post(
                f"{self.base_url}/chatkit",
                json=payload,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # Process the streaming response
            self._process_stream(response)
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error communicating with API: {e}")
        except KeyboardInterrupt:
            print("\n\n⚠️ Request interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
    
    def _process_stream(self, response: requests.Response) -> None:
        """Process the server-sent events stream"""
        assistant_response = ""
        reasoning_shown = False
        
        print("\n🤖 Assistant:", end=" ", flush=True)
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith('data: '):
                continue
            
            try:
                # Parse the JSON data
                data_str = line[6:]  # Remove 'data: ' prefix
                if data_str.strip() == '':
                    continue
                    
                data = json.loads(data_str)
                
                # Handle different event types
                if data.get('type') == 'thread.item_updated':
                    update = data.get('update', {})
                    
                    # Handle reasoning (chain of thought)
                    if update.get('type') == 'cot.entry_added' and not reasoning_shown:
                        entry = update.get('entry', {})
                        if entry.get('type') == 'thought':
                            content = entry.get('content', '')
                            if content and len(content) > 50:  # Only show substantial reasoning
                                print(f"\n💭 Reasoning: {content[:100]}..." if len(content) > 100 else f"\n💭 Reasoning: {content}")
                                reasoning_shown = True
                    
                    # Handle text deltas (streaming response)
                    elif update.get('type') == 'assistant_message.content_part.text_delta':
                        delta = update.get('delta', '')
                        assistant_response += delta
                        print(delta, end='', flush=True)
                
                elif data.get('type') == 'thread.item_done':
                    item = data.get('item', {})
                    if item.get('type') == 'assistant_message':
                        # Response is complete
                        break
                        
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue
            except Exception as e:
                print(f"\n⚠️ Error processing stream: {e}")
                continue
        
        print("\n")  # Add newline after response
    
    def run(self) -> None:
        """Main chat loop"""
        print("🚀 GPT-OSS CLI Chatbot")
        print("=" * 40)
        print("Type 'quit', 'exit', or press Ctrl+C to end the conversation")
        print("Type 'new' to start a new conversation thread")
        print("=" * 40)
        
        # Create initial thread
        self.create_thread()
        print(f"📝 Started new conversation (Thread ID: {self.thread_id})")
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    sys.exit(0)
                elif user_input.lower() in ['new', 'restart']:
                    self.create_thread()
                    print(f"\n📝 Started new conversation (Thread ID: {self.thread_id})")
                    continue
                elif not user_input:
                    continue
                
                # Send message to API
                self.send_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 Goodbye!")
                sys.exit(0)

def main():
    """Entry point for the CLI chatbot"""
    chatbot = GPTOSSChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()