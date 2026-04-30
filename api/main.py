from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from chat_handler import ChatHandler
from config import settings
from llm_service import LLMService
from mcp_client import MCPClient, MCPToolError
from models import ChatRequest, ChatResponse, HealthResponse, SessionInfo

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

mcp_client = MCPClient(settings.mcp_server_url)
llm_service = LLMService(settings.openai_api_key, settings.max_tool_iterations)
chat_handler = ChatHandler(mcp_client, llm_service)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info(
        "Starting up -- connecting to MCP server at %s", settings.mcp_server_url
    )
    try:
        await mcp_client.connect()
        logger.info("MCP connected -- %d tools loaded", mcp_client.tool_count)
    except Exception:
        logger.exception("MCP connection failed on startup -- running in degraded mode")
    yield
    logger.info("Shutting down -- disconnecting MCP client")
    await mcp_client.disconnect()


app = FastAPI(
    title="Meridian Electronics Support Chatbot",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if mcp_client.is_connected else "degraded",
        mcp_connected=mcp_client.is_connected,
        tools_loaded=mcp_client.tool_count,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await chat_handler.handle(request)
    except MCPToolError as exc:
        logger.error("MCP tool error: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Tool error: {exc.message}"
        ) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /chat")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    try:
        return StreamingResponse(
            chat_handler.handle_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except MCPToolError as exc:
        logger.error("MCP tool error: %s", exc)
        raise HTTPException(
            status_code=502, detail=f"Tool error: {exc.message}"
        ) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /chat/stream")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str) -> SessionInfo:
    info = chat_handler.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return info


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
