#!/usr/bin/env python3
"""
Longcat Chat API client with streaming support.

This module provides a thin wrapper around the public Longcat chat endpoint
to send a message and parse Server-Sent Events (SSE) streaming responses.
"""

from __future__ import annotations

import json
import random
import time
from typing import Dict, Generator, Optional

import requests


class LongcatError(Exception):
    """Raised when the Longcat API returns an error or connection fails."""


class LongcatClient:
    """Longcat chat client with SSE streaming parsing."""

    def __init__(self, timeout: int = 30, verbose: bool = False):
        self.api_url = "https://longcat.chat/api/v1/chat-completion-oversea"
        self.timeout = timeout
        self.verbose = verbose
        self.session = requests.Session()
        self._setup_headers()
        # Minimal cookie placeholders (kept for compatibility)
        self.session.cookies.update({
            "_lxsdk_cuid": "",
            "_lxsdk_s": "",
        })

    def _setup_headers(self) -> None:
        """Setup the required headers for the API request."""
        self.session.headers.update({
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,en-AU;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://longcat.chat",
            "Pragma": "no-cache",
            "Referer": "https://longcat.chat/t",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 "
                "Mobile Safari/537.36"
            ),
            "accept": "text/event-stream,application/json",
            "content-type": "application/json",
            "m-appkey": "fe_com.sankuai.friday.fe.longcat",
            "m-traceid": str(random.randint(1000000000000000000, 9999999999999999999)),
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "x-client-language": "en",
            "x-requested-with": "XMLHttpRequest",
        })

    def _generate_message_id(self) -> int:
        return random.randint(10000000, 99999999)

    def stream(self, content: str) -> Generator[str, None, None]:
        """
        Stream a completion for the given content.

        Yields chunks of assistant text as they arrive.
        """
        user_message_id = self._generate_message_id()
        assistant_message_id = self._generate_message_id()

        user_message = {
            "role": "user",
            "content": content,
            "chatStatus": "FINISHED",
            "messageId": user_message_id,
            "idType": "custom",
        }
        assistant_message = {
            "role": "assistant",
            "content": "",
            "chatStatus": "LOADING",
            "messageId": assistant_message_id,
            "idType": "custom",
        }

        payload = {
            "content": content,
            "messages": [user_message, assistant_message],
            "reasonEnabled": 0,
            "searchEnabled": 0,
            "regenerate": 0,
        }

        try:
            resp = self.session.post(
                self.api_url,
                data=json.dumps(payload),
                timeout=self.timeout,
                stream=True,
            )
        except requests.exceptions.RequestException as exc:
            raise LongcatError(f"Connection error: {exc}") from exc

        if resp.status_code != 200:
            text: Optional[str] = None
            try:
                text = resp.text
            except Exception:
                text = None
            raise LongcatError(f"HTTP {resp.status_code}: {text or 'No body'}")

        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()

            if self.verbose:
                # Print only a small prefix to avoid noise
                print(f"[longcat] << {line[:200]}")

            # Accept both 'data:' and 'data: ' prefixes
            if not (line.startswith("data:") or line.startswith("data: ")):
                continue

            json_str = line.split(":", 1)[1].strip()
            if not json_str:
                continue

            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            # Expecting OpenAI-like delta format per user's provided script
            try:
                choices = data.get("choices") or []
                if choices:
                    delta = choices[0].get("delta") or {}
                    chunk = delta.get("content")
                    if chunk is not None:
                        yield chunk

                if data.get("lastOne", False):
                    break
            except Exception:
                # Be permissive, ignore malformed items
                continue

    def ask(self, content: str) -> str:
        """Convenience method to perform a streaming request and return the full text."""
        full = []
        for chunk in self.stream(content):
            full.append(chunk)
        return "".join(full)


__all__ = ["LongcatClient", "LongcatError"]

