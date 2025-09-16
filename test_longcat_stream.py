#!/usr/bin/env python3
"""
Quick non-interactive streaming test for Longcat client.

This prints the streamed chunks and exits. Intended for CI sanity check.
"""

import sys
import time

from longcat_client import LongcatClient, LongcatError


def main() -> int:
    client = LongcatClient(timeout=30, verbose=False)
    prompt = "Say hello in one short sentence."
    print("Starting Longcat streaming test...\n")
    print("Longcat:", end=" ", flush=True)
    try:
        got_any = False
        start = time.time()
        for chunk in client.stream(prompt):
            got_any = True
            print(chunk, end='', flush=True)
            # safety timeout to avoid hanging in CI runs
            if time.time() - start > 25:
                break
        print("\n\n✓ Streaming completed.")
        if not got_any:
            print("⚠ No chunks received. The API may be rate-limited or blocked in this environment.")
        return 0
    except LongcatError as e:
        print(f"\n✗ LongcatError: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

