"""Tests for the raw agent module (Section 0c)."""

import pytest
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse, TokenUsage, ToolCall
from src.ch00.raw_agent import Agent, AgentResult
from src.ch00.tool_use import create_default_registry


def _mock_text_response(content: str) -> CompletionResponse:
    return CompletionResponse(
        content=content,
        model="mock",
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
    )


def _mock_tool_response(name: str, args: dict) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="tc_1", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
    )


@pytest.mark.asyncio
async def test_agent_returns_text_response_immediately():
    client = MockClient(responses=[_mock_text_response("The answer is 42.")])
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)
    result = await agent.run("What is the answer?")
    assert result.answer == "The answer is 42."
    assert result.steps == 1
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_agent_executes_tool_then_responds():
    client = MockClient(responses=[
        _mock_tool_response("calculator", {"operation": "add", "a": 2, "b": 3}),
        _mock_text_response("2 + 3 = 5"),
    ])
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)
    result = await agent.run("What is 2 + 3?")
    assert result.answer == "2 + 3 = 5"
    assert result.steps == 2


@pytest.mark.asyncio
async def test_agent_respects_budget():
    responses = [_mock_tool_response("search", {"query": f"attempt {i}"}) for i in range(10)]
    client = MockClient(responses=responses)
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=3)
    result = await agent.run("Find everything about everything")
    assert result.steps <= 3
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_agent_handles_unknown_tool():
    client = MockClient(responses=[
        _mock_tool_response("nonexistent_tool", {"foo": "bar"}),
        _mock_text_response("I couldn't find the tool, but here's my answer."),
    ])
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)
    result = await agent.run("Do something")
    assert result.answer is not None
    assert result.steps == 2


@pytest.mark.asyncio
async def test_agent_trace_records_steps():
    client = MockClient(responses=[
        _mock_tool_response("calculator", {"operation": "multiply", "a": 6, "b": 7}),
        _mock_text_response("6 * 7 = 42"),
    ])
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)
    result = await agent.run("What is 6 * 7?")
    assert len(result.trace) == 2
    assert result.trace[0]["type"] == "tool_call"
    assert result.trace[1]["type"] == "response"
