[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

# OpenAI-Compatible Proxy (Vercel minimal)

This service exposes an OpenAI-compatible API (`/v1/chat/completions`) and proxies requests to multiple AI model providers.

Supported models:
- gpt-4o
- gpt-4o-mini
- perplexed
- felo
- gpt-oss-20b
- gpt-oss-120b

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
  - `GPT_OSS_API_ENDPOINT` (default: `https://api.gpt-oss.com/chatkit`)

## Models

```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4o"},
    {"id": "gpt-4o-mini"},
    {"id": "perplexed"},
    {"id": "felo"},
    {"id": "gpt-oss-20b"},
    {"id": "gpt-oss-120b"}
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

- GPT-OSS models (streaming):
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-oss-120b",
    "stream": true,
    "messages": [{"role": "user", "content": "Say Hello"}]
  }'
```

Notes:
- PERPLEXED and FELO streams are converted into incremental deltas based on their respective stream formats.
- GPT-OSS models use advanced reasoning with thread-based API and LitAgent fingerprinting.

SDKs: set baseURL to your service and use the desired `model` above. No API key is required.