"""Executable self-check for the Section 0c companion-code fixes.

There is no test framework in this repo (see src/shared/, src/ch00/) --
this script is the verification path instead. Run it directly:

    python -m src.ch00.selfcheck

Each check prints PASS or FAIL. The script exits 0 if every check passes,
1 if any fails, so it also works as a CI-less gate.

Checks (map to the fixes in raw_agent.py / tool_use.py / model_client.py / types.py):
    (a) An assistant tool-call turn serializes to a `tool_use` content block
        whose id matches the following `tool_result` block's tool_use_id.
    (b) A two-tool-call mock turn executes both tools and returns both
        results in a single following message, not two separate ones.
    (c) A CompletionRequest with temperature=None omits "temperature" from
        the request payload; an explicit value is still sent.
    (d) Calling a tool with requires_approval=True returns a structured
        approval_required error and never runs the tool body.
    (e) `python -m src.ch00.raw_agent "<question>"` runs key-free and exits 0.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import subprocess
import sys
from pathlib import Path

from src.ch00.raw_agent import Agent
from src.ch00.tool_use import create_default_registry, execute_tool_call
from src.shared.model_client import AnthropicClient, ModelClient, _to_anthropic_message
from src.shared.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Role,
    TokenUsage,
    ToolCall,
    ToolResult,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _CapturingClient(ModelClient):
    """A ModelClient that records every request instead of calling an API.

    Lets a check inspect exactly what Agent.run() sends on the *next* call,
    which is the only way to verify how a turn got serialized into messages.
    """

    def __init__(self, responses: list[CompletionResponse]) -> None:
        super().__init__("capturing")
        self._responses = responses
        self.requests: list[CompletionRequest] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        return self._responses[len(self.requests) - 1]


class _FakeResponse:
    """Stands in for an httpx.Response -- just enough surface to satisfy

    AnthropicClient.complete() without a real HTTP round trip.
    """

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"content": [{"type": "text", "text": "ok"}], "usage": {}, "model": "fake"}


class _FakeAnthropicHTTP:
    """Stands in for httpx.AsyncClient, capturing the JSON payload posted."""

    def __init__(self) -> None:
        self.last_payload: dict | None = None

    async def post(self, url: str, json: dict) -> _FakeResponse:
        self.last_payload = json
        return _FakeResponse()


def check_tool_use_serialization() -> None:
    """(a) tool_use block id matches the following tool_result's tool_use_id."""
    tc = ToolCall(id="tc_1", name="calculator", arguments={"operation": "add", "a": 1, "b": 2})
    assistant_msg = Message(role=Role.ASSISTANT, content="", tool_calls=[tc])
    tool_msg = Message(
        role=Role.TOOL,
        content="",
        tool_results=[ToolResult(tool_call_id=tc.id, name=tc.name, content="3.0")],
    )

    assistant_dict = _to_anthropic_message(assistant_msg)
    tool_dict = _to_anthropic_message(tool_msg)

    assert assistant_dict["role"] == "assistant", assistant_dict
    assert isinstance(assistant_dict["content"], list), assistant_dict
    block = assistant_dict["content"][0]
    assert block == {
        "type": "tool_use",
        "id": "tc_1",
        "name": "calculator",
        "input": tc.arguments,
    }, block

    assert tool_dict["role"] == "user", tool_dict
    result_block = tool_dict["content"][0]
    assert result_block["type"] == "tool_result", result_block
    assert result_block["tool_use_id"] == block["id"] == "tc_1", result_block


