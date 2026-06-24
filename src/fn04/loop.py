"""The loop, two ways.

The difference between ``run_prompted`` and ``run_enforced`` is the entire
content of the Field Note. Same agent, same tools, same goal. One can delete
the database when the model says it is done. The other cannot, by
construction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class ToolCall:
    """A request from the agent to run a named tool with arguments."""

    name: str
    args: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Done:
    """The agent's own claim that the task is complete. Just a claim."""


Step = ToolCall | Done


@dataclass
class Tool:
    """A callable the agent can invoke. ``destructive`` tools touch state
    that cannot be undone, and the enforced loop refuses to run them without
    an out-of-band approval the agent does not hold."""

    name: str
    fn: Callable[..., object]
    destructive: bool = False


@dataclass
class Database:
    """Stand-in for the production system the loop can reach."""

    rows: list = field(default_factory=lambda: ["row-1", "row-2", "row-3"])
    deleted: bool = False

    def delete_all(self) -> None:
        self.rows = []
        self.deleted = True


class StopReason(Enum):
    AGENT_DONE = "agent_done"
    MAX_ITERATIONS = "max_iterations"
    NO_PROGRESS = "no_progress"


@dataclass
class LoopResult:
    stop_reason: StopReason
    iterations: int
    blocked_calls: list[ToolCall]
    executed_calls: list[ToolCall]


def _call_key(call: ToolCall) -> str:
    """Stable hash of a tool call and its arguments, for no-progress
    detection. Two calls with the same name and arguments hash the same."""

    payload = repr((call.name, sorted(call.args.items())))
    return hashlib.sha256(payload.encode()).hexdigest()


class ApprovalGate:
    """Holds approvals granted out of band, by a principal that is not the
    agent. The agent cannot grant its own approval; it can only request a
    tool, and a destructive request is refused unless a matching approval was
    already recorded here."""

    def __init__(self) -> None:
        self._approved: set[str] = set()

    def grant(self, call: ToolCall) -> None:
        self._approved.add(_call_key(call))

    def authorize(self, call: ToolCall) -> bool:
        return _call_key(call) in self._approved


def run_prompted(
    agent: Iterable[Step],
    tools: dict[str, Tool],
    db: Database,
    *,
    max_iterations: int = 1000,
) -> LoopResult:
    """Trust the agent. The stop condition is the agent's own ``Done``, and
    every tool, destructive or not, runs the moment it is requested."""

    steps: Iterator[Step] = iter(agent)
    executed: list[ToolCall] = []
    iterations = 0

    while iterations < max_iterations:
        step = next(steps, Done())
        if isinstance(step, Done):
            return LoopResult(StopReason.AGENT_DONE, iterations, [], executed)

        iterations += 1
        tools[step.name].fn(**step.args)
        executed.append(step)

    return LoopResult(StopReason.MAX_ITERATIONS, iterations, [], executed)


def run_enforced(
    agent: Iterable[Step],
    tools: dict[str, Tool],
    db: Database,
    *,
    max_iterations: int = 10,
    approval: ApprovalGate | None = None,
) -> LoopResult:
    """Do not trust the agent's claim of completion. Three external fences
    bound the loop: a hard iteration cap, a no-progress detector that halts
    when the same call repeats, and a capability gate that refuses a
    destructive tool unless it was approved out of band."""

    approval = approval or ApprovalGate()
    steps: Iterator[Step] = iter(agent)
    executed: list[ToolCall] = []
    blocked: list[ToolCall] = []
    seen: set[str] = set()
    iterations = 0

    while True:
        step = next(steps, Done())
        if isinstance(step, Done):
            return LoopResult(StopReason.AGENT_DONE, iterations, blocked, executed)

        iterations += 1

        key = _call_key(step)
        if key in seen:
            return LoopResult(StopReason.NO_PROGRESS, iterations, blocked, executed)
        seen.add(key)

        tool = tools[step.name]
        if tool.destructive and not approval.authorize(step):
            blocked.append(step)
        else:
            tool.fn(**step.args)
            executed.append(step)

        if iterations >= max_iterations:
            return LoopResult(StopReason.MAX_ITERATIONS, iterations, blocked, executed)
