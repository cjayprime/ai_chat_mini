"""5. LLM as a Judge — evaluate whether the assistant's response is accurate and on-topic."""

from __future__ import annotations

from typing import Any

from .models import RAGContext

PROMPT = """Evaluate this customer support response on two criteria. For each, respond PASS or FAIL with a one-line reason.

1. ACCURACY: Does the response only state facts that were provided by tool results? (no hallucinated products, prices, or order details)
2. RELEVANCE: Does the response address the customer's original question?

Customer question: {query}

Assistant response: {answer}

Respond in this exact format:
ACCURACY: PASS/FAIL - reason
RELEVANCE: PASS/FAIL - reason"""


class JudgementFailedError(Exception):
    def __init__(self, accuracy: str, relevance: str) -> None:
        self.accuracy = accuracy
        self.relevance = relevance
        super().__init__(f"Accuracy: {accuracy}, Relevance: {relevance}")


def llm_as_a_judge(ctx: RAGContext, client: Any) -> RAGContext:
    response = client.messages.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[{"role": "user", "content": PROMPT.format(
            query=ctx.original_query,
            answer=ctx.answer,
        )}],
    )
    verdict = response.content[0].text.strip()

    accuracy_line = ""
    relevance_line = ""
    for line in verdict.splitlines():
        upper = line.upper()
        if upper.startswith("ACCURACY:"):
            accuracy_line = line
        elif upper.startswith("RELEVANCE:"):
            relevance_line = line

    acc_pass = "PASS" in accuracy_line.upper()
    rel_pass = "PASS" in relevance_line.upper()

    ctx.metadata["judge_accuracy"] = accuracy_line
    ctx.metadata["judge_relevance"] = relevance_line

    if not acc_pass or not rel_pass:
        raise JudgementFailedError(accuracy_line, relevance_line)

    return ctx
