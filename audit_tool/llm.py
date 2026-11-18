"""LLM / VLM access layer.

Speaks the OpenAI-compatible /chat/completions protocol over plain HTTP —
no SDK dependency — so it works against vLLM, TGI, LiteLLM, an internal
gateway, or a hosted API. Structured output is enforced by prompt + JSON
parsing with a repair pass, then strict schema validation upstream.

MockClient replays a fixture AuditRepo so the full pipeline can be tested
offline (CI, demos, development without a GPU).
"""
from __future__ import annotations

import base64
import json
import re
import urllib.request
import urllib.error
from dataclasses import dataclass

from .config import ModelEndpoint
from .schemas import AuditRepo


class LLMError(RuntimeError):
    pass


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response.

    Handles raw JSON, ```json fences, and prose-wrapped JSON. Raises
    LLMError if nothing parseable is found.
    """
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidate = text[start : end + 1]
    if candidate is None:
        raise LLMError(f"no JSON object in response: {text[:300]!r}")
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMError(f"unparseable JSON ({exc}): {candidate[:300]!r}") from exc


@dataclass
class OpenAICompatClient:
    """Minimal client for any OpenAI-compatible chat endpoint."""

    endpoint: ModelEndpoint
    temperature: float = 0.1
    timeout_s: int = 300

    def chat(self, messages: list[dict], max_tokens: int = 8192) -> str:
        body = {
            "model": self.endpoint.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            url=f"{self.endpoint.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.endpoint.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMError(f"request to {req.full_url} failed: {exc}") from exc
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"unexpected response shape: {str(payload)[:300]!r}") from exc

    def chat_json(self, messages: list[dict], max_tokens: int = 8192) -> dict:
        """One attempt plus one self-repair retry on malformed JSON."""
        raw = self.chat(messages, max_tokens=max_tokens)
        try:
            return extract_json(raw)
        except LLMError:
            repair = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": (
                    "Your previous answer was not valid JSON. Reply with ONLY the "
                    "corrected JSON object, no prose, no markdown fences."
                )},
            ]
            return extract_json(self.chat(repair, max_tokens=max_tokens))

    @staticmethod
    def image_message(prompt: str, image_path: str, mime: str = "image/png") -> dict:
        with open(image_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }


class MockClient:
    """Offline double: replays a fixture repo regardless of the prompt.

    Lets the entire pipeline (ingest -> prompts -> validation -> store ->
    report data export) run in tests and demos without a model server.
    """

    def __init__(self, fixture_repo: AuditRepo):
        self.fixture = fixture_repo
        self.calls: list[str] = []

    def chat_json(self, messages: list[dict], max_tokens: int = 8192) -> dict:
        prompt = messages[-1]["content"]
        if isinstance(prompt, list):  # vision message
            prompt = next(p["text"] for p in prompt if p["type"] == "text")
        self.calls.append(prompt[:120])
        d = self.fixture.to_dict()
        if "PROCESS MODEL EXTRACTION" in prompt:
            return {"stages": d["stages"]}
        if "PAIN-POINT AUDIT" in prompt:
            return {"findings": d["findings"]}
        if "SOLUTION MAPPING" in prompt:
            return {"solutions": d["solutions"]}
        raise LLMError("MockClient: unrecognised prompt")

    @staticmethod
    def image_message(prompt: str, image_path: str, mime: str = "image/png") -> dict:
        return {"role": "user", "content": [{"type": "text", "text": prompt}]}
