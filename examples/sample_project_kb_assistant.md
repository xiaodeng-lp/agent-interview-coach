# Sample Project Detail: Knowledge Base Assistant

> Fictional project note for demonstrating Agent Interview Coach.

## Problem

Employees often ask repeated questions about onboarding, engineering runbooks, internal tools, and operational processes. Information is scattered across Markdown files, PDFs, and FAQ pages. A generic chatbot may hallucinate answers if retrieval is weak.

The project goal was to build a RAG-based knowledge-base assistant that answers questions with citations and refuses when it cannot find enough evidence.

## Data Sources

- Markdown onboarding documents
- PDF runbooks
- FAQ pages
- Structured metadata: document owner, version, update time, topic, and access level

## Retrieval Design

- Documents were cleaned before chunking.
- Chunk size was tuned around section boundaries instead of fixed character length only.
- Metadata filters were applied for document type, topic, and version.
- Vector search retrieved candidate chunks.
- The answer prompt required source titles and short evidence snippets.

## Answer Policy

The assistant should:

- Answer only when retrieved evidence is relevant.
- Cite source document titles.
- Say “I could not find enough evidence” when retrieval confidence is low.
- Avoid inventing internal policies.

## Evaluation

The evaluation set contained common employee questions:

- “How do I request access to the staging environment?”
- “What should I do when a deployment fails?”
- “Who owns the billing service?”
- “Where is the onboarding checklist?”

Each answer was reviewed for:

- Retrieval relevance
- Citation correctness
- Answer completeness
- Hallucination risk

## Known Limitations

- It did not implement full permission control.
- It did not have a production-grade reranker.
- The evaluation set was small and manually curated.
