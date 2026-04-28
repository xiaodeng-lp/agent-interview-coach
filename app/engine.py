from __future__ import annotations

from openai import OpenAI

from interview_corpus import CorpusChunk, select_context
from model_client import call_model
from prompts import MODES, STAGES, SYSTEM_PROMPT
from session_store import ChatSession, format_weaknesses


def build_messages(session: ChatSession, user_text: str, context: str) -> list[dict[str, str]]:
    context_prompt = f"""当前面试阶段：{session.stage}
阶段目标：{STAGES.get(session.stage, "")}
当前训练模式：{session.mode}
模式要求：{MODES.get(session.mode, "")}
已训练轮次：{session.turn_count}
历史薄弱点：
{format_weaknesses(session)}

下面是候选人的本地简历/项目材料节选，请只基于这些材料和用户本轮回答追问；没有证据的内容不要帮他编。

{context}
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_prompt},
    ]
    messages.extend(session.history[-12:])
    messages.append({"role": "user", "content": user_text})
    return messages


def generate_interview_reply(
    client: OpenAI,
    corpus: list[CorpusChunk],
    session: ChatSession,
    user_text: str,
    max_context_chars: int,
) -> str:
    context = select_context(corpus, user_text, max_chars=max_context_chars)
    messages = build_messages(session, user_text, context)
    return call_model(client, messages)
