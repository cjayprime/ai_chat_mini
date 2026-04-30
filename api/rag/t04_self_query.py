"""4. Self-Query — extract structured filters (category, status) from the query for MCP tool arguments."""

from __future__ import annotations

import json

from typing import Any

from .models import RAGContext

PROMPT = """Extract structured filters from this customer support query. Return JSON with:
- "query": the core request (without filter terms)
- "filters": object with any of: "category" (Monitors, Computers, Printers, Networking, Accessories), "status" (draft, submitted, approved, fulfilled, cancelled), "sku" (e.g. MON-0054)

If no filters are found, return empty filters.

User query: {query}"""


def self_query(ctx: RAGContext, client: Any) -> RAGContext:
    response = client.messages.create(
        model="claude-haiku-4-5-20241022",
        max_tokens=200,
        messages=[{"role": "user", "content": PROMPT.format(query=ctx.query)}],
    )
    raw = response.content[0].text.strip()
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
        if "query" in parsed:
            ctx.query = parsed["query"]
        if "filters" in parsed and isinstance(parsed["filters"], dict):
            ctx.metadata["filters"] = parsed["filters"]
    except (ValueError, json.JSONDecodeError):
        pass
    return ctx
