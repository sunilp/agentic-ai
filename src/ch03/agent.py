"""Bounded agent with iteration budget, stop conditions, and escalation.

What's different from Chapter 2:
- Explicit iteration budget (max_steps)
- Stop conditions (confidence threshold, budget exhaustion)
- Uncertainty handling (escalation when evidence is insufficient)
- State tracking (TaskState records every step)
- Graceful degradation (partial answers when budget runs out)
"""

from __future__ import annotations

import time

from src.ch02.context import ContextPipeline
from src.ch02.tool_registry import ToolRegistry
from src.ch02.tools.retriever import DocumentIndex
from src.ch03.state import TaskState
from src.shared.model_client import ModelClient
from src.shared.types import (
    AgentResponse,
    CompletionRequest,
    Message,
    Role,
    TokenUsage,
)

AGENT_SYSTEM_PROMPT = """You are a document intelligence agent with bounded autonomy.

Your goal: answer the user's question using the provided evidence.

You have tools available. You may:
- Call 'retrieve' to search for more evidence if the initial results are insufficient.
- Call 'extract_structured' to pull specific fields from text.

Constraints:
- You have a limited step budget. Use it wisely.
- Only use information from retrieved documents. Do not use training knowledge.
- If you cannot answer confidently within your budget, say what you found
  and what is missing. Do not guess.
- Cite sources using [Source: filename] notation.

After each step, decide: do I have enough evidence to answer, or should I
search again with a different query?"""


class BoundedDocumentAgent:
    """Document agent with explicit iteration budget and escalation."""

    def __init__(
        self,
        client: ModelClient,
        index: DocumentIndex,
        registry: ToolRegistry,
        max_steps: int = 5,
        confidence_threshold: float = 0.6,
    ):
        self._client = client
        self._index = index
        self._registry = registry
        self._max_steps = max_steps
        self._confidence_threshold = confidence_threshold

    async def run(self, query: str, top_k: int = 5) -> AgentResponse:
        """Run the bounded agent loop."""
        start = time.monotonic()
        task = TaskState(task_id=f"task_{int(time.time())}", query=query, max_steps=self._max_steps)
        total_usage = TokenUsage()

        citations = self._index.retrieve(query, top_k=top_k)
        task.add_step("retrieve", {"query": query, "top_k": top_k}, f"{len(citations)} results")

        context = ContextPipeline(system_prompt=AGENT_SYSTEM_PROMPT)
        messages = context.build(query=query, citations=citations)
        tools = self._registry.list_tools()

        while not task.is_complete and not task.is_over_budget:
            request = CompletionRequest(
                messages=messages,
                tools=tools if tools else None,
                temperature=0.0,
            )
            response = await self._client.complete(request)
            total_usage = _merge_usage(total_usage, response.usage)
            task.add_step("model_call", {}, response.content or "(tool calls)")

            if response.tool_calls:
                for tc in response.tool_calls:
                    result = await self._registry.execute(tc.name, tc.arguments, tc.id)
                    task.add_step(f"tool:{tc.name}", tc.arguments, result.content[:200])
                    messages.append(Message(role=Role.ASSISTANT, content=f"Calling {tc.name}"))
                    messages.append(
                        Message(
                            role=Role.TOOL,
                            content=result.content if result.success else f"Error: {result.error}",
                            tool_call_id=tc.id,
                        )
                    )
                continue

            if response.content:
                avg_relevance = (
                    sum(c.relevance_score for c in citations) / len(citations) if citations else 0.0
                )
                confidence = (
                    min(0.95, avg_relevance)
                    if "[Source:" in (response.content or "")
                    else avg_relevance * 0.7
                )
                task.mark_complete(response.content, confidence)

        elapsed = (time.monotonic() - start) * 1000

        if task.is_over_budget and not task.is_complete:
            return AgentResponse(
                answer=f"I was unable to answer confidently within my step budget ({self._max_steps} steps). "
                f"Here is what I found: {task.steps[-1].get('result', 'No results gathered.')}",
                citations=citations,
                confidence=0.2,
                escalated=True,
                escalation_reason=f"Budget exhausted ({self._max_steps} steps) without reaching confidence threshold",
                steps_taken=len(task.steps),
                token_usage=total_usage,
                latency_ms=elapsed,
            )

        return AgentResponse(
            answer=task.result or "No answer generated.",
            citations=citations,
            confidence=task.confidence,
            escalated=task.confidence < self._confidence_threshold,
            escalation_reason=(
                f"Confidence {task.confidence:.2f} below threshold {self._confidence_threshold}"
                if task.confidence < self._confidence_threshold
                else None
            ),
            steps_taken=len(task.steps),
            token_usage=total_usage,
            latency_ms=elapsed,
        )


def _merge_usage(existing: TokenUsage, new: TokenUsage | None) -> TokenUsage:
    if new is None:
        return existing
    return TokenUsage(
        prompt_tokens=existing.prompt_tokens + new.prompt_tokens,
        completion_tokens=existing.completion_tokens + new.completion_tokens,
        total_tokens=existing.total_tokens + new.total_tokens,
    )
