# Multi-Model AI Chatbot API 🤖

A powerful Python application that provides access to multiple AI model providers including GPT-OSS, Grok3API, Z.AI, and Longcat through both CLI and REST API interfaces.

## 🚀 One-Click Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

Click the button above to deploy this application to Render with zero configuration!

## ✨ Features

- **Multiple AI Model Providers**: GPT-OSS, Grok3API, Z.AI, and Longcat
- **REST API**: Full REST API for web integration
- **CLI Interface**: Interactive command-line chatbot
- **Streaming Responses**: Real-time streaming for better UX
- **Auto-Deployment**: One-click deployment to Render
- **Health Monitoring**: Built-in health check endpoints
- **Conversation Management**: History tracking and clearing

## 🔧 Supported Models

### GPT-OSS
- **Model**: gpt-oss-120b
- **Features**: Streaming, reasoning display
- **Status**: ✅ Active

### Grok3API  
- **Models**: grok-3, grok-3-image
- **Features**: Text & image generation
- **Status**: ✅ Active

### Z.AI
- **Models**: glm-4.5v, 0727-360B-API
- **Features**: Thinking process, custom parameters
- **Status**: ✅ Active

### Longcat
- **Model**: longcat-chat
- **Features**: Fast streaming responses
- **Status**: ✅ Active

## 🌐 API Endpoints

### Base URL
```
https://your-app-name.onrender.com
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API documentation |
| GET | `/health` | Health check |
| GET | `/api/providers` | List available providers |
| POST | `/api/chat/multi` | Chat with multi-model bot |
| POST | `/api/chat/longcat` | Chat with Longcat |
| GET | `/api/chat/longcat/history` | Get chat history |
| POST | `/api/chat/longcat/clear` | Clear chat history |

### Example API Usage

#### Chat with Longcat
```bash
curl -X POST https://your-app.onrender.com/api/chat/longcat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

#### List Providers
```bash
curl https://your-app.onrender.com/api/providers
```

#### Chat with Multi-Model (specify provider)
```bash
curl -X POST https://your-app.onrender.com/api/chat/multi \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "provider": "gpt-oss",
    "model": "gpt-oss-120b"
  }'
```

## 🖥️ Local Development

### Installation
```bash
git clone https://github.com/officialprakashkumarsingh/hosted-api.git
cd hosted-api
pip install -r requirements.txt
```

### Run CLI Mode
```bash
python multi_model_chatbot.py
```

### Run API Server
```bash
python app.py
```

### CLI Commands
- `quit`, `exit`, `q` - End conversation
- `providers` - List all providers and models
- `switch <provider> <model>` - Switch provider/model
- `new`, `restart` - Start new conversation

## 🚀 Deployment

### Render (Recommended)
1. Click the "Deploy to Render" button above
2. Connect your GitHub account
3. Your app will be deployed automatically!

### Manual Deployment
1. Fork this repository
2. Create a new Web Service on Render
3. Connect your forked repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Python Version**: 3.11.0

## 📁 Project Structure

```
├── app.py                 # Flask API server
├── multi_model_chatbot.py # Main CLI chatbot
├── longcat_chatbot.py     # Standalone Longcat bot
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── test_longcat.py       # Test suite
└── zai/                  # Z.AI SDK modules
    ├── client.py
    ├── models.py
    ├── custom_models.py
    └── ...
```

## 🔧 Environment Variables

The application works out of the box with no required environment variables. Optional configurations:

- `PORT` - Server port (set automatically by Render)
- `PYTHON_VERSION` - Python version (3.11.0 recommended)

## 🧪 Testing

Run the test suite:
```bash
python test_longcat.py
```

## 📊 Health Monitoring

Check application health:
```bash
curl https://your-app.onrender.com/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Multi-Model Chatbot API",
  "timestamp": 1640995200.0
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/officialprakashkumarsingh/hosted-api/issues)
- 📖 **Documentation**: This README
- 🚀 **Deploy**: Use the one-click deploy button above

## 🏗️ Built With

- **Python 3.11** - Core language
- **Flask** - Web framework
- **Gunicorn** - WSGI server
- **Render** - Deployment platform
- **Multiple AI APIs** - GPT-OSS, Grok3API, Z.AI, Longcat

---

**Ready to deploy?** Click the deploy button at the top! 🚀