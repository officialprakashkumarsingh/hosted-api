#!/usr/bin/env python3
import argparse
import sys
from typing import List

from gpt_oss_provider import GptOss


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Stream a response from GPT-OSS")
    parser.add_argument("prompt", help="User prompt to send")
    parser.add_argument(
        "--model",
        default="gpt-oss-120b",
        choices=GptOss.available_models,
        help="Model to use",
    )
    parser.add_argument(
        "--reasoning",
        default="high",
        choices=["low", "medium", "high"],
        help="Reasoning effort header value",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional HTTP/HTTPS proxy URL",
    )
    args = parser.parse_args(argv)

    print(f"Model: {args.model}\n")
    _ = GptOss.create_stream(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        reasoning_effort=args.reasoning,
        proxy=args.proxy,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))