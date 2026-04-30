"""RAG Pipeline — waterfall of 6 techniques for MCP tool-calling chatbot.

Comment out any line to skip that technique.

Usage:
    from rag import run_pipeline, RAGContext
    ctx = run_pipeline("What monitors?", client)
    print(ctx.query)
"""

from __future__ import annotations

from typing import Any

from .models import RAGContext
from .t01_input_guardrails import input_guardrails
from .t02_query_rewriting import query_rewriting
from .t03_multi_query import multi_query
from .t04_self_query import self_query
from .t05_llm_as_a_judge import llm_as_a_judge
from .t06_output_guardrails import output_guardrails


def run_pipeline(query: str, client: Any) -> RAGContext:
    ctx = RAGContext(original_query=query)

    # ── GUARDRAILS IN ──────────────────────────────────────
    ctx = input_guardrails(ctx, client)

    # ── QUERY TRANSFORMATION ───────────────────────────────
    ctx = query_rewriting(ctx, client)
    ctx = multi_query(ctx, client)

    # ── STRUCTURED EXTRACTION ──────────────────────────────
    ctx = self_query(ctx, client)

    # ── EVALUATION & GUARDRAILS OUT ────────────────────────
    ctx = llm_as_a_judge(ctx, client)
    ctx = output_guardrails(ctx, client)

    return ctx
