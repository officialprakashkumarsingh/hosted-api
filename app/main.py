from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from typing import Dict, Any, List, Optional, Generator
import requests
import json
import time
import uuid
import os

app = FastAPI(title="GPT-OSS OpenAI-Compatible Proxy")

BASE_URL = os.getenv("BASE_URL", "https://api.gpt-oss.com")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-oss-120b")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


def _now_unix() -> int:
    return int(time.time())


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def _extract_text_from_messages(messages: List[Dict[str, Any]]) -> str:
    # Concatenate the conversation into a single prompt string, marking roles
    parts: List[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, list):
            # OpenAI style array of content parts
            content_text_parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    content_text_parts.append(str(item.get("text", "")))
            content = "\n".join(content_text_parts)
        elif not isinstance(content, str):
            content = str(content)
        parts.append(f"{role}: {content}".strip())
    return "\n".join(parts).strip()


def _build_gpt_oss_payload(thread_id: str, input_text: str) -> Dict[str, Any]:
    return {
        "op": "threads.addMessage",
        "params": {
            "input": {
                "text": input_text,
                "content": [{"type": "input_text", "text": input_text}],
                "quoted_text": "",
                "attachments": []
            },
            "threadId": thread_id
        }
    }


def _new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Origin": "https://gpt-oss.com",
        "Referer": "https://gpt-oss.com/",
        "x-reasoning-effort": "high",
        "x-selected-model": DEFAULT_MODEL,
        "x-show-reasoning": "true",
    })
    return s


@app.get("/")
def root() -> PlainTextResponse:
    return PlainTextResponse("ok")


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    # Minimal OpenAI-compatible model listing
    model_id = DEFAULT_MODEL
    return {
        "object": "list",
        "data": [
            {"id": model_id, "object": "model", "created": _now_unix(), "owned_by": "gpt-oss"}
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(default=None), x_thread_id: Optional[str] = Header(default=None)):
    body = await request.json()

    # Extract parameters
    model = body.get("model") or DEFAULT_MODEL
    stream = bool(body.get("stream", False))
    messages: List[Dict[str, Any]] = body.get("messages", [])

    # Optional support for passing thread id through header or extra_body
    thread_id = x_thread_id or body.get("extra_body", {}).get("thread_id") or f"thr_{uuid.uuid4().hex[:8]}"

    # Convert messages to input text (flattened conversation)
    input_text = _extract_text_from_messages(messages) if messages else (body.get("prompt") or "")

    # Build outbound request
    payload = _build_gpt_oss_payload(thread_id=thread_id, input_text=input_text)

    # Create a new session per request to isolate headers
    session = _new_session()
    # Ensure model header matches requested model if provided
    if model:
        session.headers["x-selected-model"] = model

    def sse_event_generator() -> Generator[bytes, None, None]:
        chat_id = _generate_id("chatcmpl")
        created = _now_unix()
        # Send an initial role chunk for strict clients
        initial_chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
            ]
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

                    # Stream deltas
                    if event.get("type") == "thread.item_updated":
                        update = event.get("update", {})
                        if update.get("type") == "assistant_message.content_part.text_delta":
                            delta_text = update.get("delta", "")
                            chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {"index": 0, "delta": {"content": delta_text}, "finish_reason": None}
                                ]
                            }
                            yield f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                    elif event.get("type") == "thread.item_done":
                        item = event.get("item", {})
                        if item.get("type") == "assistant_message":
                            # Send final stop chunk
                            final_chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {"index": 0, "delta": {}, "finish_reason": "stop"}
                                ]
                            }
                            yield f"data: {json.dumps(final_chunk)}\n\n".encode("utf-8")
                            break
        except requests.exceptions.RequestException as e:
            error_chunk = {
                "id": _generate_id("err"),
                "object": "error",
                "created": _now_unix(),
                "message": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
        finally:
            # Ensure termination token for OpenAI streaming protocol
            yield b"data: [DONE]\n\n"

    if stream:
        return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

    # Non-streaming mode: accumulate text and return one-shot response
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
        return JSONResponse(status_code=502, content={
            "error": {"message": str(e), "type": "bad_gateway"}
        })

    final_text = "".join(assistant_text_parts)
    response = {
        "id": _generate_id("chatcmpl"),
        "object": "chat.completion",
        "created": _now_unix(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": final_text},
                "finish_reason": "stop"
            }
        ],
        "usage": {
            # Unknown token counts; returning zeros to adhere to schema shape some clients expect
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

    return JSONResponse(content=response)