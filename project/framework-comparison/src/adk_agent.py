"""ADK agent wrapper for the framework comparison (Section 0d).

Thin shim that imports create_adk_agent from src/ch00/adk_agent and
exposes a uniform run_agent() interface for use by compare.py.

Requires: pip install google-adk
If google-adk is not installed, ADK_AVAILABLE is False and run_adk_agent()
raises ImportError. The compare script handles this gracefully by skipping
the ADK column.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from src.ch00.adk_agent import ADK_AVAILABLE, create_adk_agent


@dataclass
class ADKResult:
    """Minimal result wrapper matching the structure expected by compare.py."""

    answer: str | None
    steps: int
    total_tokens: int
    total_cost_estimate: float
    elapsed_ms: float
    budget_exhausted: bool


async def run_adk_agent(query: str, max_steps: int = 5) -> ADKResult:
    """Run the ADK agent against *query*.

    Requires google-adk to be installed. Raises ImportError if not available.

    Args:
        query:     The user's question.
        max_steps: Passed as a hint (ADK manages its own step loop).

    Returns:
        An ADKResult with the agent's answer and timing.

    Raises:
        ImportError: If google-adk is not installed.
    """
    if not ADK_AVAILABLE:
        raise ImportError("google-adk is not installed. Install with: pip install google-adk")

    try:
        from google.adk.runners import InMemoryRunner
        from google.genai import types as genai_types
    except ImportError as exc:
        raise ImportError(f"ADK import error: {exc}") from exc

    agent = create_adk_agent()
    if agent is None:
        raise ImportError("create_adk_agent() returned None -- ADK not properly installed")

    t0 = time.monotonic()
    runner = InMemoryRunner(agent=agent)
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id="eval")

    content = genai_types.Content(role="user", parts=[genai_types.Part(text=query)])

    answer: str | None = None
    steps = 0
    async for event in runner.run_async(
        user_id="eval",
        session_id=session.id,
        new_message=content,
    ):
        steps += 1
        if event.is_final_response() and event.content and event.content.parts:
            answer = event.content.parts[0].text

    elapsed_ms = (time.monotonic() - t0) * 1000

    return ADKResult(
        answer=answer,
        steps=steps,
        total_tokens=0,  # ADK does not expose raw token counts in this runner.
        total_cost_estimate=0.0,
        elapsed_ms=round(elapsed_ms, 1),
        budget_exhausted=(answer is None),
    )
