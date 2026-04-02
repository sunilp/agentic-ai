"""Expanded research agent (Section 0c).

Builds on src/ch00/raw_agent.py to add:
- Configurable step budget
- Per-step logging with token counts and cost estimates
- Trace export to JSON
- Graceful error recovery (tool errors do not terminate the run)

The agent is compatible with any ModelClient and any ToolRegistry, making
it easy to swap in real API clients or custom tool sets.

Run with:
    python project/research-agent/src/agent.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path as _Path

# Path bootstrap for direct script execution.
_REPO_ROOT = _Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ch00.llm_basics import estimate_cost
from src.ch00.tool_use import ToolRegistry, execute_tool_call
from src.shared.model_client import ModelClient
from src.shared.types import CompletionRequest, Message, Role

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("research_agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a research assistant with access to search, calculator, URL reader, "
    "and summarizer tools. "
    "Use the available tools to answer the user's question accurately. "
    "When you have enough information to answer fully, respond with plain text. "
    "Do not call tools unnecessarily -- stop as soon as you have a good answer."
)


# ---------------------------------------------------------------------------
# Trace types
# ---------------------------------------------------------------------------


@dataclass
class StepTrace:
    """Record of one step in the agent loop."""

    step: int
    type: str  # "tool_call" | "response" | "error"
    tool: str | None = None
    arguments: dict | None = None
    result: str | None = None
    content: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    elapsed_ms: float = 0.0
    error: str | None = None


@dataclass
class AgentTrace:
    """Full trace for one agent run."""

    query: str
    model: str
    max_steps: int
    total_steps: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    total_elapsed_ms: float
    budget_exhausted: bool
    answer: str | None
    steps: list[StepTrace] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class AgentResult:
    """The outcome of a single agent run (thin wrapper for compatibility with eval harness)."""

    answer: str | None
    steps: int
    total_tokens: int
    total_cost_estimate: float
    elapsed_ms: float
    budget_exhausted: bool
    trace: AgentTrace


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ResearchAgent:
    """Agent loop with step-level instrumentation, trace export, and error recovery.

    Extends the minimal agent from src/ch00/raw_agent.py with:
    - Per-step token and cost logging.
    - A full AgentTrace that can be serialised to JSON.
    - Error recovery: tool errors are captured and returned as tool results
      rather than raising exceptions, allowing the loop to continue.

    Args:
        client:        Any ModelClient instance (real or mock).
        registry:      The tool registry for this agent.
        model_name:    Model identifier used for cost estimation.
        max_steps:     Maximum model-call iterations.
        system_prompt: Override the default system prompt if needed.
        verbose:       If True, log each step to stdout.
    """

    def __init__(
        self,
        client: ModelClient,
        registry: ToolRegistry,
        model_name: str = "claude-haiku-4-5-20251001",
        max_steps: int = 8,
        system_prompt: str = SYSTEM_PROMPT,
        verbose: bool = True,
    ) -> None:
        self.client = client
        self.registry = registry
        self.model_name = model_name
        self.max_steps = max_steps
        self.system_prompt = system_prompt
        self.verbose = verbose

    async def run(self, user_query: str) -> AgentResult:
        """Run the agent loop for a single user query.

        Args:
            user_query: The question or task from the user.

        Returns:
            An AgentResult with the answer, trace, and accumulated costs.
        """
        run_start = time.monotonic()

        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=self.system_prompt),
            Message(role=Role.USER, content=user_query),
        ]
        tool_schemas = self.registry.get_schemas()

        step_traces: list[StepTrace] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        steps_taken = 0

        for step_num in range(1, self.max_steps + 1):
            steps_taken = step_num
            step_start = time.monotonic()

            # ---- Model call ----
            try:
                request = CompletionRequest(messages=messages, tools=tool_schemas)
                response = await self.client.complete(request)
            except Exception as exc:  # noqa: BLE001
                elapsed = (time.monotonic() - step_start) * 1000
                err_trace = StepTrace(
                    step=step_num,
                    type="error",
                    error=str(exc),
                    elapsed_ms=round(elapsed, 1),
                )
                step_traces.append(err_trace)
                if self.verbose:
                    log.error("[step %d] Model call error: %s", step_num, exc)
                break

            elapsed_step = (time.monotonic() - step_start) * 1000

            # ---- Token accounting ----
            prompt_tokens = 0
            completion_tokens = 0
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens

            step_cost = estimate_cost(prompt_tokens, completion_tokens, self.model_name)
            total_cost += step_cost

            # ---- Tool call ----
            if response.tool_calls:
                tc = response.tool_calls[0]

                if self.verbose:
                    log.info(
                        "[step %d] tool_call  %s(%s)  tokens=%d  cost=$%.6f",
                        step_num,
                        tc.name,
                        tc.arguments,
                        prompt_tokens + completion_tokens,
                        step_cost,
                    )

                tool_result = execute_tool_call(self.registry, tc.name, tc.arguments)

                if self.verbose:
                    preview = tool_result[:80] + "..." if len(tool_result) > 80 else tool_result
                    log.info("[step %d] tool_result  %s", step_num, preview)

                step_traces.append(
                    StepTrace(
                        step=step_num,
                        type="tool_call",
                        tool=tc.name,
                        arguments=tc.arguments,
                        result=tool_result,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=step_cost,
                        elapsed_ms=round(elapsed_step, 1),
                    )
                )

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

            # ---- Text answer ----
            if response.content:
                if self.verbose:
                    log.info(
                        "[step %d] response  tokens=%d  cost=$%.6f  %s",
                        step_num,
                        prompt_tokens + completion_tokens,
                        step_cost,
                        response.content[:60],
                    )

                step_traces.append(
                    StepTrace(
                        step=step_num,
                        type="response",
                        content=response.content,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost_usd=step_cost,
                        elapsed_ms=round(elapsed_step, 1),
                    )
                )

                total_elapsed = (time.monotonic() - run_start) * 1000
                agent_trace = AgentTrace(
                    query=user_query,
                    model=self.model_name,
                    max_steps=self.max_steps,
                    total_steps=steps_taken,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_cost_usd=total_cost,
                    total_elapsed_ms=round(total_elapsed, 1),
                    budget_exhausted=False,
                    answer=response.content,
                    steps=step_traces,
                )
                return AgentResult(
                    answer=response.content,
                    steps=steps_taken,
                    total_tokens=total_prompt_tokens + total_completion_tokens,
                    total_cost_estimate=total_cost,
                    elapsed_ms=round(total_elapsed, 1),
                    budget_exhausted=False,
                    trace=agent_trace,
                )

        # Budget exhausted.
        total_elapsed = (time.monotonic() - run_start) * 1000
        if self.verbose:
            log.warning("Budget exhausted after %d steps.", steps_taken)

        agent_trace = AgentTrace(
            query=user_query,
            model=self.model_name,
            max_steps=self.max_steps,
            total_steps=steps_taken,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_cost_usd=total_cost,
            total_elapsed_ms=round(total_elapsed, 1),
            budget_exhausted=True,
            answer=None,
            steps=step_traces,
        )
        return AgentResult(
            answer=None,
            steps=steps_taken,
            total_tokens=total_prompt_tokens + total_completion_tokens,
            total_cost_estimate=total_cost,
            elapsed_ms=round(total_elapsed, 1),
            budget_exhausted=True,
            trace=agent_trace,
        )


def export_trace(trace: AgentTrace, output_path: str | Path) -> None:
    """Serialise an AgentTrace to a JSON file.

    Args:
        trace:       The trace to export.
        output_path: File path to write to.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(trace), fh, indent=2)
    log.info("Trace exported to %s", output_path)


