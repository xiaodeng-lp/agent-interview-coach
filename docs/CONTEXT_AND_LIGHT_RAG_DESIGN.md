# Context Budget And Lightweight RAG Design

本文档记录 Agent Interview Coach 处理两个核心问题的工程方案：

1. 长轮次面试导致 token 消耗过大、上下文污染和记忆腐化。
2. 简历原料库内容较多时，模型回答不够贴合用户真实简历和项目。

结论：

- 不能每轮把完整简历原料库塞进 prompt。
- 也不能只靠 prompt 写一句“请根据简历回答”。
- 当前阶段应做本地轻量 RAG：从当前简历原料库检索少量强证据，组成“本轮证据包”，再用硬规则 prompt 生成回答。

## 1. Problem

当前项目链路：

```text
WeChat/CLI 用户消息
  -> app/commands.py 命令或模式切换
  -> app/engine.py 组装 prompt
  -> app/interview_corpus.py 选择材料片段
  -> app/model_client.py 调模型
  -> app/wechat_channel.py / app/cli_chat.py 回复
```

`interview_corpus.py` 已经能从 `RESUME_SOURCE_DIR` 构建 corpus，并用关键词命中和文件优先级选择少量 chunk。它已经是一个最小 retrieval 机制，但还不是完整的“证据优先 RAG”。

主要问题：

- `RESUME_SOURCE_DIR` 中材料较多，完整塞入上下文会导致 token 成本高、注意力稀释、跨项目混淆。
- 当前 retrieval 偏 heuristic，可能因为关键词不匹配而漏掉真实项目证据。
- prompt 里虽然有“不许编”的规则，但必须把检索结果明确建模为可追溯证据。
- 会话历史可能包含旧模板、错误输出、raw provider object 或不适合当前模式的长回复。
- 弱点和评分长期累计后，如果每轮都塞入过多历史，会让模型被旧问题牵引。

## 2. Goals

### G1: 回答贴合当前简历原料库

- 候选人的经历、职责、项目结果和技术动作只能来自本轮证据包或用户本轮补充。
- 大模型常识只能用于解释概念、组织语言和补充通用背景，不能写成候选人已经做过。

### G2: 控制 token 成本

- 不把完整简历、完整项目材料或完整聊天历史塞进 prompt。
- 每轮只放结构化状态、最近少量干净对话、top weaknesses、top evidence chunks。

### G3: 降低记忆腐化

- 清理 raw provider object、错误堆栈、日志、超长模板回复等污染内容。
- 模式切换后，prompt 装配按当前模式选择历史，而不是无差别塞旧回复。

### G4: 保持 local-first

- 第一阶段不引入 hosted vector DB 或云端文件检索。
- 简历原料库保留在本地，cache 仍是本地 JSON。

### G5: 可诊断

- 能看到本轮用了哪些证据文件、chunk 编号和大致 score。
- 后续可通过 `/当前状态`、CLI debug 或日志排查“为什么它这么回答”。

## 3. Non-Goals

当前阶段不做：

- 引入 Milvus、Pinecone、Weaviate 等重型向量数据库。
- 把简历原料库上传到 hosted file search。
- 实现复杂多路 RAG、自动知识图谱或 agentic retrieval。
- 承诺模型完全不犯错；目标是把“可追溯证据”和“不能硬编”的边界做清楚。
- 替代用户确认真实经历。证据不足时，应反问用户，而不是生成确定表述。

## 4. Current Constraints

项目约束：

- Windows + PowerShell 本地运行。
- WeChat 移动端回复要短、稳定、不能刷屏。
- 简历材料可能包含真实个人信息，不能提交到 Git，也不应上传到第三方存储。
- `.env` 当前通过 `RESUME_SOURCE_DIR` 指向外部简历原料库。
- `app/interview_corpus_cache.json` 是 runtime cache，应继续被 `.gitignore` 忽略。
- 当前模型调用固定走 `MODEL_API_STYLE=chat`；Responses endpoint 暂不可靠。

模块边界：

