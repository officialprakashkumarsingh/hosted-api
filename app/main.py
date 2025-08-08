from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from typing import Dict, Any, List, Optional, Generator, Tuple
import requests
import json
import time
import uuid
import os

app = FastAPI(title="OpenAI-Compatible Proxy (Vercel minimal)")

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

# Supported models (Vercel minimal API)
FLOWITH_MODELS: List[str] = [
    "gpt-4.1-nano",
    "gpt-4.1-mini",
    "deepseek-chat",
    "deepseek-reasoner",
    "claude-3.5-haiku",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "grok-3-mini",
]
VERCEL_MODELS: List[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "perplexed",
    "felo",
] + FLOWITH_MODELS
VERCEL_MINIMAL_API_URL = os.getenv("VERCEL_MINIMAL_API_URL", "https://minimal-chatbot.vercel.app/api/chat")
VERCEL_SESSION_PREFIX = os.getenv("VERCEL_SESSION_PREFIX", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")

# PERPLEXED backend configuration
PERPLEXED_MODEL_ID = os.getenv("PERPLEXED_MODEL_ID", "perplexed")
PERPLEXED_API_ENDPOINT = os.getenv("PERPLEXED_API_ENDPOINT", "https://d21l5c617zttgr.cloudfront.net/stream_search")

# FELO backend configuration
FELO_MODEL_ID = os.getenv("FELO_MODEL_ID", "felo")
FELO_API_ENDPOINT = os.getenv("FELO_API_ENDPOINT", "https://api.felo.ai/search/threads")

# FLOWITH backend configuration
FLOWITH_API_ENDPOINT = os.getenv("FLOWITH_API_ENDPOINT", "https://edge.flowith.net/ai/chat?mode=general")
FLOWITH_SYSTEM_PROMPT = os.getenv("FLOWITH_SYSTEM_PROMPT", "You are a helpful assistant.")

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


def _new_flowith_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-type": "application/json",
        "origin": "https://flowith.io",
        "referer": "https://edge.flowith.net/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "dnt": "1",
        "sec-gpc": "1",
    })
    return s


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
                                        chunk_payload = {
                                            "id": chat_id,
                                            "object": "chat.completion.chunk",
                                            "created": created,
                                            "model": model,
                                            "choices": [
                                                {"index": 0, "delta": {"content": delta}, "finish_reason": None}
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
                                    chunk_payload = {
                                        "id": chat_id,
                                        "object": "chat.completion.chunk",
                                        "created": created,
                                        "model": model,
                                        "choices": [
                                            {"index": 0, "delta": {"content": delta}, "finish_reason": None}
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

    if model in FLOWITH_MODELS:
        session = _new_flowith_session()
        node_id = str(uuid.uuid4())
        payload = {
            "model": model,
            "messages": [
                {"content": FLOWITH_SYSTEM_PROMPT, "role": "system"},
                {"content": user_text, "role": "user"},
            ],
            "stream": True if stream else False,
            "nodeId": node_id,
        }

        def flowith_sse_generator() -> Generator[bytes, None, None]:
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
                with session.post(FLOWITH_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    resp.raise_for_status()
                    encoding = (resp.headers.get("Content-Encoding") or "").lower()
                    if encoding == "zstd":
                        try:
                            import zstandard as zstd  # lazy import
                            dctx = zstd.ZstdDecompressor()
                            with dctx.stream_reader(resp.raw) as reader:
                                while True:
                                    chunk = reader.read(512)
                                    if not chunk:
                                        break
                                    text = chunk.decode("utf-8", errors="replace")
                                    if not text:
                                        continue
                                    chunk_payload = {
                                        "id": chat_id,
                                        "object": "chat.completion.chunk",
                                        "created": created,
                                        "model": model,
                                        "choices": [
                                            {"index": 0, "delta": {"content": text}, "finish_reason": None}
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
                    else:
                        for chunk in resp.iter_content(chunk_size=512):
                            if not chunk:
                                break
                            text = chunk.decode("utf-8", errors="replace")
                            if not text:
                                continue
                            chunk_payload = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {"index": 0, "delta": {"content": text}, "finish_reason": None}
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
            return StreamingResponse(flowith_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming
        full_text = ""
        try:
            with session.post(FLOWITH_API_ENDPOINT, json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                resp.raise_for_status()
                encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if encoding == "zstd":
                    try:
                        import zstandard as zstd
                        dctx = zstd.ZstdDecompressor()
                        with dctx.stream_reader(resp.raw) as reader:
                            decompressed = reader.read()
                            full_text = decompressed.decode("utf-8", errors="replace")
                    except Exception as e:
                        return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})
                else:
                    full_text = resp.text
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