"""Raw agent wrapper for the framework comparison (Section 0d).

Thin shim that imports Agent from src/ch00/raw_agent and exposes a
uniform run_agent() interface for use by compare.py.

No additional dependencies required -- works with the base install.
"""

from __future__ import annotations

from typing import Any

from src.ch00.raw_agent import Agent, AgentResult
from src.ch00.tool_use import create_default_registry
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse

RAW_AVAILABLE = True


async def run_raw_agent(
    query: str,
    mock_responses: list[CompletionResponse],
    max_steps: int = 5,
) -> AgentResult:
    """Run the raw agent against *query* using pre-scripted mock responses.

    Args:
        query:          The user's question.
        mock_responses: Scripted responses for the MockClient.
        max_steps:      Step budget.

    Returns:
        An AgentResult from src/ch00/raw_agent.
    """
    registry = create_default_registry()
    client = MockClient(responses=mock_responses)
    agent = Agent(client=client, registry=registry, max_steps=max_steps)
    return await agent.run(query)
