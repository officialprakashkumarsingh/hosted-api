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
VERCEL_MODELS: List[str] = ["gpt-4o", "gpt-4o-mini"]
VERCEL_MINIMAL_API_URL = os.getenv("VERCEL_MINIMAL_API_URL", "https://minimal-chatbot.vercel.app/api/chat")
VERCEL_SESSION_PREFIX = os.getenv("VERCEL_SESSION_PREFIX", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")


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
        # Initial role chunk
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
        return StreamingResponse(vercel_sse_generator(), media_type="text/event-stream")

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