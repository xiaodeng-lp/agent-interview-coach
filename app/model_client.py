from __future__ import annotations

import os
import json

from openai import OpenAI


SAFE_MODEL_ERROR = "Model response could not be parsed safely. Please retry later."
MAX_MODEL_TEXT_CHARS = int(os.environ.get("MAX_MODEL_TEXT_CHARS", "8000"))

RAW_RESPONSE_HARD_MARKERS = (
    "{'id': 'resp_",
    '{"id":"resp_',
    '{"id": "resp_',
    '"id":"resp_',
    '"id": "resp_',
    "'id': 'resp_",
    "Response(",
    "ChatCompletion(",
)

RAW_RESPONSE_METADATA_MARKERS = (
    "created_at",
    "incomplete_details",
    "instructions",
    "metadata",
)


def create_model_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"].strip(),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
        timeout=float(os.environ.get("MODEL_TIMEOUT_SECONDS", "90")),
    )


def has_raw_response_markers(text: str) -> bool:
    compact = "".join(text.split())
    lowered = text.lower()
    compact_lowered = compact.lower()
    for marker in RAW_RESPONSE_HARD_MARKERS:
        marker_lowered = marker.lower()
        if marker_lowered in lowered or "".join(marker_lowered.split()) in compact_lowered:
            return True
    metadata_hits = 0
    for marker in RAW_RESPONSE_METADATA_MARKERS:
        if marker.lower() in lowered:
            metadata_hits += 1
    if metadata_hits >= 2 and ("resp_" in lowered or "response" in lowered or "{" in text):
        return True
    return False


def ensure_user_visible_text(text: object, source: str = "model") -> str:
    if not isinstance(text, str):
        return SAFE_MODEL_ERROR
    cleaned = text.strip()
    if not cleaned:
        return SAFE_MODEL_ERROR
    if len(cleaned) > MAX_MODEL_TEXT_CHARS:
        return SAFE_MODEL_ERROR
    if has_raw_response_markers(cleaned):
        return SAFE_MODEL_ERROR
    return cleaned


def _message_content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if isinstance(value, str):
                    chunks.append(value)
            else:
                value = getattr(item, "text", None) or getattr(item, "content", None)
                if isinstance(value, str):
                    chunks.append(value)
        return "\n".join(chunks)
    return ""


def extract_chat_text(resp) -> str:
    if isinstance(resp, str):
        parsed = extract_sse_text(resp)
        return ensure_user_visible_text(parsed or resp, "chat.string")
    if isinstance(resp, dict):
        choices = resp.get("choices") or []
        if choices:
            first = choices[0]
            message = first.get("message") or {}
            text = _message_content_to_text(message.get("content"))
            if not text:
                text = first.get("text") or ""
            return ensure_user_visible_text(text, "chat.dict")
        return SAFE_MODEL_ERROR
    choices = getattr(resp, "choices", None)
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message is not None:
            content = getattr(message, "content", None)
            if content is not None:
                return ensure_user_visible_text(_message_content_to_text(content), "chat.object")
            if isinstance(message, dict):
                return ensure_user_visible_text(_message_content_to_text(message.get("content")), "chat.object_dict")
        if isinstance(first, dict):
            message = first.get("message") or {}
            text = _message_content_to_text(message.get("content")) or first.get("text") or ""
            return ensure_user_visible_text(text, "chat.choice_dict")
    text = getattr(resp, "text", None)
    if text:
        return ensure_user_visible_text(text, "chat.text")
    return SAFE_MODEL_ERROR


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
        return ensure_user_visible_text(parsed or resp, "responses.string")
    output_text = getattr(resp, "output_text", None)
    if output_text:
        return ensure_user_visible_text(output_text, "responses.output_text")
    if isinstance(resp, dict):
        return ensure_user_visible_text(_extract_response_dict_text(resp), "responses.dict")
    try:
        data = resp.model_dump()
        return extract_response_text(data)
    except Exception:
        pass
    output = getattr(resp, "output", None) or []
    chunks: list[str] = []
    for item in output:
        content_items = getattr(item, "content", None)
        if content_items is None and isinstance(item, dict):
            content_items = item.get("content")
        for content in content_items or []:
            text = _response_content_text(content)
            if text:
                chunks.append(text)
    if chunks:
        return ensure_user_visible_text("\n".join(chunks), "responses.object_output")
    return SAFE_MODEL_ERROR


def _response_content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        value = content.get("text") or content.get("content")
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            nested = value.get("value") or value.get("text")
            return nested if isinstance(nested, str) else ""
        return ""
    value = getattr(content, "text", None) or getattr(content, "content", None)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        nested = value.get("value") or value.get("text")
        return nested if isinstance(nested, str) else ""
    return ""


def _extract_response_dict_text(resp: dict) -> str:
    output_text = resp.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    chunks: list[str] = []
    for item in resp.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            text = _response_content_text(content)
            if text:
                chunks.append(text)
    if chunks:
        return "\n".join(chunks)
    choices = resp.get("choices") or []
    if choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message") or {}
            return _message_content_to_text(message.get("content")) or first.get("text") or ""
    return ""


def call_model(client: OpenAI, messages: list[dict[str, str]]) -> str:
    model = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
    style = os.environ.get("MODEL_API_STYLE", "chat").strip().lower()
    if style == "chat":
        resp = client.chat.completions.create(model=model, messages=messages)
        return extract_chat_text(resp)
    if style == "responses":
        resp = client.responses.create(
            model=model,
            input=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
        )
        return extract_response_text(resp)
    return SAFE_MODEL_ERROR
