---
name: agent-interview-coach
description: Set up, run, customize, diagnose, or package a local WeChat AI mock interview coach that reads resume/project materials, generates AI interview background notes, and trains AI/Agent/RAG/MCP/LLM engineering interview answers. Use when the user asks for mobile mock interview practice, WeChat interview bots, resume-based AI interview coaching, dynamic follow-up interviewers, or GitHub packaging of this coach.
---

# Agent Interview Coach

Use this skill to help a user run or maintain the local WeChat interview coach.

## Safety

- Never print API keys, WeChat tokens, session files, or credential JSON.
- Never commit `.env`, `sessions.json`, `interview_corpus_cache.json`, `reviews/`, `answers/`, logs, credentials, or real resume files.
- Before packaging or publishing, inspect `.gitignore` and run a secret scan with `rg "sk-|token|OPENAI_API_KEY|bot_token|Authorization"`.

## Standard Workflow

1. Locate the project root.
2. Check Python dependencies: `python -m pip install -r requirements.txt`.
3. Check `.env`, but do not print secrets.
4. Prefer the installer on Windows: `powershell -ExecutionPolicy Bypass -File .\install_windows.ps1`.
5. Verify model from `app/`: `python smoke_test.py --model`.
6. Verify WeChat from `app/`: `python smoke_test.py --wechat`.
7. If WeChat is unavailable, run CLI fallback from `app/`: `python cli_chat.py`.
8. Start on Windows from `app/`: `powershell -ExecutionPolicy Bypass -File .\start_bot.ps1`.
9. Check logs from `app/`: `powershell -ExecutionPolicy Bypass -File .\status_bot.ps1`.
10. Run full diagnostics from repo root: `powershell -ExecutionPolicy Bypass -File .\doctor.ps1`.

## Resume Material Workflow

Tell users to either:

- Put `.docx/.pdf/.md/.txt` files in the bot's `resume_materials/` folder and send `/导入资料 <folder>`.
- Or send `/导入资料 <absolute-folder-path>` for an existing resume/project material folder.

Then send `/生成背景` to create `AI面试背景材料.generated.md`.

## WeChat Commands

- `/资料入口`: show the local folder for resume materials.
- `/导入资料 路径`: switch material folder and rebuild corpus.
- `/生成背景`: generate candidate-specific interview background.
- `/模式 教练|技术面|拷打|只面试`: switch training style.
- `开始电话面|开始一面|开始二面|开始HR面`: switch interview stage.
- `/今日弱点`: show tracked weaknesses.
- `/复盘`: write a Markdown review.
- `/标准答案`: save the latest improved answer.
- `/刷新`: reread materials.
- `/重置`: clear session state.

## Troubleshooting

- If model auth fails, check `.env` values and whether the provider supports `MODEL_API_STYLE=chat`.
- If WeChat polling fails, rerun `wechat-clawbot-cc setup`.
- If `/刷新` reads the wrong files, check `RESUME_SOURCE_DIR`.
- If output is garbled in PowerShell, set `$env:PYTHONIOENCODING='utf-8'` for terminal tests; the Python files remain UTF-8.
- If the user wants to test without WeChat, use `python cli_chat.py`.
