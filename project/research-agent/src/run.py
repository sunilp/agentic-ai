"""CLI runner for the research agent (Section 0c).

Takes a query as a command-line argument, runs the research agent against it
using a MockClient, and prints the annotated trace.

Usage:
    python project/research-agent/src/run.py "What is 15 * 7?"
    python project/research-agent/src/run.py "Search for agentic AI and summarize."
    python project/research-agent/src/run.py --export trace.json "What is 100 / 4 + 10?"

Options:
    --export PATH   Write the trace to a JSON file at PATH.
    --steps N       Maximum agent steps (default: 8).
    --help          Show this message.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Path bootstrap.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from agent import ResearchAgent, export_trace, print_trace  # noqa: E402
from tools import create_research_registry  # noqa: E402

from src.shared.model_client import MockClient  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage, ToolCall  # noqa: E402

# ---------------------------------------------------------------------------
# Mock response builder
# ---------------------------------------------------------------------------

# Scripted responses for common demo queries so the CLI is usable without
# a live API key. Real queries against a live model would omit this and use
# an OpenAIClient or AnthropicClient instead.

_SCRIPTED: dict[str, list[CompletionResponse]] = {}


def _tc(name: str, args: dict[str, Any]) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="cli", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
    )


def _tr(text: str) -> CompletionResponse:
    return CompletionResponse(
        content=text,
        model="mock",
        usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
    )


def _build_scripted_responses() -> dict[str, list[CompletionResponse]]:
    return {
        "what is 15 * 7?": [
            _tc("calculator", {"operation": "multiply", "a": 15, "b": 7}),
            _tr("15 * 7 = 105"),
        ],
        "what is 100 / 4 + 10?": [
            _tc("calculator", {"operation": "divide", "a": 100, "b": 4}),
            _tc("calculator", {"operation": "add", "a": 25.0, "b": 10}),
            _tr("100 / 4 = 25, then 25 + 10 = 35"),
        ],
        "how many words are in 'the quick brown fox jumps over the lazy dog'?": [
            _tc("calculator", {"operation": "add", "a": 0, "b": 9}),
            _tr("The phrase 'the quick brown fox jumps over the lazy dog' contains 9 words."),
        ],
        "search for agentic ai and summarize what you find.": [
            _tc("search", {"query": "agentic AI", "max_results": 2}),
            _tc("read_url", {"url": "https://en.wikipedia.org/wiki/Agentic_AI", "max_chars": 600}),
            _tr(
                "Based on search results and Wikipedia, agentic AI refers to AI systems "
                "that can autonomously plan, reason, and execute multi-step tasks using tools."
            ),
        ],
        "search for machine learning and tell me the first result.": [
            _tc("search", {"query": "machine learning", "max_results": 1}),
            _tr(
                "The first result for 'machine learning' is the Wikipedia article: "
                "https://en.wikipedia.org/wiki/Machine_learning"
            ),
        ],
    }


def _get_mock_client(query: str) -> MockClient:
    """Return a MockClient scripted for the given query (case-insensitive match).

    Falls back to a generic two-step response if no script matches.
    """
    scripted = _build_scripted_responses()
    key = query.strip().lower()
    responses = scripted.get(key)
    if responses:
        return MockClient(responses=responses)

    # Generic fallback: search then answer.
    return MockClient(
        responses=[
            _tc("search", {"query": query, "max_results": 3}),
            _tr(f"Based on my research, here is what I found about: {query}"),
        ]
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run",
        description="Run the research agent against a query and print the trace.",
    )
    parser.add_argument("query", help="The question or task for the agent.")
    parser.add_argument(
        "--export",
        metavar="PATH",
        default=None,
        help="Write the execution trace to this JSON file path.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=8,
        metavar="N",
        help="Maximum number of agent steps (default: 8).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress step-level log output.",
    )
    return parser


async def run_query(query: str, max_steps: int, export_path: str | None, verbose: bool) -> int:
    """Run the agent and print the trace. Returns exit code."""
    registry = create_research_registry()
    client = _get_mock_client(query)

    agent = ResearchAgent(
        client=client,
        registry=registry,
        model_name="claude-haiku-4-5-20251001",
        max_steps=max_steps,
        verbose=verbose,
    )

    result = await agent.run(query)
    print_trace(result.trace)

    if export_path:
        export_trace(result.trace, export_path)
        print(f"Trace exported to {export_path}")

    return 0 if result.answer is not None else 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    exit_code = asyncio.run(
        run_query(
            query=args.query,
            max_steps=args.steps,
            export_path=args.export,
            verbose=not args.quiet,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
