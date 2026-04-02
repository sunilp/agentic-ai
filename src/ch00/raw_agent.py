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
from src.shared.types import CompletionRequest, Message, Role

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

            # Model wants to call a tool.
            if response.tool_calls:
                tc = response.tool_calls[0]
                tool_result = execute_tool_call(self.registry, tc.name, tc.arguments)

                trace.append(
                    {
                        "type": "tool_call",
                        "step": steps,
                        "tool": tc.name,
                        "arguments": tc.arguments,
                        "result": tool_result,
                    }
                )

                # Append the assistant's tool-call turn and the tool result.
                messages.append(
                    Message(
                        role=Role.ASSISTANT,
                        content=f"[tool_call: {tc.name}({tc.arguments})]",
                    )
                )
                messages.append(
                    Message(
                        role=Role.TOOL,
                        content=tool_result,
                        name=tc.name,
                        tool_call_id=tc.id,
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
    from src.ch00.tool_use import create_default_registry
    from src.shared.model_client import MockClient
    from src.shared.types import CompletionResponse, TokenUsage, ToolCall

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

    async def _demo() -> None:
        registry = create_default_registry()

        examples = [
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
            # 3. Budget exhaustion (only tool calls, no final answer).
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

        for query, client in examples:
            agent = Agent(client=client, registry=registry, max_steps=3)
            result = await agent.run(query)
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

    asyncio.run(_demo())
