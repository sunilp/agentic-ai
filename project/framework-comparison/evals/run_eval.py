"""Full eval runner for the framework comparison (Section 0d).

Loads test_queries.yaml and rubric.yaml, runs all available implementations
against each query, scores results, and prints a per-implementation report.

Run with:
    python project/framework-comparison/evals/run_eval.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

# Path bootstrap.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_AGENT_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_AGENT_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_SRC_DIR))

import yaml  # noqa: E402

from src.ch00.llm_basics import estimate_cost  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage, ToolCall  # noqa: E402

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------

_EVALS_DIR = Path(__file__).parent
_QUERIES_PATH = _EVALS_DIR / "test_queries.yaml"
_RUBRIC_PATH = _EVALS_DIR / "rubric.yaml"


def load_queries() -> list[dict[str, str]]:
    with _QUERIES_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["queries"]


def load_rubric() -> dict[str, Any]:
    with _RUBRIC_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score(expected: str, actual: str, rubric: dict[str, Any]) -> float:
    scoring = rubric.get("scoring", {})
    exact_score: float = scoring.get("exact_match", 1.0)
    substr_score: float = scoring.get("substring_match", 0.8)
    no_match_score: float = scoring.get("no_match", 0.0)

    e = expected.strip().lower()
    a = actual.strip().lower()
    if e == a:
        return exact_score
    if e in a:
        return substr_score
    return no_match_score


# ---------------------------------------------------------------------------
# Mock responses (same as compare.py)
# ---------------------------------------------------------------------------


def _tc(name: str, args: dict[str, Any]) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="eval", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
    )


def _tr(text: str) -> CompletionResponse:
    return CompletionResponse(
        content=text,
        model="mock",
        usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
    )


def _mock_responses_for(query: str) -> list[CompletionResponse]:
    q = query.strip().lower()
    if "15 * 7" in q:
        return [_tc("calculator", {"operation": "multiply", "a": 15, "b": 7}), _tr("15 * 7 = 105")]
    if "100 / 4" in q and "10" in q:
        return [
            _tc("calculator", {"operation": "divide", "a": 100, "b": 4}),
            _tc("calculator", {"operation": "add", "a": 25.0, "b": 10}),
            _tr("100 / 4 + 10 = 35"),
        ]
    if "quick brown fox" in q:
        return [_tr("The sentence contains 9 words.")]
    if "agentic ai" in q:
        return [
            _tc("search", {"query": "agentic AI", "max_results": 2}),
            _tr("Wikipedia article about agentic AI: autonomous reasoning and tool use."),
        ]
    if "machine learning" in q:
        return [
            _tc("search", {"query": "machine learning", "max_results": 1}),
            _tr("The first result is the Wikipedia article about machine learning."),
        ]
    return [_tr(f"Answer for: {query}")]


# ---------------------------------------------------------------------------
# Run all implementations
# ---------------------------------------------------------------------------

MODEL = "claude-haiku-4-5-20251001"


async def _run_raw(queries: list[dict[str, str]], rubric: dict[str, Any]) -> list[dict[str, Any]]:
    from raw_agent import run_raw_agent

    results = []
    for case in queries:
        query, expected = case["query"], case["expected"]
        t0 = time.monotonic()
        result = await run_raw_agent(query, _mock_responses_for(query), max_steps=5)
        elapsed = (time.monotonic() - t0) * 1000
        actual = result.answer or ""
        tokens = result.total_tokens
        cost = estimate_cost(tokens // 2, tokens // 2, MODEL)
        results.append(
            {
                "query": query,
                "expected": expected,
                "actual": actual,
                "score": score(expected, actual, rubric),
                "tokens": tokens,
                "elapsed_ms": round(elapsed, 1),
                "cost_usd": cost,
                "skipped": False,
            }
        )
    return results


async def _run_adk(queries: list[dict[str, str]], rubric: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        from adk_agent import run_adk_agent
    except ImportError as exc:
        return [
            {
                "query": c["query"],
                "expected": c["expected"],
                "actual": "",
                "score": 0.0,
                "tokens": 0,
                "elapsed_ms": 0.0,
                "cost_usd": 0.0,
                "skipped": True,
                "skip_reason": str(exc),
            }
            for c in queries
        ]

    results = []
    for case in queries:
        query, expected = case["query"], case["expected"]
        try:
            r = await run_adk_agent(query)
            actual = r.answer or ""
            cost = estimate_cost(r.total_tokens // 2, r.total_tokens // 2, MODEL)
            results.append(
                {
                    "query": query,
                    "expected": expected,
                    "actual": actual,
                    "score": score(expected, actual, rubric),
                    "tokens": r.total_tokens,
                    "elapsed_ms": r.elapsed_ms,
                    "cost_usd": cost,
                    "skipped": False,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "query": query,
                    "expected": expected,
                    "actual": "",
                    "score": 0.0,
                    "tokens": 0,
                    "elapsed_ms": 0.0,
                    "cost_usd": 0.0,
                    "skipped": True,
                    "skip_reason": str(exc),
                }
            )
    return results


async def _run_langchain(
    queries: list[dict[str, str]], rubric: dict[str, Any]
) -> list[dict[str, Any]]:
    try:
        from langchain_agent import run_langchain_agent
    except ImportError as exc:
        return [
            {
                "query": c["query"],
                "expected": c["expected"],
                "actual": "",
                "score": 0.0,
                "tokens": 0,
                "elapsed_ms": 0.0,
                "cost_usd": 0.0,
                "skipped": True,
                "skip_reason": str(exc),
            }
            for c in queries
        ]

    results = []
    for case in queries:
        query, expected = case["query"], case["expected"]
        try:
            r = await run_langchain_agent(query)
            actual = r.answer or ""
            cost = estimate_cost(r.total_tokens // 2, r.total_tokens // 2, MODEL)
            results.append(
                {
                    "query": query,
                    "expected": expected,
                    "actual": actual,
                    "score": score(expected, actual, rubric),
                    "tokens": r.total_tokens,
                    "elapsed_ms": r.elapsed_ms,
                    "cost_usd": cost,
                    "skipped": False,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "query": query,
                    "expected": expected,
                    "actual": "",
                    "score": 0.0,
                    "tokens": 0,
                    "elapsed_ms": 0.0,
                    "cost_usd": 0.0,
                    "skipped": True,
                    "skip_reason": str(exc),
                }
            )
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_impl_results(name: str, results: list[dict[str, Any]], rubric: dict[str, Any]) -> None:
    print(f"\n{'=' * 70}")
    print(f"Implementation: {name}")
    print(f"{'=' * 70}")
    metrics = rubric.get("metrics", [])
    print(f"Metrics: {', '.join(metrics)}")
    print()

    first_skipped = next((r for r in results if r.get("skipped")), None)
    if first_skipped:
        print(f"  SKIPPED: {first_skipped.get('skip_reason', 'dependency not installed')}")
        return

    header = f"{'Query':<40} {'Expected':<12} {'Score':>6} {'Tokens':>7}"
    print(header)
    print("-" * len(header))
    for r in results:
        q = r["query"][:38] + ".." if len(r["query"]) > 40 else r["query"]
        exp = r["expected"][:10] + ".." if len(r["expected"]) > 12 else r["expected"]
        print(f"{q:<40} {exp:<12} {r['score']:>6.1f} {r['tokens']:>7}")


def _print_summary(all_results: dict[str, list[dict[str, Any]]]) -> None:
    print(f"\n{'=' * 75}")
    print("Summary")
    print(f"{'=' * 75}")
    header = (
        f"{'Implementation':<22} {'Avg Score':>10} {'Total Tokens':>13} "
        f"{'Avg ms':>8} {'Total cost':>12}"
    )
    print(header)
    print("-" * len(header))
    for name, results in all_results.items():
        active = [r for r in results if not r.get("skipped")]
        if not active:
            print(f"{name:<22}  skipped (not installed)")
            continue
        avg_score = sum(r["score"] for r in active) / len(active)
        total_tokens = sum(r["tokens"] for r in active)
        avg_ms = sum(r["elapsed_ms"] for r in active) / len(active)
        total_cost = sum(r["cost_usd"] for r in active)
        print(
            f"{name:<22} {avg_score:>10.2f} {total_tokens:>13} {avg_ms:>8.1f} ${total_cost:>11.6f}"
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def _main() -> None:
    print("Framework Comparison -- Full Eval")
    print("=" * 70)

    queries = load_queries()
    rubric = load_rubric()

    print(f"Loaded {len(queries)} queries from {_QUERIES_PATH.name}")
    print(
        f"Scoring: exact={rubric['scoring']['exact_match']}  "
        f"substring={rubric['scoring']['substring_match']}  "
        f"no_match={rubric['scoring']['no_match']}"
    )
    print()

    raw_results, adk_results, lc_results = await asyncio.gather(
        _run_raw(queries, rubric),
        _run_adk(queries, rubric),
        _run_langchain(queries, rubric),
    )

    all_results = {
        "raw_agent": raw_results,
        "adk_agent": adk_results,
        "langchain_agent": lc_results,
    }

    for name, results in all_results.items():
        _print_impl_results(name, results, rubric)

    _print_summary(all_results)


if __name__ == "__main__":
    asyncio.run(_main())
