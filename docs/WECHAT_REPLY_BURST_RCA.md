# WeChat Reply Burst RCA And Fix Spec

本文档按 `technical-spec-first` skill 编写，记录 2026-05-12 这次 WeChat 刷屏问题的根因分析、边界条件、修复方案和验收标准。

## 1. Document Purpose

这是一次 incident RCA + 修复技术规格。

目标不是责备某次操作，而是把问题拆成可验证的工程边界，防止后续再把内部模型响应、历史消息或超长文本刷到微信。

## 2. Background

项目是 local-first WeChat AI mock interview coach。

相关链路：

```text
WeChat message
  -> app/wechat_channel.py
  -> app/engine.py
  -> app/model_client.py
  -> model provider
  -> app/model_client.py extract text
  -> app/wechat_channel.py split and send
  -> WeChat user
```

本次用户现象：

- bot 启动后，微信里出现大量回复。
- 初步误判为 WeChat 历史积压消息被处理。
- 后续验证发现更直接原因是模型 Responses API 返回的原始对象被当成正文发送，`send_text()` 将 2 万多字符按 1600 字拆成多条微信消息。

## 3. Goals

1. 防止 raw model response / metadata / system instructions 被发送到微信。
2. 保留 WeChat 启动跳过积压消息的安全保护。
3. 明确 `chat` 与 `responses` 两种 API style 的验证标准。
4. 让 `smoke_test.py --model` 不只验证“不 401”，还验证“返回内容可发给用户”。
5. 修复时不改 prompt、retrieval、session 业务行为。

## 4. Non-Goals

本轮不做：

- 不重构 WeChat bot 主循环。
- 不更换模型 provider。
- 不引入新的 SDK 或依赖。
- 不改面试 prompt 内容。
- 不改 corpus retrieval 策略。
- 不删除 WeChat credential 或 sync buffer，除非用户明确要求。

## 5. Current Problems

### P0: Raw Model Response Can Leak To User

`app/model_client.py` 多处 fallback 到:

```python
return str(resp)
```

这对 CLI 调试可能方便，但对微信产品是高风险行为。

当 provider 返回结构不符合当前解析逻辑时，用户可能收到：

- response id
- created_at
- incomplete_details
- instructions
- provider metadata
- 大段系统说明
- Python dict/string dump

### P0: Smoke Test Accepted A Bad Response

`python smoke_test.py --model` exit code 为 0，但返回内容实际是 raw object。

现有 smoke test 只证明：

- API 请求没有抛异常。

它没有证明：

- 返回文本可读。
- 返回文本符合用户请求。
- 返回文本不是 metadata dump。
- 返回长度适合微信发送。

### P1: Scope Drift During Config Repair

原始目标是修复 `.env` key 读取问题。

实际发生了：

```text
fix .env BOM/key read
  -> copy Codex provider config
  -> set MODEL_API_STYLE=responses
  -> smoke test only checks no 401
  -> start WeChat bot
  -> raw response is sent in many chunks
```

其中 `MODEL_API_STYLE=responses` 是协议切换，应该单独验证，不应混在 key 修复里。

### P1: Two Reply-Burst Risks Were Confused

风险 A：启动时处理历史积压 WeChat 消息。  
风险 B：单条 raw model response 被拆成多条微信消息。

二者现象都像“刷屏”，但根因不同。

当前 `SKIP_OLD_WECHAT_MESSAGES_ON_START=true` 解决风险 A，不解决风险 B。

## 6. Proposed Architecture

目标链路：

```text
model provider response
  -> extract_chat_text / extract_response_text
  -> validate_user_visible_text
       - non-empty
       - not raw response object
       - not metadata dump
       - within reasonable length or explicitly allowed
  -> return clean text
  -> split_wechat_text
  -> send_message_weixin with timeout
```

如果解析失败：

```text
provider response
  -> parser cannot extract clean text
  -> log concise diagnostic locally
  -> return short user-facing error
```

不得把完整 raw object 发给用户。

## 7. Module Responsibilities

| Module | Responsibility | Must Not Own |
| --- | --- | --- |
| `app/model_client.py` | API style dispatch, response text extraction, safe fallback | WeChat splitting, interview prompt design |
| `app/smoke_test.py` | Connectivity and response-shape validation | Full interview workflow |
| `app/wechat_channel.py` | WeChat polling, startup backlog skip, send timeout, message splitting | Model response parsing |
| `app/engine.py` | Build interview messages and call model client | Provider-specific response parsing |
| `app/.env` | Runtime provider configuration | Source-controlled defaults |
| `.env.example` | Safe documented defaults | Real secrets |

## 8. Data Contracts

### Model Client Output Contract

`call_model(client, messages) -> str`

Required:

- returns user-visible text only
- no raw provider object dumps
- no credentials
- no huge metadata payload
- raises or returns a short controlled error if parsing fails

