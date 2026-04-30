"""6. Output Guardrails — validate the final answer before returning it to the user."""

from __future__ import annotations

import re

from typing import Any

from .models import RAGContext

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b\d{16}\b", "credit card number"),
]

SAFETY_PROMPT = """Check if this response contains any of the following problems:
1. Harmful or dangerous instructions
2. Personal insults or offensive language
3. Confidential data that should not be shared
4. Fabricated product details, prices, or order information

Respond with ONLY one word: SAFE or UNSAFE

Response to check: {answer}"""


class OutputGuardrailError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def output_guardrails(ctx: RAGContext, client: Any) -> RAGContext:
    for pattern, label in PII_PATTERNS:
        if re.search(pattern, ctx.answer):
            raise OutputGuardrailError(f"Answer contains potential {label}")

    response = client.messages.create(
        model="claude-haiku-4-5-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": SAFETY_PROMPT.format(answer=ctx.answer)}],
    )
    verdict = response.content[0].text.strip().upper()

    if verdict != "SAFE":
        raise OutputGuardrailError("LLM safety classifier flagged output as unsafe")

    ctx.metadata["output_guardrail"] = "passed"
    return ctx
