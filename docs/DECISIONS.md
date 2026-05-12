# Decisions

## 1. Local-First WeChat Interview Coach

- Decision:
  Keep the product local-first and WeChat-accessible instead of turning it into a hosted web service first.
- Why:
  The main user need is mobile interview practice with minimal deployment friction.
  The current path is faster to iterate and matches the user's real usage pattern.
- Tradeoff:
  This makes process supervision, credentials, and local environment drift more important.

## 2. File-Based Project Context Instead of Chat-Only Memory

- Decision:
  Store stable and changing project context in repository files instead of relying on a long conversation window.
- Files:
  - `AGENTS.md`
  - `docs/PROJECT_STATE.md`
  - `docs/TEST_LOG.md`
- Why:
  Long chat history increases token cost and makes project continuation brittle.
  Project files are inspectable, versionable, and reusable in new sessions.

## 3. Heuristic Corpus Cleanup Before Full RAG

- Decision:
  Clean the material corpus first instead of introducing a heavier vector RAG stack immediately.
- Why:
  The biggest immediate quality problem was noisy source material:
  multiple resume backups, before versions, and other low-signal files.
  Better source selection gives faster gains than adding infrastructure too early.
- Current rule:
  Prefer the strongest resume version and skip noisy variants such as backup, before, temp, and photo-heavy copies.
- Tradeoff:
  Retrieval is still heuristic and may miss some useful long-tail context.

## 4. Two User-Facing Interview States

- Decision:
  Support both interview-style and explanation-style usage.
- Current mapping:
  - `/模式 面试` -> regular technical interview flow
  - `/模式 讲解` -> coaching / explanation flow
- Why:
  If the user cannot answer a question, pure pressure-only follow-up creates a poor training loop.
- Remaining work:
  The explanation mode still needs better behavior, not just mode naming.

## 5. Token Control via Smaller Runtime Context

- Decision:
  Reduce runtime context instead of relying on the model to manage a large prompt gracefully.
- Applied changes:
  - smaller `MAX_CONTEXT_CHARS`
  - fewer retrieved chunks
  - shorter retained history
  - compressed stored assistant replies
  - skip redundant protocol-like retrieval in the active context
- Why:
  The previous setup re-fed too much material and too much model-generated text into later turns.

## 6. Keep Current Code As Source Of Truth

- Decision:
  When chat history and code differ, treat the current code and current files as the source of truth.
- Why:
  Long troubleshooting sessions often accumulate stale assumptions.
  This is especially important for:
  - runtime entry points
  - environment variables
  - process management behavior
  - model/API configuration

## 7. Known Fragile Areas To Reconfirm In New Sessions

- Bot process supervision:
  `start_bot.ps1`, `stop_bot.ps1`, and `status_bot.ps1` can drift when a stale `coach_bot.pid` remains.
- Encoding:
  Some Chinese-facing files show mojibake in terminal output depending on environment encoding.
- Model/API:
  Successful bot startup does not guarantee valid model credentials at runtime.
  Recent logs show a real `401 invalid_api_key` failure during message handling.
