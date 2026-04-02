"""Single-turn tool-using assistant (Section 0b).

Accepts a query, simulates model tool selection, executes the selected tool,
and returns the result. Logs tool selections and validation errors to stdout.

This is a single-turn assistant: one query -> one (optional) tool call -> one answer.
It does not implement a full agent loop. For the multi-turn loop see
project/research-agent/src/agent.py.

Uses MockClient for all demos so no API key is required.

Run with:
    python project/tool-using-assistant/src/assistant.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap -- allows running this file directly from the repo root or
# from within the project directory.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ch00.tool_use import execute_tool_call
from src.shared.model_client import MockClient, ModelClient
from src.shared.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Role,
    TokenUsage,
    ToolCall,
)

# Import tools from the same directory.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tools import create_assistant_registry  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tool_using_assistant")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class AssistantResult:
    """The outcome of a single assistant interaction."""

    query: str
    tool_selected: str | None
    tool_arguments: dict | None
    tool_result: str | None
    final_answer: str
    total_tokens: int
    elapsed_ms: float
    error: str | None = None


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------


class ToolUsingAssistant:
    """Single-turn assistant that selects and executes a tool then answers.

    Args:
        client:   The model client to use for completions.
        verbose:  If True, log each tool selection and result to stdout.
    """

    def __init__(self, client: ModelClient, verbose: bool = True) -> None:
        self.client = client
        self.registry = create_assistant_registry()
        self.verbose = verbose
        self._tool_schemas = self.registry.get_schemas()

    async def answer(self, query: str) -> AssistantResult:
        """Process a single query: optionally call a tool, then return an answer.

        Args:
            query: The user's question or request.

        Returns:
            An AssistantResult with tool selection details and the final answer.
        """
        t0 = time.monotonic()
        total_tokens = 0

        request = CompletionRequest(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content=(
                        "You are a helpful assistant with access to tools. "
                        "Use the most appropriate tool to answer the user's question. "
                        "If no tool is needed, answer directly."
                    ),
                ),
                Message(role=Role.USER, content=query),
            ],
            tools=self._tool_schemas,
        )

        try:
            response = await self.client.complete(request)
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.monotonic() - t0) * 1000
            return AssistantResult(
                query=query,
                tool_selected=None,
                tool_arguments=None,
                tool_result=None,
                final_answer="",
                total_tokens=0,
                elapsed_ms=elapsed_ms,
                error=f"Model call failed: {exc}",
            )

        if response.usage:
            total_tokens += response.usage.total_tokens

        # No tool call -- direct answer.
        if not response.tool_calls:
            elapsed_ms = (time.monotonic() - t0) * 1000
            if self.verbose:
                log.info("Query answered directly (no tool call)")
            return AssistantResult(
                query=query,
                tool_selected=None,
                tool_arguments=None,
                tool_result=None,
                final_answer=response.content or "",
                total_tokens=total_tokens,
                elapsed_ms=elapsed_ms,
            )

        # Tool call -- validate, execute, then get the final answer.
        tc: ToolCall = response.tool_calls[0]
        if self.verbose:
            log.info("Tool selected: %s  arguments: %s", tc.name, json.dumps(tc.arguments))

        tool_result = execute_tool_call(self.registry, tc.name, tc.arguments)

        if self.verbose:
            result_preview = tool_result[:120] + "..." if len(tool_result) > 120 else tool_result
            log.info("Tool result: %s", result_preview)

        # Second model call: give the tool result back and get the final answer.
        followup_request = CompletionRequest(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a helpful assistant. Summarise the tool result concisely.",
                ),
                Message(role=Role.USER, content=query),
                Message(
                    role=Role.ASSISTANT,
                    content=f"[tool_call: {tc.name}({tc.arguments})]",
                ),
                Message(
                    role=Role.TOOL,
                    content=tool_result,
                    name=tc.name,
                    tool_call_id=tc.id,
                ),
            ]
        )

        try:
            followup_response = await self.client.complete(followup_request)
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.monotonic() - t0) * 1000
            return AssistantResult(
                query=query,
                tool_selected=tc.name,
                tool_arguments=tc.arguments,
                tool_result=tool_result,
                final_answer=tool_result,  # Fall back to raw tool result.
                total_tokens=total_tokens,
                elapsed_ms=elapsed_ms,
                error=f"Follow-up call failed: {exc}",
            )

        if followup_response.usage:
            total_tokens += followup_response.usage.total_tokens

        elapsed_ms = (time.monotonic() - t0) * 1000
        return AssistantResult(
            query=query,
            tool_selected=tc.name,
            tool_arguments=tc.arguments,
            tool_result=tool_result,
            final_answer=followup_response.content or tool_result,
            total_tokens=total_tokens,
            elapsed_ms=elapsed_ms,
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def _make_tool_response(tool_name: str, args: dict) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id=f"tc_{tool_name}", name=tool_name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
    )


def _make_text_response(text: str) -> CompletionResponse:
    return CompletionResponse(
        content=text,
        model="mock",
        usage=TokenUsage(prompt_tokens=60, completion_tokens=20, total_tokens=80),
    )


DEMO_SCENARIOS: list[tuple[str, list[CompletionResponse]]] = [
    (
        "What is 99 multiplied by 7?",
        [
            _make_tool_response("calculator", {"operation": "multiply", "a": 99, "b": 7}),
            _make_text_response("99 * 7 = 693"),
        ],
    ),
    (
        "How many words are in 'to be or not to be that is the question'?",
        [
            _make_tool_response(
                "word_counter",
                {"text": "to be or not to be that is the question"},
            ),
            _make_text_response("That phrase contains 10 words."),
        ],
    ),
    (
        "Search for information about transformer neural networks.",
        [
            _make_tool_response("search", {"query": "transformer neural networks", "max_results": 3}),
            _make_text_response(
                "Found 3 results about transformer neural networks, including a Wikipedia overview "
                "and research resources."
            ),
        ],
    ),
    (
        "Read the first 3 lines of the tool-using-assistant README.",
        [
            _make_tool_response(
                "file_reader",
                {"path": "project/tool-using-assistant/README.md", "max_lines": 3},
            ),
            _make_text_response("The README describes the tool-using-assistant project."),
        ],
    ),
    (
        "What is the capital of France?",
        [_make_text_response("The capital of France is Paris.")],
    ),
]


if __name__ == "__main__":

    async def _demo() -> None:
        print("=" * 65)
        print("Tool-Using Assistant Demo")
        print("=" * 65)
        print()

        for query, mock_responses in DEMO_SCENARIOS:
            client = MockClient(responses=mock_responses)
            assistant = ToolUsingAssistant(client=client, verbose=True)
            result = await assistant.answer(query)

            print(f"Query:    {result.query}")
            if result.tool_selected:
                print(f"Tool:     {result.tool_selected}({result.tool_arguments})")
                preview = (result.tool_result or "")[:80]
                print(f"Result:   {preview}{'...' if len(result.tool_result or '') > 80 else ''}")
            else:
                print("Tool:     (none -- direct answer)")
            print(f"Answer:   {result.final_answer}")
            print(f"Tokens:   {result.total_tokens}  Latency: {result.elapsed_ms:.1f}ms")
            if result.error:
                print(f"Error:    {result.error}")
            print()

    asyncio.run(_demo())