- `app/interview_corpus.py`: 读取材料、过滤文件、切 chunk、构建/加载 cache、检索上下文。
- `app/engine.py`: prompt 装配、当前 mode/stage/weakness/context 注入、调用模型。
- `app/session_store.py`: session history、weaknesses、score、answer bank 持久化。
- `app/wechat_channel.py`: WeChat 收发、文件导入、分段发送，不承担 retrieval 或 prompt 细节。
- `app/commands.py`: 用户命令、模式切换、资料导入口，不承担 RAG 排序逻辑。

## 5. Proposed Architecture

推荐架构：

```text
User message
  -> command/mode handling
  -> build_context_bundle()
       -> structured session state
       -> clean recent history
       -> top weaknesses
       -> evidence pack from current resume source dir
  -> prompt with evidence rules
  -> model reply
  -> session history sanitization
  -> WeChat/CLI output
```

核心变化是从“拼一段 context 字符串”升级为“上下文包”：

```text
ContextBundle
  profile_summary
  session_state
  recent_history
  top_weaknesses
  evidence_items
  budget_stats
```

第一阶段可以不新增独立类，先用函数和 dict 实现；但文档先明确合同，避免后续散改。

## 6. Evidence Pack Contract

本轮证据包是模型生成候选人经历的唯一外部依据。

建议结构：

```python
EvidenceItem = {
    "id": "E1",
    "source": "C:\\...\\resume_materials\\xxx.docx",
    "title": "xxx.docx",
    "chunk_index": 3,
    "priority": 95,
    "score": 42.5,
    "matched_terms": ["MCP", "Schema"],
    "text": "...",
}
```

prompt 中格式化为：

```text
【本轮证据包】
【证据 E1】
来源文件：xxx.docx
片段编号：3
证据等级：5
命中词：MCP, Schema
正文：...
```

生成硬规则：

1. 候选人的经历、项目职责、技术动作、指标和结果，只能来自【本轮证据包】或用户本轮亲口补充。
2. 大模型常识只能用于解释概念、补充通用背景或优化表达，不能写成“候选人做过”。
3. 如果证据包没有支持某个说法，不要硬编；请说“资料里没有看到，需要你确认”。
4. 整理面试回答时，优先复用证据包里的项目名、技术栈、职责边界和真实表述。
5. 如果证据不足以回答当前问题，先问一个澄清问题，或给“可讲思路但不能当成已做经历”的版本。

## 7. Retrieval Design

### M0: Evidence-Pack Retrieval, No New Dependency

在现有 `select_context()` 基础上改造：

- 返回编号证据包，而不是普通 markdown chunk。
- 记录 source、title、chunk_index、priority、score。
- 保留 `MAX_CONTEXT_CHARS`、`MAX_CONTEXT_CHUNKS`、`MAX_CONTEXT_CHUNKS_PER_SOURCE`。
- 跳过 protocol 类材料或降低其优先级，避免面试协议被当作候选人经历。
- 对最终简历、核心项目材料、用户刚导入文件给予更高优先级。

评分初版：

```text
score = file_priority
      + keyword_hits * 8
      + title_hits * 6
      + recent_import_bonus
      - protocol_penalty
      - very_long_chunk_penalty
```

M0 价值：

- 成本低。
- 不改部署环境。
- 立刻让模型知道哪些内容是证据。

### M1: Context Budget And History Hygiene

已经完成的方向：

- sanitize polluted session history。
- mode-aware recent history selection。
- prompt 中 weakness 只放 top 5。
- evidence hard rules 每轮注入。

后续可选：

- rolling summary。
- debug/status command。

### M2: Local BM25 Rerank

如果 M0/M1 仍不够贴合，再加入本地 BM25：

- 适合中文/英文技术关键词、项目名、工具名。
- 不需要 embedding API。
- 不上传材料。
- corpus 只有百级 chunk，性能足够。

可选实现：

- 轻依赖 `rank-bm25`。
- 或在项目内实现简化 TF-IDF/BM25，减少依赖。

M2 排序建议：

```text
candidate_pool = top 20 by current heuristic
rerank by bm25(user_message, chunk.title + chunk.text)
final = diversity(source limit) + priority
```

