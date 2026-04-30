"""Shared data structures passed through the waterfall pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RAGContext:
    original_query: str
    query: str = ""
    queries: list[str] = field(default_factory=list)
    answer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.query:
            self.query = self.original_query
        if not self.queries:
            self.queries = [self.query]
