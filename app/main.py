from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from typing import Dict, Any, List, Optional, Generator, Tuple
import requests
import json
import time
import uuid
import os
from webscout.litagent import LitAgent
from webscout.AIutel import sanitize_stream
from curl_cffi.requests import Session

app = FastAPI(title="OpenAI-Compatible Proxy (Vercel minimal)")

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

# Supported models
GPT_OSS_MODELS: List[str] = [
    "gpt-oss-20b",
    "gpt-oss-120b",
]

# ExaChat Free Models (No API Key Required) - Multiple Providers
EXACHAT_MODELS: List[str] = [
    # ExaAnswer Models - Search specialized
    "exaanswer",

    # XAI Models - Advanced reasoning
    "grok-3-mini-beta",
    
    # Gemini Models - Latest Google AI
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp-image-generation",
    "gemini-2.0-flash-thinking-exp-01-21",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-pro-exp-02-05",
    "gemini-2.5-flash",
    
    # OpenRouter Free Models - Premium models without cost
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-4-maverick:free",
    
    # Groq Models - Ultra-fast inference
    "deepseek-r1-distill-llama-70b",
    "deepseek-r1-distill-qwen-32b",
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.2-90b-vision-preview",
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "qwen-2.5-32b",
    "qwen-2.5-coder-32b",
    "qwen-qwq-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    
    # Cerebras Models - Reliable performance
    "llama3.1-8b",
    "llama-3.3-70b",
    "llama-4-scout-17b-16e-instruct",
    "qwen-3-32b",
]

VERCEL_MODELS: List[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "perplexed",
    "felo",
] + GPT_OSS_MODELS + EXACHAT_MODELS
VERCEL_MINIMAL_API_URL = os.getenv("VERCEL_MINIMAL_API_URL", "https://minimal-chatbot.vercel.app/api/chat")
VERCEL_SESSION_PREFIX = os.getenv("VERCEL_SESSION_PREFIX", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")

# PERPLEXED backend configuration
PERPLEXED_MODEL_ID = os.getenv("PERPLEXED_MODEL_ID", "perplexed")
PERPLEXED_API_ENDPOINT = os.getenv("PERPLEXED_API_ENDPOINT", "https://d21l5c617zttgr.cloudfront.net/stream_search")

# FELO backend configuration
FELO_MODEL_ID = os.getenv("FELO_MODEL_ID", "felo")
FELO_API_ENDPOINT = os.getenv("FELO_API_ENDPOINT", "https://api.felo.ai/search/threads")

# GPT-OSS backend configuration
GPT_OSS_API_ENDPOINT = os.getenv("GPT_OSS_API_ENDPOINT", "https://api.gpt-oss.com/chatkit")

# ExaChat backend configuration
EXACHAT_API_ENDPOINTS = {
    "exaanswer": "https://ayle.chat/api/exaanswer",
    "gemini": "https://ayle.chat/api/gemini", 
    "openrouter": "https://ayle.chat/api/openrouter",
    "groq": "https://ayle.chat/api/groq",
    "cerebras": "https://ayle.chat/api/cerebras",
    "xai": "https://ayle.chat/api/xai",
}

# SSE headers to improve real-time delivery and disable proxy buffering
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _now_unix() -> int:
    return int(time.time())


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def _last_user_text_and_image(messages: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
    last_text = ""
    image_url: Optional[str] = None
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, list):
                text_parts: List[str] = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(str(item.get("text", "")))
                        elif item.get("type") == "image_url":
                            url_obj = item.get("image_url") or {}
                            if isinstance(url_obj, dict):
                                image_url = url_obj.get("url") or image_url
                last_text = "\n".join(text_parts)
                return last_text, image_url
            if isinstance(content, str):
                return content, None
            return str(content), None
    return "", None


def _new_vercel_session(session_id: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://minimal-chatbot.vercel.app",
        "Referer": f"https://minimal-chatbot.vercel.app/chat/{session_id}",
    })
    return s


