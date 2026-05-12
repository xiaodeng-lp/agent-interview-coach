from __future__ import annotations

import os

from openai import OpenAI

from interview_corpus import CorpusChunk, select_context
from model_client import call_model
from prompts import MODES, STAGES, SYSTEM_PROMPT
from session_store import ChatSession, format_weaknesses


UNCERTAIN_ANSWER_MARKERS = (
    "不会",
    "不知道",
    "不清楚",
    "不太懂",
    "不懂",
    "答不上来",
    "没思路",
    "没有思路",
    "不了解",
)


COACHING_RECOVERY_INSTRUCTION = """本轮用户明确表示不会或答不上来。请进入“不会答恢复流程”，不要继续高压拷问。

本轮回复必须做到：
1. 先用 2 到 4 句话讲清楚这个概念或问题的核心。
2. 再把它映射到候选人的项目表达里，给出一个可复用的回答骨架。
3. 明确提醒哪些内容资料没有支撑，不能硬编。
4. 最后只追一个更容易回答的降阶问题，帮助候选人回到面试状态。
5. 仍保留【薄弱点】字段，至少记录一个本轮暴露的短标签。
"""


COACHING_MODE_INSTRUCTION = """当前是教练模式。用户想先被讲明白，而不是继续被评分拷问。

本轮输出优先使用教学结构，不要使用完整【反馈】【评分】【更好的说法】模板：
1. 先直接讲概念：用短句解释核心，不要先打分。
2. 再给面试回答骨架：给一版候选人可以照着说的 3 到 5 句回答。
3. 最后只给一个低难度回问，帮助用户把刚学的内容复述出来。
4. 如果需要记录薄弱点，只在末尾用一行【薄弱点】列 1 到 2 个短标签；不要输出分数。
"""


EVIDENCE_USE_HARD_RULES = """证据使用硬规则：
1. 生成候选人的经历、项目职责、技术动作、指标和结果时，只能依据【本轮证据包】或用户本轮亲口补充。
2. 大模型常识只能用于解释概念、补充通用背景和优化表达，不能写成“候选人做过”的经历。
3. 如果【本轮证据包】没有支持某个说法，必须说“资料里没有看到，需要你确认”，不能硬编。
4. 整理面试回答时，优先复用证据包里的项目名、技术栈、职责边界和真实表述。
5. 如果证据不足以回答当前问题，先问一个澄清问题，或给“可讲思路但不能当成已做经历”的版本。
"""


COACHING_CONFLICT_MARKERS = (
    "【评分】",
    "总分：",
    "可信度：",
    "技术准确性：",
    "表达结构：",
    "项目真实性：",
    "【更好的说法】",
)

INTERVIEW_CONFLICT_MARKERS = (
    "当前是教练模式",
    "先直接讲概念",
    "面试回答骨架",
    "低难度回问",
    "不会答恢复流程",
)


def needs_coaching_recovery(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in UNCERTAIN_ANSWER_MARKERS)


def is_conflicting_history_message(message: dict[str, str], mode: str) -> bool:
    if message.get("role") != "assistant":
        return False
    content = message.get("content", "")
    if mode == "教练模式":
        return any(marker in content for marker in COACHING_CONFLICT_MARKERS)
    if mode in {"技术面模式", "只面试模式"}:
        return any(marker in content for marker in INTERVIEW_CONFLICT_MARKERS)
    return False


def select_recent_history(
    history: list[dict[str, str]],
    mode: str,
    max_messages: int,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for message in reversed(history):
        if is_conflicting_history_message(message, mode):
            continue
        selected.append(message)
        if len(selected) >= max_messages:
            break
    selected.reverse()
    return selected


def build_messages(session: ChatSession, user_text: str, context: str) -> list[dict[str, str]]:
    context_prompt = f"""当前面试阶段：{session.stage}
阶段目标：{STAGES.get(session.stage, "")}
当前训练模式：{session.mode}
模式要求：{MODES.get(session.mode, "")}
已训练轮次：{session.turn_count}
历史薄弱点：
{format_weaknesses(session, max_items=5)}

下面是候选人的本地简历/项目材料证据包。请严格遵守证据使用硬规则。

{EVIDENCE_USE_HARD_RULES}

{context}
"""
    if session.mode == "教练模式":
        context_prompt += f"\n\n{COACHING_MODE_INSTRUCTION}"
    if needs_coaching_recovery(user_text):
        context_prompt += f"\n\n{COACHING_RECOVERY_INSTRUCTION}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_prompt},
    ]
    history_window = int(os.environ.get("MAX_HISTORY_MESSAGES", "8"))
    messages.extend(select_recent_history(session.history, session.mode, history_window))
    messages.append({"role": "user", "content": user_text})
    return messages


def generate_interview_reply(
    client: OpenAI,
    corpus: list[CorpusChunk],
    session: ChatSession,
    user_text: str,
    max_context_chars: int,
) -> str:
    max_context_chunks = int(os.environ.get("MAX_CONTEXT_CHUNKS", "4"))
    max_chunks_per_source = int(os.environ.get("MAX_CONTEXT_CHUNKS_PER_SOURCE", "2"))
    context = select_context(
        corpus,
        user_text,
        max_chars=max_context_chars,
        max_chunks=max_context_chunks,
        max_chunks_per_source=max_chunks_per_source,
    )
    messages = build_messages(session, user_text, context)
    return call_model(client, messages)
