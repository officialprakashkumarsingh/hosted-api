import requests
import json
import sys
import time
import random
from typing import List, Dict, Any

class LongcatChatbot:
    def __init__(self):
        self.api_url = "https://longcat.chat/api/v1/chat-completion-oversea"
        self.session = requests.Session()
        self.messages: List[Dict[str, Any]] = []
        self.setup_headers()
    
    def setup_headers(self):
        """Setup the required headers for the API request"""
        self.session.headers.update({
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,en-AU;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://longcat.chat',
            'Pragma': 'no-cache',
            'Referer': 'https://longcat.chat/t',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'accept': 'text/event-stream,application/json',
            'content-type': 'application/json',
            'm-appkey': 'fe_com.sankuai.friday.fe.longcat',
            'm-traceid': str(random.randint(1000000000000000000, 9999999999999999999)),
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'x-client-language': 'en',
            'x-requested-with': 'XMLHttpRequest'
        })
        
        # Set cookies
        self.session.cookies.update({
            '_lxsdk_cuid': '',
            '_lxsdk_s': ''
        })
    
    def generate_message_id(self) -> int:
        """Generate a random message ID"""
        return random.randint(10000000, 99999999)
    
    def send_message(self, content: str) -> str:
        """Send a message to the chatbot and return the response"""
        user_message_id = self.generate_message_id()
        assistant_message_id = self.generate_message_id()
        
        # Add user message to conversation history
        user_message = {
            "role": "user",
            "content": content,
            "chatStatus": "FINISHED",
            "messageId": user_message_id,
            "idType": "custom"
        }
        
        # Add assistant message placeholder
        assistant_message = {
            "role": "assistant",
            "content": "",
            "chatStatus": "LOADING",
            "messageId": assistant_message_id,
            "idType": "custom"
        }
        
        # Prepare the current request messages
        current_messages = self.messages + [user_message, assistant_message]
        
        payload = {
            "content": content,
            "messages": current_messages,
            "reasonEnabled": 0,
            "searchEnabled": 0,
            "regenerate": 0
        }
        
        try:
            response = self.session.post(
                self.api_url,
                data=json.dumps(payload),
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data:'):
                            try:
                                # Remove 'data:' prefix and parse JSON
                                json_str = line_text[5:].strip()
                                if json_str:
                                    data = json.loads(json_str)
                                    
                                    # Extract delta content from the streaming response
                                    if ('choices' in data and 
                                        len(data['choices']) > 0 and 
                                        'delta' in data['choices'][0] and 
                                        'content' in data['choices'][0]['delta'] and
                                        data['choices'][0]['delta']['content'] is not None):
                                        
                                        chunk = data['choices'][0]['delta']['content']
                                        full_response += chunk
                                        print(chunk, end='', flush=True)
                                    
                                    # Check if this is the last message
                                    if data.get('lastOne', False):
                                        break
                                        
                            except json.JSONDecodeError:
                                continue
                
                # Update conversation history
                user_message["chatStatus"] = "FINISHED"
                assistant_message["content"] = full_response
                assistant_message["chatStatus"] = "FINISHED"
                
                self.messages.extend([user_message, assistant_message])
                
                return full_response
                
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"Connection error: {str(e)}"
    
    def clear_history(self):
        """Clear the conversation history"""
        self.messages = []
        print("Conversation history cleared.")
    
    def show_history(self):
        """Show the conversation history"""
        if not self.messages:
            print("No conversation history.")
            return
        
        print("\n--- Conversation History ---")
        for msg in self.messages:
            role = msg["role"].title()
            content = msg["content"]
            print(f"{role}: {content}")
        print("--- End of History ---\n")
    
    def run(self):
        """Run the interactive chatbot"""
        print("🐱 Longcat Terminal Chatbot")
        print("Commands: /help, /clear, /history, /quit")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == '/quit':
                    print("Goodbye! 👋")
                    break
                elif user_input.lower() == '/clear':
                    self.clear_history()
                    continue
                elif user_input.lower() == '/history':
                    self.show_history()
                    continue
                elif user_input.lower() == '/help':
                    print("\nAvailable commands:")
                    print("/help    - Show this help message")
                    print("/clear   - Clear conversation history")
                    print("/history - Show conversation history")
                    print("/quit    - Exit the chatbot")
                    continue
                
                # Send message and get response
                print("\nLongcat: ", end='')
                response = self.send_message(user_input)
                print()  # Add newline after streaming response
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                continue

def main():
    """Main function to run the chatbot"""
    chatbot = LongcatChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()