# Sample Project Detail: Support QA Agent

> Fictional project note for demonstrating Agent Interview Coach.

## Problem

Support teams often need to review large numbers of customer conversations for quality, policy compliance, escalation correctness, and coaching opportunities. Manual review is slow, while a plain summarization bot may miss policy evidence or make unsupported judgments.

The project goal was to build an evidence-grounded QA assistant that reviews a support conversation and produces a structured QA report.

## Workflow

1. User uploads or selects a support conversation.
2. Conversation parser extracts customer issue, agent actions, resolution status, and timestamps.
3. Policy retrieval node retrieves relevant support policy snippets.
4. Ticket lookup node retrieves ticket metadata such as product area, priority, and history.
5. QA analysis node checks policy compliance, tone, completeness, and escalation correctness.
6. Report node generates structured output with score, evidence, issue category, and coaching notes.
7. Guardrail node checks whether the report makes unsupported claims without evidence.

## Agent State

The workflow state contained:

- `conversation_text`
- `ticket_metadata`
- `retrieved_policies`
- `issue_category`
- `compliance_findings`
- `sentiment_summary`
- `evidence_quotes`
- `tool_errors`
- `qa_report`

## Tools

Example tool schema:

```json
{
  "name": "search_support_policy",
  "description": "Retrieve support policy snippets relevant to a customer conversation",
  "input_schema": {
    "query": "string",
    "product_area": "string",
    "limit": "integer"
  }
}
```

```json
{
  "name": "get_ticket_metadata",
  "description": "Get metadata for a support ticket",
  "input_schema": {
    "ticket_id": "string"
  }
}
```

## Error Handling

- If policy retrieval failed, the report marked policy compliance as uncertain.
- If ticket metadata was missing, the report still analyzed the conversation but avoided priority judgments.
- If model output missed required JSON fields, the system retried with a stricter schema reminder.
- If there was not enough evidence, the assistant returned “needs human review.”

## Evaluation

Small manual evaluation dimensions:

- Did the report cite relevant evidence?
- Did it avoid unsupported accusations?
- Was the issue category correct?
- Was the coaching note actionable?
- Did it preserve uncertainty when evidence was weak?

## Known Limitations

- The project used demo conversations and synthetic policies.
- QA scores were not calibrated against a large human-reviewed dataset.
- The assistant should support, not replace, human QA reviewers.
