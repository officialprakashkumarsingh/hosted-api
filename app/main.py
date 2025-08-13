from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from typing import Dict, Any, List, Optional, Generator, Tuple
import requests
import json
import time
import uuid
import os
import zstandard as zstd
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

# ExaChat Free Models (No API Key Required) - Curated Selection
EXACHAT_MODELS: List[str] = [
    # ExaAnswer Models - Search specialized
    "exaanswer",
    
    # Gemini Models - Latest Google AI (selected)
    "gemini-2.0-flash",
    "gemini-2.0-flash-thinking-exp-01-21",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.5-flash",
    
    # OpenRouter Free Models - Premium models without cost (selected)
    "deepseek/deepseek-r1:free",
    
    # Groq Models - Ultra-fast inference (selected)
    "deepseek-r1-distill-llama-70b",
    # "qwen-qwq-32b",  # Temporarily disabled due to HTTP 500 errors
    "meta-llama/llama-4-scout-17b-16e-instruct",
    
    # Cerebras Models - Reliable performance (selected)
    "llama-4-scout-17b-16e-instruct",
]

# Flowith Free Models - TEMPORARILY DISABLED due to rate limiting (429 errors)
# FLOWITH_MODELS: List[str] = [
#     # GPT-5 Models - Next generation (exclusive)
#     "gpt-5-nano",
#     "gpt-5-mini",
#     
#     # GLM Models - Advanced reasoning
#     "glm-4.5",
#     
#     # GPT-OSS Models - Large context with thinking
#     "gpt-oss-120b",
#     "gpt-oss-20b",
#     
#     # Specialized Models
#     "kimi-k2",
#     
#     # GPT-4.1 Models - Enhanced versions
#     "gpt-4.1",
#     "gpt-4.1-mini",
#     
#     # DeepSeek Models - Latest variants
#     "deepseek-chat",
#     "deepseek-reasoner",
#     
#     # Latest Generation
#     "gemini-2.5-flash",
#     "grok-3-mini",
# ]
FLOWITH_MODELS: List[str] = []  # Disabled due to rate limiting

# DeepInfra Working Models (No API Key Required) - 37 models tested working
DEEPINFRA_MODELS: List[str] = [
    # Latest Generation Models
    "moonshotai/Kimi-K2-Instruct",
    "deepseek-ai/DeepSeek-R1-0528-Turbo",
    "Qwen/Qwen3-235B-A22B-Thinking-2507",
    "Qwen/Qwen3-Coder-480B-A35B-Instruct",
    "Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo",
    "Qwen/Qwen3-235B-A22B-Instruct-2507",
    
    # Qwen 3 Models with Thinking
    "Qwen/Qwen3-30B-A3B",
    "Qwen/Qwen3-32B", 
    "Qwen/Qwen3-14B",
    "Qwen/QwQ-32B",
    
    # DeepSeek Models
    "deepseek-ai/DeepSeek-V3-0324-Turbo",
    "deepseek-ai/DeepSeek-Prover-V2-671B",
    "deepseek-ai/DeepSeek-R1-0528",
    "deepseek-ai/DeepSeek-V3-0324",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "deepseek-ai/DeepSeek-V3",
    
    # LLaMA 4 Models (Latest!)
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-Turbo",
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    
    # LLaMA 3.3 Models
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Llama-3.3-70B-Instruct",
    
    # Microsoft Models
    "microsoft/phi-4-reasoning-plus",
    "microsoft/Phi-4-multimodal-instruct",
    "microsoft/phi-4",
    
    # Google Models (Gemma 3)
    "google/gemma-3-27b-it",
    "google/gemma-3-12b-it",
    "google/gemma-3-4b-it",
    
    # Mistral Models
    "mistralai/Devstral-Small-2505",
    "mistralai/Devstral-Small-2507",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    
    # Other Notable Models
    "NovaSky-AI/Sky-T1-32B-Preview",
    "zai-org/GLM-4.5-Air",
    "zai-org/GLM-4.5",
    "zai-org/GLM-4.5V",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allenai/olmOCR-7B-0725-FP8",
]

