from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from wechat_clawbot.api.client import close_shared_client, get_updates
from wechat_clawbot.claude_channel.credentials import load_credentials
from wechat_clawbot.storage.sync_buf import get_sync_buf_file_path, load_get_updates_buf

from model_client import SAFE_MODEL_ERROR, call_model, has_raw_response_markers


ROOT = Path(__file__).resolve().parent
MODEL_SMOKE_PHRASE = "MODEL_SMOKE_OK"
MAX_MODEL_SMOKE_CHARS = 200


def safe_print(text: str) -> None:
    print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def validate_model_smoke_reply(reply: str) -> None:
    cleaned = reply.strip() if isinstance(reply, str) else ""
    if not cleaned:
        raise RuntimeError("model smoke failed: empty response")
    if cleaned == SAFE_MODEL_ERROR:
        raise RuntimeError("model smoke failed: response parser returned safe error")
    if len(cleaned) > MAX_MODEL_SMOKE_CHARS:
        raise RuntimeError(f"model smoke failed: response too long ({len(cleaned)} chars)")
    if has_raw_response_markers(cleaned):
        raise RuntimeError("model smoke failed: response looks like raw provider object")
    if MODEL_SMOKE_PHRASE not in cleaned:
        raise RuntimeError(f"model smoke failed: expected phrase {MODEL_SMOKE_PHRASE!r} not found")


def test_model() -> None:
    load_dotenv(ROOT / ".env", override=True)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-REPLACE"):
        raise RuntimeError("Please set OPENAI_API_KEY in app/.env before model smoke testing.")
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
    )
    reply = call_model(
        client,
        [
            {"role": "system", "content": "Reply with exactly the requested smoke-test token and no other text."},
            {"role": "user", "content": f"Reply exactly: {MODEL_SMOKE_PHRASE}"},
        ],
    )
    validate_model_smoke_reply(reply)
    safe_print(f"model ok: {reply.strip()}")


async def test_wechat() -> None:
    account = load_credentials()
    if not account:
        raise RuntimeError("No WeChat credentials found. Run wechat-clawbot-cc setup first.")
    sync_path = get_sync_buf_file_path(account.account_id)
    buf = load_get_updates_buf(sync_path) or ""
    resp = await get_updates(account.base_url, account.token, buf, timeout_ms=5000)
    print(f"wechat ok: ret={resp.ret}, msgs={len(resp.msgs or [])}, has_buf={bool(resp.get_updates_buf)}")
    await close_shared_client()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="store_true")
    parser.add_argument("--wechat", action="store_true")
    args = parser.parse_args()

    if not args.model and not args.wechat:
        args.model = True
        args.wechat = True
    if args.model:
        test_model()
    if args.wechat:
        asyncio.run(test_wechat())


if __name__ == "__main__":
    main()
