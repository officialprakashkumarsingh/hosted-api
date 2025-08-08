[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

# OpenAI-Compatible Proxy (Vercel minimal)

This service exposes an OpenAI-compatible API (`/v1/chat/completions`) and proxies requests to the Vercel minimal API.

Supported models:
- gpt-4o
- gpt-4o-mini
- perplexed

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

## Models

```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4o"},
    {"id": "gpt-4o-mini"},
    {"id": "perplexed"}
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

- Image input:
```bash
curl -N https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o-mini",
    "stream": true,
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "https://picsum.photos/400"}}
      ]
    }]
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

SDKs: set baseURL to your service and use the desired `model` above. No API key is required.