# Sample Resume: Alex Chen

> This is a fully fictional resume for demonstration. It does not describe a real person.

## Basic Info

- Name: Alex Chen
- Target Role: AI Application Engineer / Agent Engineer / LLM Backend Developer
- Education: M.S. in Software Engineering, fictional university
- Email: sample@example.com

## Summary

Software engineering graduate student interested in building practical LLM applications. Project experience focuses on Agent workflows, RAG systems, tool calling, backend APIs, evaluation, and deployment basics.

Comfortable with Python, FastAPI, PostgreSQL, Redis, vector search, OpenAI-compatible APIs, and graph-style Agent orchestration. Looking for entry-level AI application engineering roles where LLMs are connected to real documents, tools, and business workflows.

## Skills

- Programming: Python, SQL, basic TypeScript
- Backend: FastAPI, REST APIs, async jobs, Docker basics
- LLM Apps: Agent workflows, ReAct, tool calling, prompt design, structured output
- RAG: chunking, embeddings, vector search, metadata filtering, reranking concepts
- Data: PostgreSQL, Redis, pandas
- Evaluation: answer groundedness checks, retrieval recall checks, manual review sets
- Deployment: Linux basics, OpenAI-compatible serving APIs, simple observability logs

## Project 1: Support QA Agent

Built a customer support quality-assurance assistant that reviews support conversations, checks policy compliance, extracts issue categories, and generates coaching notes for support agents.

Responsibilities:

- Designed an Agent workflow with conversation parsing, policy retrieval, violation detection, sentiment summary, and final QA report generation.
- Wrapped policy lookup, ticket lookup, and escalation rule lookup as tool functions with explicit input schemas.
- Used RAG to retrieve relevant support policy snippets from a small internal knowledge base.
- Added structured output for QA score, issue category, evidence quotes, and recommended coaching notes.
- Added guardrails to avoid unsupported accusations when policy evidence was missing.

Tech Stack:

- Python, FastAPI, PostgreSQL, Redis
- Vector search, BGE-style embeddings, RAG retrieval
- OpenAI-compatible model API, graph-style Agent workflow

What I learned:

- In workflow Agent projects, tool and retrieval failures need explicit state and fallback handling.
- QA-style applications need evidence-grounded outputs, not just fluent summaries.
- Structured output is easier to evaluate than free-form text.

## Project 2: Knowledge Base Assistant

Built an internal knowledge-base assistant for answering employee questions from onboarding documents, engineering runbooks, and FAQ pages.

Responsibilities:

- Implemented document ingestion for Markdown and PDF files.
- Designed chunking rules and metadata fields such as document type, owner, version, and update time.
- Combined vector search with metadata filters to avoid retrieving outdated documents.
- Added citation-style answer output with retrieved source titles.
- Built a small evaluation set of common questions to compare retrieval settings.

Tech Stack:

- Python, FastAPI, PostgreSQL, FAISS/Milvus-style vector store
- Embedding model API, RAG, metadata filtering

What I learned:

- RAG quality depends on document cleaning, chunk boundaries, metadata, and evaluation.
- “No answer found” is better than hallucinating when retrieval confidence is low.

## Project 3: Ticket Routing Agent

Built a ticket triage assistant that classifies incoming issue reports, selects a responsible team, and suggests next actions.

Responsibilities:

- Defined a taxonomy of issue categories and responsible teams.
- Used tool calls to fetch service ownership and recent incident notes.
- Generated structured routing output: category, team, urgency, evidence, and next step.
- Logged prediction results for later manual review.

Tech Stack:

- Python, FastAPI, PostgreSQL, Redis
- Tool calling, structured JSON output, simple evaluation scripts

What I learned:

- Classification tasks need clear labels and reviewable evidence.
- Routing decisions should preserve uncertainty instead of forcing a team when evidence is weak.

## Interview Risk Points

- Do not overclaim production-scale deployment.
- Be clear about what was personally implemented versus simulated for a project demo.
- Be ready to explain tool schemas, Agent state, RAG chunking, metadata filters, and evaluation.
- Do not say “the Agent is always correct”; emphasize evidence, uncertainty, and fallback behavior.
