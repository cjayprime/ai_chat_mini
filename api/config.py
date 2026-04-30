from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = ""
    mcp_server_url: str = "https://order-mcp-74afyau24q-uc.a.run.app/mcp"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    log_level: str = "INFO"
    max_tool_iterations: int = 10
    session_ttl_minutes: int = 30
    max_history_messages: int = 20

    @classmethod
    def from_env(cls) -> Settings:
        origins_raw = os.getenv("CORS_ORIGINS", "*")
        origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            mcp_server_url=os.getenv("MCP_SERVER_URL", cls.mcp_server_url),
            cors_origins=origins,
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            max_tool_iterations=int(os.getenv("MAX_TOOL_ITERATIONS", str(cls.max_tool_iterations))),
            session_ttl_minutes=int(os.getenv("SESSION_TTL_MINUTES", str(cls.session_ttl_minutes))),
            max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", str(cls.max_history_messages))),
        )


settings = Settings.from_env()