def _new_perplexed_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://d37ozmhmvu2kcg.cloudfront.net",
        "referer": "https://d37ozmhmvu2kcg.cloudfront.net/",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
        # Reasonable desktop UA
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    })
    return s


def _new_felo_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://felo.ai",
        "referer": "https://felo.ai/",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    })
    return s


def _new_exachat_session() -> Session:
    """Create a new ExaChat session with proper headers"""
    session = Session()
    agent = LitAgent()
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://ayle.chat/",
        "referer": "https://ayle.chat/",
        "user-agent": agent.random(),
    }
    
    session.headers.update(headers)
    session.cookies.update({"session": uuid.uuid4().hex})
    return session


def _get_exachat_provider_from_model(model: str) -> str:
    """Determine the ExaChat provider based on the model name"""
    if model == "exaanswer":
        return "exaanswer"
    elif model == "grok-3-mini-beta":
        return "xai"
    elif model.startswith("gemini-"):
        return "gemini"
    elif "/" in model and any(x in model for x in ["mistralai", "deepseek", "google", "meta-llama"]):
        return "openrouter"
    elif model in ["deepseek-r1-distill-llama-70b", "deepseek-r1-distill-qwen-32b", "gemma2-9b-it", 
                   "llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.2-3b-preview", 
                   "llama-3.2-90b-vision-preview", "llama-3.3-70b-specdec", "llama-3.3-70b-versatile",
                   "llama3-70b-8192", "llama3-8b-8192", "qwen-2.5-32b", "qwen-2.5-coder-32b", 
                   "qwen-qwq-32b", "meta-llama/llama-4-scout-17b-16e-instruct"]:
        return "groq"
    elif model in ["llama3.1-8b", "llama-3.3-70b", "llama-4-scout-17b-16e-instruct", "qwen-3-32b"]:
        return "cerebras"
    return "groq"  # Default fallback


def _build_exachat_payload(conversation_prompt: str, model: str, provider: str) -> Dict[str, Any]:
    """Build the appropriate payload based on the ExaChat provider"""
    if provider == "exaanswer":
        return {
            "query": conversation_prompt,
            "messages": []
        }
    elif provider == "gemini":
        return {
            "query": conversation_prompt,
            "model": model,
            "messages": []
        }
    elif provider == "cerebras":
        return {
            "query": conversation_prompt,
            "model": model,
            "messages": []
        }
    else:  # openrouter, groq, xai
        return {
            "query": conversation_prompt + "\n",  # Add newline for better formatting
            "model": model,
            "messages": []
        }


def _exachat_content_extractor(chunk: Dict[str, Any]) -> Optional[str]:
    """Extract content from ExaChat stream JSON objects"""
    if isinstance(chunk, dict):
        return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
    return None





