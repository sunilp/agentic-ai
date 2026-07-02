"""Tests for the provider-neutral model client."""

import pytest

from src.shared.model_client import ModelClient, create_client
from src.shared.types import CompletionRequest, Message, Role, ToolSchema


def test_create_client_returns_model_client():
    """create_client should return a ModelClient regardless of provider."""
    client = create_client(provider="openai", api_key="test-key", model_name="gpt-4o")
    assert isinstance(client, ModelClient)


def test_create_client_unknown_provider_raises():
    """Unknown provider should raise ValueError with a clear message."""
    with pytest.raises(ValueError, match="Unknown provider"):
        create_client(provider="nonexistent", api_key="test", model_name="test")


def test_build_tool_schema_openai_format():
    """Tool schemas should be convertible to OpenAI function calling format."""
    from src.shared.model_client import _to_openai_tool

    schema = ToolSchema(
        name="search",
        description="Search documents",
        parameters=[],
    )
    result = _to_openai_tool(schema)
    assert result["type"] == "function"
    assert result["function"]["name"] == "search"


def test_completion_request_defaults():
    """CompletionRequest should have sensible defaults."""
    req = CompletionRequest(messages=[Message(role=Role.USER, content="hello")])
    assert req.temperature is None
    assert req.max_tokens == 4096
    assert req.tools is None
