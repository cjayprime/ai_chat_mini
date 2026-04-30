"""2. Query Rewriting — rewrite the user query to be clearer for tool selection."""

from __future__ import annotations

from typing import Any

from .models import RAGContext

PROMPT = """Rewrite this customer support query to be more specific and actionable.
The system has tools for: product search, product details, customer verification,
order placement, and order tracking.
Return ONLY the rewritten query, nothing else.

Original query: {query}"""


def query_rewriting(ctx: RAGContext, client: Any) -> RAGContext:
    response = client.messages.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[{"role": "user", "content": PROMPT.format(query=ctx.query)}],
    )
    ctx.query = response.content[0].text.strip()
    ctx.queries = [ctx.query]
    return ctx