# HeckAI Working Models (No API Key Required) - 5 models tested working
HECKAI_MODELS: List[str] = [
    # DeepSeek Models
    "deepseek/deepseek-chat",
    "deepseek/deepseek-r1",
    
    # OpenAI Models
    "openai/gpt-4o-mini",
    
    # X.AI Models (Unique Grok Access!)
    "x-ai/grok-3-mini-beta",
    
    # Meta Models
    "meta-llama/llama-4-scout",
]

# SCNet Models (No API Key Required) - 1 model: MiniMax 456B
SCNET_MODELS: List[str] = [
    # MiniMax Models (456B Parameters - MASSIVE!)
    "minimax-text-01-456B",
]

VERCEL_MODELS: List[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "perplexed",
    "felo",
] + GPT_OSS_MODELS + EXACHAT_MODELS + FLOWITH_MODELS + DEEPINFRA_MODELS + HECKAI_MODELS + SCNET_MODELS
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

# Flowith backend configuration - TEMPORARILY DISABLED
# FLOWITH_API_ENDPOINT = "https://edge.flowith.net/ai/chat?mode=general"

# DeepInfra backend configuration
DEEPINFRA_API_ENDPOINT = "https://api.deepinfra.com/v1/openai/chat/completions"

# HeckAI backend configuration
HECKAI_API_ENDPOINT = "https://api.heckai.weight-wave.com/api/ha/v1/chat"

# SCNet backend configuration
SCNET_API_ENDPOINT = "https://www.scnet.cn/acx/chatbot/v1/chat/completion"

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
    elif model.startswith("gemini-"):
        return "gemini"
    elif "/" in model and any(x in model for x in ["deepseek", "meta-llama"]):
        return "openrouter"
    elif model in ["deepseek-r1-distill-llama-70b", "meta-llama/llama-4-scout-17b-16e-instruct"]:
        return "groq"
    elif model in ["llama-4-scout-17b-16e-instruct"]:
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


def _new_flowith_session() -> requests.Session:
    """Create a new Flowith session with proper headers"""
    session = requests.Session()
    agent = LitAgent()
    fingerprint = agent.generate_fingerprint("chrome")
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-type": "application/json",
        "origin": "https://flowith.io",
        "referer": "https://edge.flowith.net/",
        "user-agent": fingerprint["user_agent"],
        "dnt": "1",
        "sec-gpc": "1"
    }
    
    session.headers.update(headers)
    return session


def _build_flowith_payload(conversation_prompt: str, model: str, stream: bool = False) -> Dict[str, Any]:
    """Build the appropriate payload for Flowith API"""
    return {
        "model": model,
        "messages": [
            {"content": "You are a helpful assistant.", "role": "system"},
            {"content": conversation_prompt, "role": "user"}
        ],
        "stream": stream,
        "nodeId": str(uuid.uuid4())
    }


def _new_deepinfra_session() -> Session:
    """Create a new DeepInfra session with proper headers"""
    session = Session()
    agent = LitAgent()
    fingerprint = agent.generate_fingerprint("chrome")
    
    headers = {
        "Accept": fingerprint["accept"],
        "Accept-Language": fingerprint["accept_language"],
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Origin": "https://deepinfra.com",
        "Pragma": "no-cache",
        "Referer": "https://deepinfra.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "X-Deepinfra-Source": "web-embed",
        "User-Agent": fingerprint.get("user_agent", ""),
        "Sec-CH-UA": fingerprint.get("sec_ch_ua", ""),
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": f'"{fingerprint.get("platform", "")}"',
        "X-Forwarded-For": fingerprint.get("x-forwarded-for", ""),
        "X-Real-IP": fingerprint.get("x-real-ip", ""),
        "X-Client-IP": fingerprint.get("x-client-ip", ""),
        "Forwarded": fingerprint.get("forwarded", ""),
        "X-Forwarded-Proto": fingerprint.get("x-forwarded-proto", ""),
        "X-Request-Id": fingerprint.get("x-request-id", ""),
    }
    
    session.headers.update(headers)
    return session


def _build_deepinfra_payload(conversation_prompt: str, model: str, stream: bool = False) -> Dict[str, Any]:
    """Build the appropriate payload for DeepInfra API"""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": conversation_prompt}
        ],
        "stream": stream
    }


def _deepinfra_content_extractor(chunk: Dict[str, Any]) -> Optional[str]:
    """Extract content from DeepInfra stream JSON objects"""
    if isinstance(chunk, dict):
        return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
    return None


