#!/usr/bin/env python3
"""
Simple Flask API wrapper focused on Longcat chatbot
"""

from flask import Flask, request, jsonify
import json
import os
import time
import requests
import random

app = Flask(__name__)

class SimpleLongcatChatbot:
    def __init__(self):
        self.api_url = "https://longcat.chat/api/v1/chat-completion-oversea"
        self.session = requests.Session()
        self.messages = []
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
        
        self.session.cookies.update({
            '_lxsdk_cuid': '',
            '_lxsdk_s': ''
        })
    
    def generate_message_id(self):
        return random.randint(10000000, 99999999)
    
    def send_message(self, content):
        """Send a message to the chatbot and return the response"""
        user_message_id = self.generate_message_id()
        assistant_message_id = self.generate_message_id()
        
        user_message = {
            "role": "user",
            "content": content,
            "chatStatus": "FINISHED",
            "messageId": user_message_id,
            "idType": "custom"
        }
        
        assistant_message = {
            "role": "assistant",
            "content": "",
            "chatStatus": "LOADING",
            "messageId": assistant_message_id,
            "idType": "custom"
        }
        
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
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data:'):
                            try:
                                json_str = line_text[5:].strip()
                                if json_str:
                                    data = json.loads(json_str)
                                    
                                    if ('choices' in data and 
                                        len(data['choices']) > 0 and 
                                        'delta' in data['choices'][0] and 
                                        'content' in data['choices'][0]['delta'] and
                                        data['choices'][0]['delta']['content'] is not None):
                                        
                                        chunk = data['choices'][0]['delta']['content']
                                        full_response += chunk
                                    
                                    if data.get('lastOne', False):
                                        break
                                        
                            except json.JSONDecodeError:
                                continue
                
                user_message["chatStatus"] = "FINISHED"
                assistant_message["content"] = full_response
                assistant_message["chatStatus"] = "FINISHED"
                
                self.messages.extend([user_message, assistant_message])
                
                return full_response
                
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Connection error: {str(e)}"

# Global chatbot instance
chatbot = SimpleLongcatChatbot()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Simple Longcat API",
        "timestamp": time.time()
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "Simple Longcat Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/chat": "Chat with Longcat (POST)",
            "/history": "Get chat history",
            "/clear": "Clear chat history (POST)"
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    message = data['message']
    
    try:
        response = chatbot.send_message(message)
        return jsonify({
            "response": response,
            "provider": "longcat",
            "model": "longcat-chat",
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({
        "history": chatbot.messages,
        "count": len(chatbot.messages)
    })

@app.route('/clear', methods=['POST'])
def clear_history():
    chatbot.messages = []
    return jsonify({"message": "History cleared successfully"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Simple Longcat API starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)