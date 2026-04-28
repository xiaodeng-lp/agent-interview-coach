from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from paths import ANSWERS_DIR, REVIEW_DIR, SESSIONS_PATH
from prompts import WEAKNESS_KEYWORDS


@dataclass
class ChatSession:
    stage: str = "电话筛选面"
    mode: str = "技术面模式"
    history: list[dict[str, str]] = field(default_factory=list)
    weaknesses: dict[str, int] = field(default_factory=dict)
    score_history: list[dict[str, Any]] = field(default_factory=list)
    answer_bank: list[dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    updated_at: float = field(default_factory=time.time)


def load_sessions() -> dict[str, ChatSession]:
    try:
        raw = json.loads(SESSIONS_PATH.read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    sessions: dict[str, ChatSession] = {}
    for user_id, payload in raw.items():
        sessions[user_id] = ChatSession(
            stage=payload.get("stage", "电话筛选面"),
            mode=payload.get("mode", "技术面模式"),
            history=payload.get("history", [])[-16:],
            weaknesses=payload.get("weaknesses", {}),
            score_history=payload.get("score_history", [])[-80:],
            answer_bank=payload.get("answer_bank", [])[-80:],
            turn_count=payload.get("turn_count", 0),
            updated_at=payload.get("updated_at", time.time()),
        )
    return sessions


def save_sessions(sessions: dict[str, ChatSession]) -> None:
    payload = {user_id: asdict(session) for user_id, session in sessions.items()}
    SESSIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")


def reset_session(session: ChatSession) -> None:
    session.stage = "电话筛选面"
    session.mode = "技术面模式"
    session.history.clear()
    session.weaknesses.clear()
    session.score_history.clear()
    session.answer_bank.clear()
    session.turn_count = 0
    session.updated_at = time.time()


def format_weaknesses(session: ChatSession) -> str:
    if not session.weaknesses:
        return "现在还没有记录到稳定薄弱点。继续答几轮，我会开始抓你的短板。"
    items = sorted(session.weaknesses.items(), key=lambda item: item[1], reverse=True)
    lines = ["当前累计薄弱点："]
    for name, count in items[:10]:
        lines.append(f"- {name}: {count}")
    return "\n".join(lines)


def avg_score(session: ChatSession) -> int | None:
    scores = [item.get("total") for item in session.score_history if isinstance(item.get("total"), int)]
    if not scores:
        return None
    return round(sum(scores) / len(scores))


def build_local_review(session: ChatSession) -> str:
    score = avg_score(session)
    score_text = f"{score}/100" if score is not None else "暂无"
    recent = session.score_history[-5:]
    lines = [
        f"训练复盘：{session.stage} / {session.mode}",
        f"已训练轮次：{session.turn_count}",
        f"平均分：{score_text}",
        "",
        format_weaknesses(session),
        "",
        "最近建议：",
    ]
    if recent:
        for item in recent:
            weak = "、".join(item.get("weaknesses", [])) or "未识别"
            lines.append(f"- {item.get('time', '')}：{item.get('total', '未知')} 分，弱点：{weak}")
    else:
        lines.append("- 还没有足够记录。先完成 3 到 5 轮问答。")
    lines.extend(
        [
            "",
            "下一轮建议：",
            "用“问题-方案-实现-结果-风险边界”的结构回答，不要只堆 MCP、LangGraph、RAG 这些名词。",
        ]
    )
    return "\n".join(lines)


def write_review_file(user_id: str, session: ChatSession) -> Path:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_user = re.sub(r"[^a-zA-Z0-9_.-]+", "_", user_id)[:60]
    path = REVIEW_DIR / f"review_{safe_user}_{stamp}.md"
    lines = [
        f"# 面试训练复盘 {stamp}",
        "",
        f"- 阶段：{session.stage}",
        f"- 模式：{session.mode}",
        f"- 轮次：{session.turn_count}",
        f"- 平均分：{avg_score(session) or '暂无'}",
        "",
        "## 薄弱点",
        "",
        format_weaknesses(session),
        "",
        "## 最近对话",
        "",
    ]
    for msg in session.history[-12:]:
        role = "你" if msg["role"] == "user" else "面试官"
        lines.append(f"### {role}")
        lines.append(msg["content"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def extract_score(reply: str) -> dict[str, Any]:
    score_block: dict[str, Any] = {}
    total_match = re.search(r"总分[：:]\s*(\d{1,3})", reply)
    if total_match:
        score_block["total"] = max(0, min(100, int(total_match.group(1))))
    for label, key in [
        ("可信度", "credibility"),
        ("技术准确性", "technical"),
        ("表达结构", "structure"),
        ("项目真实性", "authenticity"),
    ]:
        match = re.search(label + r"[：:]\s*(\d{1,3})", reply)
        if match:
            score_block[key] = max(0, min(100, int(match.group(1))))
    return score_block


def extract_weaknesses(reply: str, user_text: str) -> list[str]:
    found: list[str] = []
    block_match = re.search(r"【薄弱点】(?P<block>.*?)(?:【|$)", reply, flags=re.S)
    if block_match:
        for line in block_match.group("block").splitlines():
            cleaned = line.strip().lstrip("-•· ").strip()
            cleaned = re.sub(r"[，,。；;：:].*$", "", cleaned).strip()
            if 1 < len(cleaned) <= 18:
                found.append(cleaned)
    combined = reply + "\n" + user_text
    for keyword in WEAKNESS_KEYWORDS:
        if keyword.lower() in combined.lower():
            found.append(keyword)
    normalized: list[str] = []
    for item in found:
        if item and item not in normalized:
            normalized.append(item)
    return normalized[:6]


def extract_better_answer(reply: str) -> str:
    match = re.search(r"【更好的说法】(?P<block>.*?)(?:【继续追问】|$)", reply, flags=re.S)
    return match.group("block").strip() if match else ""


def guess_answer_title(text: str) -> str:
    lowered = text.lower()
    if "自我介绍" in text or "背景" in text:
        return "自我介绍/转行动机"
    if "mcp" in lowered:
        return "MCP 项目解释"
    if "langgraph" in lowered:
        return "LangGraph 项目解释"
    if "rag" in lowered:
        return "RAG 项目解释"
    if "support" in lowered or "客服" in text or "质检" in text:
        return "Support QA Agent"
    if "knowledge" in lowered or "知识库" in text or "kb" in lowered:
        return "Knowledge Base Assistant"
    if "ppt" in lowered:
        return "PPTAgent"
    return text.strip()[:24] or "面试回答"


def record_training_result(session: ChatSession, user_text: str, reply: str) -> None:
    score = extract_score(reply)
    weaknesses = extract_weaknesses(reply, user_text)
    for weakness in weaknesses:
        session.weaknesses[weakness] = session.weaknesses.get(weakness, 0) + 1
    if score or weaknesses:
        score["time"] = datetime.now().strftime("%m-%d %H:%M")
        score["weaknesses"] = weaknesses
        session.score_history.append(score)
        session.score_history = session.score_history[-80:]
    better = extract_better_answer(reply)
    if better:
        session.answer_bank.append(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "stage": session.stage,
                "mode": session.mode,
                "title": guess_answer_title(user_text),
                "answer": better[:2000],
            }
        )
        session.answer_bank = session.answer_bank[-80:]


def save_latest_answer(user_id: str, session: ChatSession) -> str:
    if not session.answer_bank:
        return "还没有可沉淀的标准答案。你先回答一轮，我点评后再发 /标准答案。"
    ANSWERS_DIR.mkdir(parents=True, exist_ok=True)
    latest = session.answer_bank[-1]
    safe_title = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_.-]+", "_", latest["title"])[:40]
    path = ANSWERS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}.md"
    content = (
        f"# {latest['title']}\n\n"
        f"- 用户：{user_id}\n"
        f"- 阶段：{latest['stage']}\n"
        f"- 模式：{latest['mode']}\n"
        f"- 时间：{latest['time']}\n\n"
        "## 推荐回答\n\n"
        f"{latest['answer']}\n"
    )
    path.write_text(content, encoding="utf-8")
    return f"已保存最近一版标准答案：{latest['title']}\n路径：{path}"
