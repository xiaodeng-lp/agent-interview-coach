# Agent Interview Coach

> 简历写得很漂亮，面试一问就发慌？让 AI 面试官替你先问到崩。

**Agent Interview Coach** 是一个面向 AI/Agent 岗位的本地面试陪练工具。  
你把简历、项目文档、复盘笔记丢进去，它会自动整理成“面试官视角”的背景材料，然后通过 **微信** 或 **命令行** 追着你练：问项目、拆细节、打分、抓漏洞、生成复盘，还会把更好的回答沉淀成标准答案。

它不是温柔题库，也不是泛泛聊天。  
它更像一个提前坐在你对面的技术面试官：你简历上写了什么，它就沿着什么追；你哪里说虚了，它就继续往下问。

## 你是不是也遇到过这些问题？

- 简历上写了 Agent、RAG、MCP、LangGraph、LoRA、vLLM，真被问到只能解释名词。
- 项目能跑，README 也能写，但说不清“我到底做了哪一块”。
- 面试官问“失败怎么办、怎么评估、怎么上线”，回答立刻变空。
- 自我介绍像背稿，转岗/转方向动机听起来不够可信。
- 找 ChatGPT 练面试，它太礼貌、太容易放过你，不会持续拷问简历漏洞。
- 每次面完都知道自己答得烂，但不知道到底烂在哪里、下一轮该怎么补。

**Agent Interview Coach** 做的事情很直接：  
把“写在简历上的项目”，训练成“面试里讲得清楚、经得起追问的经历”。

```text
上传简历 / 项目材料
  -> 自动生成面试官背景材料
  -> 微信或 CLI 开始模拟面试
  -> 按阶段动态追问
  -> 每轮打分、抓薄弱点
  -> 生成复盘和标准答案
  -> 下一轮继续针对短板追问
```

## 它适合谁？

- 准备 AI 应用开发、Agent、RAG、LLM 后端岗位的人。
- 简历里有项目，但担心项目经不起细问的人。
- 靠教程、开源项目、vibe coding 做出 demo，想把项目讲扎实的人。
- 转岗/转方向，需要把动机和项目逻辑讲可信的人。
- 想在手机微信里碎片化练面试的人。

> 当前项目是 experimental / MVP。微信能力依赖 `wechat-clawbot` 及其上游服务

---

## 30 秒看效果：它到底能帮你练什么？

### 1. 先吃掉你的简历和项目材料

仓库提供了一套完全虚构的 demo，不包含真实个人信息：

- [examples/sample_resume.md](examples/sample_resume.md)
- [examples/sample_project_support_qa_agent.md](examples/sample_project_support_qa_agent.md)
- [examples/sample_project_kb_assistant.md](examples/sample_project_kb_assistant.md)

候选人项目包括：

- **Support QA Agent**：客服质检辅助 Agent
- **Knowledge Base Assistant**：企业知识库 RAG 助手
- **Ticket Routing Agent**：工单分流 Agent

### 2. 自动生成“面试官视角”的背景材料

运行：

```text
/生成背景
```

得到类似：

[examples/sample_generated_background.md](examples/sample_generated_background.md)

```text
候选人的优势是：有后端开发基础，做过多个 LLM 应用项目，覆盖 Agent workflow、RAG、tool calling、结构化输出、评估和简单部署。

候选人的风险是：项目多为学习/原型性质，需要避免包装成生产级系统；同时要能讲清楚自己具体做了哪些模块，而不是只堆 Agent、RAG、MCP 这些名词。
```

### 3. 像技术面试官一样继续追问

```text
你说 Support QA Agent 里用了 tool calling。
请你具体说一个 tool 的输入 schema、输出字段，以及工具失败时 Agent 怎么处理。
```

如果你回答太泛，它不会客气，会继续往细节里压：

```text
【反馈】
可信度：中等。你确实知道工具调用的大概流程，但回答太泛，像是在讲概念。

技术准确性：偏弱。你没有说 schema、输出结构、错误类型，也没有说失败信息如何进入 Agent state。

表达结构：一般。应该按“tool 目的-输入-输出-失败处理-state 更新”来回答。

风险点：如果继续这么答，面试官会怀疑你只是知道“工具调用”这个词，但没有真正设计过工具接口。

【评分】
总分：62
可信度：65
技术准确性：55
表达结构：60
项目真实性：58

【继续追问】
如果政策检索工具返回了 5 条相似政策，其中有过期版本和低相关片段，你的 Agent 怎么过滤？
```

完整复盘示例：

[examples/sample_interview_review.md](examples/sample_interview_review.md)

---

## 为什么不是直接问 ChatGPT？

你当然可以直接问 ChatGPT：“请模拟面试我。”

但普通聊天容易变成泛泛问答。这个项目做了几件更适合面试训练的事：

| 能力 | 普通聊天 | Agent Interview Coach |
|---|---|---|
| 读取简历/项目材料 | 手动贴上下文 | 从本地资料目录抽取 |
| 生成候选人画像 | 临时生成 | `/生成背景` 固化为面试背景 |
| 动态追问 | 容易跑题 | 基于阶段、模式、弱点和项目材料 |
| 项目真实性追问 | 不稳定 | 专门追 state、tool schema、RAG、失败处理 |
| 训练记录 | 容易丢 | 保存评分、弱点、复盘、标准答案 |
| 移动端练习 | 不方便 | 微信收发消息 |
| 微信不可用时 | 无 fallback | CLI 模式可用 |