def _new_heckai_session() -> Session:
    """Create a new HeckAI session with proper headers"""
    session = Session()
    agent = LitAgent()
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://heck.ai',
        'Referer': 'https://heck.ai/',
        'User-Agent': agent.random(),
    }
    
    session.headers.update(headers)
    return session


def _build_heckai_payload(conversation_prompt: str, model: str, session_id: str, previous_question: str = None, previous_answer: str = None) -> Dict[str, Any]:
    """Build the appropriate payload for HeckAI API"""
    return {
        "model": model,
        "question": conversation_prompt,
        "language": "English",
        "sessionId": session_id,
        "previousQuestion": previous_question,
        "previousAnswer": previous_answer,
        "imgUrls": [],
        "superSmartMode": False
    }


def _new_scnet_session() -> Session:
    """Create a new SCNet session with proper headers and cookies"""
    session = Session()
    
    # Generate a random token for cookies
    import secrets
    token = secrets.token_hex(16)
    
    headers = {
        "accept": "text/event-stream",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "referer": "https://www.scnet.cn/ui/chatbot/temp_1744712663464",
        "origin": "https://www.scnet.cn",
    }
    
    session.headers.update(headers)
    session.cookies.set("Token", token)
    return session


def _build_scnet_payload(conversation_prompt: str, model: str) -> Dict[str, Any]:
    """Build the appropriate payload for SCNet API"""
    # Map model name to model ID
    model_map = {
        "minimax-text-01-456B": 8,  # MiniMax 456B model
    }
    
    model_id = model_map.get(model, 8)  # Default to MiniMax if not found
    
    return {
        "conversationId": "",
        "content": f"SYSTEM: You are a helpful assistant. USER: {conversation_prompt}",
        "thinking": 0,
        "online": 0,
        "modelId": model_id,
        "textFile": [],
        "imageFile": [],
        "clusterId": ""
    }