def print_trace(trace: AgentTrace) -> None:
    """Print an annotated trace to stdout."""
    print(f"\nTrace for: {trace.query!r}")
    print(f"Model: {trace.model}  max_steps: {trace.max_steps}")
    print("-" * 60)
    for step in trace.steps:
        if step.type == "tool_call":
            print(f"[{step.step}] tool_call  {step.tool}({step.arguments})")
            result_preview = (step.result or "")[:80]
            if len(step.result or "") > 80:
                result_preview += "..."
            print(f"      -> {result_preview}")
            print(
                f"      tokens={step.prompt_tokens + step.completion_tokens}  "
                f"cost=${step.cost_usd:.6f}  {step.elapsed_ms:.1f}ms"
            )
        elif step.type == "response":
            print(f"[{step.step}] response  {(step.content or '')[:60]!r}")
            print(
                f"      tokens={step.prompt_tokens + step.completion_tokens}  "
                f"cost=${step.cost_usd:.6f}  {step.elapsed_ms:.1f}ms"
            )
        elif step.type == "error":
            print(f"[{step.step}] ERROR     {step.error}")
    print("-" * 60)
    status = "BUDGET_EXHAUSTED" if trace.budget_exhausted else "COMPLETED"
    print(
        f"Summary: {trace.total_steps} steps  "
        f"{trace.total_prompt_tokens + trace.total_completion_tokens} tokens  "
        f"${trace.total_cost_usd:.6f}  {trace.total_elapsed_ms:.1f}ms  [{status}]"
    )
    if trace.answer:
        print(f"Answer:  {trace.answer}")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    from src.shared.model_client import MockClient
    from src.shared.types import CompletionResponse, TokenUsage, ToolCall

    # Import tools from the same directory.
    _tools_dir = str(Path(__file__).resolve().parent)
    if _tools_dir not in sys.path:
        sys.path.insert(0, _tools_dir)
    from tools import create_research_registry  # noqa: E402

    def _tool_resp(name: str, args: dict[str, Any]) -> CompletionResponse:
        return CompletionResponse(
            content=None,
            tool_calls=[ToolCall(id="demo", name=name, arguments=args)],
            model="mock",
            usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
        )

    def _text_resp(text: str) -> CompletionResponse:
        return CompletionResponse(
            content=text,
            model="mock",
            usage=TokenUsage(prompt_tokens=60, completion_tokens=20, total_tokens=80),
        )

    async def _demo() -> None:
        registry = create_research_registry()
        scenarios = [
            (
                "What is 15 * 7?",
                [
                    _tool_resp("calculator", {"operation": "multiply", "a": 15, "b": 7}),
                    _text_resp("15 * 7 = 105"),
                ],
            ),
            (
                "Search for agentic AI and summarize what you find.",
                [
                    _tool_resp("search", {"query": "agentic AI", "max_results": 2}),
                    _tool_resp(
                        "read_url",
                        {"url": "https://en.wikipedia.org/wiki/Agentic_AI", "max_chars": 500},
                    ),
                    _text_resp(
                        "Agentic AI refers to AI systems capable of autonomous multi-step reasoning and tool use."
                    ),
                ],
            ),
        ]

        for query, mock_responses in scenarios:
            client = MockClient(responses=mock_responses)
            agent = ResearchAgent(
                client=client,
                registry=registry,
                model_name="claude-haiku-4-5-20251001",
                max_steps=5,
                verbose=False,
            )
            result = await agent.run(query)
            print_trace(result.trace)

    asyncio.run(_demo())