---

## 快速开始

### 1. 安装

```powershell
git clone <repo-url>
cd agent-interview-coach
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
```

安装脚本会：

- 安装 Python 依赖
- 创建 `app\.env`
- 创建 `app\resume_materials`
- 提示后续操作

### 2. 配置模型 API

编辑：

```text
app\.env
```

填写：

```text
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4.1-mini
MODEL_API_STYLE=chat
RESUME_SOURCE_DIR=./resume_materials
MAX_CONTEXT_CHARS=18000
ALLOWED_WECHAT_USER_ID=
```

如果你使用 OpenAI-compatible 服务，修改：

```text
OPENAI_BASE_URL
MODEL_NAME
MODEL_API_STYLE
```

### 3. 先跑 CLI 模式

微信链路可能受环境影响。建议先确认核心面试官可用：

```powershell
cd app
python smoke_test.py --model
python cli_chat.py
```

CLI 里输入：

```text
/导入资料 ..\examples
/生成背景
开始电话面
/模式 拷打
```

### 4. 再接微信

扫码登录：

```powershell
wechat-clawbot-cc setup
```

测试：

```powershell
python smoke_test.py --wechat
```

启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_bot.ps1
```

查看状态：

```powershell
powershell -ExecutionPolicy Bypass -File .\status_bot.ps1
```

停止：

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_bot.ps1
```

---

## 微信里怎么用？

### 直接发送文件

你可以把这些文件直接发给微信 bot：

```text
.docx
.pdf
.md
.txt
```

bot 会自动下载到：

```text
app\resume_materials
```

然后回复你下一步运行：

```text
/生成背景
```

### 或者导入本地目录

```text
/资料入口
/导入资料 C:\path\to\resume_materials
/生成背景
开始电话面
```

### 常用命令

```text
/帮助
/资料入口
/导入资料 路径
/生成背景
/模式 教练
/模式 技术面
/模式 拷打
/模式 只面试
开始电话面
开始一面
开始二面
开始HR面
/拷打 Support QA Agent
/解释 MCP
/今日弱点
/复盘
/标准答案
/刷新
/重置
```

模式说明：

- `教练模式`：先补基础，再按面试标准纠偏。
- `技术面模式`：正常技术面节奏，追问项目实现、技术取舍和真实细节。
- `拷打模式`：高压追问，重点抓名词堆砌、项目真实性和边界风险。
- `只面试模式`：减少教学解释，主要连续问问题。

---

## 它会追问什么？

它尤其会盯这些容易露馅的点：

- 这个项目的输入/输出是什么？
- Agent state 里有哪些字段？
- 每个 workflow node 负责什么？
- tool schema 怎么定义？
- 工具超时、失败、返回脏数据怎么办？
- RAG 怎么切 chunk？
- metadata filter 怎么设计？
- 怎么评估召回质量？
- 为什么需要 Redis/PostgreSQL？
- 哪些部分只是 demo，不是生产级？
- 这个项目里你本人到底做了什么？

---

## 项目结构

```text
agent-interview-coach/
├─ app/
│  ├─ coach_bot.py          # 启动入口
│  ├─ wechat_channel.py     # 微信长轮询、文件导入、回复发送
│  ├─ commands.py           # 微信/CLI 命令路由
│  ├─ engine.py             # 面试 prompt 组装和模型调用
│  ├─ session_store.py      # 会话、评分、弱点、复盘、标准答案
│  ├─ materials.py          # 资料目录、缓存刷新、微信文件下载
│  ├─ interview_corpus.py   # docx/pdf/md/txt 抽取和检索
│  ├─ profile_builder.py    # 生成 AI 面试背景材料
│  ├─ model_client.py       # OpenAI-compatible API 调用
│  ├─ prompts.py            # 阶段、模式、系统提示词
│  ├─ cli_chat.py           # 命令行 fallback
│  └─ smoke_test.py         # 连通性测试
├─ examples/                # 完全虚构的简历、项目、背景、复盘示例
├─ docs/
│  ├─ setup.md
│  ├─ architecture.md
│  └─ privacy.md
├─ skill/
│  └─ SKILL.md              # Codex/Claude skill 使用说明
├─ install_windows.ps1
├─ doctor.ps1
├─ requirements.txt
├─ .env.example
└─ README.md
```

---

## 诊断

遇到问题时运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\doctor.ps1
```

它会检查：

- Python 是否可用
- 依赖是否安装
- `.env` 是否存在
- API key 是否填写，但不会打印 key
- 模型是否连通
- 微信凭据是否存在
- 微信接口是否连通

---

## 隐私与安全

模型 API 本身不能直接读取你的电脑文件。这个项目的本地 Python 程序会读取你指定的资料目录，然后把相关片段作为上下文发给模型。

不要提交这些文件：

```text
.env
sessions.json
interview_corpus_cache.json
reviews/
answers/
resume_materials/
真实简历和项目材料
微信凭据
API key 或 token
```

更多说明见：

[docs/privacy.md](docs/privacy.md)

---

## 限制

- 微信能力依赖 `wechat-clawbot` 和上游服务，可能因为环境或上游变化而失效。
- 当前项目更适合个人学习和面试训练，不适合群发、营销或商业自动化。
- `/生成背景` 和面试追问质量取决于模型能力、简历材料质量和上下文长度。
- 示例项目只用于面试训练，不代表真实公司系统或生产级实践。

---

## License

MIT
