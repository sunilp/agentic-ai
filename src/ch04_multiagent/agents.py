"""Role-based agents for multi-agent document intelligence.

Each agent has one job. The retriever searches. The reasoner synthesizes.
The verifier checks. This is the value proposition of multi-agent:
specialization allows focused system prompts and clearer failure attribution.

The cost: coordination overhead, more tokens, higher latency.
Chapter 4 evaluates whether the tradeoff is worth it for this task.
"""

from __future__ import annotations

from src.ch02.tools.retriever import DocumentIndex
from src.ch04_multiagent.contracts import (
    ReasoningRequest,
    ReasoningResult,
    RetrievalRequest,
    RetrievalResult,
    VerificationRequest,
    VerificationResult,
)
from src.shared.model_client import ModelClient
from src.shared.types import (
    CompletionRequest,
    Message,
    Role,
    TokenUsage,
)


class RetrieverAgent:
    """Searches and retrieves relevant document chunks.

    This agent does not reason or answer. It only retrieves.
    """

    def __init__(self, index: DocumentIndex):
        self._index = index
        self.total_usage = TokenUsage()

    async def run(self, request: RetrievalRequest) -> RetrievalResult:
        citations = self._index.retrieve(request.query, top_k=request.top_k)
        return RetrievalResult(
            citations=citations,
            chunks_searched=request.top_k,
        )


class ReasoningAgent:
    """Synthesizes an answer from evidence with citations.

    This agent receives pre-retrieved evidence and focuses purely
    on reasoning and answer generation. It does not search.
    """

    SYSTEM_PROMPT = """You are a reasoning agent. Your job is to synthesize an answer
from the provided evidence excerpts.

Rules:
- Only use information from the provided excerpts.
- Cite sources using [Source: filename] notation.
- If the evidence is insufficient, say so clearly.
- Be precise and concise."""

    def __init__(self, client: ModelClient):
        self._client = client
        self.total_usage = TokenUsage()

    async def run(self, request: ReasoningRequest) -> ReasoningResult:
        evidence_parts = []
        for i, c in enumerate(request.citations, 1):
            evidence_parts.append(f"[Excerpt {i}] (Source: {c.source})\n{c.text}")
        evidence_text = "\n\n".join(evidence_parts) if evidence_parts else "No evidence provided."

        messages = [
            Message(role=Role.SYSTEM, content=self.SYSTEM_PROMPT),
            Message(
                role=Role.USER, content=f"Evidence:\n{evidence_text}\n\nQuestion: {request.query}"
            ),
        ]

        response = await self._client.complete(CompletionRequest(messages=messages, temperature=0.0))
        self.total_usage = _merge_usage(self.total_usage, response.usage)

        cited = [c.source for c in request.citations if c.source in (response.content or "")]

        return ReasoningResult(
            answer=response.content or "Unable to synthesize an answer.",
            cited_sources=cited,
        )


class VerifierAgent:
    """Checks that citations in an answer are supported by source text.

    This agent does not generate answers. It only verifies that claims
    made in the answer are actually present in the cited evidence.
    """

    SYSTEM_PROMPT = """You are a verification agent. Your job is to check whether
an answer's citations are supported by the provided evidence.

For each citation in the answer:
1. Find the corresponding evidence excerpt
2. Check if the claim is actually supported by that excerpt
3. Flag any unsupported claims

Return a JSON object with:
- "verified": true/false
- "issues": list of strings describing any problems found

If all citations are supported, return {"verified": true, "issues": []}.
Return valid JSON only."""

    def __init__(self, client: ModelClient):
        self._client = client
        self.total_usage = TokenUsage()

    async def run(self, request: VerificationRequest) -> VerificationResult:
        evidence_parts = []
        for c in request.citations:
            evidence_parts.append(f"[Source: {c.source}]\n{c.text}")
        evidence_text = "\n\n".join(evidence_parts) if evidence_parts else "No evidence."

        messages = [
            Message(role=Role.SYSTEM, content=self.SYSTEM_PROMPT),
            Message(
                role=Role.USER,
                content=f"Answer to verify:\n{request.answer}\n\nEvidence:\n{evidence_text}",
            ),
        ]

        response = await self._client.complete(
            CompletionRequest(messages=messages, response_format={"type": "json_object"}, temperature=0.0)
        )
        self.total_usage = _merge_usage(self.total_usage, response.usage)

        import json

        try:
            result = json.loads(
                response.content or '{"verified": false, "issues": ["No response"]}'
            )
            return VerificationResult(
                verified=result.get("verified", False),
                issues=result.get("issues", []),
            )
        except json.JSONDecodeError:
            return VerificationResult(
                verified=False,
                issues=["Verifier returned invalid JSON"],
            )


def _merge_usage(existing: TokenUsage, new: TokenUsage | None) -> TokenUsage:
    if new is None:
        return existing
    return TokenUsage(
        prompt_tokens=existing.prompt_tokens + new.prompt_tokens,
        completion_tokens=existing.completion_tokens + new.completion_tokens,
        total_tokens=existing.total_tokens + new.total_tokens,
    )
