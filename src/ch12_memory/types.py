"""Memory system type definitions for Chapter 12."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryCategory(StrEnum):
    """Categories that determine how a memory record is prioritised and retained."""

    CORRECTION = "correction"
    ESCALATION = "escalation"
    NEGATIVE_RETRIEVAL = "negative_retrieval"
    HIGH_VALUE_SUCCESS = "high_value_success"


class ScopeType(StrEnum):
    """Visibility scope for shared memory entries."""

    AGENT = "agent"
    TEAM = "team"
    GLOBAL = "global"


class MemoryRecord(BaseModel):
    """A single episodic memory captured from agent execution."""

    id: str = ""
    query: str
    context: str
    outcome: str
    correction: str | None = None
    category: MemoryCategory
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    usefulness_score: float = 0.0
    embedding: list[float] = Field(default_factory=list, exclude=True)


class SharedEntry(BaseModel):
    """A key-value entry shared across agents or teams."""

    scope: ScopeType
    key: str
    value: str
    version: int = 1
    agent_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""


class TruncationResult(BaseModel):
    """Result of a context-window truncation operation."""

    messages: list[dict] = Field(default_factory=list)
    dropped_count: int = 0
    total_tokens_estimate: int = 0


class MemoryStoreStats(BaseModel):
    """Aggregate statistics for a memory store."""

    total_records: int = 0
    stale_records: int = 0
    avg_usefulness: float = 0.0
    avg_access_count: float = 0.0
