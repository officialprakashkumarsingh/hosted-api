import json
import uuid
from typing import Any, Dict, Iterable, Optional

import requests

try:
    # Prefer user-provided utilities if they exist
    from webscout.litagent import LitAgent  # type: ignore
    from webscout.AIutel import sanitize_stream  # type: ignore
except Exception:  # Fallbacks if webscout is not available
    LitAgent = None  # type: ignore

    def sanitize_stream(
        line_iter: Iterable[str],
        intro_value: str = "data: ",
        to_json: bool = True,
        skip_markers: Optional[Iterable[str]] = None,
        strip_chars: Optional[str] = None,
        content_extractor=None,
        yield_raw_on_error: bool = False,
        encoding: str = "utf-8",
        raw: bool = False,
    ) -> Iterable[str]:
        """Minimal SSE sanitizer compatible with the expected GPT-OSS payloads.
        Yields string deltas extracted via the provided content_extractor.
        """
        skip_markers = set(skip_markers or [])
        for line in line_iter:
            try:
                if not line:
                    continue
                if isinstance(line, bytes):
                    try:
                        line = line.decode(encoding, errors="ignore")
                    except Exception:
                        continue
                if strip_chars:
                    line = line.strip(strip_chars)
                if not line.startswith(intro_value):
                    continue
                payload = line[len(intro_value) :]
                if any(marker in payload for marker in skip_markers):
                    continue
                if not payload.strip():
                    continue
                if to_json:
                    try:
                        data = json.loads(payload)
                    except Exception:
                        if yield_raw_on_error:
                            yield payload
                        continue
                    if content_extractor:
                        extracted = content_extractor(data)
                        if extracted is not None:
                            yield extracted
                    elif raw:
                        yield data
                else:
                    yield payload
            except Exception:
                # Swallow and continue on malformed lines
                continue


class GptOss:
    api_endpoint = "https://api.gpt-oss.com/chatkit"

    available_models = ["gpt-oss-20b", "gpt-oss-120b"]

    @classmethod
    def _default_headers(cls) -> Dict[str, str]:
        # Use LitAgent if available to generate fingerprint-like headers
        if LitAgent is not None:
            try:
                headers = LitAgent().generate_fingerprint()  # type: ignore[attr-defined]
                # Ensure required headers exist/override as needed
                headers.setdefault(
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                )
                headers.setdefault("Origin", "https://gpt-oss.com")
                headers.setdefault("Referer", "https://gpt-oss.com/")
                headers.setdefault("accept", "text/event-stream")
                return headers
            except Exception:
                pass
        # Fallback headers
        return {
            "Content-Type": "application/json",
            "accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Origin": "https://gpt-oss.com",
            "Referer": "https://gpt-oss.com/",
        }

    @classmethod
    def create_stream(
        cls,
        model: str,
        messages: Iterable[Dict[str, Any]],
        reasoning_effort: str = "high",
        proxy: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Create a streaming chat completion using GPT-OSS SSE endpoint.

        - model: one of available_models; falls back to the first if unknown
        - messages: list of {role, content}; last user message is sent
        - reasoning_effort: header value, e.g., "low" | "medium" | "high"
        - proxy: optional proxy URL applied to http/https
        """
        messages = list(messages)
        if not messages:
            raise ValueError("messages must contain at least one message")
        user_message = messages[-1].get("content", "")

        # Align with provided script: always create a new thread on each call
        payload: Dict[str, Any] = {
            "op": "threads.create",
            "params": {
                "input": {
                    "text": user_message,
                    "content": [{"type": "input_text", "text": user_message}],
                    "quoted_text": "",
                    "attachments": [],
                }
            },
        }

        headers = cls._default_headers()
        headers.update(
            {
                "x-reasoning-effort": str(reasoning_effort),
                "x-selected-model": model if model in cls.available_models else cls.available_models[0],
                "x-show-reasoning": "true",
            }
        )

        proxies = {"http": proxy, "https": proxy} if proxy else None

        full_response_content = ""
        try:
            with requests.post(
                cls.api_endpoint,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
                proxies=proxies,
            ) as response:
                response.raise_for_status()

                for chunk in sanitize_stream(
                    response.iter_lines(decode_unicode=True),
                    intro_value="data: ",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    strip_chars=None,
                    content_extractor=lambda d: d.get("update", {}).get("delta")
                    if d.get("type") == "thread.item_updated"
                    and d.get("update", {}).get("type")
                    == "assistant_message.content_part.text_delta"
                    else None,
                    yield_raw_on_error=False,
                    encoding="utf-8",
                    raw=False,
                ):
                    if chunk:
                        print(chunk, end="", flush=True)
                        full_response_content += chunk
        except Exception as exc:
            print(f"Error: {exc}")
        finally:
            # Ensure a newline after the stream finishes for clean stdout
            print()

        return full_response_content


if __name__ == "__main__":
    # Simple manual test
    GptOss.create_stream(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )