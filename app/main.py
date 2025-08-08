from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from typing import Dict, Any, List, Optional, Generator, Tuple
import requests
import json
import time
import uuid
import os

app = FastAPI(title="GPT-OSS OpenAI-Compatible Proxy")

BASE_URL = os.getenv("BASE_URL", "https://api.gpt-oss.com")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-oss-120b")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
REASONING_EFFORT_DEFAULT = os.getenv("REASONING_EFFORT_DEFAULT", "high")

# Upstreams
GPT_OSS_MODELS: List[str] = ["gpt-oss-20b", "gpt-oss-120b"]
VERCEL_MODELS: List[str] = ["gpt-4o", "gpt-4o-mini"]
VERCEL_MINIMAL_API_URL = os.getenv("VERCEL_MINIMAL_API_URL", "https://minimal-chatbot.vercel.app/api/chat")
VERCEL_SESSION_PREFIX = os.getenv("VERCEL_SESSION_PREFIX", "")


def _now_unix() -> int:
    return int(time.time())


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def _extract_text_from_messages(messages: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, list):
            content_text_parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    content_text_parts.append(str(item.get("text", "")))
            content = "\n".join(content_text_parts)
        elif not isinstance(content, str):
            content = str(content)
        parts.append(f"{role}: {content}".strip())
    return "\n".join(parts).strip()


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
    return _extract_text_from_messages(messages), None


def _build_gpt_oss_payload_threads_create(input_text: str) -> Dict[str, Any]:
    return {
        "op": "threads.create",
        "params": {
            "input": {
                "text": input_text,
                "content": [{"type": "input_text", "text": input_text}],
                "quoted_text": "",
                "attachments": []
            }
        }
    }


def _new_gpt_oss_session(selected_model: str, reasoning_effort: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Origin": "https://gpt-oss.com",
        "Referer": "https://gpt-oss.com/",
        "x-reasoning-effort": reasoning_effort,
        "x-selected-model": selected_model,
        "x-show-reasoning": "true",
    })
    return s


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
    for m in GPT_OSS_MODELS + VERCEL_MODELS:
        data.append({"id": m, "object": "model", "created": _now_unix(), "owned_by": "proxy"})
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(default=None), x_reasoning_effort: Optional[str] = Header(default=None)):
    body = await request.json()

    requested_model = body.get("model") or DEFAULT_MODEL
    stream = bool(body.get("stream", False))
    messages: List[Dict[str, Any]] = body.get("messages", [])

    if requested_model in VERCEL_MODELS:
        # Route to Vercel minimal API
        user_text, image_url = _last_user_text_and_image(messages) if messages else (body.get("prompt") or "", None)
        session_id = (VERCEL_SESSION_PREFIX + "-") if VERCEL_SESSION_PREFIX else ""
        session_id += str(uuid.uuid4())

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

        payload = {
            "id": session_id,
            "modelId": requested_model,
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
                "model": requested_model,
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
                            # The token is JSON-encoded string; fall back to raw
                            try:
                                clean = json.loads(token)
                            except json.JSONDecodeError:
                                clean = token
                            chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": requested_model,
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

        # Non-stream: accumulate
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
            "model": requested_model,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return JSONResponse(content=response)

    # Route to GPT-OSS
    reasoning_effort = (x_reasoning_effort or body.get("reasoning_effort") or REASONING_EFFORT_DEFAULT)
    # Pick model: keep requested if valid else default first
    selected_model = requested_model if requested_model in GPT_OSS_MODELS else GPT_OSS_MODELS[0]

    input_text = ""
    if messages:
        # Use last user message content for upstream
        input_text, _ = _last_user_text_and_image(messages)
    else:
        input_text = body.get("prompt") or ""

    payload = _build_gpt_oss_payload_threads_create(input_text=input_text)
    session = _new_gpt_oss_session(selected_model=selected_model, reasoning_effort=reasoning_effort)

    def gpt_oss_sse_generator() -> Generator[bytes, None, None]:
        chat_id = _generate_id("chatcmpl")
        created = _now_unix()
        initial_chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": selected_model,
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
            ],
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n".encode("utf-8")

        try:
            with session.post(f"{BASE_URL}/chatkit", json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line or not raw_line.startswith("data: "):
                        continue
                    data_str = raw_line[6:].strip()
                    if not data_str:
                        continue
                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if event.get("type") == "thread.item_updated":
                        update = event.get("update", {})
                        if update.get("type") == "assistant_message.content_part.text_delta":
                            delta_text = update.get("delta", "")
                            chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": selected_model,
                                "choices": [
                                    {"index": 0, "delta": {"content": delta_text}, "finish_reason": None}
                                ],
                            }
                            yield f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                    elif event.get("type") == "thread.item_done":
                        item = event.get("item", {})
                        if item.get("type") == "assistant_message":
                            final_chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": selected_model,
                                "choices": [
                                    {"index": 0, "delta": {}, "finish_reason": "stop"}
                                ],
                            }
                            yield f"data: {json.dumps(final_chunk)}\n\n".encode("utf-8")
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
        return StreamingResponse(gpt_oss_sse_generator(), media_type="text/event-stream")

    # Non-streaming GPT-OSS
    assistant_text_parts: List[str] = []
    try:
        with session.post(f"{BASE_URL}/chatkit", json=payload, stream=True, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                data_str = raw_line[6:].strip()
                if not data_str:
                    continue
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "thread.item_updated":
                    update = event.get("update", {})
                    if update.get("type") == "assistant_message.content_part.text_delta":
                        assistant_text_parts.append(update.get("delta", ""))
                elif event.get("type") == "thread.item_done":
                    item = event.get("item", {})
                    if item.get("type") == "assistant_message":
                        break
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=502, content={"error": {"message": str(e), "type": "bad_gateway"}})

    final_text = "".join(assistant_text_parts)
    response = {
        "id": _generate_id("chatcmpl"),
        "object": "chat.completion",
        "created": _now_unix(),
        "model": selected_model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": final_text}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

    return JSONResponse(content=response)