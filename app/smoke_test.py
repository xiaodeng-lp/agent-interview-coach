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

from model_client import call_model


ROOT = Path(__file__).resolve().parent


def safe_print(text: str) -> None:
    print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def test_model() -> None:
    load_dotenv(ROOT / ".env", override=True)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("填"):
        raise RuntimeError("请先在 .env 里填写 OPENAI_API_KEY")
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
    )
    reply = call_model(
        client,
        [
            {"role": "system", "content": "你只用一句中文回答。"},
            {"role": "user", "content": "回复：模型连通。"},
        ],
    )
    safe_print(reply[:1000])


async def test_wechat() -> None:
    account = load_credentials()
    if not account:
        raise RuntimeError("没有微信凭据，请先运行 wechat-clawbot-cc setup")
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
