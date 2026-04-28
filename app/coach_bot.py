from __future__ import annotations

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from wechat_clawbot.api.client import close_shared_client
from wechat_clawbot.claude_channel.credentials import load_credentials

from materials import current_source_dir_from_env, ensure_corpus
from model_client import create_model_client
from paths import ENV_PATH
from wechat_channel import run_wechat_bot


def log(message: str) -> None:
    print(f"[coach-bot] {message}", flush=True)


async def run_bot(refresh_corpus: bool = False) -> None:
    load_dotenv(ENV_PATH, override=True)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(f"请先在 .env 里填写 OPENAI_API_KEY：{ENV_PATH}")

    account = load_credentials()
    if not account:
        raise RuntimeError("没有找到微信登录凭据。请先运行：wechat-clawbot-cc setup")

    source_dir = current_source_dir_from_env()
    max_context_chars = int(os.environ.get("MAX_CONTEXT_CHARS", "18000"))
    corpus = ensure_corpus(source_dir, refresh=refresh_corpus)
    client = create_model_client()
    await run_wechat_bot(account, client, source_dir, corpus, max_context_chars)


def main() -> None:
    parser = argparse.ArgumentParser(description="WeChat AI interview coach.")
    parser.add_argument("--refresh-corpus", action="store_true", help="重新读取简历资料")
    args = parser.parse_args()

    try:
        asyncio.run(run_bot(refresh_corpus=args.refresh_corpus))
    except KeyboardInterrupt:
        log("已停止。")
    finally:
        if sys.version_info >= (3, 7):
            try:
                asyncio.run(close_shared_client())
            except Exception:
                pass


if __name__ == "__main__":
    main()
