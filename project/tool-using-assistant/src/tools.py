"""Tools for the tool-using assistant (Section 0b).

Defines four tools with Pydantic input validation:
- calculator:    arithmetic operations
- word_counter:  counts words in a string
- search:        simulated web search returning mock results
- file_reader:   reads a local file (sandboxed to safe paths)

Each tool is registered in a ToolRegistry so it can be called via the shared
execute_tool_call function from src/ch00/tool_use.py.

Run with:
    python project/tool-using-assistant/src/tools.py
"""

from __future__ import annotations

import json
import os
import sys
from enum import StrEnum
from pathlib import Path

# Path bootstrap for direct script execution.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic import BaseModel, Field, field_validator  # noqa: E402

from src.ch00.tool_use import ToolRegistry, execute_tool_call  # noqa: E402

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


class WordCounterInput(BaseModel):
    """Input schema for the word counter tool."""

    text: str = Field(description="The text whose words should be counted.")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class SearchInput(BaseModel):
    """Input schema for the simulated search tool."""

    query: str = Field(description="Search query string.")
    max_results: int = Field(default=3, ge=1, le=10, description="Max results to return (1-10).")


class FileReaderInput(BaseModel):
    """Input schema for the file reader tool.

    File paths are restricted to the project directory for safety.
    Absolute paths outside the project root are rejected.
    """

    path: str = Field(description="Relative path to a file within the project directory.")
    max_lines: int = Field(
        default=50, ge=1, le=500, description="Maximum number of lines to read."
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def calculator(operation: str, a: float, b: float) -> str:
    """Perform an arithmetic operation and return the result as a string.

    Args:
        operation: One of add, subtract, multiply, divide, power, modulo.
        a:         Left operand.
        b:         Right operand.

    Returns:
        The numeric result as a string, or an error message.
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


def word_counter(text: str) -> str:
    """Count the words in *text*, including basic statistics.

    Args:
        text: Input text to analyse.

    Returns:
        A JSON string with word_count, character_count, and sentence_count.
    """
    words = text.split()
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    result = {
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": len(sentences),
        "avg_word_length": round(sum(len(w) for w in words) / max(1, len(words)), 1),
    }
    return json.dumps(result)


def search(query: str, max_results: int = 3) -> str:
    """Return simulated search results for demonstration purposes.

    In a production system this would call a real search API.
    The simulated results include a Wikipedia-style entry and a few
    more specific pages.

    Args:
        query:       Search query string.
        max_results: Maximum results to return (1-10).

    Returns:
        A JSON string representing mock search results.
    """
    # Simulate a realistic-looking result set.
    base_results = [
        {
            "title": f"{query.title()} - Wikipedia",
            "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            "snippet": (
                f"{query.title()} is a broad topic covering several important concepts. "
                "Wikipedia provides an overview with references to primary sources."
            ),
        },
        {
            "title": f"Introduction to {query.title()} | Example Docs",
            "url": f"https://docs.example.com/{query.replace(' ', '-').lower()}",
            "snippet": (
                f"This documentation page introduces {query.lower()} "
                "with practical examples and usage guidance."
            ),
        },
        {
            "title": f"{query.title()}: A Practical Guide",
            "url": f"https://blog.example.com/guide-to-{query.replace(' ', '-').lower()}",
            "snippet": (
                f"A hands-on guide to understanding and applying {query.lower()} "
                "in real-world scenarios."
            ),
        },
        {
            "title": f"Research on {query.title()} | arXiv",
            "url": f"https://arxiv.org/search/?query={query.replace(' ', '+')}&searchtype=all",
            "snippet": (
                f"Recent research papers and preprints related to {query.lower()}. "
                "Includes peer-reviewed and preprint results."
            ),
        },
        {
            "title": f"{query.title()} Forum Discussion",
            "url": f"https://forum.example.com/t/{query.replace(' ', '-').lower()}",
            "snippet": (
                f"Community discussion about {query.lower()} including practical "
                "tips and troubleshooting advice."
            ),
        },
    ]
    capped = base_results[: max(1, min(max_results, 10))]
    return json.dumps(capped, indent=2)


def file_reader(path: str, max_lines: int = 50) -> str:
    """Read a file from within the project directory.

    Sandboxed to the current working directory for safety. Absolute paths
    and traversal attempts (../../) are rejected.

    Args:
        path:      Relative path to the file.
        max_lines: Maximum number of lines to return.

    Returns:
        The file contents (up to max_lines lines), or an error string.
    """
    try:
        resolved = Path(path).resolve()
        cwd = Path.cwd().resolve()
        # Safety: reject paths outside the working directory.
        if not str(resolved).startswith(str(cwd)):
            return f"Error: access denied -- path is outside the project directory: {path!r}"
        if not resolved.exists():
            return f"Error: file not found: {path!r}"
        if not resolved.is_file():
            return f"Error: path is not a file: {path!r}"
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
        truncated = len(lines) > max_lines
        output_lines = lines[:max_lines]
        content = "\n".join(output_lines)
        if truncated:
            content += f"\n... (truncated at {max_lines} lines; file has {len(lines)} total)"
        return content
    except PermissionError:
        return f"Error: permission denied reading {path!r}"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading {path!r}: {exc}"


# ---------------------------------------------------------------------------
# Registry factory
# ---------------------------------------------------------------------------


def create_assistant_registry() -> ToolRegistry:
    """Build a ToolRegistry with all four assistant tools registered.

    Returns:
        A populated ToolRegistry ready for use with execute_tool_call.
    """
    registry = ToolRegistry()
    registry.register(
        name="calculator",
        description=(
            "Perform arithmetic: add, subtract, multiply, divide, power, or modulo two numbers."
        ),
        fn=calculator,
        input_model=CalculatorInput,
    )
    registry.register(
        name="word_counter",
        description=(
            "Count the words in a piece of text. "
            "Returns word count, character count, and sentence count."
        ),
        fn=word_counter,
        input_model=WordCounterInput,
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
        name="file_reader",
        description=(
            "Read the contents of a file in the project directory. "
            "Provide a relative path from the project root."
        ),
        fn=file_reader,
        input_model=FileReaderInput,
    )
    return registry


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    registry = create_assistant_registry()

    print("Registered tools:")
    for schema in registry.get_schemas():
        print(f"\n  {schema.name}: {schema.description}")
        for param in schema.parameters:
            req = "required" if param.required else "optional"
            enum_hint = f" (enum: {param.enum})" if param.enum else ""
            print(f"    - {param.name} [{param.type}] {req}{enum_hint}")

    print("\n" + "=" * 50)
    print("Direct tool invocations:")

    # Calculator
    for op, a, b in [("add", 15, 7), ("power", 2, 10), ("modulo", 17, 5)]:
        result = execute_tool_call(registry, "calculator", {"operation": op, "a": a, "b": b})
        print(f"  calculator({op}, {a}, {b}) -> {result}")

    # Word counter
    result = execute_tool_call(
        registry, "word_counter", {"text": "the quick brown fox jumps over the lazy dog"}
    )
    print(f"  word_counter('the quick brown fox...') -> {result}")

    # Search
    result = execute_tool_call(registry, "search", {"query": "agentic AI", "max_results": 2})
    print(f"  search('agentic AI', max_results=2) -> {result[:120]}...")

    # File reader (README exists)
    result = execute_tool_call(registry, "file_reader", {"path": "project/tool-using-assistant/README.md", "max_lines": 5})
    print(f"  file_reader('project/tool-using-assistant/README.md', 5) -> {result[:120]}...")

    # Validation error
    result = execute_tool_call(registry, "calculator", {"operation": "sqrt", "a": 9, "b": 0})
    print(f"  calculator('sqrt', 9, 0) [invalid op] -> {result}")

    # Empty text
    result = execute_tool_call(registry, "word_counter", {"text": "   "})
    print(f"  word_counter('   ') [empty text] -> {result}")