async def check_parallel_tool_calls() -> None:
    """(b) Two tool calls in one turn both execute; both results travel in

    a single following message.
    """
    registry = create_default_registry()
    tool_turn = CompletionResponse(
        content=None,
        tool_calls=[
            ToolCall(id="p1", name="calculator", arguments={"operation": "add", "a": 1, "b": 2}),
            ToolCall(
                id="p2", name="calculator", arguments={"operation": "multiply", "a": 3, "b": 4}
            ),
        ],
        model="mock",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    final_turn = CompletionResponse(content="done", model="mock")
    client = _CapturingClient([tool_turn, final_turn])

    agent = Agent(client=client, registry=registry, max_steps=3)
    result = await agent.run("add 1+2 and multiply 3*4")

    tool_call_entries = [e for e in result.trace if e["type"] == "tool_call"]
    assert len(tool_call_entries) == 2, f"expected 2 tool_call trace entries, got {tool_call_entries}"
    assert tool_call_entries[0]["result"] == "3.0", tool_call_entries[0]
    assert tool_call_entries[1]["result"] == "12.0", tool_call_entries[1]

    # requests[1] is what the agent sent on its second call -- i.e. right
    # after executing both tools from the first turn.
    second_request = client.requests[1]
    assistant_messages = [m for m in second_request.messages if m.tool_calls]
    tool_result_messages = [m for m in second_request.messages if m.tool_results]
    assert len(assistant_messages) == 1, "expected exactly one assistant message with tool_calls"
    assert len(tool_result_messages) == 1, "expected exactly one message with tool_results"

    sent_calls = assistant_messages[0].tool_calls or []
    sent_results = tool_result_messages[0].tool_results or []
    assert len(sent_calls) == 2, sent_calls
    assert len(sent_results) == 2, sent_results
    ids = {tr.tool_call_id for tr in sent_results}
    assert ids == {"p1", "p2"}, ids


async def check_temperature_omitted() -> None:
    """(c) temperature=None omits the key; an explicit value is still sent."""
    fake_http = _FakeAnthropicHTTP()
    client = AnthropicClient(api_key="fake-key", model_name="fake-model")
    client._client = fake_http  # type: ignore[assignment]

    await client.complete(
        CompletionRequest(messages=[Message(role=Role.USER, content="hi")], temperature=None)
    )
    assert fake_http.last_payload is not None
    assert "temperature" not in fake_http.last_payload, fake_http.last_payload

    await client.complete(
        CompletionRequest(messages=[Message(role=Role.USER, content="hi")], temperature=0.7)
    )
    assert fake_http.last_payload["temperature"] == 0.7, fake_http.last_payload


def check_gated_tool() -> None:
    """(d) A requires_approval tool refuses before dispatch."""
    registry = create_default_registry()
    result = execute_tool_call(registry, "delete_record", {"record_id": "rec_1"})
    assert result.startswith("approval_required:"), result
    assert "delete_record" in result, result
    assert "Deleted record" not in result, "tool body ran despite the approval gate"


def check_argv_run() -> None:
    """(e) `python -m src.ch00.raw_agent "<question>"` exits 0, key-free."""
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)  # force the key-free MockClient path
    proc = subprocess.run(
        [sys.executable, "-m", "src.ch00.raw_agent", "What is 15 * 7 + 3?"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert proc.returncode == 0, f"exit code {proc.returncode}\nstderr:\n{proc.stderr}"
    assert "15 * 7 + 3 = 108.0" in proc.stdout, proc.stdout


CHECKS = [
    ("tool_use_serialization", check_tool_use_serialization),
    ("parallel_tool_calls", check_parallel_tool_calls),
    ("temperature_omitted", check_temperature_omitted),
    ("gated_tool", check_gated_tool),
    ("argv_run", check_argv_run),
]


async def _run_all() -> bool:
    all_passed = True
    for name, check in CHECKS:
        try:
            if inspect.iscoroutinefunction(check):
                await check()
            else:
                check()
        except AssertionError as exc:
            print(f"FAIL: {name}: {exc}")
            all_passed = False
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {name}: unexpected {type(exc).__name__}: {exc}")
            all_passed = False
        else:
            print(f"PASS: {name}")
    return all_passed


if __name__ == "__main__":
    passed = asyncio.run(_run_all())
    sys.exit(0 if passed else 1)
