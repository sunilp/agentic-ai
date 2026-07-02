"""Raw agent module (Section 0c).

Demonstrates the simplest possible agent loop: a model that can call tools,
observe results, and iterate until it produces a final text answer or exhausts
its step budget.

This is intentionally minimal -- no memory, no planning, no parallelism.
The goal is to make the core loop completely legible before adding complexity.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from src.ch00.tool_use import ToolRegistry, execute_tool_call
from src.shared.model_client import ModelClient
from src.shared.types import CompletionRequest, Message, Role, ToolResult

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a research assistant with access to tools. "
    "Use the available tools to answer the user's question accurately. "
    "When you have enough information to answer fully, respond with plain text. "
    "Do not call tools unnecessarily -- stop as soon as you can give a good answer."
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class AgentResult:
    """The outcome of a single agent run."""

    answer: str | None
    steps: int
    total_tokens: int
    total_cost_estimate: float
    elapsed_ms: float
    budget_exhausted: bool
    trace: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class Agent:
    """A minimal agent that loops between model calls and tool execution.

    The loop runs until:
    - The model returns a text answer (no tool calls), or
    - The step budget is exhausted.

    Args:
        client:        The model client to call for completions.
        registry:      The tool registry used to look up and run tools.
        max_steps:     Maximum number of model-call iterations before giving up.
        system_prompt: Override the default system prompt if needed.
    """

    def __init__(
        self,
        client: ModelClient,
        registry: ToolRegistry,
        max_steps: int = 5,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self.client = client
        self.registry = registry
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    async def run(self, user_query: str) -> AgentResult:
        """Run the agent loop for a single user query.

        Args:
            user_query: The question or task from the user.

        Returns:
            An AgentResult with the answer, step count, token usage, and trace.
        """
        start_time = time.monotonic()

        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=self.system_prompt),
            Message(role=Role.USER, content=user_query),
        ]
        tool_schemas = self.registry.get_schemas()
        trace: list[dict] = []
        total_tokens = 0
        steps = 0

        for step in range(self.max_steps):
            steps = step + 1
            request = CompletionRequest(messages=messages, tools=tool_schemas)
            response = await self.client.complete(request)

            if response.usage:
                total_tokens += response.usage.total_tokens

            # Model wants to call one or more tools. The API allows multiple
            # tool_use blocks per assistant turn (parallel tool calls); every
            # one of them needs to be executed, and every result needs to
            # come back in a single following message.
            if response.tool_calls:
                results: list[ToolResult] = []
                for tc in response.tool_calls:
                    tool_result = execute_tool_call(self.registry, tc.name, tc.arguments)
                    results.append(ToolResult(tool_call_id=tc.id, name=tc.name, content=tool_result))

                    # One trace entry per tool call, sharing this turn's step
                    # number -- keeps the single-call trace shape (and the
                    # chapter's printed example) unchanged when a turn makes
                    # only one call, and makes parallel calls visible as
                    # sibling entries under the same step otherwise.
                    trace.append(
                        {
                            "type": "tool_call",
                            "step": steps,
                            "tool": tc.name,
                            "arguments": tc.arguments,
                            "result": tool_result,
                        }
                    )

                # Append the assistant's tool-call turn -- with the actual
                # ToolCall objects, not a text stand-in -- and every result
                # from this turn in a single following message.
                messages.append(
                    Message(
                        role=Role.ASSISTANT,
                        content="",
                        tool_calls=list(response.tool_calls),
                    )
                )
                messages.append(
                    Message(
                        role=Role.TOOL,
                        content="",
                        tool_results=results,
                    )
                )
                continue

            # Model returned a text answer -- we are done.
            if response.content:
                trace.append(
                    {
                        "type": "response",
                        "step": steps,
                        "content": response.content,
                    }
                )
                elapsed_ms = (time.monotonic() - start_time) * 1000
                return AgentResult(
                    answer=response.content,
                    steps=steps,
                    total_tokens=total_tokens,
                    total_cost_estimate=0.0,
                    elapsed_ms=elapsed_ms,
                    budget_exhausted=False,
                    trace=trace,
                )

        # Step budget exhausted without a final text answer.
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return AgentResult(
            answer=None,
            steps=steps,
            total_tokens=total_tokens,
            total_cost_estimate=0.0,
            elapsed_ms=elapsed_ms,
            budget_exhausted=True,
            trace=trace,
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import os
    import sys

    from src.ch00.tool_use import ToolRegistry, create_default_registry
    from src.shared.model_client import MockClient, create_client
    from src.shared.types import CompletionResponse, TokenUsage, ToolCall

    # Real API calls use this model. Key-free by default: only reached when
    # ANTHROPIC_API_KEY is set. See src/ch00/llm_basics.py and
    # src/ch00/langchain_agent.py for the same model choice elsewhere in the
    # companion code.
    LIVE_MODEL_NAME = "claude-haiku-4-5-20251001"

    def _make_tool_response(name: str, args: dict) -> CompletionResponse:
        return CompletionResponse(
            content=None,
            tool_calls=[ToolCall(id="demo_tc", name=name, arguments=args)],
            model="mock",
            usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
        )

    def _make_text_response(text: str) -> CompletionResponse:
        return CompletionResponse(
            content=text,
            model="mock",
            usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
        )

    def _demo_examples() -> list[tuple[str, MockClient]]:
        """The canned (query, MockClient) pairs used by both the demo suite

        and, key-free, an argv question that matches the demo suite exactly.
        Called fresh each time so MockClient's internal call counter always
        starts at zero.
        """
        return [
            # 1. Direct text answer -- no tools needed.
            (
                "What is the capital of France?",
                MockClient(responses=[_make_text_response("The capital of France is Paris.")]),
            ),
            # 2. Tool call then answer.
            (
                "What is 12 multiplied by 13?",
                MockClient(
                    responses=[
                        _make_tool_response(
                            "calculator", {"operation": "multiply", "a": 12, "b": 13}
                        ),
                        _make_text_response("12 * 13 = 156.0"),
                    ]
                ),
            ),
            # 3. Two-step arithmetic -- the chapter's worked example
            # ("What is 15 * 7 + 3?"): multiply, then add, then answer.
            # 55 + 55 + 85 = 195 total tokens, matching the chapter's trace.
            (
                "What is 15 * 7 + 3?",
                MockClient(
                    responses=[
                        _make_tool_response(
                            "calculator", {"operation": "multiply", "a": 15, "b": 7}
                        ),
                        _make_tool_response("calculator", {"operation": "add", "a": 105, "b": 3}),
                        _make_text_response("15 * 7 + 3 = 108.0"),
                    ]
                ),
            ),
            # 4. Budget exhaustion (only tool calls, no final answer).
            (
                "Search for everything ever written about AI.",
                MockClient(
                    responses=[
                        _make_tool_response("search", {"query": "AI history"}),
                        _make_tool_response("search", {"query": "AI future"}),
                        _make_tool_response("search", {"query": "AI ethics"}),
                    ]
                ),
            ),
        ]

    def _print_result(query: str, result: AgentResult) -> None:
        print(f"Query:           {query}")
        print(f"Answer:          {result.answer!r}")
        print(f"Steps:           {result.steps}")
        print(f"Total tokens:    {result.total_tokens}")
        print(f"Budget exhausted:{result.budget_exhausted}")
        print(f"Trace ({len(result.trace)} entries):")
        for entry in result.trace:
            if entry["type"] == "tool_call":
                print(
                    f"  [{entry['step']}] tool_call  {entry['tool']}({entry['arguments']}) -> {entry['result'][:60]!r}"
                )
            else:
                print(f"  [{entry['step']}] response   {entry['content'][:60]!r}")
        print()

    async def _demo() -> None:
        registry = create_default_registry()
        for query, client in _demo_examples():
            # max_steps=3 matches every example's canned response count
            # exactly, so the budget-exhaustion example (search x3) still
            # exhausts instead of falling through to MockClient's default
            # "Mock response" text on a 4th call.
            agent = Agent(client=client, registry=registry, max_steps=3)
            result = await agent.run(query)
            _print_result(query, result)

    async def _run_query(query: str, registry: ToolRegistry) -> None:
        """Run a single question through the agent.

        Uses the real Anthropic API when ANTHROPIC_API_KEY is set (as the
        chapter's run instructions do); otherwise stays key-free: replays
        the matching canned example if the question matches the demo suite
        exactly, or falls back to a plain MockClient (a one-step "Mock
        response" answer) so the script always exits 0 without a key.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            client = create_client(provider="anthropic", api_key=api_key, model_name=LIVE_MODEL_NAME)
        else:
            client = next(
                (demo_client for demo_query, demo_client in _demo_examples() if demo_query == query),
                MockClient(),
            )
        agent = Agent(client=client, registry=registry, max_steps=5)
        result = await agent.run(query)
        _print_result(query, result)

    if len(sys.argv) > 1:
        asyncio.run(_run_query(sys.argv[1], create_default_registry()))
    else:
        asyncio.run(_demo())
