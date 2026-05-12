# Test Log

This file records validation history for Agent Interview Coach.

## Current Environment Snapshot

- Project: `agent-interview-coach`
- Bot entry: `app/coach_bot.py`
- Bot management:
  - `app/start_bot.ps1`
  - `app/stop_bot.ps1`
  - `app/status_bot.ps1`
- Default corpus source: `app/resume_materials`
- Current safe model style: `MODEL_API_STYLE=chat`

## Verified Paths

### 1. Bot Startup Path

- Path: `start_bot.ps1` -> `coach_bot.py` -> corpus load -> WeChat long polling
- Expected: bot starts, loads corpus cache, loads WeChat account, and begins listening
- Observed: verified working in earlier live run
- Status: Pass

### 2. Material Import And Corpus Build Path

- Path: local material folder -> `app/resume_materials` -> `python interview_corpus.py` -> cache file
- Expected: imported materials are parsed into a usable cache
- Observed:
  - initial import produced 23 files and 132 chunks
  - cleanup rules later reduced the active corpus to 13 files and 122 chunks
- Status: Pass

### 3. Corpus Cleanup Validation

- Path: filtered source files -> cleaned corpus cache
- Expected: backup / before / noisy resume variants should be excluded from the active corpus
- Observed: cleaned cache retained the strongest resume/project files and skipped noisy variants
- Status: Pass

### 4. WeChat Message Handling Chain

- Path: WeChat message -> receive -> command / interview routing -> model call -> reply
- Expected: bot receives user message and returns a response
- Observed: bot successfully received a real message; one earlier failure occurred at model call due to API key/provider config, not at receive stage
- Status: Partial pass

## Issue Log

### Issue 1: Stale / Missing PID File Caused Process-State Confusion

- Symptom: bot process could still exist while `status_bot.ps1` reported not running, or `start_bot.ps1` claimed bot was already running after stop attempts.
- Scope: `app/start_bot.ps1`, `app/status_bot.ps1`, `app/stop_bot.ps1`
- What changed:
  - start script removes stale or invalid PID files
  - start script launches `coach_bot.py` with an absolute path
  - status script distinguishes running, stale PID, invalid PID, PID pointing elsewhere, and running-without-pid cases
  - stop script stops only confirmed coach bot processes
- Verification:
  - `start_bot.ps1 -> status_bot.ps1 -> stop_bot.ps1 -> status_bot.ps1`
- Status: Pass
- Residual risk: processes started by older scripts may still need manual cleanup.

### Issue 2: Token Usage Was Too High During Iterative Interview Turns

- Symptom: long chats consumed tokens too quickly.
- Scope: prompt assembly, retrieval, session history.
- What changed:
  - reduced context size
  - reduced history window
  - compressed retained history messages
  - limited retrieved chunks per source
  - avoided redundant protocol-like retrieval in active context
- Status: Mitigated
- Residual risk: long-session behavior still depends on workflow and topic discipline.

### Issue 3: Noisy Resume Corpus Reduced Retrieval Quality

- Symptom: multiple resume versions and backups made the material library noisy.
- Scope: `app/interview_corpus.py`
- What changed:
  - added cleanup / dedupe rules
  - preferred the strongest resume version
- Status: Mitigated
- Residual risk: heuristic cleanup may still need project-specific tuning.

### Issue 4: Real Runtime Model Failure Due To Invalid API Key

- Symptom: bot received a message but failed to answer.
- Observed error: `401 invalid_api_key`
- Meaning: bot receive path was alive, but configured model credentials were rejected.
- Status: Open
- Residual risk: a healthy bot process does not imply a healthy end-to-end reply path.

### Issue 5: Runtime JSON Writes And Corrupt Cache Recovery

- Date: 2026-05-12
- Scope: `app/session_store.py`, `app/interview_corpus.py`, `app/materials.py`
- Problem: runtime JSON files were written directly, and corrupt `sessions.json` / `interview_corpus_cache.json` could make startup brittle.
- What changed:
  - session saves now write to a temp file and atomically replace `sessions.json`
  - invalid session files are backed up as `sessions.json.corrupt.<timestamp>`
  - corpus cache saves now write atomically
  - corpus cache records the actual imported `source_dir`
  - corrupt corpus cache files are backed up
  - corpus source-dir mismatches trigger rebuild
