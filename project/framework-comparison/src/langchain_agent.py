"""LangChain agent wrapper for the framework comparison (Section 0d).

Thin shim that imports create_langchain_agent from src/ch00/langchain_agent and
exposes a uniform run_agent() interface for use by compare.py.

Requires: pip install langchain-core langchain-anthropic langgraph
If dependencies are missing, LANGCHAIN_AVAILABLE is False and
run_langchain_agent() raises ImportError. The compare script handles this
gracefully by skipping the LangChain column.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from src.ch00.langchain_agent import LANGCHAIN_AVAILABLE, create_langchain_agent


@dataclass
class LangChainResult:
    """Minimal result wrapper matching the structure expected by compare.py."""

    answer: str | None
    steps: int
    total_tokens: int
    total_cost_estimate: float
    elapsed_ms: float
    budget_exhausted: bool


async def run_langchain_agent(query: str, max_steps: int = 5) -> LangChainResult:
    """Run the LangChain agent against *query*.

    Requires langchain-core, langchain-anthropic, and langgraph to be installed.
    Raises ImportError if any dependency is missing.

    Args:
        query:     The user's question.
        max_steps: Passed as a hint (LangGraph manages its own step loop).

    Returns:
        A LangChainResult with the agent's answer and timing.

    Raises:
        ImportError: If langchain dependencies are not installed.
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "langchain-core is not installed. "
            "Install with: pip install langchain-core langchain-anthropic langgraph"
        )

    agent = create_langchain_agent()
    if agent is None:
        raise ImportError(
            "create_langchain_agent() returned None -- "
            "langchain-anthropic or langgraph may be missing."
        )

    try:
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        raise ImportError(f"LangChain import error: {exc}") from exc

    t0 = time.monotonic()

    try:
        result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
    except Exception:  # noqa: BLE001
        elapsed_ms = (time.monotonic() - t0) * 1000
        return LangChainResult(
            answer=None,
            steps=0,
            total_tokens=0,
            total_cost_estimate=0.0,
            elapsed_ms=round(elapsed_ms, 1),
            budget_exhausted=True,
        )

    elapsed_ms = (time.monotonic() - t0) * 1000

    # Extract the final text answer from the message list.
    messages = result.get("messages", [])
    answer: str | None = None
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
            answer = msg.content.strip()
            break

    # Count steps as the number of AI messages (each represents a model call).
    steps = sum(1 for msg in messages if getattr(msg, "type", None) == "ai")

    # Token usage -- LangChain exposes this on the response metadata when available.
    total_tokens = 0
    for msg in messages:
        usage = getattr(msg, "usage_metadata", None)
        if usage:
            total_tokens += getattr(usage, "total_tokens", 0)

    return LangChainResult(
        answer=answer,
        steps=max(steps, 1),
        total_tokens=total_tokens,
        total_cost_estimate=0.0,
        elapsed_ms=round(elapsed_ms, 1),
        budget_exhausted=(answer is None),
    )
