from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from config import settings
from llm_service import LLMService
from mcp_client import MCPClient
from models import ChatMessage, ChatRequest, ChatResponse, SessionInfo, ToolCallRecord

logger = logging.getLogger(__name__)


class Session:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.history: list[ChatMessage] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self.authenticated_customer_id: str | None = None

    def is_expired(self, ttl_minutes: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=ttl_minutes)
        return self.last_active < cutoff

    def touch(self) -> None:
        self.last_active = datetime.now(timezone.utc)

    def add_message(self, role: str, content: str) -> None:
        self.history.append(ChatMessage(role=role, content=content))
        if len(self.history) > settings.max_history_messages:
            self.history = self.history[-settings.max_history_messages :]

    def to_info(self) -> SessionInfo:
        return SessionInfo(
            session_id=self.session_id,
            created_at=self.created_at,
            last_active=self.last_active,
            message_count=len(self.history),
            authenticated_customer_id=self.authenticated_customer_id,
        )


_sessions: dict[str, Session] = {}


def _purge_expired() -> None:
    expired = [
        sid
        for sid, s in _sessions.items()
        if s.is_expired(settings.session_ttl_minutes)
    ]
    for sid in expired:
        del _sessions[sid]
    if expired:
        logger.info("Purged %d expired session(s)", len(expired))


def _get_or_create_session(session_id: str) -> Session:
    _purge_expired()
    session = _sessions.get(session_id)
    if session is None or session.is_expired(settings.session_ttl_minutes):
        session = Session(session_id)
        _sessions[session_id] = session
        logger.info("Created new session: %s", session_id)
    session.touch()
    return session


def _detect_customer_id(tool_records: list[ToolCallRecord]) -> str | None:
    for record in tool_records:
        if record.tool_name == "verify_customer_pin" and "Error" not in record.result:
            for line in record.result.splitlines():
                if "ID:" in line:
                    return line.split("ID:")[-1].strip()
    return None


class ChatHandler:
    def __init__(self, mcp_client: MCPClient, llm_service: LLMService) -> None:
        self._mcp = mcp_client
        self._llm = llm_service

    async def handle_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        session = _get_or_create_session(request.session_id)
        session.add_message("user", request.message)

        tools = self._mcp.get_tools_for_openai()
        full_text = ""
        tool_records: list[ToolCallRecord] = []

        async for event in self._llm.generate_response_stream(
            user_message=request.message,
            history=session.history[:-1],
            tools=tools,
            call_tool_fn=self._mcp.call_tool,
            session_id=request.session_id,
        ):
            if event["type"] == "delta":
                full_text += event["content"]
            elif event["type"] == "done":
                tool_records = [ToolCallRecord(**tc) for tc in event.get("tool_calls", [])]

            yield f"data: {json.dumps(event)}\n\n"

        customer_id = _detect_customer_id(tool_records)
        if customer_id:
            session.authenticated_customer_id = customer_id

        session.add_message("assistant", full_text.strip())

        logger.info(
            "Session %s: %d messages, %d tool calls this turn",
            session.session_id, len(session.history), len(tool_records),
        )

    async def handle(self, request: ChatRequest) -> ChatResponse:
        session = _get_or_create_session(request.session_id)
        session.add_message("user", request.message)

        tools = self._mcp.get_tools_for_openai()
        reply_text, tool_records = await self._llm.generate_response(
            user_message=request.message,
            history=session.history[:-1],
            tools=tools,
            call_tool_fn=self._mcp.call_tool,
            session_id=request.session_id,
        )

        customer_id = _detect_customer_id(tool_records)
        if customer_id:
            session.authenticated_customer_id = customer_id

        session.add_message("assistant", reply_text)

        logger.info(
            "Session %s: %d messages, %d tool calls this turn",
            session.session_id, len(session.history), len(tool_records),
        )

        return ChatResponse(
            session_id=session.session_id,
            message=reply_text,
            tool_calls_made=tool_records,
        )

    @staticmethod
    def get_session_info(session_id: str) -> SessionInfo | None:
        session = _sessions.get(session_id)
        if session is None or session.is_expired(settings.session_ttl_minutes):
            return None
        return session.to_info()