- Verification:
  - `python -m compileall app`
  - temporary-file checks for session save/load
  - temporary corrupt session recovery
  - temporary corrupt corpus cache rebuild
  - temporary corpus source-dir mismatch rebuild
- Status: Pass

### Issue 6: Coaching Recovery For Unknown Answers

- Date: 2026-05-12
- Scope: `app/commands.py`, `app/engine.py`, `app/session_store.py`
- Problem: users could say they did not know an answer or ask for teaching mode, but recovery behavior depended too much on prompt behavior and slash commands.
- What changed:
  - natural language teaching-mode switches are recognized
  - help text tells users they can directly say `不会` / `不知道` / `答不上来`
  - `engine.py` injects a recovery instruction for uncertain answers
  - recovery asks the model to explain, map to the user's project, avoid unsupported claims, and end with one easier follow-up
  - `session_store.py` records `答不上来/概念不清` as a stable weakness
- Verification:
  - `python -m compileall app`
  - local behavior check for natural language teaching-mode switch
  - local behavior check for recovery prompt injection
  - local behavior check for weakness tracking
- Status: Pass

### Issue 7: Startup Backlog Caused WeChat Reply Burst

- Date: 2026-05-12
- Scope: `app/wechat_channel.py`, `.env.example`, `app/.env`
- Problem: when the bot had been offline, starting it could process queued WeChat messages and send many delayed replies.
- What changed:
  - added `SKIP_OLD_WECHAT_MESSAGES_ON_START=true`
  - first poll after startup saves latest sync buffer and skips returned messages when enabled
  - startup logs report skipped backlog count
  - added `WECHAT_SEND_TIMEOUT_SECONDS=20`
  - WeChat sends are wrapped with `asyncio.wait_for`
- Verification:
  - `python -m compileall app`
  - local env-flag behavior test for true/false values
  - checked `.env` contains startup-safety settings without printing secrets
- Status: Pass for code-level validation
- Remaining validation: start bot with queued WeChat messages and confirm no old replies are sent.

### Issue 8: Raw Responses Object Caused WeChat Reply Burst

- Date: 2026-05-12
- Scope: `app/model_client.py`, `app/smoke_test.py`, `app/.env`
- Problem: with `MODEL_API_STYLE=responses`, provider returned metadata with no user-visible output. The old parser could fall back to raw object text and send provider metadata to WeChat.
- What changed:
  - removed raw `str(resp)` fallbacks
  - added safe text extraction for chat and responses styles
  - added raw response marker detection
  - parser failures now return a short controlled error
  - `smoke_test.py --model` requires deterministic `MODEL_SMOKE_OK`
  - `.env` was changed back to `MODEL_API_STYLE=chat`
- Verification:
  - `python -m compileall app`
  - local fake response parser checks
  - `cd app && python smoke_test.py --model`
- Observed:
  - responses live probe returned HTTP 200 with empty output and metadata only
  - chat completions live smoke returned `model ok: MODEL_SMOKE_OK`
- Status: Pass for local/model safety validation
- Residual risk: provider Responses shape may change later; keep chat style until smoke passes with responses.

### Issue 9: Stuck-And-Explain Phrase Did Not Persistently Enter Coaching Mode

- Date: 2026-05-12
- Scope: `app/commands.py`
- Problem: a message like `我不知道，你给我讲一下` triggered one-turn recovery but did not update `session.mode`.
- What changed:
  - added a narrow natural-language rule for stuck-answer marker plus explanation request
  - matching messages switch the session to `教练模式` and continue into normal model reply path
- Verification:
  - `python -m compileall app`
  - local positive and negative phrase checks
  - restarted WeChat bot in that earlier validation round
- Status: Pass

### Issue 10: Coaching Mode Still Looked Like Interview Scoring