### M3: Optional Local Embeddings

只有当 BM25 对“语义相关但无共享关键词”的问题召回不足时再做。

可选方案：

- local `sentence-transformers` multilingual embedding
- FAISS 或 numpy cosine similarity
- SQLite 存 embedding metadata

风险：

- Windows 安装复杂度上升。
- 本地模型体积和首次加载时间增加。
- 需要处理 embedding cache 版本和重建。

因此 M3 不作为当前阶段目标。

## 8. Context Budget Design

每轮上下文建议分层装配：

```text
固定系统规则
+ 当前 mode/stage/session slots
+ 短候选人画像或 rolling summary
+ 最近 2-4 轮干净对话
+ top weaknesses 3-5 个
+ evidence pack 3-5 chunks
```

建议预算：

| Layer | Target |
| --- | --- |
| System prompt | 稳定，但避免重复长模板 |
| Session state | 500-1000 chars |
| Rolling summary | 600-1200 chars |
| Recent history | 2-4 turns |
| Weaknesses | top 5 |
| Evidence pack | 3-5 chunks, 4000-8000 chars |
| WeChat reply | 1000-1600 chars preferred |

后续可根据体验调整：

```text
MAX_CONTEXT_CHARS=8000-12000
MAX_CONTEXT_CHUNKS=4
MAX_CONTEXT_CHUNKS_PER_SOURCE=1-2
MAX_HISTORY_MESSAGES=4-6
```

教练模式可更短：

- 更少历史评分。
- 更多当前概念相关证据。
- 输出教学结构，不输出完整评分模板。

只面试模式可更短：

- 少放教学历史。
- 只放当前追问所需证据。
- 回复更短。

## 9. Session Memory Hygiene

必须防止以下内容进入长期 history：

- raw provider response object
- `resp_...`
- `created_at`
- `incomplete_details`
- `instructions`
- `ChatCompletion(`
- `Response(`
- API error dump
- traceback
- 超长 assistant message
- 与当前 mode 强冲突的旧模板输出

策略：

- 命中 raw response marker：替换成 `[model response parse error omitted]`。
- 命中错误堆栈：替换成 `[error output omitted]`。
- assistant 内容超过阈值：压缩或截断。
- 教练模式下旧评分模板不进入 prompt。
- 面试模式下旧长教学解释不进入 prompt。

## 10. Prompt Assembly Contract

`engine.py` 后续应避免直接拼散乱字符串，推荐收敛到：

```python
def build_context_bundle(session, user_text, corpus, budget) -> ContextBundle:
    ...

def render_context_prompt(bundle) -> str:
    ...
```

prompt 结构建议：

```text
当前训练状态
- stage
- mode
- turn_count
- top weaknesses

证据使用规则
- 经历只能来自证据包或用户本轮补充
- 常识只能用于解释，不能改写为经历
- 证据不足要确认

本轮证据包
- E1...
- E2...

最近对话摘要 / 历史
- ...

本轮用户消息
- ...
```

注意：

- `wechat_channel.py` 不参与 prompt 拼装。
- `commands.py` 只改 mode/stage/source_dir 等状态，不决定证据内容。
- `interview_corpus.py` 不写产品话术，只返回 evidence item 或格式化证据。

## 11. Failure Semantics

| Failure | Meaning | User Behavior | Log/Debug |
| --- | --- | --- | --- |
| `corpus_empty` | 当前简历原料库没有可用 chunk | 提示导入资料或检查路径 | source_dir, file count |
| `evidence_empty` | 本轮没有检索到相关证据 | 让模型问澄清，不硬编经历 | query, top candidate count |
| `evidence_too_long` | 证据包超预算 | 裁剪低分证据 | budget, selected count |
| `history_polluted` | history 命中 raw/error marker | 丢弃污染片段 | user_id, marker type |
| `mode_context_conflict` | 当前 mode 与历史模板冲突 | 当前 mode 优先 | mode, omitted history count |
| `cache_stale` | cache source_dir 不匹配 | 自动重建 | expected/actual source_dir |

