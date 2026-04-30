"""3. Multi-Query Expansion — generate query variants that may trigger different tools."""

from __future__ import annotations

from typing import Any

from .models import RAGContext

PROMPT = """Generate 3 different ways to ask this customer support question.
Each variant should approach the request from a different angle to help
the system pick the best tools (product search, order lookup, account verification).
Return one query per line, nothing else.

Question: {query}"""


def multi_query(ctx: RAGContext, client: Any) -> RAGContext:
    response = client.messages.create(
        model="claude-haiku-4-5-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": PROMPT.format(query=ctx.query)}],
    )
    variants = [
        line.strip()
        for line in response.content[0].text.strip().splitlines()
        if line.strip()
    ]
    ctx.queries = [ctx.query] + variants[:3]
    return ctx