- Date: 2026-05-12
- Scope: `app/engine.py`, `app/wechat_channel.py`
- Problem: after switching to coaching mode, replies still followed the global scoring template.
- What changed:
  - added stronger coaching-mode instruction in prompt assembly
  - changed WeChat pre-reply prefix for coaching mode
- Verification:
  - `python -m compileall app`
  - local prompt check for coaching and recovery instructions
  - restarted WeChat bot in that earlier validation round
- Status: Pass

### Issue 11: M0 Evidence Pack And Hard Prompt Rules

- Date: 2026-05-12
- Scope: `app/interview_corpus.py`, `app/engine.py`
- Problem: retrieval context was small but not consistently presented as a formal evidence pack, and prompt assembly lacked explicit hard rules for grounding candidate experience claims.
- What changed:
  - `select_context()` renders a numbered `【本轮证据包】`
  - evidence items include source file, chunk index, evidence level, and body
  - empty retrieval says no relevant evidence was found
  - `engine.build_messages()` injects evidence-use hard rules on every turn
  - candidate experience claims must come from current evidence pack or current-turn user supplement
  - common sense can explain concepts and polish expression, not invent candidate experience
- Verification:
  - `python -m compileall app`
  - local contract script for numbered evidence pack
  - local contract script for empty evidence output
  - local contract script confirming `engine.build_messages()` contains evidence rules
  - `cd app && python smoke_test.py --model`
- Observed: model smoke returned `model ok: MODEL_SMOKE_OK`
- Status: Pass
- Residual risk: retrieval is still heuristic and can miss relevant material.

### Issue 12: M1-A Session History Sanitization

- Date: 2026-05-12
- Scope: `app/session_store.py`
- Problem: long-running sessions could retain raw provider objects, traceback/error dumps, or overlong assistant replies.
- What changed:
  - added raw provider response detection
  - added traceback / API error dump detection
  - raw provider output becomes `[model response parse error omitted]`
  - error dumps become `[error output omitted]`
  - invalid roles, non-string content, and empty messages are dropped
  - `load_sessions()` and `save_sessions()` sanitize history
- Verification:
  - `python -m compileall app`
  - local contract checks for normal message preservation, raw response replacement, traceback replacement, long assistant truncation, and invalid item removal
  - `cd app && python smoke_test.py --model`
- Observed: model smoke returned `model ok: MODEL_SMOKE_OK`
- Status: Pass

### Issue 13: M1-B Mode-Aware History Selection

- Date: 2026-05-12
- Scope: `app/engine.py`
- Problem: valid but mode-conflicting assistant replies could still be re-fed into prompt assembly.
- What changed:
  - added `select_recent_history()`
  - user messages are preserved for coherence
  - coaching mode omits old scoring-template assistant replies
  - technical interview modes omit old coaching/recovery teaching templates
  - selected history still respects `MAX_HISTORY_MESSAGES`
- Verification:
  - `python -m compileall app`
  - local contract script for coaching-mode history filtering
  - local contract script for technical-interview history filtering
  - local contract script for `MAX_HISTORY_MESSAGES`
  - local contract script confirming evidence hard rules still exist
  - `cd app && python smoke_test.py --model`
- Observed: model smoke returned `model ok: MODEL_SMOKE_OK`
- Status: Pass
- Residual risk: filtering is heuristic and marker-based.

### Issue 14: M1-C Weakness And History Budget Tightening

- Date: 2026-05-12
- Scope: `app/session_store.py`, `app/engine.py`
- Problem: long-running sessions can accumulate many weakness labels. Feeding too many historical weaknesses into every prompt increases token cost and can pull the model toward stale issues.
- What changed:
  - `format_weaknesses(session)` accepts optional `max_items`
  - default remains top 10 for compatibility
  - `engine.build_messages()` renders prompt weaknesses with `format_weaknesses(session, max_items=5)`
  - full `session.weaknesses` dictionary remains intact
  - `MAX_HISTORY_MESSAGES` remains unchanged at default 8 for now
- Verification:
  - `python -m compileall app`
  - local contract script confirming default top 10
  - local contract script confirming prompt top 5
  - local contract script confirming `session.weaknesses` is not mutated
  - local contract script confirming M0 evidence hard rules remain
  - local contract script confirming M1-B history filtering remains active
  - `cd app && python smoke_test.py --model`