Invalid outputs:

```text
{'id': 'resp_...', 'created_at': ...}
{"id":"resp_...", ...}
Response(...)
ChatCompletion(...)
```

### Smoke Test Contract

`python smoke_test.py --model` should fail if:

- response is empty
- response starts with raw object markers
- response contains obvious metadata-only fields
- response length is unexpectedly huge
- response does not contain the expected test phrase or close equivalent

## 9. Runtime Lifecycle

### Safe Model Reply Lifecycle

```text
call_model()
  -> choose style from MODEL_API_STYLE
  -> call provider
  -> extract text
  -> validate text shape
  -> return clean reply
```

### WeChat Startup Lifecycle

```text
run_wechat_bot()
  -> load sync buf
  -> first get_updates
  -> save latest sync buf
  -> if SKIP_OLD_WECHAT_MESSAGES_ON_START=true:
       skip first returned batch
  -> next poll handles new messages normally
```

## 10. Failure Semantics

| Failure Type | Meaning | User-Facing Behavior | Local Log |
| --- | --- | --- | --- |
| `auth_failed` | provider returns 401 | short config error | status code and provider, no key |
| `unsupported_api_style` | unknown `MODEL_API_STYLE` | short config error | style value |
| `response_parse_failed` | parser cannot find clean text | short parser error | response type and short preview |
| `raw_response_detected` | output looks like provider object | short parser error | response type and first safe preview |
| `response_too_long` | model output exceeds safe threshold unexpectedly | short truncation/error policy | length and style |
| `wechat_startup_backlog_skipped` | first poll returned old messages | no WeChat reply | skipped count |
| `wechat_send_timeout` | send hangs past timeout | no retry storm; log error | user id, timeout seconds |

## 11. Fix Plan

### M0: Immediate Stop-The-Bleed

1. Keep bot stopped until model output is safe.
2. Set `MODEL_API_STYLE=chat` temporarily and test.
3. If `chat` works with current provider/key, use `chat` for now.
4. If `chat` fails, keep `responses` but fix parsing before restarting bot.

### M1: Safe Model Client

In `app/model_client.py`:

1. Replace `return str(resp)` fallbacks with controlled parse failure.
2. Add helper:

```python
def ensure_user_visible_text(text: str, source: str) -> str:
    ...
```

3. Detect raw-object markers such as:

```text
{'id': 'resp_
{"id":"resp_
created_at
incomplete_details
instructions
```

4. Return a short controlled error if unsafe.

### M2: Better Responses Parsing

If using `responses`:

- inspect provider response shape with a local test
- support dict, SDK object, and nested output formats
- prefer `output_text`
- then `output[].content[].text`
- then known provider-compatible fields
- never fallback to full object string

### M3: Stronger Smoke Test

In `app/smoke_test.py`:

1. Ask for a deterministic short phrase.
2. Assert output length is reasonable.
3. Reject raw-object markers.
4. Exit non-zero on unsafe output.

### M4: Live WeChat Validation

Only after M1-M3:

1. Start bot.
2. Confirm no startup backlog replies are sent.
3. Send one fresh WeChat message.
4. Confirm exactly one normal reply sequence, not raw metadata.

## 12. Validation Plan

### Required Local Checks

```powershell
python -m compileall app
```

```powershell
cd app
python smoke_test.py --model
```

### Model Client Unit-Style Checks

Use fake response samples:

- normal chat completion
- normal responses output
- raw dict with `id: resp_...`
- empty response
- malformed response

Expected:

- normal samples extract clean text
- raw/malformed samples return controlled failure, not raw object string

### WeChat Safety Check

Before live restart:

```powershell
cd app
.\status_bot.ps1
```

Expected:

```text
coach_bot not running
```

Then:

```powershell
.\start_bot.ps1
.\status_bot.ps1
```

Expected logs:

- bot running
- if backlog exists, log skipped count
- no old-message reply burst

## 13. Review Checklist

Before restarting WeChat bot:

- `MODEL_API_STYLE` was intentionally chosen and tested.
- `smoke_test.py --model` returned clean user-visible text.
- `model_client.py` cannot return raw provider object dumps.
- `SKIP_OLD_WECHAT_MESSAGES_ON_START=true` remains enabled.
- `WECHAT_SEND_TIMEOUT_SECONDS` remains set.
- bot is not already running.
- no secrets were printed or committed.

## 14. 待确认问题

1. packyapi 对 `gpt-5.5` 是否支持 Chat Completions，还是只支持 Responses？
2. packyapi 的 `responses.create` 返回值到底是 OpenAI SDK 的 `Response` 对象、dict，还是字符串化后的 dict？
3. 即使模型响应解析已经修复，微信回复是否还需要额外设置总字符数上限？
4. `smoke_test.py --model` 是否应该自动更新 `docs/TEST_LOG.md`，还是保持人工记录？
