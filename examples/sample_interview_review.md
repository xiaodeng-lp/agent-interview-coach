# Sample Interview Review

> Fictional review generated from a mock interview session.

## Session

- Stage: 技术一面
- Mode: 拷打模式
- Topic: Support QA Agent
- Turns: 5
- Average Score: 68/100

## Weaknesses

- Tool schema: 3
- Project authenticity: 3
- RAG evaluation: 2
- Error handling: 2
- Evidence grounding: 2

## Example Turn

### Interviewer

你说 Support QA Agent 里用了 tool calling。请你具体说一个 tool 的输入 schema、输出字段，以及工具失败时 Agent 怎么处理。

### Candidate Answer

我这里主要是让模型调用政策查询工具，然后返回相关政策。如果失败的话就重试，最后生成质检报告。

### Feedback

可信度：中等。你确实知道工具调用的大概流程，但回答太泛，像是在讲概念。

技术准确性：偏弱。你没有说 schema、输出结构、错误类型，也没有说失败信息如何进入 Agent state。

表达结构：一般。应该按“tool 目的-输入-输出-失败处理-state 更新”来回答。

风险点：如果继续这么答，面试官会怀疑你只是知道“工具调用”这个词，但没有真正设计过工具接口。

### Score

- Total: 62
- Credibility: 65
- Technical Accuracy: 55
- Structure: 60
- Project Authenticity: 58

### Better Answer

我举一个 `search_support_policy` 工具。它的输入主要是 `query`、`product_area` 和 `limit`，比如用户投诉退款流程时，query 会包含“refund escalation policy”，product_area 是对应业务线。

输出不是一段自然语言，而是结构化字段，包括 policy title、matched section、evidence snippet、version 和 updated_at。这样后面的 QA analysis node 可以判断引用是否可靠。

失败时我不会让模型自己猜。工具会返回明确的 error type，比如 timeout、no_match、permission_denied。Agent node 会把错误写到 `tool_errors`。如果是 timeout 会重试一次；如果是 no_match，报告会把政策合规判断标记为 uncertain；如果关键证据缺失，最终报告会建议 human review，而不是强行给质检结论。

### Follow-Up

如果政策检索工具返回了 5 条相似政策，其中有过期版本和低相关片段，你的 Agent 怎么过滤？这个过滤逻辑放在 retrieval 阶段、tool 内部，还是 graph node 里？

## Recommended Next Practice

Practice answering with this structure:

```text
问题背景 -> 我的方案 -> 具体实现 -> 异常处理 -> 结果与边界
```

Avoid saying only:

```text
我用了 Agent、RAG、tool calling。
```

Instead say:

```text
我把政策查询、工单信息查询和升级规则查询封装成工具，每个工具有明确 schema。workflow 负责在 node 之间传递 state，并根据 tool_errors 做重试、降级或 human review。
```
