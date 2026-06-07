"""The two systems under test: a workflow router and a 3-agent hierarchy.

Both answer short-horizon customer-support queries in one of four categories
(billing, technical, account, escalation), backed by the same deterministic mock
tools and the same underlying model. The contrast the experiment measures:

- Router: a rule-based category switch (no model call) hands the query to one
  category-specialized agent. One decision-maker, minimal coordination.
- Hierarchy: an LLM classifier picks the category, a worker answers, and a
  verifier checks the answer and can trigger one re-answer. More model calls,
  an extra place to misroute, an extra place to rubber-stamp.

Both reuse the provider-neutral model client and types from src/shared.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from pydantic import BaseModel, Field

from labs.lab_001.tools import ToolRegistry
from src.shared.model_client import ModelClient
from src.shared.types import (
    CompletionRequest,
    Message,
    Role,
    ToolSchema,
)

CATEGORIES = ["billing", "technical", "account", "escalation"]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "billing": [
        "invoice", "payment", "charge", "charged", "refund", "bill", "billing",
        "fee", "subscription cost", "price", "pay",
    ],
    "technical": [
        "delivery", "deliver", "ship", "shipping", "track", "tracking", "order",
        "address", "broken", "not working", "error", "bug", "fault",
    ],
    "account": [
        "account", "password", "log in", "login", "sign in", "profile", "newsletter",
        "subscribe", "unsubscribe", "email address", "username",
    ],
    "escalation": [
        "complaint", "complain", "manager", "terrible", "unacceptable", "lawyer",
        "dispute", "fraud", "scam", "angry", "escalate", "supervisor",
    ],
}

_AGENT_SYSTEM = {
    cat: (
        f"You are a customer-support agent specialising in {cat} issues. "
        "Answer the customer's question directly and concisely in 1 to 3 sentences. "
        "You may call kb_lookup to consult the knowledge base, account_lookup if the "
        "customer gives an account id, and create_ticket for issues that need a human. "
        "Base your answer on tool results when you use them. Do not invent policy."
    )
    for cat in CATEGORIES
}


class StepRecord(BaseModel):
    stage: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    tool_calls: list[str] = Field(default_factory=list)


class SystemResult(BaseModel):
    system: str
    query_id: str
    category_true: str
    category_used: str
    answer: str
    model_calls: int = 0
    tool_calls: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    steps: list[StepRecord] = Field(default_factory=list)
    flags: dict[str, Any] = Field(default_factory=dict)


def rule_classify(query: str) -> str:
    """Deterministic keyword switch. This is the router's 'switch statement'."""
    q = query.lower()
    best_cat = "account"
    best_hits = 0
    for cat in CATEGORIES:  # stable order, ties resolve to the earlier category
        hits = sum(1 for kw in _CATEGORY_KEYWORDS[cat] if kw in q)
        if hits > best_hits:
            best_hits = hits
            best_cat = cat
    return best_cat


async def _answer_with_tools(
    client: ModelClient,
    system_prompt: str,
    query: str,
    category: str,
    registry: ToolRegistry,
    tools: list[ToolSchema],
    max_tool_steps: int = 3,
) -> tuple[str, list[StepRecord]]:
    """Run one agent turn with a bounded tool loop. Returns (answer, step records)."""
    messages = [
        Message(role=Role.SYSTEM, content=system_prompt),
        Message(role=Role.USER, content=f"[category: {category}]\nCustomer: {query}"),
    ]
    steps: list[StepRecord] = []
    answer = ""
    for _ in range(max_tool_steps):
        resp = await client.complete(
            CompletionRequest(messages=messages, tools=tools, temperature=0.0, max_tokens=512)
        )
        usage = resp.usage
        step = StepRecord(
            stage="agent",
            model=resp.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=resp.latency_ms,
            tool_calls=[tc.name for tc in resp.tool_calls],
        )
        steps.append(step)
        answer = resp.content or answer
        if not resp.tool_calls:
            break
        messages.append(Message(role=Role.ASSISTANT, content=resp.content or ""))
        for tc in resp.tool_calls:
            result = await registry.execute(tc.name, tc.arguments, tc.id)
            messages.append(
                Message(
                    role=Role.TOOL,
                    content=result.content if result.success else f"Error: {result.error}",
                    tool_call_id=tc.id,
                    name=tc.name,
                )
            )
    return answer.strip(), steps


