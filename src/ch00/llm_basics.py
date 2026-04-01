"""LLM basics module (Section 0a).

Demonstrates the fundamental mechanics of calling a language model:
token estimation, cost accounting, structured output parsing, and
making a single completion call through the shared ModelClient interface.
"""

from __future__ import annotations

import asyncio
import json
import re

from src.shared.model_client import MockClient, ModelClient
from src.shared.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Role,
    TokenUsage,
)

# Pricing per 1M tokens: (prompt_price, completion_price)
# Sources: provider pricing pages as of 2025-Q4 (subject to change).
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
}

# Default fallback for unknown models (conservative mid-tier estimate).
_DEFAULT_PRICING: tuple[float, float] = (1.00, 5.00)


def count_tokens_estimate(text: str) -> int:
    """Estimate the number of tokens in *text*.

    Uses the common rule-of-thumb of ~4 characters per token.
    This is not a tiktoken or sentencepiece count; it is a quick
    approximation that works well enough for rough cost projections.

    Args:
        text: The text to estimate.

    Returns:
        Estimated token count (minimum 1).
    """
    return max(1, len(text) // 4)


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Estimate the dollar cost of a completion.

    Uses MODEL_PRICING if the model is known; falls back to a sensible
    default for unrecognised model identifiers.

    Args:
        prompt_tokens:     Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        model:             Model identifier string.

    Returns:
        Estimated cost in USD as a float.
    """
    prompt_price, completion_price = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    cost = (prompt_tokens / 1_000_000) * prompt_price + (completion_tokens / 1_000_000) * completion_price
    return float(cost)


def parse_structured_output(text: str) -> dict | None:
    """Parse a JSON object from model output.

    Tries three strategies in order:
    1. Direct json.loads on the full text.
    2. Regex extraction of the first {...} block.
    3. Returns None if both strategies fail.

    Args:
        text: Raw text from the model.

    Returns:
        Parsed dict, or None if no valid JSON object was found.
    """
    # Strategy 1: the whole text is valid JSON.
    try:
        result = json.loads(text.strip())
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract the first {...} block.
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    return None


async def call_llm(
    client: ModelClient,
    user_message: str,
    system_message: str = "You are a helpful assistant.",
    temperature: float = 0.0,
) -> CompletionResponse:
    """Make a single completion call through the shared ModelClient.

    Constructs a minimal two-message conversation (system + user) and
    returns the typed CompletionResponse without any post-processing.

    Args:
        client:         Any ModelClient instance (real or mock).
        user_message:   The user's prompt text.
        system_message: Optional system instruction (defaults to helpful assistant).
        temperature:    Sampling temperature; 0.0 for deterministic output.

    Returns:
        CompletionResponse from the model.
    """
    request = CompletionRequest(
        messages=[
            Message(role=Role.SYSTEM, content=system_message),
            Message(role=Role.USER, content=user_message),
        ],
        temperature=temperature,
    )
    return await client.complete(request)


if __name__ == "__main__":
    """Demo: run simple examples of each function in this module."""

    async def _demo() -> None:
        # --- Token estimation ---
        sample = "Large language models process text as tokens, not characters."
        estimated = count_tokens_estimate(sample)
        print(f"Text: {sample!r}")
        print(f"Estimated tokens: {estimated}\n")

        # --- Cost estimation ---
        for model in ("gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"):
            cost = estimate_cost(prompt_tokens=1000, completion_tokens=500, model=model)
            print(f"Cost for {model}: ${cost:.6f}")
        print()

        # --- Structured output parsing ---
        examples = [
            '{"status": "ok", "confidence": 0.95}',
            'The analysis is complete. {"result": "pass", "score": 87} End of report.',
            "This response contains no JSON.",
        ]
        for ex in examples:
            parsed = parse_structured_output(ex)
            print(f"Input:  {ex!r}")
            print(f"Parsed: {parsed}\n")

        # --- Simple API call with MockClient ---
        client = MockClient(
            responses=[
                CompletionResponse(
                    content="I am a language model running on a neural network.",
                    model="mock",
                    usage=TokenUsage(prompt_tokens=12, completion_tokens=11, total_tokens=23),
                )
            ]
        )
        response = await call_llm(client, "What are you?")
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.usage.total_tokens if response.usage else 'unknown'}")

        # --- Temperature comparison (determinism demonstration) ---
        print("\nTemperature comparison (mock):")
        for temp in (0.0, 0.7, 1.0):
            r = await call_llm(client, "Generate a creative sentence.", temperature=temp)
            print(f"  temp={temp}: {r.content!r}")

    asyncio.run(_demo())
