# Agent Interview Coach 工程化规格

本文档约束后续工程迭代的边界、模块职责、失败语义和验证方式。
它不是用户说明书，也不是流水账；当前状态看 `docs/PROJECT_STATE.md`，验证记录看 `docs/TEST_LOG.md`。

## 1. 文档目的

本文件服务三个场景：

- 新一轮 Codex/Claude 接手项目时，先理解工程边界再改代码。
- 做 bot 稳定性、讲解模式、检索、隐私发布等任务时，避免散装改动。
- 发布或提交前，用统一清单检查风险。

后续所有非平凡改动都应先确认：改动是否符合本文档的边界条件。

## 2. 项目背景

Agent Interview Coach 是一个 local-first AI mock interview coach。

当前主链路：

```text
本地简历 / 项目材料
  -> app/interview_corpus.py 构建 corpus
  -> app/engine.py 组装面试上下文
  -> app/model_client.py 调用 OpenAI-compatible API
  -> app/wechat_channel.py 或 app/cli_chat.py 返回给用户
  -> app/session_store.py 记录评分、弱点、复盘和标准答案
```

当前工程重点：

- WeChat 端可用性和长运行稳定性。
- 面试模式和讲解 / 教练模式的明确区分。
- 用户答不上来时能恢复训练，而不是只继续施压。
- 材料检索优先使用最强、最干净的简历 / 项目证据。
- 避免真实简历、凭据、日志、session 和生成物进入 Git。

## 3. 目标

### G1: 稳定运行

Bot 能在本地 Windows 环境稳定启动、停止、查看状态，并能通过 CLI fallback 继续训练。

### G2: 清晰边界

每个模块只做自己该做的事：命令路由、WeChat 收发、corpus、prompt、model、session 不互相吞职责。

### G3: 面试体验可信

面试官应围绕用户材料动态追问，避免固定题库感；讲解模式应能教会用户如何恢复回答。

### G4: 本地优先和隐私安全

默认只读取本地指定材料，只把被选中的上下文片段发给模型 API；绝不提交真实个人材料和凭据。

### G5: 可验证

每类改动都要有最小验证路径：compile、CLI、smoke test、doctor、WeChat 手测或日志检查。

## 4. 非目标

当前阶段不做：

- 改成 hosted SaaS。
- 引入云数据库、远程队列或 hosted vector DB。
- 多用户商业化权限系统。
- 把 WeChat 能力抽象成复杂插件平台。
- 为了“更像 agent”引入不必要的 agent 框架。
- 把示例材料替换成真实简历。

未来可以考虑但不属于当前阶段：

- 本地 BM25 或向量 RAG。
- Web UI。
- 多用户隔离。
- 更完整的评测集和自动化回归。

## 5. 当前问题

### P0: 中文编码和文档可读性风险

部分中文文件曾经出现 mojibake，会影响用户命令说明、prompt 维护、后续 agent 接手和发布检查。

### P1: bot 进程状态可能漂移

`coach_bot.pid` 和真实 Python 进程可能不同步。脚本已做加固，但旧方式手动启动的进程仍可能需要人工确认。

### P1: 运行时 JSON 写入稳定性

`sessions.json`、corpus cache 等运行时文件如果写入中断，可能损坏。当前已改为原子写并支持 corrupt 备份。

### P1: 讲解模式仍需要实测

项目已有面试 / 讲解两种状态，也有“不知道 / 不会 / 答不上来”的恢复流程，但还需要真实 WeChat 流程验证。

### P2: 检索可解释性不足

当前 retrieval 是 heuristic，能跑但难诊断：不知道选中了哪些材料、为什么选中、是否漏掉关键项目证据。

## 6. 边界条件

### 6.1 产品边界

必须保持：

- local-first。
- WeChat 可用，CLI 可 fallback。
- 训练目标是 AI/Agent/RAG/MCP/LLM 工程岗位面试。
- 面试官基于用户材料追问，不凭空编造经历。

不得引入：

- 必须联网托管才能使用的核心依赖。
- 会弱化移动端 WeChat 体验的流程。
- 与面试训练无关的大型平台化能力。

### 6.2 数据边界

允许读取：

- `app/resume_materials/`
- 用户通过 `/导入资料 <path>` 指定的本地目录
- `examples/` 中的虚构示例

允许写入：

- `app/sessions.json`
- `app/interview_corpus_cache.json`
- `app/reviews/`
- `app/answers/`
- `app/AI面试背景材料.generated.md`
- bot 日志和 pid 文件

不得提交：

- `.env`
- `sessions.json`
- `interview_corpus_cache.json`
- `reviews/`
- `answers/`
- `app/resume_materials/`
- logs
- WeChat credentials
- API keys / tokens
- 真实简历、截图、证书、项目私密材料

### 6.3 模型上下文边界

模型 API 只能收到：