@app.get("/")
def root() -> PlainTextResponse:
    return PlainTextResponse("ok")


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    data = []
    for m in VERCEL_MODELS:
        data.append({"id": m, "object": "model", "created": _now_unix(), "owned_by": "proxy"})
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    requested_model = body.get("model") or DEFAULT_MODEL
    stream = bool(body.get("stream", False))
    messages: List[Dict[str, Any]] = body.get("messages", [])

    # Validate model
    model = requested_model if requested_model in VERCEL_MODELS else VERCEL_MODELS[0]

    # Prepare input
    if messages:
        user_text, image_url = _last_user_text_and_image(messages)
    else:
        user_text = body.get("prompt") or ""
        image_url = None

    # Route by model
    if model == PERPLEXED_MODEL_ID:
        session = _new_perplexed_session()
        payload = {"user_prompt": user_text}

        def perplexed_sse_generator() -> Generator[bytes, None, None]:
            chat_id = _generate_id("chatcmpl")
            created = _now_unix()
            initial_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

            buffer = ""
            accumulated_text = ""
            try:
                with session.post(PERPLEXED_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    resp.raise_for_status()
                    for chunk in resp.iter_content(chunk_size=64, decode_unicode=True):
                        if not chunk:
                            continue
                        buffer += chunk
                        sep = "[/PERPLEXED-SEPARATOR]"
                        while sep in buffer:
                            part, buffer = buffer.split(sep, 1)
                            part = part.strip()
                            if not part:
                                continue
                            try:
                                data = json.loads(part)
                            except json.JSONDecodeError:
                                continue
                            if isinstance(data, dict) and data.get("success") and data.get("answer"):
                                new_text = str(data.get("answer") or "")
                                if len(new_text) > len(accumulated_text):
                                    delta = new_text[len(accumulated_text):]
                                    accumulated_text = new_text
                                    if delta:
                                        step = 32
                                        for i in range(0, len(delta), step):
                                            piece = delta[i:i+step]
                                            chunk_payload = {
                                                "id": chat_id,
                                                "object": "chat.completion.chunk",
                                                "created": created,
                                                "model": model,
                                                "choices": [
                                                    {"index": 0, "delta": {"content": piece}, "finish_reason": None}
                                                ],
                                            }
                                            yield f"data: {json.dumps(chunk_payload)}\n\n".encode("utf-8")
            except requests.exceptions.RequestException as e:
                error_chunk = {
                    "id": _generate_id("err"),
                    "object": "error",
                    "created": _now_unix(),
                    "message": str(e),
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(perplexed_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming: accumulate deltas
        full_text = ""
        buffer = ""
        accumulated_text = ""
        try:
            with session.post(PERPLEXED_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=64, decode_unicode=True):
                    if not chunk:
                        continue
                    buffer += chunk
                    sep = "[/PERPLEXED-SEPARATOR]"
                    while sep in buffer:
                        part, buffer = buffer.split(sep, 1)
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            data = json.loads(part)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(data, dict) and data.get("success") and data.get("answer"):
                            new_text = str(data.get("answer") or "")
                            if len(new_text) > len(accumulated_text):
                                delta = new_text[len(accumulated_text):]
                                accumulated_text = new_text
                                full_text += delta
        except requests.exceptions.RequestException as e:
            return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})

        response = {
            "id": _generate_id("chatcmpl"),
            "object": "chat.completion",
            "created": _now_unix(),
            "model": model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return JSONResponse(content=response)

    if model == FELO_MODEL_ID:
        session = _new_felo_session()
        payload = {
            "query": user_text,
            "search_uuid": uuid.uuid4().hex,
            "lang": "",
            "agent_lang": "en",
            "search_options": {
                "langcode": "en-US",
                "search_image": True,
                "search_video": True,
            },
            "search_video": True,
            "model": "",
            "contexts_from": "google",
            "auto_routing": True,
        }

        def felo_sse_generator() -> Generator[bytes, None, None]:
            chat_id = _generate_id("chatcmpl")
            created = _now_unix()
            initial_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

            accumulated_text = ""
            try:
                with session.post(FELO_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    resp.raise_for_status()
                    for raw_line in resp.iter_lines(decode_unicode=True):
                        if not raw_line:
                            continue
                        line = raw_line.strip()
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(data, dict) and data.get("type") == "answer":
                            inner = data.get("data") or {}
                            new_text = inner.get("text")
                            if not isinstance(new_text, str):
                                continue
                            if len(new_text) > len(accumulated_text):
                                delta = new_text[len(accumulated_text):]
                                accumulated_text = new_text
                                if delta:
                                    step = 32
                                    for i in range(0, len(delta), step):
                                        piece = delta[i:i+step]
                                        chunk_payload = {
                                            "id": chat_id,
                                            "object": "chat.completion.chunk",
                                            "created": created,
                                            "model": model,
                                            "choices": [
                                                {"index": 0, "delta": {"content": piece}, "finish_reason": None}
                                            ],
                                        }
                                        yield f"data: {json.dumps(chunk_payload)}\n\n".encode("utf-8")
            except requests.exceptions.RequestException as e:
                error_chunk = {
                    "id": _generate_id("err"),
                    "object": "error",
                    "created": _now_unix(),
                    "message": str(e),
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(felo_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming: accumulate deltas
        full_text = ""
        accumulated_text = ""
        try:
            with session.post(FELO_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict) and data.get("type") == "answer":
                        inner = data.get("data") or {}
                        new_text = inner.get("text")
                        if not isinstance(new_text, str):
                            continue
                        if len(new_text) > len(accumulated_text):
                            delta = new_text[len(accumulated_text):]
                            accumulated_text = new_text
                            full_text += delta
        except requests.exceptions.RequestException as e:
            return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})

        response = {
            "id": _generate_id("chatcmpl"),
            "object": "chat.completion",
            "created": _now_unix(),
            "model": model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return JSONResponse(content=response)

    if model in GPT_OSS_MODELS:
        # Use GPT-OSS API with proper thread creation
        data = {
            "op": "threads.create",
            "params": {
                "input": {
                    "text": user_text,
                    "content": [{"type": "input_text", "text": user_text}],
                    "quoted_text": "",
                    "attachments": []
                }
            }
        }

        # Generate headers using LitAgent
        headers = LitAgent().generate_fingerprint()
        headers.update({
            "accept": "text/event-stream",
            "x-reasoning-effort": "high",
            "x-selected-model": model if model in GPT_OSS_MODELS else GPT_OSS_MODELS[0],
            "x-show-reasoning": "true"
        })

        def gpt_oss_sse_generator() -> Generator[bytes, None, None]:
            chat_id = _generate_id("chatcmpl")
            created = _now_unix()
            initial_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

            try:
                with requests.post(GPT_OSS_API_ENDPOINT, headers=headers, json=data, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                    response.raise_for_status()
                    for chunk in sanitize_stream(
                        response.iter_lines(),
                        intro_value="data: ",
                        to_json=True,
                        skip_markers=["[DONE]"],
                        strip_chars=None,
                        content_extractor=lambda d: d.get('update', {}).get('delta') if d.get('type') == 'thread.item_updated' and d.get('update', {}).get('type') == 'assistant_message.content_part.text_delta' else None,
                        yield_raw_on_error=False,
                        encoding="utf-8",
                        raw=False
                    ):
                        if chunk:
                            chunk_payload = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {"index": 0, "delta": {"content": chunk}, "finish_reason": None}
                                ],
                            }
                            yield f"data: {json.dumps(chunk_payload)}\n\n".encode("utf-8")
            except Exception as e:
                error_chunk = {
                    "id": _generate_id("err"),
                    "object": "error",
                    "created": _now_unix(),
                    "message": str(e),
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(gpt_oss_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming: accumulate all chunks
        full_text = ""
        try:
            with requests.post(GPT_OSS_API_ENDPOINT, headers=headers, json=data, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                response.raise_for_status()
                for chunk in sanitize_stream(
                    response.iter_lines(),
                    intro_value="data: ",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    strip_chars=None,
                    content_extractor=lambda d: d.get('update', {}).get('delta') if d.get('type') == 'thread.item_updated' and d.get('update', {}).get('type') == 'assistant_message.content_part.text_delta' else None,
                    yield_raw_on_error=False,
                    encoding="utf-8",
                    raw=False
                ):
                    if chunk:
                        full_text += chunk
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})

        response = {
            "id": _generate_id("chatcmpl"),
            "object": "chat.completion",
            "created": _now_unix(),
            "model": model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return JSONResponse(content=response)

    if model in EXACHAT_MODELS:
        # Use ExaChat API - Multiple providers, no API key required
        provider = _get_exachat_provider_from_model(model)
        endpoint = EXACHAT_API_ENDPOINTS[provider]
        payload = _build_exachat_payload(user_text, model, provider)
        
        session = _new_exachat_session()

        def exachat_sse_generator() -> Generator[bytes, None, None]:
            chat_id = _generate_id("chatcmpl")
            created = _now_unix()
            initial_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

            try:
                response = session.post(
                    endpoint,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    stream=True,
                    impersonate="chrome120"
                )
                response.raise_for_status()
                
                # Process streaming response with sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value=None,
                    to_json=True,
                    content_extractor=_exachat_content_extractor,
                    yield_raw_on_error=False,
                    raw=False
                )
                
                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
                        # Clean up escaped characters
                        content_chunk = content_chunk.replace('\\\\', '\\').replace('\\"', '"')
                        chunk_payload = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [
                                {"index": 0, "delta": {"content": content_chunk}, "finish_reason": None}
                            ],
                        }
                        yield f"data: {json.dumps(chunk_payload)}\n\n".encode("utf-8")
                        
            except Exception as e:
                error_chunk = {
                    "id": _generate_id("err"),
                    "object": "error", 
                    "created": _now_unix(),
                    "message": f"ExaChat API error: {str(e)}",
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                session.close()
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(exachat_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming request
        session = _new_exachat_session()
        try:
            response = session.post(
                endpoint,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
                stream=True,
                impersonate="chrome120"
            )
            response.raise_for_status()
            
            # Collect all chunks into full response
            full_text = ""
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=None),
                intro_value=None,
                to_json=True,
                content_extractor=_exachat_content_extractor,
                yield_raw_on_error=False,
                raw=False
            )
            
            for content_chunk in processed_stream:
                if content_chunk and isinstance(content_chunk, str):
                    content_chunk = content_chunk.replace('\\\\', '\\').replace('\\"', '"')
                    full_text += content_chunk
            
            response_obj = {
                "id": _generate_id("chatcmpl"),
                "object": "chat.completion",
                "created": _now_unix(),
                "model": model,
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            return JSONResponse(content=response_obj)
            
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": {"message": f"ExaChat API error: {str(e)}", "type": "bad_gateway"}})
        finally:
            session.close()

    # Build message payload matching minimal-chatbot expectations
    if image_url:
        message_obj: Dict[str, Any] = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    else:
        message_obj = {"role": "user", "content": user_text}

    session_id = (VERCEL_SESSION_PREFIX + "-") if VERCEL_SESSION_PREFIX else ""
    session_id += str(uuid.uuid4())

    payload = {
        "id": session_id,
        "modelId": model,
        "messages": [message_obj],
    }

    session = _new_vercel_session(session_id=session_id)

    def vercel_sse_generator() -> Generator[bytes, None, None]:
        chat_id = _generate_id("chatcmpl")
        created = _now_unix()
        initial_chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
            ],
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

        try:
            with session.post(VERCEL_MINIMAL_API_URL, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if line.startswith("0:"):
                        token = line[2:].strip()
                        try:
                            clean = json.loads(token)
                        except json.JSONDecodeError:
                            clean = token
                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model,
                            "choices": [
                                {"index": 0, "delta": {"content": clean}, "finish_reason": None}
                            ],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                    elif line.startswith("e:"):
                        break
        except requests.exceptions.RequestException as e:
            error_chunk = {
                "id": _generate_id("err"),
                "object": "error",
                "created": _now_unix(),
                "message": str(e),
            }
            yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
        finally:
            yield b"data: [DONE]\n\n"

    if stream:
        return StreamingResponse(vercel_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

    # Non-streaming: accumulate
    full_text = ""
    try:
        with session.post(VERCEL_MINIMAL_API_URL, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if line.startswith("0:"):
                    token = line[2:].strip()
                    try:
                        clean = json.loads(token)
                    except json.JSONDecodeError:
                        clean = token
                    full_text += clean
                elif line.startswith("e:"):
                    break
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})

    response = {
        "id": _generate_id("chatcmpl"),
        "object": "chat.completion",
        "created": _now_unix(),
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    return JSONResponse(content=response)