## 12. Validation Plan

通用验证：

```powershell
python -m compileall app
```

Corpus 验证：

```powershell
cd app
python interview_corpus.py --source-dir "C:\path\to\resume_materials"
```

模型输出验证：

```powershell
cd app
python smoke_test.py --model
```

本地行为测试建议：

- 查询一个明确在简历原料库中的项目，例如 MCP / RAG / LangGraph。
- 确认证据包选中的 source 来自当前 `RESUME_SOURCE_DIR`。
- 查询一个资料里没有的经历，例如“Redis 限流怎么做的”。
- 预期模型说资料里未看到，不应编成已做经历。
- 切到教练模式后，确认输出是教学结构，不是完整评分模板。
- 切到只面试模式后，确认回复短且只追问一个问题。

后续可加 `/当前状态` 或 debug 输出：

```text
source_dir
corpus chunk count
selected evidence titles
selected evidence scores
history messages used
estimated context chars
mode/stage/top weaknesses
```

## 13. Phased Implementation Plan

### M0: Evidence Pack And Hard Prompt Rules

Files:

- `app/interview_corpus.py`
- `app/engine.py`
- optional `docs/TEST_LOG.md`

Tasks:

- Make selected chunks render as numbered evidence items.
- Add evidence-use hard rules to `engine.py`.
- Keep current cache format compatible if possible.
- Add local checks for evidence exists and evidence empty behavior.

Expected outcome:

- Model replies are more clearly grounded in current resume materials.
- No new dependencies.

### M1: Context Budget And History Hygiene

Files:

- `app/session_store.py`
- `app/engine.py`
- optional `app/commands.py` for `/当前状态`

Tasks:

- Sanitize polluted history on load/save.
- Select mode-aware recent history.
- Limit weaknesses to top 5 in prompt.
- Add rolling summary field if needed.
- Add debug/status command.

Expected outcome:

- Lower token use.
- Less old-template contamination.
- Easier diagnosis.

### M2: Local BM25 Rerank

Files:

- `app/interview_corpus.py`
- `requirements.txt` if using dependency

Tasks:

- Add BM25 scoring over cached chunks.
- Combine BM25 score with file priority and source diversity.
- Keep fallback to heuristic scoring if BM25 dependency unavailable.

Expected outcome:

- Better retrieval when corpus grows.
- Still local-first.

### M3: Optional Local Embeddings

Only if M1/M2 do not provide enough recall.

Tasks:

- Evaluate local multilingual embedding model.
- Add embedding cache keyed by chunk content hash and model name.
- Add cosine similarity retrieval.
- Keep BM25 fallback.

Expected outcome:

- Better semantic recall.
- Higher environment complexity, so defer.

## 14. Review Risks

Main risks reviewers should watch:

- Evidence prompt is too strict and makes replies overly hesitant.
- Evidence retrieval misses relevant material, causing unnecessary clarification.
- Context budget too small, making model lose continuity.
- Debug/status command could reveal private source paths in WeChat if too verbose.
- BM25/embedding dependency could weaken local-first simplicity.
- Existing mojibake in code comments or prompt strings can make maintenance harder.

## 15. Open Questions

1. Should evidence source titles be visible to the WeChat user, or only used internally?
2. Should `/当前状态` be available in WeChat, CLI only, or behind a debug env flag?
3. Should generated background material be treated as strong evidence or only as a summary layer?
4. Should user-uploaded latest files get temporary priority over older corpus files?
5. Should the system refuse to answer experience questions when evidence is empty, or provide a generic learning explanation plus a clarification question?

## 16. Recommended Decision

Adopt M0 and M1 first.

Do not put the full resume material library into every prompt.

Do not rely on prompt-only grounding.

Use local lightweight evidence retrieval first:

```text
current RESUME_SOURCE_DIR
  -> corpus chunks
  -> top evidence items
  -> evidence-use prompt rules
  -> mode-aware reply
```

This keeps the project local-first, reduces token cost, and makes answers more faithful to the user's actual resume/project materials.
