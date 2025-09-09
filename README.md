# Multi-Model Hosted API

A powerful command-line chatbot supporting multiple AI model providers including GPT-OSS, Grok3API, and Z.AI models.

## Features

- **Multiple AI Model Providers**: Support for GPT-OSS, Grok3API (Grok-3), and Z.AI (GLM-4.5v, 0727-360B-API)
- **Dynamic Model Switching**: Switch between different models and providers on-the-fly
- **Image Generation**: Support for image generation via Grok3API
- **Streaming Responses**: Real-time streaming responses where supported
- **Automatic Fallback**: Graceful handling when providers are unavailable
- **Command Interface**: Rich command interface for provider management

## Supported Models

### GPT-OSS
- **gpt-oss-120b**: Advanced reasoning model with streaming responses

### Grok3API  
- **grok-3**: Text generation with reasoning capabilities
- **grok-3-image**: Text and image generation (requires Chrome browser)

### Z.AI
- **glm-4.5v**: Advanced visual understanding and analysis model  
- **0727-360B-API**: Advanced coding and tool use model

## Installation

1. Clone the repository:
```bash
git clone https://github.com/officialprakashkumarsingh/hosted-api.git
cd hosted-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. For Grok3API support, ensure Google Chrome is installed on your system.

## Usage

### Basic Usage

Run the multi-model chatbot:
```bash
python3 multi_model_chatbot.py
```

Run the original GPT-OSS chatbot:
```bash
python3 "t (1).py"
```

### Multi-Model Commands

- **providers** - List all available providers and models
- **switch <provider> <model>** - Switch to a specific provider and model
  - Example: `switch grok grok-3`
  - Example: `switch zai glm-4.5v`  
- **new** - Start a new conversation thread
- **quit/exit** - End the session

### Example Session

```
👤 You: providers
📋 Available Model Providers:
GPT-OSS: ✓ Available  
  → gpt-oss-120b
Grok3API: ✓ Available
    grok-3
    grok-3-image
Z.AI: ✓ Available
    glm-4.5v
    0727-360B-API

👤 You: switch grok grok-3
✓ Switched to Grok3API - grok-3

👤 You: Hello, how are you?
🤖 Grok: Hello! I'm doing well, thank you for asking...
```

## API Integration

The project includes modular support for:

1. **GPT-OSS API** - Original implementation with streaming
2. **Grok3API** - Third-party library with automatic cookie management  
3. **Z.AI SDK** - Complete Python SDK with multiple models

## Project Structure

```
hosted-api/
├── multi_model_chatbot.py   # Enhanced multi-provider chatbot
├── t (1).py                 # Original GPT-OSS chatbot
├── zai/                     # Z.AI Python SDK
│   ├── client.py
│   ├── models.py
│   ├── core/
│   ├── operations/
│   └── utils/
├── requirements.txt         # Dependencies
├── test_integration.py      # Integration tests
└── README.md               # This file
```

## Dependencies

- **requests**: HTTP client for API communication
- **grok3api**: Official Grok3 API client library
- **selenium** (via grok3api): Browser automation for cookie management
- **undetected-chromedriver** (via grok3api): Chrome automation

## Error Handling

The chatbot gracefully handles:
- Network connectivity issues  
- Provider unavailability
- Authentication failures
- Browser dependencies (for Grok3API)

When a provider is unavailable, the system automatically falls back to available providers.

## Testing

Run integration tests:
```bash
python3 test_integration.py  
```

## Notes

- **Grok3API** requires Google Chrome browser for automatic cookie management
- **Z.AI** requires network access to chat.z.ai for authentication
- **GPT-OSS** works independently without additional dependencies
- All providers support graceful degradation when unavailable

## Contributing

Contributions are welcome! Please ensure your code follows the existing patterns and includes appropriate error handling.

## License

This project integrates multiple third-party libraries. Please check individual library licenses:
- Grok3API: Check [boykopovar/Grok3API](https://github.com/boykopovar/Grok3API) 
- Z.AI SDK: Check [iotbackdoor/zai-python-sdk](https://github.com/iotbackdoor/zai-python-sdk)