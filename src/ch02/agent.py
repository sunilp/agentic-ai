"""The first working agent -- observe-think-act loop."""

from __future__ import annotations

import time

from src.ch02.context import ContextPipeline
from src.ch02.tool_registry import ToolRegistry
from src.ch02.tools.retriever import DocumentIndex
from src.shared.model_client import ModelClient
from src.shared.types import (
    AgentResponse,
    Citation,
    CompletionRequest,
    Message,
    Role,
    TokenUsage,
)


class DocumentAgent:
    """A document intelligence agent.

    Takes a query, retrieves relevant evidence, and answers with citations.
    Uses the observe-think-act loop.
    """

    def __init__(
        self,
        client: ModelClient,
        index: DocumentIndex,
        registry: ToolRegistry,
        context_pipeline: ContextPipeline | None = None,
        max_steps: int = 5,
    ):
        self._client = client
        self._index = index
        self._registry = registry
        self._context = context_pipeline or ContextPipeline()
        self._max_steps = max_steps

    async def run(self, query: str, top_k: int = 5) -> AgentResponse:
        """Run the agent loop for a single query."""
        start = time.monotonic()
        total_usage = TokenUsage()
        steps = 0

        citations = self._index.retrieve(query, top_k=top_k)

        messages = self._context.build(query=query, citations=citations)
        tools = self._registry.list_tools()

        request = CompletionRequest(
            messages=messages,
            tools=tools if tools else None,
            temperature=0.0,
        )
        response = await self._client.complete(request)
        total_usage = _merge_usage(total_usage, response.usage)
        steps += 1

        while response.tool_calls and steps < self._max_steps:
            for tc in response.tool_calls:
                result = await self._registry.execute(tc.name, tc.arguments, tc.id)
                messages.append(
                    Message(
                        role=Role.ASSISTANT,
                        content=f"Calling tool: {tc.name}",
                    )
                )
                messages.append(
                    Message(
                        role=Role.TOOL,
                        content=result.content if result.success else f"Error: {result.error}",
                        tool_call_id=tc.id,
                    )
                )

            request = CompletionRequest(messages=messages, tools=tools if tools else None, temperature=0.0)
            response = await self._client.complete(request)
            total_usage = _merge_usage(total_usage, response.usage)
            steps += 1

        elapsed = (time.monotonic() - start) * 1000

        confidence = _estimate_confidence(citations, response.content or "")

        return AgentResponse(
            answer=response.content or "I could not generate an answer.",
            citations=citations,
            confidence=confidence,
            escalated=confidence < 0.3,
            escalation_reason="Low confidence -- insufficient evidence"
            if confidence < 0.3
            else None,
            steps_taken=steps,
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


def _estimate_confidence(citations: list[Citation], answer: str) -> float:
    """Rough confidence estimate based on retrieval quality."""
    if not citations:
        return 0.1
    avg_relevance = sum(c.relevance_score for c in citations) / len(citations)
    has_citation_markers = "[Source:" in answer or "[source:" in answer.lower()
    if has_citation_markers and avg_relevance > 0.7:
        return min(0.95, avg_relevance)
    elif avg_relevance > 0.5:
        return avg_relevance * 0.8
    else:
        return avg_relevance * 0.5