- 当前用户消息。
- 最近、压缩、过滤后的对话历史。
- 当前 stage/mode/weakness 信息。
- retrieval 选中的简历 / 项目片段。

模型 API 不应收到：

- 整个资料目录。
- 未被选中的大文件全文。
- `.env`、日志、凭据或 session 原始文件。

### 6.4 模块边界

| 模块 | 应该负责 | 不应该负责 |
| --- | --- | --- |
| `app/coach_bot.py` | 启动参数、环境加载、主流程装配 | 命令细节、prompt 细节、WeChat 消息解析 |
| `app/wechat_channel.py` | WeChat 轮询、去重、文件导入、分段发送 | 面试业务规则、检索打分、session 结构定义 |
| `app/cli_chat.py` | CLI fallback 和本地手测入口 | WeChat 专属逻辑 |
| `app/commands.py` | 用户命令、模式切换、阶段切换、手动操作入口 | 长 prompt 拼装、模型 API 调用细节 |
| `app/engine.py` | prompt 组装、context 选择、模型调用入口 | 文件导入、WeChat 发送、session 持久化 |
| `app/prompts.py` | stage/mode/system prompt 文案 | 运行时状态写入、文件 IO |
| `app/interview_corpus.py` | 文件解析、清洗、chunk、retrieval | WeChat 下载、session 记录、用户命令 |
| `app/materials.py` | 资料目录、cache refresh、WeChat 文件保存辅助 | prompt 组装、评分解析 |
| `app/model_client.py` | OpenAI-compatible client 和响应文本提取 | 产品模式判断、材料检索 |
| `app/session_store.py` | session 数据模型、评分、弱点、复盘、答案沉淀 | WeChat 收发、模型调用 |
| `app/*.ps1` | Windows 进程管理和诊断 | Python 业务逻辑 |

### 6.5 运行边界

必须支持：

- Windows PowerShell。
- 本地 Python 环境。
- `.env` 配置 OpenAI-compatible API。
- WeChat 不可用时用 CLI 训练。

不保证：

- Linux/macOS 一键脚本完全等价。
- WeChat 上游服务永久稳定。
- 所有 PDF 都能准确抽取文本。

### 6.6 发布边界

发布前必须满足：

- 示例材料全部虚构。
- `.gitignore` 覆盖 runtime/private artifacts。
- secret scan 无未解释风险。
- README、skill、AGENTS、PROJECT_STATE 可读。
- `python -m compileall app` 通过。

## 7. 数据模型与契约

### 7.1 ChatSession

定义位置：`app/session_store.py`

职责：

- 保存当前面试阶段。
- 保存当前训练模式。
- 保存短历史。
- 保存弱点计数。
- 保存评分历史。
- 保存标准答案候选。

契约：

- `history` 只保存压缩后的短文本，不保存无限长原始对话。
- `score_history` 和 `answer_bank` 必须有长度上限。
- 写入 session 时应使用原子写，避免中断损坏。
- prompt 中只使用 top weaknesses，不裁剪完整累计数据。

### 7.2 CorpusChunk

定义位置：`app/interview_corpus.py`

字段含义：

- `source`: 原始文件路径。
- `title`: 文件名。
- `suffix`: 文件类型。
- `priority`: 来源优先级。
- `chunk_index`: 文件内片段编号。
- `text`: 片段正文。

契约：

- 不应包含 `.env`、日志、session、凭据等非材料文件。
- chunk 数和来源文件应可诊断。
- cache 应能反映实际 `source_dir`。

### 7.3 Model Messages

构造位置：`app/engine.py`

契约：

- system prompt 描述面试官角色。
- context prompt 描述 stage/mode/weakness 和证据包。
- recent history 必须受 `MAX_HISTORY_MESSAGES` 限制。
- retrieval context 必须受 `MAX_CONTEXT_CHARS`、chunk 数和每来源 chunk 数限制。
- 候选人经历相关陈述必须遵守 evidence hard rules。

## 8. 运行生命周期

### 8.1 WeChat 生命周期

```text
start_bot.ps1
  -> coach_bot.py
  -> load .env
  -> load WeChat credentials
  -> ensure corpus
  -> run_wechat_bot()
  -> get_updates long polling
  -> message dedupe
  -> file import or command routing
  -> interview reply generation
  -> record session
  -> send segmented WeChat reply
```

### 8.2 CLI 生命周期

```text
cli_chat.py
  -> load .env
  -> ensure corpus
  -> read user input
  -> command routing or interview reply
  -> update in-memory session
  -> print reply
```

### 8.3 材料导入生命周期

```text
source_dir / WeChat uploaded file
  -> sanitize file name
  -> save to app/resume_materials
  -> build_corpus()
  -> filter noisy files
  -> read docx/pdf/md/txt
  -> chunk text
  -> save corpus cache
```

## 9. 失败语义

