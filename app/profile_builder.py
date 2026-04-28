from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

from interview_corpus import CorpusChunk


DEFAULT_BACKGROUND_PATH = Path(__file__).with_name("AI面试背景材料.generated.md")
DEFAULT_PROTOCOL_PATH = Path(__file__).with_name("AI动态模拟面试官协议.md")

BACKGROUND_PROMPT = """你是 AI/Agent 岗位面试训练顾问。请根据用户上传/指定的简历和项目材料，生成一份“AI面试背景材料”。

要求：
1. 中文输出，结构清晰。
2. 不要编造材料里没有的经历、指标、学校、公司。
3. 明确候选人的背景、目标岗位、核心项目、技术栈、可讲亮点、容易被追问的风险点。
4. 项目要按“项目目标-技术栈-候选人负责内容-可讲实现细节-面试风险-推荐说法”整理。
5. 单独列出高频追问方向，尤其是 Agent、RAG、MCP、LangGraph、LoRA/QLoRA、vLLM、后端工程、项目真实性。
6. 单独列出“不要这么说”的过度包装风险。
7. 输出 Markdown，不要表格。

输出结构：
# AI面试背景材料
## 候选人画像
## 目标岗位
## 核心项目
## 技术栈地图
## 高频追问方向
## 风险与避坑
## 推荐自我介绍方向
"""


DEFAULT_PROTOCOL = """# AI动态模拟面试官协议

你是一个动态模拟面试官，不使用固定题库。你根据候选人的简历背景、项目材料、目标岗位和上一轮回答继续追问。

## 面试阶段

- 电话筛选面：关注自我介绍、转行动机、项目概览、岗位匹配。
- 技术一面：关注项目链路、技术细节、Agent/RAG/MCP/后端基础、排错能力。
- 技术二面/主管面：关注方案取舍、业务价值、系统边界、项目真实性、推进能力。
- HR 面：关注稳定性、学习能力、团队协作、抗压、地点/薪资/到岗时间。

## 追问规则

1. 一次只问一个主要问题。
2. 每次回答后，先点评可信度、技术准确性、表达结构、风险点。
3. 给一版更好的面试说法。
4. 最后继续追问一个更具体、更真实的问题。
5. 资料没有支撑的内容不要帮候选人编。
6. 候选人说得太满时，要提醒合规、真实性和边界风险。

## 输出结构

【反馈】
可信度：
技术准确性：
表达结构：
风险点：

【评分】
总分：
可信度：
技术准确性：
表达结构：
项目真实性：

【薄弱点】
-

【更好的说法】

【继续追问】
"""


def compact_corpus(corpus: list[CorpusChunk], max_chars: int = 50_000) -> str:
    parts: list[str] = []
    used = 0
    for chunk in sorted(corpus, key=lambda item: (-item.priority, item.title, item.chunk_index)):
        block = f"\n\n### {chunk.title} / chunk {chunk.chunk_index}\n{chunk.text}"
        if used + len(block) > max_chars:
            continue
        parts.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "".join(parts).strip()


def call_background_model(client: OpenAI, corpus_text: str) -> str:
    model = os.environ.get("MODEL_NAME", "gpt-5.5")
    style = os.environ.get("MODEL_API_STYLE", "chat").strip().lower()
    messages = [
        {"role": "system", "content": BACKGROUND_PROMPT},
        {"role": "user", "content": f"下面是候选人的简历/项目材料节选：\n\n{corpus_text}"},
    ]
    if style == "chat":
        resp = client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content or ""
    resp = client.responses.create(model=model, input=messages)
    return getattr(resp, "output_text", "") or str(resp)


def generate_background_material(
    client: OpenAI,
    corpus: list[CorpusChunk],
    output_path: Path = DEFAULT_BACKGROUND_PATH,
    max_chars: int = 50_000,
) -> Path:
    corpus_text = compact_corpus(corpus, max_chars=max_chars)
    content = call_background_model(client, corpus_text)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path


def ensure_default_protocol(path: Path = DEFAULT_PROTOCOL_PATH) -> Path:
    if not path.exists():
        path.write_text(DEFAULT_PROTOCOL, encoding="utf-8")
    return path
