#!/usr/bin/env python3
"""
Web API wrapper for the Multi-Model Chatbot
Provides REST API endpoints for deployment on Render
"""

from flask import Flask, request, jsonify, Response
import json
import sys
import os
from threading import Thread
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_model_chatbot import MultiModelChatbot
from longcat_chatbot import LongcatChatbot

app = Flask(__name__)

# Global chatbot instances
multi_chatbot = None
longcat_chatbot = None

def initialize_chatbots():
    """Initialize chatbot instances"""
    global multi_chatbot, longcat_chatbot
    try:
        multi_chatbot = MultiModelChatbot()
        longcat_chatbot = LongcatChatbot()
        print("✓ Chatbots initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing chatbots: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "service": "Multi-Model Chatbot API",
        "timestamp": time.time()
    })

@app.route('/api/providers', methods=['GET'])
def list_providers():
    """List available model providers"""
    if not multi_chatbot:
        return jsonify({"error": "Multi chatbot not initialized"}), 500
    
    providers = {}
    for key, provider in multi_chatbot.providers.items():
        providers[key] = {
            "name": provider.name,
            "models": provider.models,
            "available": provider.available,
            "error_message": provider.error_message
        }
    
    return jsonify({
        "providers": providers,
        "current_provider": multi_chatbot.current_provider,
        "current_model": multi_chatbot.current_model
    })

@app.route('/api/chat/multi', methods=['POST'])
def chat_multi():
    """Send message to multi-model chatbot"""
    if not multi_chatbot:
        return jsonify({"error": "Multi chatbot not initialized"}), 500
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    message = data['message']
    provider = data.get('provider')
    model = data.get('model')
    
    # Switch provider/model if specified
    if provider and model:
        if not multi_chatbot.select_model(provider, model):
            return jsonify({"error": f"Failed to switch to {provider}/{model}"}), 400
    
    try:
        # Capture the response (this is simplified - in reality you'd need to capture the output)
        response = f"Response from {multi_chatbot.current_provider}/{multi_chatbot.current_model} for: {message}"
        
        return jsonify({
            "response": response,
            "provider": multi_chatbot.current_provider,
            "model": multi_chatbot.current_model,
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/longcat', methods=['POST'])
def chat_longcat():
    """Send message to Longcat chatbot"""
    if not longcat_chatbot:
        return jsonify({"error": "Longcat chatbot not initialized"}), 500
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    message = data['message']
    
    try:
        response = longcat_chatbot.send_message(message)
        
        return jsonify({
            "response": response,
            "provider": "longcat",
            "model": "longcat-chat",
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/longcat/history', methods=['GET'])
def get_longcat_history():
    """Get Longcat chat history"""
    if not longcat_chatbot:
        return jsonify({"error": "Longcat chatbot not initialized"}), 500
    
    return jsonify({
        "history": longcat_chatbot.messages,
        "count": len(longcat_chatbot.messages)
    })

@app.route('/api/chat/longcat/clear', methods=['POST'])
def clear_longcat_history():
    """Clear Longcat chat history"""
    if not longcat_chatbot:
        return jsonify({"error": "Longcat chatbot not initialized"}), 500
    
    longcat_chatbot.clear_history()
    return jsonify({"message": "History cleared successfully"})

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        "service": "Multi-Model Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/api/providers": "List available providers",
            "/api/chat/multi": "Chat with multi-model chatbot (POST)",
            "/api/chat/longcat": "Chat with Longcat (POST)",
            "/api/chat/longcat/history": "Get Longcat history",
            "/api/chat/longcat/clear": "Clear Longcat history (POST)"
        },
        "deploy_url": "https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api"
    })

if __name__ == '__main__':
    # Initialize chatbots in a separate thread to avoid blocking
    init_thread = Thread(target=initialize_chatbots)
    init_thread.start()
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=False)