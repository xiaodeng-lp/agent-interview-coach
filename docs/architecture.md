# Architecture

```text
WeChat
  -> wechat-clawbot long polling
  -> wechat_channel.py message/file routing
  -> commands.py command router
  -> materials.py corpus refresh and file import
  -> engine.py interview prompt assembly
  -> model_client.py OpenAI-compatible model API
  -> WeChat reply
```

## Core Files

- `app/coach_bot.py`: thin CLI entry point.
- `app/wechat_channel.py`: WeChat long polling, direct file-message import, reply sending.
- `app/commands.py`: WeChat command router.
- `app/engine.py`: interview prompt assembly and model call.
- `app/session_store.py`: session state, scoring, weakness tracking, review and answer bank.
- `app/materials.py`: local material directory, cache refresh, WeChat file downloads.
- `app/prompts.py`: stages, modes, weakness labels, system prompt.
- `app/interview_corpus.py`: local material extraction and context selection.
- `app/profile_builder.py`: generated AI interview background material.
- `app/smoke_test.py`: model and WeChat connectivity checks.

## User Flow

1. User prepares resume/project materials.
2. User imports a folder with `/导入资料`, or sends a supported file directly in WeChat.
3. Bot builds corpus cache.
4. User runs `/生成背景`.
5. Bot conducts staged dynamic mock interviews.
6. Bot records scores, weaknesses, reviews, and improved answer drafts.
