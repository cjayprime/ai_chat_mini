"""Adapter to run RAG pipeline steps using the OpenAI client."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .models import RAGContext

logger = logging.getLogger(__name__)

RAG_MODEL = "gpt-4o-mini"


@dataclass
class _TextBlock:
    text: str


@dataclass
class _FakeResponse:
    content: list[_TextBlock]


class OpenAIShim:
    """Wraps OpenAI client with a .messages.create() interface matching the RAG modules."""

    def __init__(self, openai_client: OpenAI) -> None:
        self._client = openai_client
        self.messages = self

    def create(
        self,
        *,
        model: str = "",
        max_tokens: int = 256,
        messages: list[dict[str, Any]],
        **_: Any,
    ) -> _FakeResponse:
        response = self._client.chat.completions.create(
            model=RAG_MODEL,
            max_tokens=max_tokens,
            messages=messages,
        )
        text = response.choices[0].message.content or ""
        return _FakeResponse(content=[_TextBlock(text=text)])


def run_rag_guardrails(query: str, openai_api_key: str) -> str:
    """Run input guardrails on a query. Returns the query unchanged on success.

    Raises InputGuardrailError on rejection.
    """
    client = OpenAIShim(OpenAI(api_key=openai_api_key))
    ctx = RAGContext(original_query=query)

    # ── Comment out any line to skip that step ──────────────
    from .t01_input_guardrails import input_guardrails

    ctx = input_guardrails(ctx, client)
    # from .pipeline import run_pipeline
    # ctx = run_pipeline(query, client)
    # ────────────────────────────────────────────────────────

    return ctx.query
