# AGENTS.md

This file defines stable project-level instructions for AI coding agents working in this repository.

## Project Purpose

Agent Interview Coach is a local-first AI mock interview coach for AI/Agent roles.
It imports resume and project materials, builds interview context, and runs staged mock interviews through WeChat or CLI.

## Primary Working Areas

- `app/`: bot logic, commands, prompt assembly, corpus building, session state
- `docs/`: setup, privacy, architecture, project state
- `examples/`: fictional demo materials only

## Stable Project Rules

1. Keep edits scoped and practical. Prefer small improvements over broad refactors.
2. Preserve the repo's local-first workflow. Do not introduce hosted dependencies unless clearly needed.
3. Treat WeChat usability as important. Changes should not make the mobile workflow more fragile.
4. Prefer resume/project realism over flashy AI abstractions.
5. Never commit secrets, sessions, logs, or real personal material.

## Interview Product Rules

1. The interviewer should feel dynamic, not like a fixed question bank.
2. The product should support at least two user-facing training states:
   - interview mode
   - explanation / coaching mode
3. If the user clearly does not know an answer, the system should help them recover instead of only escalating pressure.
4. Resume/project retrieval should prefer the strongest and cleanest source files over noisy backups.

## Context And Token Discipline

When continuing work in this repo, use a layered context strategy:

1. Read `docs/PROJECT_STATE.md` first for the latest project snapshot.
2. Only open the files relevant to the current task.
3. Do not paste large logs or long file contents into the chat when direct file inspection is possible.
4. Keep each conversation focused on one task at a time.
5. If the task changes substantially, start a fresh thread instead of dragging a long mixed history.
6. If the conversation gets long, summarize current state before continuing.

## Preferred Continuation Pattern

For future sessions, the recommended starting prompt is:

`请先读 docs/PROJECT_STATE.md 和 AGENTS.md，再继续这轮任务。`

Then specify one concrete task, for example:

- `这轮只做 bot 稳定性排查`
- `这轮只做讲解模式优化`
- `这轮只做 README 改写`
- `这轮只做检索可诊断性增强`

## Important Files

- `docs/PROJECT_STATE.md`: changing project snapshot and token-saving continuation notes
- `docs/ENGINEERING.md`: engineering spec, boundaries, contracts, validation plan
- `docs/CONTEXT_AND_LIGHT_RAG_DESIGN.md`: context budget and lightweight RAG design
- `docs/TEST_LOG.md`: validation history and issue log
- `app/commands.py`: command router and user-facing mode behavior
- `app/interview_corpus.py`: material filtering and retrieval
- `app/engine.py`: prompt assembly
- `app/wechat_channel.py`: WeChat polling and reply loop

## Publishing Notes

Before packaging or publishing:

1. ensure examples are fictional
2. ensure no real resume or credential files are included
3. review `.gitignore`
4. check `app/resume_materials/`, logs, and generated artifacts before commit
