"""Configuration for the audit engine. All values come from environment
variables so the same code runs against a local vLLM server, an internal
OpenAI-compatible gateway, or a hosted API without edits.

  AUDIT_LLM_BASE_URL   e.g. http://localhost:8000/v1   (text model endpoint)
  AUDIT_LLM_MODEL      e.g. Qwen/Qwen2.5-72B-Instruct
  AUDIT_LLM_API_KEY    token if the endpoint requires one (default: EMPTY)
  AUDIT_VLM_BASE_URL   vision model endpoint (defaults to the LLM endpoint)
  AUDIT_VLM_MODEL      e.g. Qwen/Qwen2.5-VL-72B-Instruct
  AUDIT_VLM_API_KEY    token for the vision endpoint (default: EMPTY)
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEndpoint:
    base_url: str
    model: str
    api_key: str


@dataclass(frozen=True)
class AuditConfig:
    llm: ModelEndpoint
    vlm: ModelEndpoint
    max_chars_per_doc: int = 120_000      # per-document context budget
    max_code_files: int = 200             # cap for the code-scan pass
    temperature: float = 0.1              # audit work wants determinism
    request_timeout_s: int = 300

    @staticmethod
    def from_env() -> "AuditConfig":
        llm = ModelEndpoint(
            base_url=os.environ.get("AUDIT_LLM_BASE_URL", "http://localhost:8000/v1"),
            model=os.environ.get("AUDIT_LLM_MODEL", "default"),
            api_key=os.environ.get("AUDIT_LLM_API_KEY", "EMPTY"),
        )
        vlm = ModelEndpoint(
            base_url=os.environ.get("AUDIT_VLM_BASE_URL", llm.base_url),
            model=os.environ.get("AUDIT_VLM_MODEL", llm.model),
            api_key=os.environ.get("AUDIT_VLM_API_KEY", "EMPTY"),
        )
        return AuditConfig(llm=llm, vlm=vlm)
