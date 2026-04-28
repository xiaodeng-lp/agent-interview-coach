# AI面试背景材料

> This is a fictional generated example. It demonstrates the expected output of `/生成背景`.

## 候选人画像

Alex Chen 是一名软件工程背景的硕士生，目标方向是 AI 应用开发、Agent 工程和 LLM 后端开发。简历里的项目重点不是训练大模型本身，而是把大模型接入文档、工具、检索系统和业务流程。

候选人的优势是：有后端开发基础，做过多个 LLM 应用项目，覆盖 Agent workflow、RAG、tool calling、结构化输出、评估和简单部署。

候选人的风险是：项目多为学习/原型性质，需要避免包装成生产级系统；同时要能讲清楚自己具体做了哪些模块，而不是只堆 Agent、RAG、MCP 这些名词。

## 目标岗位

适合投递：

- AI Application Engineer
- Agent Engineer
- LLM Backend Developer
- RAG Application Developer
- Junior AI Platform Engineer

不建议把自己包装成：

- 资深算法工程师
- 大模型训练专家
- 企业级 AI 平台负责人

## 核心项目

### Support QA Agent

项目目标：自动审阅客服对话，检查政策合规、问题分类、服务态度和升级处理，并生成结构化质检报告。

技术栈：Python、FastAPI、PostgreSQL、Redis、向量检索、OpenAI-compatible API、graph-style Agent workflow。

候选人负责内容：

- 设计 Agent 工作流：对话解析、政策检索、工单信息查询、质检分析、报告生成、证据检查。
- 将政策检索和工单查询封装成工具函数，并设计输入 schema。
- 用 RAG 检索相关政策片段，要求输出包含证据引用。
- 设计结构化输出字段：QA score、issue category、evidence quotes、coaching notes。

可讲实现细节：

- state 包括 `conversation_text`、`ticket_metadata`、`retrieved_policies`、`issue_category`、`compliance_findings`、`evidence_quotes`、`tool_errors`、`qa_report`。
- 如果政策检索失败，报告会把合规判断标记为 uncertain，而不是强行下结论。
- 如果模型输出缺少必填 JSON 字段，会用更严格的 schema reminder 重试。

面试风险：

- 不要说“系统可以替代人工质检”。
- 不要说“质检分数一定准确”，除非能解释标注集和校准方式。
- 要讲清楚证据引用和不确定性处理。

推荐说法：

这个项目我更愿意把它定义成“客服质检辅助 Agent”。它不是替代人工 QA，而是把对话解析、政策检索、工单查询和结构化报告生成串起来，帮助 QA 人员更快定位问题。

### Knowledge Base Assistant

项目目标：从 onboarding 文档、工程 runbook 和 FAQ 中回答内部问题，并给出来源引用。

技术栈：Python、FastAPI、PostgreSQL、FAISS/Milvus-style vector store、embedding API、RAG、metadata filtering。

候选人负责内容：

- 实现 Markdown/PDF 文档导入。
- 设计 chunking 规则和 metadata 字段，如 owner、version、topic、update time。
- 结合向量检索和 metadata filter，减少过期文档召回。
- 构建小型评估集，比较不同检索设置。

面试风险：

- 不要只说“用了 RAG”，要讲 chunk、metadata、召回质量和拒答策略。
- 不要说“完全解决幻觉”，建议说“通过证据引用和低置信拒答降低幻觉风险”。

## 技术栈地图

- Agent：workflow state、node、tool calling、错误处理、guardrail。
- RAG：chunking、embedding、metadata filtering、vector search、retrieval quality。
- Tool calling：tool schema、输入校验、错误返回、工具超时。
- 后端：FastAPI、PostgreSQL、Redis、Docker basics。
- 评估：retrieval relevance、citation correctness、manual review set、structured output checks。

## 高频追问方向

1. 你项目里的 Agent state 长什么样？
2. 每个 workflow node 做什么？
3. tool schema 怎么定义？错误怎么返回？
4. 工具调用失败、超时、返回脏数据怎么办？
5. RAG 怎么切 chunk，怎么做 metadata filter？
6. 怎么评估 RAG 召回质量？
7. 结构化输出失败怎么办？
8. 为什么需要 Redis/PostgreSQL？
9. 项目有哪些不是生产级的地方？
10. 你如何证明这些项目不是只跟着教程跑？

## 风险与避坑

- 不要说“系统能替代人工 QA”，建议说“辅助人工 QA 提效”。
- 不要说“完全解决企业知识库幻觉”，建议说“用证据引用和拒答策略降低风险”。
- 不要说“已经生产级上线”，除非有真实证据。
- 不要只背框架名，要讲具体 state、tool schema、失败处理和评估。

## 推荐自我介绍方向

我软件工程背景，主要关注 AI 应用开发和 Agent 工程。相比训练大模型本身，我更感兴趣的是把模型能力接入真实文档、工具和业务流程里。

我做过几个代表性项目，比如 Support QA Agent 和 Knowledge Base Assistant。前者重点是用工具调用和 RAG 把客服对话、政策文档和工单信息串起来，生成有证据的质检报告；后者重点是用文档导入、metadata filter 和向量检索来回答内部知识库问题，并在证据不足时拒答。

我的优势是有后端开发和工程拆解基础，能把 LLM 应用从 prompt 进一步落到数据、工具、状态和评估上。目前我希望从 AI 应用开发、Agent/RAG 后端这类岗位切入。
