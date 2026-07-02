"""Shared types for the agentic AI examples.

These Pydantic models define the contracts between components.
They are provider-neutral -- no OpenAI or Anthropic types leak through.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class SideEffect(StrEnum):
    """Classifies what a tool does to the world.

    This matters for permission scoping and audit logging.
    A read tool can be retried freely. A write tool needs more care.
    """

    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class ToolCall(BaseModel):
    """A request from the model to execute a tool."""

    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """The result of executing a tool."""

    tool_call_id: str
    name: str
    content: str
    success: bool = True
    error: str | None = None


class Message(BaseModel):
    """A single message in a conversation.

    An assistant turn that calls tools carries them structurally in
    `tool_calls` rather than encoding them into `content` -- this is what
    lets the model client serialize a proper `tool_use` content block
    instead of a plain-text stand-in the API can't reconcile with the
    `tool_result` that follows it. Symmetrically, `tool_results` carries
    every result from a turn's tool calls (there may be more than one --
    the API executes them in parallel) so they can be returned together in
    a single following message, as the API requires.
    """

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None


class ToolParameter(BaseModel):
    """A single parameter in a tool schema."""

    name: str
    type: str
    description: str
    required: bool = True
    enum: list[str] | None = None


class ToolSchema(BaseModel):
    """The contract for a tool -- what it does, what it accepts, what it returns."""

    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    side_effect: SideEffect = SideEffect.READ
    requires_approval: bool = False


class CompletionRequest(BaseModel):
    """A request to a language model."""

    messages: list[Message]
    tools: list[ToolSchema] | None = None
    temperature: float | None = None
    max_tokens: int = 4096
    response_format: dict[str, Any] | None = None


class TokenUsage(BaseModel):
    """Token accounting for a single completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    """A response from a language model."""

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage | None = None
    model: str = ""
    latency_ms: float = 0.0


class Citation(BaseModel):
    """A reference to a specific source passage."""

    source: str
    page: int | None = None
    chunk_id: str | None = None
    text: str
    relevance_score: float = 0.0


class AgentResponse(BaseModel):
    """The final output of an agent run."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    escalated: bool = False
    escalation_reason: str | None = None
    steps_taken: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
