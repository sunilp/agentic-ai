"""Expanded tool set for the research agent (Section 0c).

Provides four tools with Pydantic input validation:
- calculator:  arithmetic (matches tool_use.py but adds power/modulo)
- search:      simulated web search returning mock results
- read_url:    simulated URL fetch returning mock article content
- summarize:   calls the model to summarise a piece of text (LLM tool)

All tools are standalone functions that can be registered in any ToolRegistry.
The summarize tool requires a ModelClient; pass it as a module-level default
before running the agent (or inject via the agent constructor).

Run this file directly to see all tools exercised:
    python project/research-agent/src/tools.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

# Path bootstrap for direct script execution.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic import BaseModel, Field, field_validator  # noqa: E402

from src.ch00.tool_use import ToolRegistry, execute_tool_call  # noqa: E402

if TYPE_CHECKING:
    from src.shared.model_client import ModelClient

# ---------------------------------------------------------------------------
# Module-level summarize client (injected before use)
# ---------------------------------------------------------------------------

_summarize_client: ModelClient | None = None


def set_summarize_client(client: ModelClient) -> None:
    """Inject a ModelClient to be used by the summarize tool.

    Call this before running any agent that uses the summarize tool.
    If not set, summarize() returns a placeholder string.

    Args:
        client: Any ModelClient instance.
    """
    global _summarize_client
    _summarize_client = client


# ---------------------------------------------------------------------------
# Enums and input models
# ---------------------------------------------------------------------------


class ArithmeticOp(StrEnum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    POWER = "power"
    MODULO = "modulo"


class CalculatorInput(BaseModel):
    """Input schema for the calculator tool."""

    operation: ArithmeticOp
    a: float
    b: float


class SearchInput(BaseModel):
    """Input schema for the search tool."""

    query: str = Field(description="Search query string.")
    max_results: int = Field(default=3, ge=1, le=10)


class ReadUrlInput(BaseModel):
    """Input schema for the URL reader tool."""

    url: str = Field(description="URL to fetch content from.")
    max_chars: int = Field(default=1000, ge=100, le=5000)

    @field_validator("url")
    @classmethod
    def url_looks_valid(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class SummarizeInput(BaseModel):
    """Input schema for the summarize tool."""

    text: str = Field(description="Text to summarise.")
    max_words: int = Field(default=50, ge=10, le=200, description="Target summary word count.")


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def calculator(operation: str, a: float, b: float) -> str:
    """Perform an arithmetic operation.

    Args:
        operation: One of add, subtract, multiply, divide, power, modulo.
        a:         Left operand.
        b:         Right operand.

    Returns:
        The result as a string, or an error message.
    """
    op = ArithmeticOp(operation)
    match op:
        case ArithmeticOp.ADD:
            return str(a + b)
        case ArithmeticOp.SUBTRACT:
            return str(a - b)
        case ArithmeticOp.MULTIPLY:
            return str(a * b)
        case ArithmeticOp.DIVIDE:
            if b == 0:
                return "Error: division by zero"
            return str(a / b)
        case ArithmeticOp.POWER:
            return str(a**b)
        case ArithmeticOp.MODULO:
            if b == 0:
                return "Error: modulo by zero"
            return str(a % b)


def search(query: str, max_results: int = 3) -> str:
    """Return simulated search results.

    Args:
        query:       Search query string.
        max_results: Maximum results to return (1-10).

    Returns:
        A JSON string of mock search results with title, url, and snippet.
    """
    n = max(1, min(max_results, 10))
    results = [
        {
            "title": f"{query.title()} - Wikipedia",
            "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            "snippet": (
                f"Wikipedia article about {query.lower()}. "
                "Provides an encyclopaedic overview with references."
            ),
        }
    ]
    for i in range(1, n):
        results.append(
            {
                "title": f"Result {i + 1} for '{query}'",
                "url": f"https://example.com/search/{i + 1}",
                "snippet": f"Additional information about {query.lower()}, result {i + 1}.",
            }
        )
    return json.dumps(results, indent=2)


def read_url(url: str, max_chars: int = 1000) -> str:
    """Fetch and return simulated article content from a URL.

    In a production system this would use httpx or requests to fetch the
    URL and extract text. Here it returns mock content based on the URL
    so experiments are reproducible without network access.

    Args:
        url:       URL to "fetch."
        max_chars: Maximum characters to return.

    Returns:
        Simulated article text for the URL.
    """
    if "wikipedia.org/wiki/" in url:
        topic = url.split("/wiki/")[-1].replace("_", " ")
        content = (
            f"{topic}\n\n"
            f"{topic} is a well-documented topic with extensive research literature. "
            f"The field has evolved significantly over the past decade, with major "
            f"contributions from academic institutions and industry research labs. "
            f"Key concepts include foundational theory, practical applications, and "
            f"ongoing debates about best practices and limitations.\n\n"
            f"History\n"
            f"The origins of {topic.lower()} date back to foundational work in the "
            f"mid-twentieth century, with accelerating progress from the 1990s onward.\n\n"
            f"Applications\n"
            f"Practical applications of {topic.lower()} span multiple industries "
            f"including healthcare, finance, manufacturing, and scientific research."
        )
    else:
        domain = url.split("/")[2] if "://" in url else url
        content = (
            f"Content from {domain}\n\n"
            f"This page discusses relevant information related to the topic. "
            f"The author presents several key points with supporting evidence. "
            f"Further reading is available via the references section."
        )
    return content[:max_chars]


def summarize(text: str, max_words: int = 50) -> str:
    """Summarise *text* using the injected model client.

    If no client has been injected via set_summarize_client(), returns a
    placeholder so the agent loop can continue without raising an error.

    Args:
        text:      Text to summarise.
        max_words: Target word count for the summary.

    Returns:
        A summary string (or a placeholder if no client is configured).
    """
    if _summarize_client is None:
        # Graceful degradation: return a truncated version as a fallback.
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + " [... summarization client not configured]"

    # Run the async summarize call synchronously via a new event loop.
    # This works because tool functions are called from synchronous context
    # inside the agent loop.
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context; schedule as a coroutine.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _async_summarize(text, max_words))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(_async_summarize(text, max_words))
    except Exception as exc:  # noqa: BLE001
        return f"Summarization error: {exc}. Original text (truncated): {text[:200]}"


async def _async_summarize(text: str, max_words: int) -> str:
    """Async helper for the summarize tool."""
    from src.ch00.llm_basics import call_llm

    if _summarize_client is None:
        return text[:200]

    response = await call_llm(
        client=_summarize_client,
        user_message=f"Summarise the following text in at most {max_words} words:\n\n{text}",
        system_message="You are a concise summarizer. Return only the summary, no preamble.",
    )
    return response.content or text[:200]


# ---------------------------------------------------------------------------
# Registry factory
# ---------------------------------------------------------------------------


def create_research_registry() -> ToolRegistry:
    """Build a ToolRegistry with the four research agent tools.

    Returns:
        A populated ToolRegistry.
    """
    registry = ToolRegistry()
    registry.register(
        name="calculator",
        description="Perform arithmetic: add, subtract, multiply, divide, power, or modulo.",
        fn=calculator,
        input_model=CalculatorInput,
    )
    registry.register(
        name="search",
        description=(
            "Search for information on a topic and return the top results with titles, "
            "URLs, and snippets."
        ),
        fn=search,
        input_model=SearchInput,
    )
    registry.register(
        name="read_url",
        description=(
            "Fetch the text content of a URL. Returns the page content up to max_chars characters."
        ),
        fn=read_url,
        input_model=ReadUrlInput,
    )
    registry.register(
        name="summarize",
        description=(
            "Summarise a piece of text in at most max_words words. "
            "Use after read_url to condense long articles."
        ),
        fn=summarize,
        input_model=SummarizeInput,
    )
    return registry


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    registry = create_research_registry()

    print("Research agent tools:")
    for schema in registry.get_schemas():
        print(f"  {schema.name}: {schema.description[:60]}")

    print("\nCalculator examples:")
    for op, a, b in [("add", 15, 7), ("multiply", 15, 7), ("power", 2, 8)]:
        print(
            f"  {op}({a}, {b}) = {execute_tool_call(registry, 'calculator', {'operation': op, 'a': a, 'b': b})}"
        )

    print("\nSearch:")
    result = execute_tool_call(registry, "search", {"query": "agentic AI", "max_results": 2})
    print(f"  {result[:200]}...")

    print("\nRead URL:")
    result = execute_tool_call(
        registry,
        "read_url",
        {"url": "https://en.wikipedia.org/wiki/Machine_learning", "max_chars": 300},
    )
    print(f"  {result[:200]}...")

    print("\nSummarize (no client):")
    result = execute_tool_call(
        registry,
        "summarize",
        {
            "text": "Agentic AI refers to AI systems that can autonomously plan and execute multi-step tasks.",
            "max_words": 10,
        },
    )
    print(f"  {result}")
