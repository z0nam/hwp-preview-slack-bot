#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["slack-sdk>=3.27", "python-dotenv>=1.0"]
# ///
"""One-shot maintenance: join the bot to every public channel in the workspace.

Requires the bot token (SLACK_BOT_TOKEN in .env) and these scopes on the app:
  - channels:read   (list public channels)
  - channels:join   (self-join public channels)

Already-joined channels and archived ones are skipped. Re-run is idempotent.
"""
from __future__ import annotations

import os
import pathlib
import sys
import time

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("SLACK_BOT_TOKEN not set (check .env)", file=sys.stderr)
        return 2

    client = WebClient(token=token)

    joined: list[str] = []
    already: list[str] = []
    failed: list[tuple[str, str]] = []
    cursor: str | None = None
    seen = 0

    while True:
        resp = client.conversations_list(
            types="public_channel",
            exclude_archived=True,
            limit=200,
            cursor=cursor,
        )
        for ch in resp.get("channels", []):
            seen += 1
            cid = ch["id"]
            name = ch.get("name", cid)
            if ch.get("is_member"):
                already.append(name)
                continue
            try:
                client.conversations_join(channel=cid)
                joined.append(name)
                print(f"  joined  #{name}")
                time.sleep(0.3)
            except SlackApiError as e:
                err = e.response.get("error", str(e))
                failed.append((name, err))
                print(f"  FAILED  #{name}: {err}", file=sys.stderr)
                if err == "ratelimited":
                    retry = int(e.response.headers.get("Retry-After", "5"))
                    print(f"  ... sleeping {retry}s", file=sys.stderr)
                    time.sleep(retry)

        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break

    print()
    print(f"scanned {seen} public channels")
    print(f"  joined:        {len(joined)}")
    print(f"  already in:    {len(already)}")
    print(f"  failed:        {len(failed)}")
    if failed:
        for name, err in failed:
            print(f"    #{name}: {err}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
