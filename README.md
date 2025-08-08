[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

# GPT-OSS OpenAI-Compatible Proxy

This service exposes an OpenAI-compatible API (`/v1/chat/completions`) and proxies requests to multiple upstreams:
- gpt-oss-20b, gpt-oss-120b → GPT-OSS chatkit
- gpt-4o, gpt-4o-mini → Vercel minimal API (`https://minimal-chatbot.vercel.app/api/chat`)

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
  - `BASE_URL` (default: `https://api.gpt-oss.com`)
  - `DEFAULT_MODEL` (default: `gpt-oss-120b`)
  - `REQUEST_TIMEOUT_SECONDS` (default: `30`)
  - `REASONING_EFFORT_DEFAULT` (default: `high`)
  - `VERCEL_MINIMAL_API_URL` (default: `https://minimal-chatbot.vercel.app/api/chat`)
  - `VERCEL_SESSION_PREFIX` (default: empty)

## Models

```json
{
  "object": "list",
  "data": [
    {"id": "gpt-oss-20b"},
    {"id": "gpt-oss-120b"},
    {"id": "gpt-4o"},
    {"id": "gpt-4o-mini"}
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

- Image input (for gpt-4o / gpt-4o-mini):
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

SDKs: set baseURL to your service and use the desired `model` above. No API key is required for these upstreams by default.