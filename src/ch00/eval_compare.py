"""Eval comparison module (Section 0d).

Provides a simple evaluation harness for comparing agent implementations
side-by-side. The scoring logic is deliberately minimal: the goal is to show
the *structure* of an eval loop, not a production-grade benchmark.

Scoring rules:
- Exact match (case-insensitive): 1.0
- Expected string is a substring of actual (case-insensitive): 0.8
- No match: 0.0
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from src.ch00.llm_basics import estimate_cost
from src.ch00.tool_use import create_default_registry
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse, TokenUsage, ToolCall

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class EvalResult:
    """The outcome of evaluating a single query."""

    query: str
    expected: str
    actual: str
    score: float  # 0.0 to 1.0
    tokens: int
    latency_ms: float
    cost_estimate: float  # USD


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_answer(query: str, expected: str, actual: str) -> EvalResult:
    """Score an agent answer against an expected string.

    Uses simple substring matching (case-insensitive). No semantic similarity
    is computed -- this is intentional; the module is meant to illustrate eval
    structure, not to be a production scorer.

    Args:
        query:    The original user query.
        expected: The ground-truth answer string.
        actual:   The answer produced by the agent.

    Returns:
        An EvalResult with score 1.0 (exact), 0.8 (substring), or 0.0 (miss).
        Tokens and latency are set to 0 / 0.0 when called directly; the
        run_eval helper populates them from the agent result.
    """
    norm_expected = expected.strip().lower()
    norm_actual = actual.strip().lower()

    if norm_expected == norm_actual:
        score = 1.0
    elif norm_expected in norm_actual:
        score = 0.8
    else:
        score = 0.0

    return EvalResult(
        query=query,
        expected=expected,
        actual=actual,
        score=score,
        tokens=0,
        latency_ms=0.0,
        cost_estimate=0.0,
    )


# ---------------------------------------------------------------------------
# Test queries
# ---------------------------------------------------------------------------

TEST_QUERIES: list[dict[str, str]] = [
    {
        "query": "What is 12 plus 8?",
        "expected": "20",
    },
    {
        "query": "What is 9 multiplied by 7?",
        "expected": "63",
    },
    {
        "query": "How many words are in the sentence: the quick brown fox?",
        "expected": "4",
    },
    {
        "query": "Search for information about machine learning.",
        "expected": "machine learning",
    },
    {
        "query": "What is 100 divided by 4?",
        "expected": "25",
    },
]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_comparison(results: dict[str, list[EvalResult]]) -> None:
    """Print per-query results and a summary table for each implementation.

    Args:
        results: Mapping from implementation name to list of EvalResult objects,
                 one per TEST_QUERY entry.
    """
    # Per-query detail.
    for impl_name, eval_results in results.items():
        print(f"\n{'=' * 60}")
        print(f"Implementation: {impl_name}")
        print(f"{'=' * 60}")
        print(f"{'Query':<40} {'Expected':<12} {'Got':<25} {'Score'}")
        print(f"{'-' * 40} {'-' * 12} {'-' * 25} {'-' * 5}")
        for r in eval_results:
            query_short = r.query[:38] + ".." if len(r.query) > 40 else r.query
            actual_short = r.actual[:23] + ".." if len(r.actual) > 25 else r.actual
            print(f"{query_short:<40} {r.expected:<12} {actual_short:<25} {r.score:.1f}")

    # Summary table.
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    header = f"{'Implementation':<20} {'Avg Score':>10} {'Total Tokens':>13} {'Avg Latency ms':>15} {'Total Cost USD':>15}"
    print(header)
    print("-" * len(header))
    for impl_name, eval_results in results.items():
        if not eval_results:
            continue
        avg_score = sum(r.score for r in eval_results) / len(eval_results)
        total_tokens = sum(r.tokens for r in eval_results)
        avg_latency = sum(r.latency_ms for r in eval_results) / len(eval_results)
        total_cost = sum(r.cost_estimate for r in eval_results)
        print(
            f"{impl_name:<20} {avg_score:>10.2f} {total_tokens:>13} "
            f"{avg_latency:>15.1f} {total_cost:>15.6f}"
        )


# ---------------------------------------------------------------------------
# Demo runner (raw agent)
# ---------------------------------------------------------------------------


async def _run_raw_agent_evals() -> list[EvalResult]:
    """Run the raw agent against TEST_QUERIES using a scripted MockClient.

    This demo shows how to wire up the Agent class from raw_agent.py with
    eval harness. Because we use MockClient, no real API call is made.
    """
    # Import here to avoid a circular-import at module level.
    from src.ch00.raw_agent import Agent

    registry = create_default_registry()
    eval_results: list[EvalResult] = []

    # Scripted responses for each TEST_QUERY entry.
    # Each tuple: (optional tool_call, final_text_answer)
    scripted: list[tuple[ToolCall | None, str]] = [
        (
            ToolCall(id="tc1", name="calculator", arguments={"operation": "add", "a": 12, "b": 8}),
            "12 + 8 = 20",
        ),
        (
            ToolCall(
                id="tc2", name="calculator", arguments={"operation": "multiply", "a": 9, "b": 7}
            ),
            "9 * 7 = 63",
        ),
        (
            ToolCall(id="tc3", name="word_count", arguments={"text": "the quick brown fox"}),
            "There are 4 words in that sentence.",
        ),
        (
            ToolCall(
                id="tc4", name="search", arguments={"query": "machine learning", "max_results": 2}
            ),
            "Here are results about machine learning.",
        ),
        (
            ToolCall(
                id="tc5", name="calculator", arguments={"operation": "divide", "a": 100, "b": 4}
            ),
            "100 / 4 = 25",
        ),
    ]

    model = "claude-haiku-4-5-20251001"

    for item, (tool_call, final_text) in zip(TEST_QUERIES, scripted):
        mock_responses: list[CompletionResponse] = []
        if tool_call is not None:
            mock_responses.append(
                CompletionResponse(
                    content=None,
                    tool_calls=[tool_call],
                    model=model,
                    usage=TokenUsage(prompt_tokens=40, completion_tokens=20, total_tokens=60),
                )
            )
        mock_responses.append(
            CompletionResponse(
                content=final_text,
                model=model,
                usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
            )
        )

        client = MockClient(responses=mock_responses)
        agent = Agent(client=client, registry=registry, max_steps=5)

        t0 = time.monotonic()
        agent_result = await agent.run(item["query"])
        latency_ms = (time.monotonic() - t0) * 1000

        actual = agent_result.answer or ""
        base_result = score_answer(query=item["query"], expected=item["expected"], actual=actual)

        tokens = agent_result.total_tokens
        cost = estimate_cost(
            prompt_tokens=tokens // 2,
            completion_tokens=tokens // 2,
            model=model,
        )

        eval_results.append(
            EvalResult(
                query=base_result.query,
                expected=base_result.expected,
                actual=base_result.actual,
                score=base_result.score,
                tokens=tokens,
                latency_ms=latency_ms,
                cost_estimate=cost,
            )
        )

    return eval_results


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":

    async def _demo() -> None:
        print("Running eval harness against raw agent (MockClient)...")
        raw_results = await _run_raw_agent_evals()
        print_comparison({"raw_agent": raw_results})

    asyncio.run(_demo())
