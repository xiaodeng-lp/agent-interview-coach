from __future__ import annotations

import os

from openai import OpenAI


def create_model_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"].strip(),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip(),
    )


def call_model(client: OpenAI, messages: list[dict[str, str]]) -> str:
    model = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
    style = os.environ.get("MODEL_API_STYLE", "chat").strip().lower()
    if style == "chat":
        resp = client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content or ""
    resp = client.responses.create(
        model=model,
        input=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
    )
    output_text = getattr(resp, "output_text", None)
    if output_text:
        return output_text
    return str(resp)