def _scnet_content_extractor(chunk: Dict[str, Any]) -> Optional[str]:
    """Extract content from SCNet stream JSON objects"""
    if isinstance(chunk, dict):
        return chunk.get("content")
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

    if model in FLOWITH_MODELS:
        # Use Flowith API - TEMPORARILY DISABLED due to rate limiting (429 errors)
        payload = _build_flowith_payload(user_text, model, stream)
        session = _new_flowith_session()

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
                response = session.post(
                    FLOWITH_API_ENDPOINT,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    stream=True
                )
                response.raise_for_status()
                
                # Handle potential ZSTD compression
                encoding = response.headers.get('Content-Encoding', '').lower()
                if encoding == 'zstd':
                    dctx = zstd.ZstdDecompressor()
                    with dctx.stream_reader(response.raw) as reader:
                        while True:
                            chunk = reader.read(4096)
                            if not chunk:
                                break
                            text = chunk.decode('utf-8', errors='replace')
                            if text.strip():
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
                else:
                    for chunk in response.iter_content(chunk_size=4096):
                        if not chunk:
                            break
                        text = chunk.decode('utf-8', errors='replace')
                        if text.strip():
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
                    "message": f"Flowith API error: {str(e)}",
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(flowith_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming request
        try:
            response = session.post(
                FLOWITH_API_ENDPOINT,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            # Handle potential ZSTD compression
            encoding = response.headers.get('Content-Encoding', '').lower()
            if encoding == 'zstd':
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(response.raw) as reader:
                    decompressed = reader.read()
                    full_text = decompressed.decode('utf-8', errors='replace')
            else:
                full_text = response.text
            
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
            return JSONResponse(status_code=502, content={"error": {"message": f"Flowith API error: {str(e)}", "type": "bad_gateway"}})

    if model in DEEPINFRA_MODELS:
        # Use DeepInfra API - 37 models, no API key required, latest AI models
        payload = _build_deepinfra_payload(user_text, model, stream)
        session = _new_deepinfra_session()

        def deepinfra_sse_generator() -> Generator[bytes, None, None]:
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
                    DEEPINFRA_API_ENDPOINT,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    impersonate="chrome110"
                )
                response.raise_for_status()
                
                # Process streaming response with sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=_deepinfra_content_extractor,
                    yield_raw_on_error=False
                )
                
                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
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
                    "message": f"DeepInfra API error: {str(e)}",
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(deepinfra_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming request
        try:
            response = session.post(
                DEEPINFRA_API_ENDPOINT,
                data=json.dumps(payload),
                timeout=REQUEST_TIMEOUT_SECONDS,
                impersonate="chrome110"
            )
            response.raise_for_status()
            
            # Parse non-streaming JSON response
            processed_stream = sanitize_stream(
                data=response.text,
                to_json=True,
                intro_value=None,
                content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(chunk, dict) else None,
                yield_raw_on_error=False
            )
            
            full_text = next(processed_stream, "")
            full_text = full_text if isinstance(full_text, str) else ""
            
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
            return JSONResponse(status_code=502, content={"error": {"message": f"DeepInfra API error: {str(e)}", "type": "bad_gateway"}})

    if model in HECKAI_MODELS:
        # Use HeckAI API - 5 models, no API key required, includes unique Grok 3 access
        session_id = str(uuid.uuid4())
        payload = _build_heckai_payload(user_text, model, session_id)
        session = _new_heckai_session()

        def heckai_sse_generator() -> Generator[bytes, None, None]:
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
                    HECKAI_API_ENDPOINT,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    impersonate="chrome110"
                )
                response.raise_for_status()
                
                # Process streaming response with sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=1024),
                    intro_value="data: ",
                    to_json=False,
                    start_marker="data: [ANSWER_START]",
                    end_marker="data: [ANSWER_DONE]",
                    skip_markers=["data: [RELATE_Q_START]", "data: [RELATE_Q_DONE]", "data: [REASON_START]", "data: [REASON_DONE]"],
                    yield_raw_on_error=True,
                    strip_chars=" \n\r\t",
                    raw=False
                )
                
                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
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
                    "message": f"HeckAI API error: {str(e)}",
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(heckai_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming request
        try:
            response = session.post(
                HECKAI_API_ENDPOINT,
                data=json.dumps(payload),
                timeout=REQUEST_TIMEOUT_SECONDS,
                impersonate="chrome110"
            )
            response.raise_for_status()
            
            # Process non-streaming response with sanitize_stream
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=1024),
                intro_value="data: ",
                to_json=False,
                start_marker="data: [ANSWER_START]",
                end_marker="data: [ANSWER_DONE]",
                skip_markers=["data: [RELATE_Q_START]", "data: [RELATE_Q_DONE]", "data: [REASON_START]", "data: [REASON_DONE]"],
                yield_raw_on_error=True,
                strip_chars=" \n\r\t",
                raw=False
            )
            
            full_text = ""
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
            return JSONResponse(status_code=502, content={"error": {"message": f"HeckAI API error: {str(e)}", "type": "bad_gateway"}})

    if model in SCNET_MODELS:
        # Use SCNet API - 1 model: MiniMax 456B (largest available model)
        payload = _build_scnet_payload(user_text, model)
        session = _new_scnet_session()

        def scnet_sse_generator() -> Generator[bytes, None, None]:
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
                    SCNET_API_ENDPOINT,
                    json=payload,
                    stream=True,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    impersonate="chrome120"
                )
                response.raise_for_status()
                
                # Process streaming response with sanitize_stream
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[done]"],
                    content_extractor=_scnet_content_extractor,
                    yield_raw_on_error=False
                )
                
                for content_chunk in processed_stream:
                    if content_chunk and isinstance(content_chunk, str):
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
                    "message": f"SCNet API error: {str(e)}",
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode("utf-8")
            finally:
                yield b"data: [DONE]\n\n"

        if stream:
            return StreamingResponse(scnet_sse_generator(), media_type="text/event-stream", headers=SSE_HEADERS)

        # Non-streaming request
        try:
            response = session.post(
                SCNET_API_ENDPOINT,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
                impersonate="chrome120"
            )
            response.raise_for_status()
            
            # Process non-streaming response with sanitize_stream
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=None),
                intro_value="data:",
                to_json=True,
                skip_markers=["[done]"],
                content_extractor=_scnet_content_extractor,
                yield_raw_on_error=False
            )
            
            full_text = ""
            for content_chunk in processed_stream:
                if content_chunk and isinstance(content_chunk, str):
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
            return JSONResponse(status_code=502, content={"error": {"message": f"SCNet API error: {str(e)}", "type": "bad_gateway"}})

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