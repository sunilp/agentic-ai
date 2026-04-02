"""Tests for the LLM basics module (Section 0a).

These tests use MockClient so they run without API keys.
"""

import pytest

from src.ch00.llm_basics import (
    call_llm,
    count_tokens_estimate,
    estimate_cost,
    parse_structured_output,
)
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse, TokenUsage


def test_count_tokens_estimate():
    text = "Hello world, this is a test of token counting."
    count = count_tokens_estimate(text)
    assert 8 <= count <= 15


def test_estimate_cost():
    cost = estimate_cost(prompt_tokens=1000, completion_tokens=500, model="gpt-4o")
    assert cost > 0
    assert isinstance(cost, float)


def test_estimate_cost_unknown_model_uses_default():
    cost = estimate_cost(prompt_tokens=100, completion_tokens=50, model="unknown-model")
    assert cost > 0


def test_parse_structured_output_valid_json():
    result = parse_structured_output('{"name": "Alice", "age": 30}')
    assert result == {"name": "Alice", "age": 30}


def test_parse_structured_output_invalid_json():
    result = parse_structured_output("This is not JSON at all.")
    assert result is None


def test_parse_structured_output_extracts_json_from_text():
    result = parse_structured_output('Here is the result: {"status": "ok"} and some more text')
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_call_llm_returns_response():
    client = MockClient(
        responses=[
            CompletionResponse(
                content="Hello! I'm a language model.",
                model="mock",
                usage=TokenUsage(prompt_tokens=10, completion_tokens=8, total_tokens=18),
            )
        ]
    )
    result = await call_llm(client, "Say hello")
    assert result.content == "Hello! I'm a language model."
    assert result.usage.total_tokens == 18
