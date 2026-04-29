from __future__ import annotations

import os
import json

from openai import OpenAI


def create_model_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"].strip(),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
        timeout=float(os.environ.get("MODEL_TIMEOUT_SECONDS", "90")),
    )


def extract_chat_text(resp) -> str:
    if isinstance(resp, str):
        parsed = extract_sse_text(resp)
        return parsed or resp
    if isinstance(resp, dict):
        try:
            return resp["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            return str(resp)
    choices = getattr(resp, "choices", None)
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message is not None:
            content = getattr(message, "content", None)
            if content is not None:
                return content
            if isinstance(message, dict):
                return message.get("content") or ""
        if isinstance(first, dict):
            return first.get("message", {}).get("content") or first.get("text") or ""
    text = getattr(resp, "text", None)
    if text:
        return text
    return str(resp)


def extract_sse_text(text: str) -> str:
    chunks: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:") :].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for choice in data.get("choices", []):
            delta = choice.get("delta") or {}
            message = choice.get("message") or {}
            if delta.get("content"):
                chunks.append(delta["content"])
            elif message.get("content"):
                chunks.append(message["content"])
            elif choice.get("text"):
                chunks.append(choice["text"])
    return "".join(chunks).strip()


def extract_response_text(resp) -> str:
    if isinstance(resp, str):
        parsed = extract_sse_text(resp)
        return parsed or resp
    output_text = getattr(resp, "output_text", None)
    if output_text:
        return output_text
    if isinstance(resp, dict):
        output = resp.get("output") or []
        chunks: list[str] = []
        for item in output:
            for content in item.get("content", []):
                if content.get("text"):
                    chunks.append(content["text"])
        if chunks:
            return "\n".join(chunks)
        return str(resp)
    try:
        data = resp.model_dump()
        return extract_response_text(data)
    except Exception:
        return str(resp)


def call_model(client: OpenAI, messages: list[dict[str, str]]) -> str:
    model = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
    style = os.environ.get("MODEL_API_STYLE", "chat").strip().lower()
    if style == "chat":
        resp = client.chat.completions.create(model=model, messages=messages)
        return extract_chat_text(resp)
    resp = client.responses.create(
        model=model,
        input=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
    )
    return extract_response_text(resp)
