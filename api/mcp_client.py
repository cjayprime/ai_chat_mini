from __future__ import annotations

import asyncio
import logging
import time
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, Tool

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0


class MCPToolError(Exception):
    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"MCP tool '{tool_name}' failed: {message}")


def _mcp_tool_to_openai(tool: Tool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def _extract_text(result: CallToolResult) -> str:
    parts: list[str] = []
    for block in result.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts) if parts else "(no text content returned)"


class MCPClient:
    """Connects to an MCP server over streamable HTTP, discovers tools,
    and exposes them in OpenAI's tool-calling format."""

    def __init__(self, server_url: str) -> None:
        self._server_url = server_url
        self._exit_stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._tools: list[Tool] = []
        self._openai_tools: list[dict[str, Any]] = []
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    async def connect(self) -> None:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await self._try_connect()
                return
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    logger.error(
                        "MCP connection failed after %d attempts: %s", MAX_RETRIES, exc
                    )
                    raise
                delay = RETRY_BACKOFF_BASE * attempt
                logger.warning(
                    "MCP connection attempt %d/%d failed (%s) — retrying in %.1fs",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

    async def _try_connect(self) -> None:
        await self.disconnect()

        stack = AsyncExitStack()
        try:
            read_stream, write_stream, _ = await stack.enter_async_context(
                streamablehttp_client(self._server_url)
            )
            session: ClientSession = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

            tools_result = await session.list_tools()
            self._tools = tools_result.tools
            self._openai_tools = [_mcp_tool_to_openai(t) for t in self._tools]

            self._session = session
            self._exit_stack = stack
            self._connected = True

            logger.info(
                "MCP connected — %d tools discovered: %s",
                len(self._tools),
                [t.name for t in self._tools],
            )
        except BaseException:
            await stack.aclose()
            raise

    async def disconnect(self) -> None:
        self._connected = False
        self._session = None
        self._tools = []
        self._openai_tools = []
        if self._exit_stack is not None:
            try:
                await self._exit_stack.aclose()
            except Exception as exc:
                logger.warning("Error closing MCP connection: %s", exc)
            self._exit_stack = None
        logger.info("MCP client disconnected")

    def get_tools_for_openai(self) -> list[dict[str, Any]]:
        return list(self._openai_tools)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        if not self._connected or self._session is None:
            raise MCPToolError(tool_name, "MCP client is not connected")

        known_names = {t.name for t in self._tools}
        if tool_name not in known_names:
            raise MCPToolError(
                tool_name,
                f"Unknown tool. Available: {', '.join(sorted(known_names))}",
            )

        logger.info("Calling MCP tool '%s' with args: %s", tool_name, arguments)
        start = time.monotonic()

        try:
            result: CallToolResult = await self._session.call_tool(
                tool_name, arguments
            )
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            logger.error(
                "MCP tool '%s' raised after %.0fms: %s", tool_name, duration, exc
            )
            raise MCPToolError(tool_name, str(exc)) from exc

        duration = (time.monotonic() - start) * 1000
        text = _extract_text(result)

        if result.isError:
            logger.warning(
                "MCP tool '%s' returned error in %.0fms: %s",
                tool_name,
                duration,
                text,
            )
            raise MCPToolError(tool_name, text)

        logger.info(
            "MCP tool '%s' succeeded in %.0fms (%d content blocks)",
            tool_name,
            duration,
            len(result.content),
        )
        logger.debug("MCP tool '%s' result: %s", tool_name, text)
        return text

    async def __aenter__(self) -> MCPClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.disconnect()
