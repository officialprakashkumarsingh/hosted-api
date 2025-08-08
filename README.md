[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

# OpenAI-Compatible Proxy (Vercel minimal)

This service exposes an OpenAI-compatible API (`/v1/chat/completions`) and proxies requests to the Vercel minimal API.

Supported models:
- gpt-4o
- gpt-4o-mini
- perplexed
- felo
- gpt-4.1-nano
- gpt-4.1-mini
- deepseek-chat
- deepseek-reasoner
- claude-3.5-haiku
- gemini-2.0-flash
- gemini-2.5-flash
- grok-3-mini

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## Deploy to Render

- Use the button above, or create a Web Service with:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Optional env vars:
  - `REQUEST_TIMEOUT_SECONDS` (default: `30`)
  - `VERCEL_MINIMAL_API_URL` (default: `https://minimal-chatbot.vercel.app/api/chat`)
  - `VERCEL_SESSION_PREFIX` (default: empty)
  - `DEFAULT_MODEL` (default: `gpt-4o`)
  - `PERPLEXED_API_ENDPOINT` (default: `https://d21l5c617zttgr.cloudfront.net/stream_search`)
  - `PERPLEXED_MODEL_ID` (default: `perplexed`)
  - `FELO_API_ENDPOINT` (default: `https://api.felo.ai/search/threads`)
  - `FELO_MODEL_ID` (default: `felo`)
  - `FLOWITH_API_ENDPOINT` (default: `https://edge.flowith.net/ai/chat?mode=general`)
  - `FLOWITH_SYSTEM_PROMPT` (default: `You are a helpful assistant.`)

## Models

```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4o"},
    {"id": "gpt-4o-mini"},
    {"id": "perplexed"},
    {"id": "felo"},
    {"id": "gpt-4.1-nano"},
    {"id": "gpt-4.1-mini"},
    {"id": "deepseek-chat"},
    {"id": "deepseek-reasoner"},
    {"id": "claude-3.5-haiku"},
    {"id": "gemini-2.0-flash"},
    {"id": "gemini-2.5-flash"},
    {"id": "grok-3-mini"}
  ]
}
```

## Usage (OpenAI-compatible)

- Non-streaming:
```bash
curl https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

- Streaming:
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o",
    "stream": true,
    "messages": [{"role": "user", "content": "Write a short poem"}]
  }'
```

- PERPLEXED (streaming):
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "perplexed",
    "stream": true,
    "messages": [{"role": "user", "content": "What is Python?"}]
  }'
```

- FELO (streaming):
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "felo",
    "stream": true,
    "messages": [{"role": "user", "content": "Tell me about AI"}]
  }'
```

- FLOWITH models (streaming):
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4.1-mini",
    "stream": true,
    "messages": [{"role": "user", "content": "Say Hello"}]
  }'
```

Notes:
- FLOWITH may return zstd-compressed streams; the proxy handles this and emits OpenAI-compatible SSE deltas.
- PERPLEXED and FELO streams are converted into incremental deltas based on their respective stream formats.

SDKs: set baseURL to your service and use the desired `model` above. No API key is required.