- Observed:
  - compile passed
  - M1-C contract checks passed
  - model smoke returned `model ok: MODEL_SMOKE_OK`
  - WeChat bot was not started
- Status: Pass
- Residual risk: weakness ordering is still simple count-based sorting.

### Issue 15: Key Technical Docs Mojibake Repair

- Date: 2026-05-12
- Scope:
  - `AGENTS.md`
  - `docs/PROJECT_STATE.md`
  - `docs/ENGINEERING.md`
  - `docs/CONTEXT_AND_LIGHT_RAG_DESIGN.md`
  - `docs/TEST_LOG.md`
- Problem: key Chinese-facing docs contained mojibake, making continuation prompts, engineering rules, context/RAG design, and validation history hard for future agents to read.
- What changed:
  - restored the continuation prompt in `AGENTS.md`
  - rewrote `PROJECT_STATE.md` as a clean current-state snapshot
  - rewrote `ENGINEERING.md` as a readable engineering contract
  - rewrote `CONTEXT_AND_LIGHT_RAG_DESIGN.md` as a readable context budget and lightweight RAG design
  - rewrote `TEST_LOG.md` as a clean validation ledger through M1-C
- Verification:
  - docs-only diff check
  - mojibake marker scan on key docs
- Status:
  Pass

### Issue 16: M2-Prep Retrieval Diagnostics

- Date: 2026-05-12
- Scope: `app/interview_corpus.py`, `docs/PROJECT_STATE.md`, `docs/TEST_LOG.md`
- Problem: heuristic corpus retrieval produced an evidence pack, but there was no local way to inspect why chunks were selected.
- What changed:
  - added shared scoring helpers for query terms, chunk score, matched terms, and score reason
  - added `trace_retrieval()` and `format_retrieval_diagnostics()`
  - added `python app/interview_corpus.py --debug-query "..."`
  - diagnostics show selected/skipped state, title, source, chunk index, priority, score, matched terms, reason, and a final evidence pack preview
  - runtime `select_context()` now uses the same selection helper, so diagnostics and prompt evidence stay aligned
- Verification:
  - `python -m compileall app`
  - `python app\interview_corpus.py --debug-query "Support QA Agent RAG" --trace-limit 6 --max-chunks 3`
- Status:
  Pass
- Residual risk: retrieval remains priority + keyword heuristic only; this change intentionally does not add BM25, embeddings, or new dependencies.

### Issue 17: Chinese Text Repair Pass

- Date: 2026-05-12
- Scope: `app/`, `docs/PROJECT_STATE.md`, `docs/CONTEXT_AND_LIGHT_RAG_DESIGN.md`, `docs/WECHAT_REPLY_BURST_RCA.md`
- Problem: Windows terminal output could make valid UTF-8 Chinese look garbled, while earlier project notes still listed Chinese repair as a next step.
- What changed:
  - verified app and docs files decode as UTF-8
  - confirmed key runtime user-facing prompts in `commands.py`, `engine.py`, `cli_chat.py`, and `interview_corpus.py` are stored as real Chinese text
  - localized remaining English open-question sections in key design/RCA docs
  - updated `PROJECT_STATE.md` so future agents do not treat PowerShell display mojibake as file corruption
- Verification:
  - `python C:\Users\PC\.codex\skills\windows-utf8-chinese\scripts\check_utf8_text.py --paths app docs AGENTS.md README.md .env.example`
  - UTF-8 Python inspection of key runtime prompt files
- Status:
  Pass
- Residual risk: PowerShell may still display Chinese incorrectly unless the terminal session is configured for UTF-8.

## Re-Check Items For Next Session

1. Reconfirm the active API key / provider configuration before testing replies.
2. Reconfirm that the bot can both receive and answer a live message end to end.
3. Reconfirm whether PID handling still behaves after repeated stop/start cycles.
4. Reconfirm explanation-mode behavior with a real WeChat user flow.
5. Use retrieval diagnostics to tune file priorities or chunk limits before BM25 or embeddings.
