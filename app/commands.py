from __future__ import annotations

import time
from pathlib import Path

from openai import OpenAI

from interview_corpus import CorpusChunk
from materials import ensure_corpus, update_env_value
from paths import MATERIALS_INBOX
from profile_builder import ensure_default_protocol, generate_background_material
from prompts import MODES, STAGES
from session_store import (
    ChatSession,
    build_local_review,
    format_weaknesses,
    reset_session,
    save_latest_answer,
    write_review_file,
)


def stage_from_text(text: str) -> str | None:
    lowered = text.lower()
    if "电话" in text or "筛选" in text or "hr筛" in lowered:
        return "电话筛选面"
    if "一面" in text or "技术面" in text:
        return "技术一面"
    if "二面" in text or "主管" in text or "leader" in lowered:
        return "技术二面/主管面"
    if "hr" in lowered or "人事" in text:
        return "HR 面"
    return None


def mode_from_text(text: str) -> str | None:
    lowered = text.lower()
    if "教练" in text or "轻松" in text or "补基础" in text:
        return "教练模式"
    if "拷打" in text or "高压" in text or "压力" in text:
        return "拷打模式"
    if "只面试" in text or "暂停教学" in text or "纯面试" in text:
        return "只面试模式"
    if "技术面" in text or "正常" in text or "标准" in text:
        return "技术面模式"
    return None


def help_text(session: ChatSession) -> str:
    return (
        f"当前：{session.stage} / {session.mode}\n\n"
        "常用指令：\n"
        "/模式 教练 / /模式 技术面 / /模式 拷打 / /模式 只面试\n"
        "开始电话面 / 开始一面 / 开始二面 / 开始HR面\n"
        "/资料入口：查看可放简历材料的文件夹，也可以直接发 docx/pdf/md/txt 文件\n"
        "/导入资料 路径：切换简历材料目录\n"
        "/生成背景：根据材料生成 AI面试背景材料\n"
        "/复盘：总结最近表现和弱点\n"
        "/今日弱点：查看累计薄弱点\n"
        "/标准答案：把最近一轮沉淀成可背答案\n"
        "/拷打 Support QA Agent：进入拷打模式并追问指定项目\n"
        "/解释 MCP：先补基础，再给面试追问\n"
        "/重置：清空当前对话记忆\n"
        "/刷新：重新读取简历资料"
    )


async def handle_command(
    text: str,
    session: ChatSession,
    user_id: str,
    client: OpenAI,
    corpus: list[CorpusChunk],
    source_dir: Path,
) -> tuple[str | None, list[CorpusChunk], Path]:
    stripped = text.strip()
    if stripped in {"/帮助", "帮助", "/help"}:
        return help_text(session), corpus, source_dir
    if stripped in {"/重置", "重置"}:
        reset_session(session)
        return "已重置。进入 电话筛选面 / 技术面模式。请先用 1 分钟做一个自我介绍。", corpus, source_dir
    if stripped in {"/今日弱点", "今日弱点", "/弱点"}:
        return format_weaknesses(session), corpus, source_dir
    if stripped in {"/复盘", "复盘"}:
        path = write_review_file(user_id, session)
        return build_local_review(session) + f"\n\n复盘文件已保存：{path}", corpus, source_dir
    if stripped in {"/标准答案", "标准答案"}:
        return save_latest_answer(user_id, session), corpus, source_dir
    if stripped in {"/资料入口", "资料入口"}:
        MATERIALS_INBOX.mkdir(parents=True, exist_ok=True)
        return (
            "简历入口目录已经准备好：\n"
            f"{MATERIALS_INBOX}\n\n"
            "你可以：\n"
            "1. 直接在微信里发送 .docx/.pdf/.md/.txt 文件；\n"
            "2. 或把文件放进这个目录后发：\n"
            f"/导入资料 {MATERIALS_INBOX}\n"
            "然后发：/生成背景",
            corpus,
            source_dir,
        )
    if stripped.startswith("/导入资料") or stripped.startswith("导入资料"):
        raw_path = stripped.replace("/导入资料", "", 1).replace("导入资料", "", 1).strip()
        target_dir = Path(raw_path.strip('"')) if raw_path else MATERIALS_INBOX
        if not target_dir.exists() or not target_dir.is_dir():
            return f"这个资料目录不存在：{target_dir}", corpus, source_dir
        update_env_value("RESUME_SOURCE_DIR", str(target_dir))
        next_corpus = ensure_corpus(target_dir, refresh=True)
        return (
            f"已导入资料目录：{target_dir}\n"
            f"当前抽取到 {len(next_corpus)} 个资料片段。\n"
            "下一步可以发：/生成背景",
            next_corpus,
            target_dir,
        )
    if stripped in {"/生成背景", "生成背景"}:
        ensure_default_protocol()
        background_path = generate_background_material(client, corpus)
        return (
            "已生成个性化 AI面试背景材料：\n"
            f"{background_path}\n\n"
            "后续面试会继续使用当前资料库动态追问。你可以发：开始电话面",
            corpus,
            source_dir,
        )
    if stripped.startswith("/模式") or stripped.startswith("模式"):
        mode = mode_from_text(stripped)
        if not mode:
            return "模式可以选：教练、技术面、拷打、只面试。比如：/模式 拷打", corpus, source_dir
        session.mode = mode
        session.updated_at = time.time()
        return f"已切换到：{mode}。\n{MODES[mode]}", corpus, source_dir
    if stripped.startswith("/阶段") or stripped.startswith("阶段"):
        stage = stage_from_text(stripped)
        if not stage:
            return "阶段可以选：电话面、一面、二面、HR面。比如：/阶段 一面", corpus, source_dir
        session.stage = stage
        session.updated_at = time.time()
        return f"已切换到：{stage}。\n{STAGES[stage]}", corpus, source_dir
    if stripped.startswith("/拷打") or stripped.startswith("拷打"):
        session.mode = "拷打模式"
        topic = stripped.replace("/拷打", "", 1).replace("拷打", "", 1).strip() or "你简历里最核心的 Agent 项目"
        return (
            f"进入拷打模式。问题：请你先用 2 分钟讲清楚“{topic}”的完整链路，"
            "重点说你自己做了哪几块、遇到过什么具体问题。",
            corpus,
            source_dir,
        )
    if stripped.startswith("/解释") or stripped.startswith("解释"):
        session.mode = "教练模式"
        topic = stripped.replace("/解释", "", 1).replace("解释", "", 1).strip() or "你想补的概念"
        return f"先按教练模式来。你先说说你现在对“{topic}”的理解，我会先纠偏，再追一个面试问题。", corpus, source_dir
    stage = stage_from_text(stripped)
    if stripped.startswith("开始") and stage:
        session.stage = stage
        session.history.clear()
        session.updated_at = time.time()
        return (
            f"好的，进入{stage} / {session.mode}。第一个问题：请你用 1 分钟介绍一下自己，"
            "以及为什么转向 AI/Agent 开发？",
            corpus,
            source_dir,
        )
    return None, corpus, source_dir
