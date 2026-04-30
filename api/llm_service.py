from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Awaitable, Callable

from openai import AsyncOpenAI, RateLimitError

from models import ChatMessage, ToolCallRecord
from rag.adapter import run_rag_guardrails

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """\
You are Meridian Support, the customer service assistant for Meridian Electronics.

Meridian Electronics sells:
- Monitors (24", 27", 32", ultrawide)
- Keyboards (mechanical, wireless, ergonomic)
- Printers (laser, inkjet, multifunction)
- Networking gear (routers, switches, access points)
- Accessories (cables, adapters, stands, docking stations)

You have access to tools that let you:
- Search and browse the product catalog
- Look up product details by SKU
- Verify customer identity (email + PIN)
- Place new orders
- View order history and order details

Rules:
1. Before accessing any customer-specific data (orders, account info) or placing an order, \
you MUST verify the customer's identity using verify_customer_pin. Ask for their email and \
4-digit PIN if they haven't provided them.
2. For product browsing and search, no authentication is needed.
3. Be concise. Give direct answers. Don't repeat information the customer already knows.
4. When showing products, highlight the key details: name, SKU, price, and stock availability.
5. When placing an order, confirm the items and quantities with the customer before calling create_order.
6. If a tool call fails, explain the issue in plain language and suggest next steps.
7. Never fabricate product information — only use data returned by tools.\
"""

RETRY_ERRORS = (RateLimitError,)
MAX_API_RETRIES = 3
BACKOFF_BASE = 2.0


def _build_messages(
    user_message: str, history: list[ChatMessage]
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


class LLMService:
    def __init__(self, api_key: str, max_iterations: int = 10) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._max_iterations = max_iterations

    async def _call_openai(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        trace: dict[str, Any],
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": messages,
            "store": True,
            "metadata": {
                "trace_id": trace["trace_id"],
                "session_id": trace.get("session_id", ""),
                "iteration": str(len(trace["llm_calls"]) + 1),
            },
        }
        if tools:
            kwargs["tools"] = tools

        for attempt in range(1, MAX_API_RETRIES + 1):
            try:
                start = time.monotonic()
                response = await self._client.chat.completions.create(**kwargs)
                duration = (time.monotonic() - start) * 1000
                trace["llm_calls"].append({
                    "model": MODEL,
                    "duration_ms": round(duration, 1),
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0),
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                    "completion_id": response.id,
                })
                return response
            except RETRY_ERRORS as exc:
                if attempt == MAX_API_RETRIES:
                    logger.error("OpenAI API failed after %d retries: %s", MAX_API_RETRIES, exc)
                    raise
                delay = BACKOFF_BASE ** attempt
                logger.warning(
                    "OpenAI API %s (attempt %d/%d) -- retrying in %.1fs",
                    type(exc).__name__, attempt, MAX_API_RETRIES, delay,
                )
                await asyncio.sleep(delay)

    async def generate_response_stream(
        self,
        user_message: str,
        history: list[ChatMessage],
        tools: list[dict[str, Any]],
        call_tool_fn: Callable[[str, dict[str, Any]], Awaitable[str]] | None = None,
        session_id: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        # ── RAG guardrails + query rewriting (comment out to disable) ──
        try:
            user_message = await asyncio.to_thread(
                run_rag_guardrails, user_message, self._client.api_key
            )
        except Exception as exc:
            logger.warning("RAG guardrail rejected input: %s", exc)
            yield {"type": "delta", "content": f"I can't process that request: {exc}"}
            yield {"type": "done", "tool_calls": []}
            return
        # ── end RAG ──

        messages = _build_messages(user_message, history)
        tool_records: list[ToolCallRecord] = []

        trace: dict[str, Any] = {
            "trace_id": str(uuid.uuid4()),
            "session_id": session_id,
            "model": MODEL,
            "user_message_length": len(user_message),
            "llm_calls": [],
            "tool_calls": [],
            "total_start": time.monotonic(),
        }

        for iteration in range(self._max_iterations):
            response = await self._call_openai(messages, tools, trace)
            choice = response.choices[0]

            logger.info(
                "LLM response (iteration %d): finish_reason=%s",
                iteration + 1, choice.finish_reason,
            )

            if choice.finish_reason != "tool_calls":
                final_text = choice.message.content or "I'm sorry, I couldn't generate a response."

                for word in final_text.split(" "):
                    yield {"type": "delta", "content": word + " "}
                    await asyncio.sleep(0.02)

                trace["total_ms"] = round((time.monotonic() - trace["total_start"]) * 1000, 1)
                del trace["total_start"]
                trace["iterations"] = iteration + 1
                trace["tool_calls_count"] = len(tool_records)
                logger.info("Trace: %s", json.dumps(trace))

                yield {"type": "done", "tool_calls": [r.model_dump() for r in tool_records]}
                return

            messages.append({
                "role": "assistant",
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            })

            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                yield {"type": "tool_start", "tool_name": tool_name, "arguments": arguments}

                start = time.monotonic()
                try:
                    if call_tool_fn is None:
                        raise RuntimeError("No tool executor provided")
                    result_text = await call_tool_fn(tool_name, arguments)
                    is_error = False
                except Exception as exc:
                    result_text = f"Error: {exc}"
                    is_error = True
                    logger.warning("Tool '%s' execution failed: %s", tool_name, exc)

                duration_ms = (time.monotonic() - start) * 1000

                tool_records.append(ToolCallRecord(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result_text,
                    duration_ms=round(duration_ms, 1),
                ))

                trace["tool_calls"].append({
                    "tool": tool_name,
                    "duration_ms": round(duration_ms, 1),
                    "error": is_error,
                })

                yield {"type": "tool_result", "tool_name": tool_name, "duration_ms": round(duration_ms, 1)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

                logger.info("Tool '%s' completed in %.0fms (error=%s)", tool_name, duration_ms, is_error)

        logger.warning("Agentic loop hit max iterations (%d)", self._max_iterations)
        fallback = (
            "I've been working on your request but it's taking more steps than expected. "
            "Could you try rephrasing or breaking it into smaller parts?"
        )
        yield {"type": "delta", "content": fallback}

        trace["total_ms"] = round((time.monotonic() - trace["total_start"]) * 1000, 1)
        del trace["total_start"]
        trace["iterations"] = self._max_iterations
        trace["hit_max_iterations"] = True
        logger.info("Trace: %s", json.dumps(trace))

        yield {"type": "done", "tool_calls": [r.model_dump() for r in tool_records]}

    async def generate_response(
        self,
        user_message: str,
        history: list[ChatMessage],
        tools: list[dict[str, Any]],
        call_tool_fn: Callable[[str, dict[str, Any]], Awaitable[str]] | None = None,
        session_id: str = "",
    ) -> tuple[str, list[ToolCallRecord]]:
        full_text = ""
        tool_calls: list[ToolCallRecord] = []

        async for event in self.generate_response_stream(user_message, history, tools, call_tool_fn, session_id):
            if event["type"] == "delta":
                full_text += event["content"]
            elif event["type"] == "done":
                tool_calls = [ToolCallRecord(**tc) for tc in event.get("tool_calls", [])]

        return full_text.strip(), tool_calls
