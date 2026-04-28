from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from openai import OpenAI
from wechat_clawbot.api.client import WeixinApiOptions, get_updates
from wechat_clawbot.api.types import MessageType
from wechat_clawbot.auth.accounts import CDN_BASE_URL
from wechat_clawbot.claude_channel.credentials import AccountData
from wechat_clawbot.messaging.inbound import body_from_item_list
from wechat_clawbot.messaging.send import markdown_to_plain_text, send_message_weixin
from wechat_clawbot.storage.sync_buf import get_sync_buf_file_path, load_get_updates_buf, save_get_updates_buf

from commands import handle_command
from engine import generate_interview_reply
from interview_corpus import CorpusChunk
from materials import ensure_corpus, import_wechat_file, update_env_value
from paths import MATERIALS_INBOX
from session_store import ChatSession, load_sessions, record_training_result, save_sessions


def log(message: str) -> None:
    print(f"[coach-bot] {message}", flush=True)


def split_wechat_text(text: str, limit: int = 1600) -> list[str]:
    text = markdown_to_plain_text(text).strip()
    if not text:
        return ["我这边没有生成有效回复，你再发一次。"]
    parts: list[str] = []
    while len(text) > limit:
        split_at = max(text.rfind("\n", 0, limit), text.rfind("。", 0, limit))
        if split_at < limit // 2:
            split_at = limit
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        parts.append(text)
    return parts


async def send_text(to_user: str, text: str, opts: WeixinApiOptions) -> None:
    for part in split_wechat_text(text):
        await send_message_weixin(to_user, part, opts)
        await asyncio.sleep(0.3)


async def run_wechat_bot(
    account: AccountData,
    client: OpenAI,
    source_dir: Path,
    corpus: list[CorpusChunk],
    max_context_chars: int,
) -> None:
    sessions = load_sessions()
    sync_path = get_sync_buf_file_path(account.account_id)
    get_updates_buf = load_get_updates_buf(sync_path) or ""
    allowed_user_id = os.environ.get("ALLOWED_WECHAT_USER_ID", "").strip()
    cdn_base_url = os.environ.get("WECHAT_CDN_BASE_URL", CDN_BASE_URL)
    seen: set[str] = set()

    log(f"微信账号已载入: {account.account_id}")
    log("开始监听微信消息。按 Ctrl+C 停止。")

    while True:
        resp = await get_updates(
            base_url=account.base_url,
            token=account.token,
            get_updates_buf=get_updates_buf,
        )
        if resp.get_updates_buf:
            get_updates_buf = resp.get_updates_buf
            save_get_updates_buf(sync_path, get_updates_buf)

        for msg in resp.msgs or []:
            if msg.message_type != MessageType.USER:
                continue
            user_id = msg.from_user_id or ""
            if allowed_user_id and user_id != allowed_user_id:
                continue

            body = body_from_item_list(msg.item_list).strip()
            dedupe_key = str(msg.message_id or msg.client_id or f"{user_id}:{msg.create_time_ms}:{body}")
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            if len(seen) > 1000:
                seen = set(list(seen)[-500:])

            opts = WeixinApiOptions(
                base_url=account.base_url,
                token=account.token,
                context_token=msg.context_token,
            )
            session = sessions.setdefault(user_id, ChatSession())

            uploaded = await import_wechat_file(msg.item_list, cdn_base_url)
            if uploaded:
                MATERIALS_INBOX.mkdir(parents=True, exist_ok=True)
                update_env_value("RESUME_SOURCE_DIR", str(MATERIALS_INBOX))
                source_dir = MATERIALS_INBOX
                corpus = ensure_corpus(source_dir, refresh=True)
                save_sessions(sessions)
                await send_text(
                    user_id,
                    f"已收到资料文件：{uploaded.name}\n"
                    f"已自动导入资料入口：{MATERIALS_INBOX}\n"
                    f"当前抽取到 {len(corpus)} 个资料片段。\n"
                    "下一步可以发：/生成背景",
                    opts,
                )
                continue

            if not body:
                continue

            log(f"收到 {user_id}: {body[:80]}")
            if body.strip() in {"/刷新", "刷新"}:
                corpus = ensure_corpus(source_dir, refresh=True)
                await send_text(user_id, f"已刷新资料库，共 {len(corpus)} 个资料片段。", opts)
                continue

            try:
                command_reply, corpus, source_dir = await handle_command(
                    body,
                    session,
                    user_id,
                    client,
                    corpus,
                    source_dir,
                )
            except Exception as exc:
                log(f"命令处理失败: {exc}")
                command_reply = f"命令处理失败：{exc}"

            if command_reply:
                save_sessions(sessions)
                await send_text(user_id, command_reply, opts)
                continue

            prefix = "收到。我按当前阶段和模式追问。" if session.mode == "只面试模式" else "收到，我先按面试官视角判断一下。"
            await send_text(user_id, prefix, opts)
            try:
                reply = generate_interview_reply(
                    client=client,
                    corpus=corpus,
                    session=session,
                    user_text=body,
                    max_context_chars=max_context_chars,
                )
            except Exception as exc:
                log(f"模型调用失败: {exc}")
                reply = f"模型 API 调用失败：{exc}\n\n先检查 .env 里的 OPENAI_API_KEY、OPENAI_BASE_URL、MODEL_NAME、MODEL_API_STYLE。"

            session.turn_count += 1
            record_training_result(session, body, reply)
            session.history.extend(
                [
                    {"role": "user", "content": body},
                    {"role": "assistant", "content": reply},
                ]
            )
            session.history = session.history[-16:]
            session.updated_at = time.time()
            save_sessions(sessions)
            await send_text(user_id, reply, opts)
