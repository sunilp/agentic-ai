"""ADK agent stub (Section 0d).

Demonstrates how to wrap the same calculator/word_count/search tools in
Google Agent Development Kit (ADK) conventions. This file is a STUB --
actual execution requires google-adk to be installed.

When google-adk is not present, ADK_AVAILABLE is False and
create_adk_agent() returns None, allowing the rest of the codebase to
import this module without hard-failing on a missing optional dependency.

Install the real package with:
    pip install google-adk
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Optional import
# ---------------------------------------------------------------------------

try:
    from google.adk.agents import Agent as _ADKAgent
    from google.adk.tools import FunctionTool

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


# ---------------------------------------------------------------------------
# Standalone tool functions (same logic as tool_use.py, no registry needed)
# ---------------------------------------------------------------------------


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


def word_count(text: str) -> str:
    """Count the number of words in *text*.

    Args:
        text: Input text to count.

    Returns:
        A human-readable string with the word count.
    """
    count = len(text.split())
    return f"Word count: {count}"


def search(query: str, max_results: int = 3) -> str:
    """Return fake search results for demonstration purposes.

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


def create_adk_agent():  # type: ignore[return]
    """Create and return an ADK Agent if google-adk is available.

    The agent is configured with the three standard demo tools
    (calculator, word_count, search) wrapped as FunctionTool instances.

    Returns:
        An ADK Agent instance, or None if google-adk is not installed.
    """
    if not ADK_AVAILABLE:
        return None

    tools = [
        FunctionTool(func=calculator),
        FunctionTool(func=word_count),
        FunctionTool(func=search),
    ]

    return _ADKAgent(
        name="foundations_agent",
        model="gemini-3.5-flash",
        instruction=(
            "You are a helpful assistant. Use the available tools to answer "
            "the user's question accurately. Stop as soon as you have a good answer."
        ),
        tools=tools,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    if ADK_AVAILABLE:
        agent = create_adk_agent()
        print(f"ADK available. Agent created: {agent}")
    else:
        print(
            "google-adk is not installed. This is a stub file.\n"
            "Install with: pip install google-adk\n"
            "The create_adk_agent() function returns None when the package is absent."
        )