| 类型 | 含义 | 用户侧表现 | 日志要求 |
| --- | --- | --- | --- |
| `missing_env` | `.env` 不存在或关键配置为空 | 提示用户配置 `.env` | 不打印 secret |
| `invalid_api_key` | 模型 API key 被拒绝 | 提示检查 provider/key/model | 记录错误类型，不打印 key |
| `wechat_credentials_missing` | WeChat 凭据不存在 | 提示运行 setup | 记录 credential path 检查结果 |
| `wechat_poll_failed` | 长轮询失败 | 自动退避重试 | 记录次数、delay、异常类型 |
| `wechat_send_failed` | 回复发送失败 | 可在下一轮继续 | 记录 user_id 和异常类型 |
| `file_import_failed` | 文件下载或保存失败 | 提示重新发送或改用本地导入 | 记录文件名、大小、异常类型 |
| `unsupported_file_type` | 文件类型不支持 | 提示支持 docx/pdf/md/txt | 记录 suffix |
| `corpus_empty` | 没有可用材料片段 | 提示导入资料 | 记录 source_dir |
| `cache_corrupt` | corpus cache JSON 损坏 | 自动重建或提示刷新 | 记录 cache path |
| `session_corrupt` | session JSON 损坏 | 安全回退为空 session | 保留坏文件备份 |
| `model_timeout` | 模型响应超时 | 提示稍后重试或缩短材料 | 记录 timeout seconds |
| `parse_score_failed` | 模型输出无法解析评分 | 不影响回复 | 记录一条 debug 信息 |

## 10. 验证计划

### 10.1 通用验证

每次 Python 代码改动至少运行：

```powershell
python -m compileall app
```

### 10.2 模型验证

改动 `engine.py`、`prompts.py`、`model_client.py` 后运行：

```powershell
cd app
python smoke_test.py --model
```

如果没有有效 API key，必须在结果里说明未运行原因。

### 10.3 WeChat 验证

改动 `wechat_channel.py`、`coach_bot.py`、PowerShell 管理脚本后运行：

```powershell
cd app
powershell -ExecutionPolicy Bypass -File .\start_bot.ps1
powershell -ExecutionPolicy Bypass -File .\status_bot.ps1
powershell -ExecutionPolicy Bypass -File .\stop_bot.ps1
```

有真实 WeChat 凭据时再运行：

```powershell
cd app
python smoke_test.py --wechat
```

### 10.4 CLI 验证

改动命令、prompt、retrieval 后，至少手动验证：

```powershell
cd app
python cli_chat.py
```

推荐手测路径：

```text
/帮助
/导入资料 ..\examples
/生成背景
开始电话面
/模式 讲解
不会
```

### 10.5 发布验证

```powershell
rg -n "sk-|token|OPENAI_API_KEY|bot_token|Authorization|api_key|secret" .
git status --short
```

逐条确认命中结果不是泄密。

## 11. 分阶段实施计划

### M0: 工程底座修正

- 修复中文编码和用户可见文案。
- 明确 `docs/ENGINEERING.md` 为工程化入口。
- 确保 `python -m compileall app` 通过。
- 确保 README、skill、AGENTS、PROJECT_STATE 可读。

### M1: 运行稳定性和上下文卫生

- harden `start_bot.ps1` / `stop_bot.ps1` / `status_bot.ps1`。
- session 写入改成原子写。
- corpus cache 损坏时安全重建。
- sanitize session history。
- select mode-aware recent history。
- limit prompt weaknesses to top 5。

### M2: 面试体验

- 显式实现“不会答恢复流程”。
- `/模式 面试` 和 `/模式 讲解` 行为可预测。
- 弱点记录能识别“不会答”的主题。
- 讲解结束后能回到面试追问。

### M3: retrieval 可诊断

- 增加 `/当前状态` 或 debug 命令。
- 显示 source_dir、chunk_count、stage、mode、recent weaknesses。
- 可选：CLI/debug 模式展示 selected chunk titles、scores、matched terms。

### Future

- 本地 BM25 rerank。
- 本地 embeddings。
- 结构化评分输出。
- 小型回归测试集。

## 12. Review Checklist

提交或交接前检查：

- 改动是否保持 local-first。
- 是否影响 WeChat 移动端体验。
- 是否保留 CLI fallback。
- 是否读取或写入隐私敏感文件。
- 是否改变模块职责边界。
- 是否有明确失败语义。
- 是否运行了最小验证命令。
- 是否更新了 `docs/PROJECT_STATE.md` 或 `docs/TEST_LOG.md`。
- 是否避免提交 runtime artifacts。
- 是否能让下一轮 agent 低上下文接手。

## 13. 当前开放问题

- 是否需要把中文命令同时保留英文 alias，降低编码和输入法风险？
- 是否需要把 retrieval debug 限制在 CLI，避免 WeChat 回复过长或暴露本地路径？
- 是否需要固定 `requirements.txt` 版本，减少上游依赖漂移？
- 是否需要把 rolling summary 作为 M1 后续，进一步降低长会话污染？
