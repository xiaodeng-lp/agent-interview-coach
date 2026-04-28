from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from commands import handle_command
from engine import generate_interview_reply
from materials import current_source_dir_from_env, ensure_corpus
from model_client import create_model_client
from paths import ENV_PATH
from session_store import ChatSession, record_training_result


def print_reply(text: str) -> None:
    print("\n" + text.strip() + "\n")


async def run_cli(refresh_corpus: bool = False) -> None:
    load_dotenv(ENV_PATH, override=True)
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise RuntimeError(f"请先在 .env 里填写 OPENAI_API_KEY：{ENV_PATH}")

    client = create_model_client()
    source_dir = current_source_dir_from_env()
    max_context_chars = int(os.environ.get("MAX_CONTEXT_CHARS", "18000"))
    corpus = ensure_corpus(source_dir, refresh=refresh_corpus)
    session = ChatSession()
    user_id = "cli-user"

    print_reply(
        "CLI 面试官已启动。可输入：/帮助、/导入资料 路径、/生成背景、开始电话面、/模式 拷打。\n"
        "输入 /退出 结束。"
    )

    while True:
        try:
            user_text = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text in {"/退出", "退出", "exit", "quit"}:
            break

        command_reply, corpus, source_dir = await handle_command(
            user_text,
            session,
            user_id,
            client,
            corpus,
            source_dir,
        )
        if command_reply:
            print_reply(command_reply)
            continue

        print_reply("收到，我先按面试官视角判断一下。")
        reply = generate_interview_reply(
            client=client,
            corpus=corpus,
            session=session,
            user_text=user_text,
            max_context_chars=max_context_chars,
        )
        session.turn_count += 1
        record_training_result(session, user_text, reply)
        session.history.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": reply},
            ]
        )
        session.history = session.history[-16:]
        print_reply(reply)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local CLI fallback for Agent Interview Coach.")
    parser.add_argument("--refresh-corpus", action="store_true", help="重新读取简历资料")
    args = parser.parse_args()

    import asyncio

    asyncio.run(run_cli(refresh_corpus=args.refresh_corpus))


if __name__ == "__main__":
    main()
