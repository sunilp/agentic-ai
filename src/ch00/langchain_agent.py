"""LangChain agent stub (Section 0d).

Demonstrates how to wrap the same calculator/word_count/search tools in
LangChain conventions. This file is a STUB -- actual execution requires
langchain-core, langchain-anthropic, langchain, and langgraph to be installed.

When the dependencies are absent, LANGCHAIN_AVAILABLE is False and
create_langchain_agent() returns None, allowing the rest of the codebase
to import this module without hard-failing on missing optional packages.

Install the real packages with:
    pip install langchain-core langchain-anthropic langchain langgraph
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------

try:
    from langchain_core.tools import tool as langchain_tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

    # Provide a no-op decorator so the function definitions below remain valid
    # even when langchain_core is absent.
    def langchain_tool(fn):  # type: ignore[misc]
        return fn


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

# The @langchain_tool decorator is applied unconditionally. When langchain_core
# is not installed the no-op fallback above leaves the function unchanged.


@langchain_tool
def calculator(operation: str, a: float, b: float) -> str:
    """Perform a basic arithmetic operation.

    Args:
        operation: One of add, subtract, multiply, divide.
        a:         Left operand.
        b:         Right operand.

    Returns:
        The numeric result as a string, or an error message.
    """
    op = operation.lower()
    if op == "add":
        return str(float(a + b))
    elif op == "subtract":
        return str(float(a - b))
    elif op == "multiply":
        return str(float(a * b))
    elif op == "divide":
        if b == 0:
            return "Error: division by zero"
        return str(float(a / b))
    return f"Error: unknown operation '{operation}'"


@langchain_tool
def word_count(text: str) -> str:
    """Count the number of words in the input text.

    Args:
        text: Input text to count.

    Returns:
        A human-readable string with the word count.
    """
    count = len(text.split())
    return f"Word count: {count}"


@langchain_tool
def search(query: str, max_results: int = 3) -> str:
    """Search for information and return mock results.

    Args:
        query:       Search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        A JSON string representing mock search results.
    """
    results = [
        {"title": f"Result {i + 1} for '{query}'", "url": f"https://example.com/{i + 1}"}
        for i in range(max(1, min(max_results, 10)))
    ]
    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def create_langchain_agent():  # type: ignore[return]
    """Create and return a LangChain agent if dependencies are available.

    Builds a ChatAnthropic model bound to the three demo tools and wraps it
    with langchain.agents.create_agent, the LangChain v1 agent factory
    (replaces the deprecated langgraph.prebuilt.create_react_agent).

    Returns:
        A compiled LangGraph agent, or None if langchain deps are not installed.
    """
    if not LANGCHAIN_AVAILABLE:
        return None

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain.agents import create_agent
    except ImportError:
        return None

    model = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    tools = [calculator, word_count, search]
    return create_agent(model, tools)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    if LANGCHAIN_AVAILABLE:
        agent = create_langchain_agent()
        if agent is not None:
            print(f"LangChain available. Agent created: {agent}")
        else:
            print(
                "langchain_core is present but langchain-anthropic or langchain/langgraph is missing.\n"
                "Install with: pip install langchain-anthropic langchain langgraph"
            )
    else:
        print(
            "langchain-core is not installed. This is a stub file.\n"
            "Install with: pip install langchain-core langchain-anthropic langchain langgraph\n"
            "The create_langchain_agent() function returns None when packages are absent."
        )