def _aggregate(result: SystemResult) -> None:
    result.model_calls = len(result.steps)
    result.total_tokens = sum(s.total_tokens for s in result.steps)
    result.latency_ms = sum(s.latency_ms for s in result.steps)
    result.tool_calls = sum(len(s.tool_calls) for s in result.steps)


async def run_router(
    client: ModelClient, query: str, query_id: str, category_true: str
) -> SystemResult:
    """Rule-based switch picks the category, one specialized agent answers."""
    registry = ToolRegistry()
    category = rule_classify(query)  # the switch: no model call
    answer, steps = await _answer_with_tools(
        client, _AGENT_SYSTEM[category], query, category, registry, registry.schemas
    )
    result = SystemResult(
        system="router",
        query_id=query_id,
        category_true=category_true,
        category_used=category,
        answer=answer,
        steps=steps,
        flags={"misroute": category != category_true},
    )
    _aggregate(result)
    return result


async def _classify_llm(client: ModelClient, query: str) -> tuple[str, StepRecord]:
    """LLM classifier for the hierarchy. Can be wrong (that is the point)."""
    prompt = (
        "Classify the customer's support request into exactly one category: "
        "billing, technical, account, or escalation. Reply with only the category word."
    )
    resp = await client.complete(
        CompletionRequest(
            messages=[
                Message(role=Role.SYSTEM, content=prompt),
                Message(role=Role.USER, content=query),
            ],
            temperature=0.0,
            max_tokens=8,
        )
    )
    raw = (resp.content or "").strip().lower()
    category = next((c for c in CATEGORIES if c in raw), "account")
    usage = resp.usage
    step = StepRecord(
        stage="classifier",
        model=resp.model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
        latency_ms=resp.latency_ms,
    )
    return category, step


async def _verify_llm(
    client: ModelClient, query: str, answer: str
) -> tuple[bool, StepRecord]:
    """Verifier agent. Returns (ok, step). Lenient JSON parse."""
    prompt = (
        "You are a verification agent. Decide whether the support answer actually "
        "addresses the customer's question and states no policy it could not know. "
        'Reply with strict JSON: {"ok": true|false, "issues": ["..."]}.'
    )
    resp = await client.complete(
        CompletionRequest(
            messages=[
                Message(role=Role.SYSTEM, content=prompt),
                Message(role=Role.USER, content=f"Question: {query}\n\nAnswer: {answer}"),
            ],
            temperature=0.0,
            max_tokens=128,
            response_format={"type": "json_object"},
        )
    )
    ok = True
    content = resp.content or ""
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            ok = bool(json.loads(match.group(0)).get("ok", True))
        except json.JSONDecodeError:
            ok = True  # unparseable verifier defaults to pass (this is the rubber-stamp risk)
    usage = resp.usage
    step = StepRecord(
        stage="verifier",
        model=resp.model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
        latency_ms=resp.latency_ms,
    )
    return ok, step


async def run_hierarchy(
    client: ModelClient,
    query: str,
    query_id: str,
    category_true: str,
    max_rounds: int = 2,
) -> SystemResult:
    """Classifier -> worker -> verifier, with one re-answer round on failure."""
    registry = ToolRegistry()
    steps: list[StepRecord] = []

    category, clf_step = await _classify_llm(client, query)
    steps.append(clf_step)

    answer, worker_steps = await _answer_with_tools(
        client, _AGENT_SYSTEM[category], query, category, registry, registry.schemas
    )
    steps.extend(worker_steps)

    verifier_passed = False
    rounds = 0
    retried = False
    while rounds < max_rounds:
        ok, ver_step = await _verify_llm(client, query, answer)
        steps.append(ver_step)
        rounds += 1
        if ok:
            verifier_passed = True
            break
        retried = True
        followup = (
            f"{query}\n\nA reviewer flagged the previous answer. Re-answer the question "
            "directly using the knowledge base."
        )
        answer, redo_steps = await _answer_with_tools(
            client, _AGENT_SYSTEM[category], followup, category, registry, registry.schemas
        )
        steps.extend(redo_steps)

    result = SystemResult(
        system="hierarchy",
        query_id=query_id,
        category_true=category_true,
        category_used=category,
        answer=answer,
        steps=steps,
        flags={
            "misroute": category != category_true,
            "verifier_passed": verifier_passed,
            "verifier_retried": retried,
        },
    )
    _aggregate(result)
    return result
