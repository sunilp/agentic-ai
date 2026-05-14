"""Provider-neutral model client.

This is the interface between your agent code and any LLM provider.
The rest of the codebase never imports openai or anthropic directly.

Why this matters:
- You can switch providers without rewriting agent logic.
- You can test with a mock client.
- You can add cost tracking in one place.
- You can route between cheap and expensive models without changing callers.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.shared.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Role,
    TokenUsage,
    ToolCall,
    ToolSchema,
)


class ModelClient(ABC):
    """Abstract base for all model providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request and return a typed response."""
        ...


class OpenAIClient(ModelClient):
    """Client for OpenAI-compatible APIs (OpenAI, Azure, local via ollama/vllm)."""

    def __init__(self, api_key: str, model_name: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        start = time.monotonic()
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [_to_openai_message(m) for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            payload["tools"] = [_to_openai_tool(t) for t in request.tools]
        if request.response_format:
            payload["response_format"] = request.response_format

        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed = (time.monotonic() - start) * 1000

        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage", {})

        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )
                )

        return CompletionResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            model=data.get("model", self.model_name),
            latency_ms=elapsed,
        )


class AnthropicClient(ModelClient):
    """Client for the Anthropic Messages API."""

    def __init__(self, api_key: str, model_name: str):
        super().__init__(model_name)
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=120.0,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        start = time.monotonic()

        system_msg = None
        messages = []
        for m in request.messages:
            if m.role == Role.SYSTEM:
                system_msg = m.content
            else:
                messages.append(_to_anthropic_message(m))

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if system_msg:
            payload["system"] = system_msg
        if request.tools:
            payload["tools"] = [_to_anthropic_tool(t) for t in request.tools]

        resp = await self._client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed = (time.monotonic() - start) * 1000

        content = None
        tool_calls = []
        for block in data.get("content", []):
            if block["type"] == "text":
                content = block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        name=block["name"],
                        arguments=block["input"],
                    )
                )

        usage = data.get("usage", {})
        return CompletionResponse(
            content=content,
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            ),
            model=data.get("model", self.model_name),
            latency_ms=elapsed,
        )


class MockClient(ModelClient):
    """Mock client for testing. Returns canned responses."""

    def __init__(self, responses: list[CompletionResponse] | None = None):
        super().__init__("mock")
        self._responses = responses or []
        self._call_count = 0

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if self._call_count < len(self._responses):
            resp = self._responses[self._call_count]
        else:
            resp = CompletionResponse(content="Mock response", model="mock")
        self._call_count += 1
        return resp


def create_client(
    provider: str,
    api_key: str = "",
    model_name: str = "",
    base_url: str | None = None,
) -> ModelClient:
    """Factory function to create the right client for a provider.

    Supported providers: openai, anthropic, local, mock
    """
    if provider == "openai":
        return OpenAIClient(api_key=api_key, model_name=model_name)
    elif provider == "anthropic":
        return AnthropicClient(api_key=api_key, model_name=model_name)
    elif provider == "local":
        url = base_url or "http://localhost:11434/v1"
        # FIX: Resolve hardcoded 'local' key by prioritizing provided api_key.
        actual_key = api_key if api_key else "local"
        return OpenAIClient(api_key=actual_key, model_name=model_name, base_url=url)
    elif provider == "mock":
        return MockClient()
    else:
        raise ValueError(
            f"Unknown provider: '{provider}'. Supported: openai, anthropic, local, mock"
        )


# --- Format converters (internal) ---


def _to_openai_message(msg: Message) -> dict[str, Any]:
    d: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
    if msg.name:
        d["name"] = msg.name
    if msg.tool_call_id:
        d["tool_call_id"] = msg.tool_call_id
    return d


def _to_openai_tool(schema: ToolSchema) -> dict[str, Any]:
    properties = {}
    required = []
    for p in schema.parameters:
        prop: dict[str, Any] = {"type": p.type, "description": p.description}
        if p.enum:
            prop["enum"] = p.enum
        properties[p.name] = prop
        if p.required:
            required.append(p.name)

    return {
        "type": "function",
        "function": {
            "name": schema.name,
            "description": schema.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _to_anthropic_message(msg: Message) -> dict[str, Any]:
    role = "user" if msg.role in (Role.USER, Role.TOOL) else "assistant"
    if msg.role == Role.TOOL:
        return {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": msg.tool_call_id, "content": msg.content}
            ],
        }
    return {"role": role, "content": msg.content}


def _to_anthropic_tool(schema: ToolSchema) -> dict[str, Any]:
    properties = {}
    required = []
    for p in schema.parameters:
        prop: dict[str, Any] = {"type": p.type, "description": p.description}
        if p.enum:
            prop["enum"] = p.enum
        properties[p.name] = prop
        if p.required:
            required.append(p.name)

    return {
        "name": schema.name,
        "description": schema.description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }
