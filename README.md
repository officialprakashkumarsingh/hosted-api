[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/officialprakashkumarsingh/hosted-api)

# GPT-OSS OpenAI-Compatible Proxy

This service exposes an OpenAI-compatible API (`/v1/chat/completions`) and proxies requests to the GPT-OSS streaming endpoint.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## Deploy to Render

1. Push this repo to GitHub.
2. In Render, create a new Web Service and select this repo.
3. Ensure these settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Optionally set environment variables:
   - `BASE_URL` (default: `https://api.gpt-oss.com`)
   - `DEFAULT_MODEL` (default: `gpt-oss-120b`)
   - `REQUEST_TIMEOUT_SECONDS` (default: `30`)

Alternatively, use the included `render.yaml` as a Blueprint and "Deploy to Render".

## OpenAI-compatible usage

- Endpoint base URL: `https://<your-render-service>.onrender.com`
- List models:

```bash
curl -s https://<host>/v1/models | jq
```

- Chat completions (non-streaming):

```bash
curl https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-oss-120b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

- Chat completions (streaming):

```bash
curl https://<host>/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-oss-120b",
    "stream": true,
    "messages": [
      {"role": "user", "content": "Write a short poem about the sea"}
    ]
  }'
```

You can also use OpenAI SDKs by pointing `baseURL` to this service and any dummy `apiKey` (no key is required by the upstream).