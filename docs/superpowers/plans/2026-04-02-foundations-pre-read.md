# Foundations Pre-Read Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a four-section "Foundations" pre-read that takes developers from zero LLM experience to building agents, integrated into the existing Agentic AI code companion repo.

**Architecture:** Four markdown chapters (00a-00d) in `docs/book/`, with companion Python code in `src/ch00/`, four companion projects in `project/`, and 14 hand-crafted SVG diagrams. Sections build sequentially: LLM basics -> tool use -> raw agent -> frameworks. All code uses the existing `src/shared/model_client.py` abstraction.

**Tech Stack:** Python 3.11+, Anthropic/OpenAI APIs (via existing model_client), Pydantic, Google ADK, LangChain, MkDocs Material, hand-crafted SVGs.

---

## Task 1: Infrastructure Setup

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`
- Modify: `.env.example`
- Create: `src/ch00/__init__.py`

- [ ] **Step 1: Add foundations dependencies to pyproject.toml**

Add `google-adk`, `langchain`, `langchain-core`, and `langchain-anthropic` to dependencies:

```toml
# Add to [project.optional-dependencies]
foundations = [
    "google-adk>=1.0",
    "langchain>=0.3",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
]
```

In `pyproject.toml`, add after the `dev` optional-dependencies block:

```toml
foundations = [
    "google-adk>=1.0",
    "langchain>=0.3",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
]
```

Also add to the ruff per-file-ignores:

```toml
"src/ch00/*.py" = ["E402"]
```

- [ ] **Step 2: Add Makefile targets**

Append to `Makefile`:

```makefile
foundations:
	python src/ch00/llm_basics.py
	python src/ch00/tool_use.py
	python src/ch00/raw_agent.py

foundations-compare:
	python src/ch00/eval_compare.py
```

- [ ] **Step 3: Create src/ch00/__init__.py**

```python
"""Foundations: code companion for the pre-read sections (0a-0d)."""
```

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p src/ch00
mkdir -p project/llm-explorer/src project/llm-explorer/docs
mkdir -p project/tool-using-assistant/src project/tool-using-assistant/docs
mkdir -p project/research-agent/src project/research-agent/evals project/research-agent/docs
mkdir -p project/framework-comparison/src project/framework-comparison/evals project/framework-comparison/docs
mkdir -p tests/unit/ch00
touch tests/unit/ch00/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add src/ch00/__init__.py tests/unit/ch00/__init__.py pyproject.toml Makefile
git commit -m "feat: add foundations infrastructure (directories, deps, makefile targets)"
```

---

## Task 2: Section 0a Code -- LLM Basics Module

**Files:**
- Create: `src/ch00/llm_basics.py`
- Create: `tests/unit/ch00/test_llm_basics.py`

- [ ] **Step 1: Write tests for llm_basics**

```python
"""Tests for the LLM basics module (Section 0a).

These tests use MockClient so they run without API keys.
"""

import asyncio
import pytest
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse, TokenUsage
from src.ch00.llm_basics import (
    call_llm,
    count_tokens_estimate,
    estimate_cost,
    parse_structured_output,
)


def test_count_tokens_estimate():
    """Token count estimate should be roughly 1 token per 4 chars."""
    text = "Hello world, this is a test of token counting."
    count = count_tokens_estimate(text)
    assert 8 <= count <= 15  # Roughly 11 tokens


def test_estimate_cost():
    """Cost estimate should multiply tokens by per-token price."""
    cost = estimate_cost(prompt_tokens=1000, completion_tokens=500, model="gpt-4o")
    assert cost > 0
    assert isinstance(cost, float)


def test_estimate_cost_unknown_model_uses_default():
    """Unknown model should use a default price, not crash."""
    cost = estimate_cost(prompt_tokens=100, completion_tokens=50, model="unknown-model")
    assert cost > 0


def test_parse_structured_output_valid_json():
    """Valid JSON string should parse to dict."""
    result = parse_structured_output('{"name": "Alice", "age": 30}')
    assert result == {"name": "Alice", "age": 30}


def test_parse_structured_output_invalid_json():
    """Invalid JSON should return None, not crash."""
    result = parse_structured_output("This is not JSON at all.")
    assert result is None


def test_parse_structured_output_extracts_json_from_text():
    """JSON embedded in surrounding text should still be extracted."""
    result = parse_structured_output('Here is the result: {"status": "ok"} and some more text')
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_call_llm_returns_response():
    """call_llm should return the content from the model."""
    client = MockClient(
        responses=[
            CompletionResponse(
                content="Hello! I'm a language model.",
                model="mock",
                usage=TokenUsage(prompt_tokens=10, completion_tokens=8, total_tokens=18),
            )
        ]
    )
    result = await call_llm(client, "Say hello")
    assert result.content == "Hello! I'm a language model."
    assert result.usage.total_tokens == 18
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ch00/test_llm_basics.py -v`
Expected: FAIL with import errors (module not yet created)

- [ ] **Step 3: Implement llm_basics.py**

```python
"""LLM Basics -- Section 0a code companion.

The essential operations for working with LLMs as an engineer:
- Making API calls
- Counting tokens and estimating cost
- Parsing structured output
- Understanding what you're actually building on top of

This module uses the shared model_client abstraction so it works
with OpenAI, Anthropic, or local models. No framework dependencies.
"""

from __future__ import annotations

import json
import re

from src.shared.model_client import ModelClient
from src.shared.types import CompletionRequest, CompletionResponse, Message, Role

# Rough per-token pricing (USD). These change -- the exact numbers
# matter less than the habit of tracking them.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "claude-sonnet-4-20250514": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-haiku-4-5-20251001": {"input": 0.80 / 1_000_000, "output": 4.00 / 1_000_000},
}

# Default pricing for unknown models
_DEFAULT_PRICING = {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000}


def count_tokens_estimate(text: str) -> int:
    """Estimate token count. Roughly 1 token per 4 characters in English.

    This is a fast approximation. For exact counts, use tiktoken (OpenAI)
    or the provider's tokenizer. But for budgeting and back-of-envelope
    calculations, this is close enough.
    """
    return max(1, len(text) // 4)


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> float:
    """Estimate the cost of an API call in USD.

    Uses known pricing for common models. Falls back to a default
    for unknown models -- better to estimate high than ignore cost.
    """
    pricing = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    return (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])


def parse_structured_output(text: str) -> dict | None:
    """Try to parse JSON from model output.

    Models don't always return clean JSON. Sometimes they wrap it
    in markdown code blocks or add commentary. This function tries
    the obvious parse first, then looks for JSON embedded in text.

    Returns None if no valid JSON is found -- never crashes.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to extract JSON object from surrounding text
    match = re.search(r"\{[^{}]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


async def call_llm(
    client: ModelClient,
    user_message: str,
    system_message: str = "You are a helpful assistant.",
    temperature: float = 0.0,
) -> CompletionResponse:
    """Make a single LLM call. The simplest possible interaction.

    This is the foundation. Every agent, every chain, every RAG pipeline
    starts with this operation: send text, get text back.
    """
    request = CompletionRequest(
        messages=[
            Message(role=Role.SYSTEM, content=system_message),
            Message(role=Role.USER, content=user_message),
        ],
        temperature=temperature,
        max_tokens=1024,
    )
    return await client.complete(request)


# --- Runnable demo ---

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    from src.shared.model_client import create_client

    load_dotenv()

    async def main():
        provider = os.getenv("MODEL_PROVIDER", "openai")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
        model = os.getenv("MODEL_NAME", "gpt-4o")

        client = create_client(provider=provider, api_key=api_key, model_name=model)

        # 1. Simple API call
        print("--- Simple API Call ---")
        response = await call_llm(client, "What is 2 + 2? Answer in one word.")
        print(f"Response: {response.content}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Estimated cost: ${estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens, model):.6f}")

        # 2. Token estimation
        print("\n--- Token Estimation ---")
        sample_text = "The quick brown fox jumps over the lazy dog."
        print(f"Text: '{sample_text}'")
        print(f"Estimated tokens: {count_tokens_estimate(sample_text)}")

        # 3. Structured output
        print("\n--- Structured Output ---")
        response = await call_llm(
            client,
            'Extract the name and age from this text and return as JSON: "Alice is 30 years old."',
            system_message="Return only valid JSON. No other text.",
        )
        print(f"Raw response: {response.content}")
        parsed = parse_structured_output(response.content or "")
        print(f"Parsed: {parsed}")

        # 4. Temperature comparison
        print("\n--- Temperature Comparison ---")
        prompt = "Suggest a name for a pet cat."
        for temp in [0.0, 0.5, 1.0]:
            r = await call_llm(client, prompt, temperature=temp)
            print(f"  temp={temp}: {r.content}")

    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ch00/test_llm_basics.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/ch00/llm_basics.py tests/unit/ch00/test_llm_basics.py
git commit -m "feat: add section 0a code -- LLM basics module with tests"
```

---

## Task 3: Section 0b Code -- Tool Use Module

**Files:**
- Create: `src/ch00/tool_use.py`
- Create: `tests/unit/ch00/test_tool_use.py`

- [ ] **Step 1: Write tests for tool_use**

```python
"""Tests for the tool use module (Section 0b).

Tests function calling, tool registry, and Pydantic validation.
"""

import pytest
from pydantic import ValidationError
from src.ch00.tool_use import (
    Tool,
    ToolRegistry,
    CalculatorInput,
    calculator,
    word_count,
    execute_tool_call,
)


def test_calculator_add():
    result = calculator(operation="add", a=2, b=3)
    assert result == "5.0"


def test_calculator_divide_by_zero():
    result = calculator(operation="divide", a=1, b=0)
    assert "error" in result.lower()


def test_word_count():
    result = word_count(text="hello world foo bar")
    assert "4" in result


def test_calculator_input_validation():
    """Pydantic should reject invalid operation."""
    with pytest.raises(ValidationError):
        CalculatorInput(operation="modulo", a=1, b=2)


def test_tool_registry_register_and_list():
    registry = ToolRegistry()
    registry.register("calc", "A calculator", calculator, CalculatorInput)
    names = registry.list_tools()
    assert "calc" in names


def test_tool_registry_get_schemas():
    registry = ToolRegistry()
    registry.register("calc", "A calculator", calculator, CalculatorInput)
    schemas = registry.get_schemas()
    assert len(schemas) == 1
    assert schemas[0].name == "calc"


def test_execute_tool_call_valid():
    registry = ToolRegistry()
    registry.register("calc", "A calculator", calculator, CalculatorInput)
    result = execute_tool_call(registry, "calc", {"operation": "add", "a": 5, "b": 3})
    assert result == "8.0"


def test_execute_tool_call_unknown_tool():
    registry = ToolRegistry()
    result = execute_tool_call(registry, "nonexistent", {})
    assert "error" in result.lower() or "unknown" in result.lower()


def test_execute_tool_call_invalid_args():
    registry = ToolRegistry()
    registry.register("calc", "A calculator", calculator, CalculatorInput)
    result = execute_tool_call(registry, "calc", {"operation": "bad", "a": 1, "b": 2})
    assert "error" in result.lower() or "validation" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ch00/test_tool_use.py -v`
Expected: FAIL with import errors

- [ ] **Step 3: Implement tool_use.py**

```python
"""Tool Use -- Section 0b code companion.

Function calling demystified: how LLMs call your code, and how
to make it safe with validation.

Key concepts:
- Tools are just functions with schemas
- The model outputs JSON saying "call this function"
- Your code does the actual calling
- Pydantic validation catches hallucinated arguments
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel

from src.shared.types import ToolSchema, ToolParameter


# --- Tool definitions with Pydantic validation ---


class Operation(str, Enum):
    add = "add"
    subtract = "subtract"
    multiply = "multiply"
    divide = "divide"


class CalculatorInput(BaseModel):
    """Input schema for the calculator tool."""
    operation: Operation
    a: float
    b: float


class WordCountInput(BaseModel):
    """Input schema for the word count tool."""
    text: str


class SearchInput(BaseModel):
    """Input schema for the search tool."""
    query: str
    max_results: int = 3


def calculator(operation: str, a: float, b: float) -> str:
    """A simple calculator. Returns the result as a string."""
    ops = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b if b != 0 else None,
    }
    fn = ops.get(operation)
    if fn is None:
        return f"Error: unknown operation '{operation}'"
    result = fn()
    if result is None:
        return "Error: division by zero"
    return str(result)


def word_count(text: str) -> str:
    """Count words in text. Returns the count as a string."""
    count = len(text.split())
    return f"{count} words"


def fake_search(query: str, max_results: int = 3) -> str:
    """Simulated search tool. Returns fake results for demonstration."""
    return (
        f"Search results for '{query}' (top {max_results}):\n"
        f"1. Wikipedia article about {query}\n"
        f"2. Research paper: 'A Survey of {query}'\n"
        f"3. Blog post: 'Understanding {query} in Practice'"
    )


# --- Tool Registry ---


class ToolEntry:
    """A registered tool with its function, schema, and validator."""

    def __init__(
        self,
        name: str,
        description: str,
        fn: Callable[..., str],
        input_model: type[BaseModel],
    ):
        self.name = name
        self.description = description
        self.fn = fn
        self.input_model = input_model


class ToolRegistry:
    """Registry of available tools.

    The registry serves two purposes:
    1. Generate schemas that tell the model what tools exist
    2. Validate and execute tool calls from the model
    """

    def __init__(self):
        self._tools: dict[str, ToolEntry] = {}

    def register(
        self,
        name: str,
        description: str,
        fn: Callable[..., str],
        input_model: type[BaseModel],
    ) -> None:
        self._tools[name] = ToolEntry(name, description, fn, input_model)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> list[ToolSchema]:
        """Generate schemas for the model. This is what goes in the API call."""
        schemas = []
        for entry in self._tools.values():
            params = []
            json_schema = entry.input_model.model_json_schema()
            properties = json_schema.get("properties", {})
            required_fields = json_schema.get("required", [])

            for field_name, field_info in properties.items():
                field_type = field_info.get("type", "string")
                # Handle enum types
                if "enum" in field_info:
                    field_type = "string"
                params.append(
                    ToolParameter(
                        name=field_name,
                        type=field_type,
                        description=field_info.get("description", field_info.get("title", "")),
                        required=field_name in required_fields,
                        enum=field_info.get("enum"),
                    )
                )

            schemas.append(
                ToolSchema(
                    name=entry.name,
                    description=entry.description,
                    parameters=params,
                )
            )
        return schemas

    def get(self, name: str) -> ToolEntry | None:
        return self._tools.get(name)


def execute_tool_call(
    registry: ToolRegistry,
    tool_name: str,
    arguments: dict[str, Any],
) -> str:
    """Execute a tool call with validation.

    This is where Pydantic earns its keep. The model WILL hallucinate
    arguments -- wrong types, missing fields, invented parameters.
    Validation catches these before they reach your function.
    """
    entry = registry.get(tool_name)
    if entry is None:
        return f"Error: unknown tool '{tool_name}'. Available: {registry.list_tools()}"

    # Validate with Pydantic
    try:
        validated = entry.input_model(**arguments)
    except Exception as e:
        return f"Error: validation failed for tool '{tool_name}': {e}"

    # Execute
    try:
        return entry.fn(**validated.model_dump())
    except Exception as e:
        return f"Error: tool '{tool_name}' raised: {e}"


def create_default_registry() -> ToolRegistry:
    """Create a registry with the standard demo tools."""
    registry = ToolRegistry()
    registry.register(
        "calculator",
        "Perform arithmetic operations: add, subtract, multiply, divide",
        calculator,
        CalculatorInput,
    )
    registry.register(
        "word_count",
        "Count the number of words in a text string",
        word_count,
        WordCountInput,
    )
    registry.register(
        "search",
        "Search for information on a topic. Returns top results.",
        fake_search,
        SearchInput,
    )
    return registry


# --- Runnable demo ---

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    from src.shared.model_client import create_client
    from src.shared.types import CompletionRequest, Message, Role

    load_dotenv()

    async def main():
        provider = os.getenv("MODEL_PROVIDER", "openai")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
        model = os.getenv("MODEL_NAME", "gpt-4o")
        client = create_client(provider=provider, api_key=api_key, model_name=model)

        registry = create_default_registry()
        schemas = registry.get_schemas()

        print("--- Registered Tools ---")
        for s in schemas:
            print(f"  {s.name}: {s.description}")

        print("\n--- Tool Call: 'What is 15 * 7?' ---")
        request = CompletionRequest(
            messages=[
                Message(role=Role.SYSTEM, content="Use tools to answer questions. Do not calculate yourself."),
                Message(role=Role.USER, content="What is 15 * 7?"),
            ],
            tools=schemas,
            temperature=0.0,
            max_tokens=256,
        )
        response = await client.complete(request)

        if response.tool_calls:
            for tc in response.tool_calls:
                print(f"  Model wants to call: {tc.name}({tc.arguments})")
                result = execute_tool_call(registry, tc.name, tc.arguments)
                print(f"  Result: {result}")
        else:
            print(f"  Model responded with text: {response.content}")

        # Demonstrate validation catching bad input
        print("\n--- Validation Demo ---")
        bad_result = execute_tool_call(registry, "calculator", {"operation": "modulo", "a": 1, "b": 2})
        print(f"  Bad operation: {bad_result}")

        unknown_result = execute_tool_call(registry, "nonexistent", {})
        print(f"  Unknown tool: {unknown_result}")

    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ch00/test_tool_use.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/ch00/tool_use.py tests/unit/ch00/test_tool_use.py
git commit -m "feat: add section 0b code -- tool use module with registry and validation"
```

---

## Task 4: Section 0c Code -- Raw Agent Module

**Files:**
- Create: `src/ch00/raw_agent.py`
- Create: `tests/unit/ch00/test_raw_agent.py`

- [ ] **Step 1: Write tests for raw_agent**

```python
"""Tests for the raw agent module (Section 0c).

Tests the agent loop, budget enforcement, and tool execution.
"""

import asyncio
import pytest
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse, TokenUsage, ToolCall
from src.ch00.raw_agent import Agent, AgentResult
from src.ch00.tool_use import create_default_registry


def _mock_text_response(content: str) -> CompletionResponse:
    return CompletionResponse(
        content=content,
        model="mock",
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
    )


def _mock_tool_response(name: str, args: dict) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="tc_1", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
    )


@pytest.mark.asyncio
async def test_agent_returns_text_response_immediately():
    """If the model returns text (no tool calls), agent should stop."""
    client = MockClient(responses=[_mock_text_response("The answer is 42.")])
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)

    result = await agent.run("What is the answer?")
    assert result.answer == "The answer is 42."
    assert result.steps == 1
    assert result.total_tokens > 0


@pytest.mark.asyncio
async def test_agent_executes_tool_then_responds():
    """Agent should call tool, get result, then produce final answer."""
    client = MockClient(
        responses=[
            _mock_tool_response("calculator", {"operation": "add", "a": 2, "b": 3}),
            _mock_text_response("2 + 3 = 5"),
        ]
    )
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)

    result = await agent.run("What is 2 + 3?")
    assert result.answer == "2 + 3 = 5"
    assert result.steps == 2


@pytest.mark.asyncio
async def test_agent_respects_budget():
    """Agent should stop at max_steps even if model keeps calling tools."""
    # Model always calls search -- never produces a final answer
    responses = [
        _mock_tool_response("search", {"query": f"attempt {i}"})
        for i in range(10)
    ]
    client = MockClient(responses=responses)
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=3)

    result = await agent.run("Find everything about everything")
    assert result.steps <= 3
    assert result.budget_exhausted is True


@pytest.mark.asyncio
async def test_agent_handles_unknown_tool():
    """If model calls a tool that doesn't exist, agent should recover."""
    client = MockClient(
        responses=[
            _mock_tool_response("nonexistent_tool", {"foo": "bar"}),
            _mock_text_response("I couldn't find the tool, but here's my answer."),
        ]
    )
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)

    result = await agent.run("Do something")
    assert result.answer is not None
    assert result.steps == 2


@pytest.mark.asyncio
async def test_agent_trace_records_steps():
    """Agent should record a trace of all steps."""
    client = MockClient(
        responses=[
            _mock_tool_response("calculator", {"operation": "multiply", "a": 6, "b": 7}),
            _mock_text_response("6 * 7 = 42"),
        ]
    )
    registry = create_default_registry()
    agent = Agent(client=client, registry=registry, max_steps=5)

    result = await agent.run("What is 6 * 7?")
    assert len(result.trace) == 2
    assert result.trace[0]["type"] == "tool_call"
    assert result.trace[1]["type"] == "response"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ch00/test_raw_agent.py -v`
Expected: FAIL with import errors

- [ ] **Step 3: Implement raw_agent.py**

```python
"""Raw Agent -- Section 0c code companion.

A complete agent in ~100 lines. No framework. No magic.
Every line is here because it does something you need to understand.

The architecture:
    while budget_remaining:
        observation = assemble_context(history)
        response = call_llm(observation)
        if response.has_tool_calls:
            result = execute_tool(response.tool_calls[0])
            history.append(tool_call + result)
        else:
            return response.content  # Final answer

That's it. Everything else is error handling and logging.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.shared.model_client import ModelClient
from src.shared.types import CompletionRequest, Message, Role
from src.ch00.tool_use import ToolRegistry, execute_tool_call


@dataclass
class AgentResult:
    """What the agent returns after a run."""
    answer: str | None
    steps: int
    total_tokens: int
    total_cost_estimate: float
    elapsed_ms: float
    budget_exhausted: bool
    trace: list[dict] = field(default_factory=list)


SYSTEM_PROMPT = """You are a helpful research assistant with access to tools.

Use tools when you need to calculate, search, or look up information.
When you have enough information to answer the user's question, respond
with your final answer as plain text (do not call a tool).

Be concise and cite your sources when applicable."""


class Agent:
    """A minimal agent with an observe-think-act loop.

    This is the entire agent architecture. Everything else --
    every framework, every SDK -- is a wrapper around this pattern.
    """

    def __init__(
        self,
        client: ModelClient,
        registry: ToolRegistry,
        max_steps: int = 5,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.client = client
        self.registry = registry
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    async def run(self, user_query: str) -> AgentResult:
        """Run the agent loop until it produces an answer or exhausts its budget."""
        start = time.monotonic()
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=self.system_prompt),
            Message(role=Role.USER, content=user_query),
        ]
        schemas = self.registry.get_schemas()
        total_tokens = 0
        trace: list[dict] = []

        for step in range(1, self.max_steps + 1):
            # OBSERVE + THINK: send current context to the model
            request = CompletionRequest(
                messages=messages,
                tools=schemas if schemas else None,
                temperature=0.0,
                max_tokens=1024,
            )
            response = await self.client.complete(request)
            total_tokens += response.usage.total_tokens

            # ACT: did the model call a tool, or produce an answer?
            if response.tool_calls:
                tc = response.tool_calls[0]  # Handle one tool call per step
                result = execute_tool_call(self.registry, tc.name, tc.arguments)

                trace.append({
                    "step": step,
                    "type": "tool_call",
                    "tool": tc.name,
                    "arguments": tc.arguments,
                    "result": result,
                    "tokens": response.usage.total_tokens,
                })

                # Add tool call and result to conversation history
                messages.append(Message(
                    role=Role.ASSISTANT,
                    content=f"[Calling tool: {tc.name}({tc.arguments})]",
                ))
                messages.append(Message(
                    role=Role.TOOL,
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.name,
                ))
            else:
                # Model produced a final answer
                trace.append({
                    "step": step,
                    "type": "response",
                    "content": response.content,
                    "tokens": response.usage.total_tokens,
                })

                elapsed = (time.monotonic() - start) * 1000
                return AgentResult(
                    answer=response.content,
                    steps=step,
                    total_tokens=total_tokens,
                    total_cost_estimate=0.0,
                    elapsed_ms=elapsed,
                    budget_exhausted=False,
                    trace=trace,
                )

        # Budget exhausted -- return best effort
        elapsed = (time.monotonic() - start) * 1000
        last_content = None
        for msg in reversed(messages):
            if msg.role == Role.TOOL:
                last_content = f"[Budget exhausted after {self.max_steps} steps. Last tool result: {msg.content}]"
                break

        return AgentResult(
            answer=last_content or f"[Budget exhausted after {self.max_steps} steps]",
            steps=self.max_steps,
            total_tokens=total_tokens,
            total_cost_estimate=0.0,
            elapsed_ms=elapsed,
            budget_exhausted=True,
            trace=trace,
        )


# --- Runnable demo ---

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    from src.shared.model_client import create_client
    from src.ch00.tool_use import create_default_registry

    load_dotenv()

    async def main():
        provider = os.getenv("MODEL_PROVIDER", "openai")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
        model = os.getenv("MODEL_NAME", "gpt-4o")
        client = create_client(provider=provider, api_key=api_key, model_name=model)
        registry = create_default_registry()

        agent = Agent(client=client, registry=registry, max_steps=5)

        queries = [
            "What is 15 * 7 + 3?",
            "Search for information about agentic AI and summarize what you find.",
            "How many words are in the sentence 'The quick brown fox jumps over the lazy dog'?",
        ]

        for query in queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")

            result = await agent.run(query)

            print(f"\nAnswer: {result.answer}")
            print(f"Steps: {result.steps}")
            print(f"Tokens: {result.total_tokens}")
            print(f"Time: {result.elapsed_ms:.0f}ms")
            print(f"Budget exhausted: {result.budget_exhausted}")

            print("\nTrace:")
            for entry in result.trace:
                if entry["type"] == "tool_call":
                    print(f"  Step {entry['step']}: {entry['tool']}({entry['arguments']}) -> {entry['result'][:80]}")
                else:
                    content = entry['content'] or ''
                    print(f"  Step {entry['step']}: [answer] {content[:80]}")

    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ch00/test_raw_agent.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/ch00/raw_agent.py tests/unit/ch00/test_raw_agent.py
git commit -m "feat: add section 0c code -- raw agent with loop, budget, and tracing"
```

---

## Task 5: Section 0d Code -- Framework Agents and Eval

**Files:**
- Create: `src/ch00/adk_agent.py`
- Create: `src/ch00/langchain_agent.py`
- Create: `src/ch00/eval_compare.py`
- Create: `tests/unit/ch00/test_eval_compare.py`

- [ ] **Step 1: Write eval tests**

```python
"""Tests for the eval comparison module (Section 0d).

Tests scoring logic -- does not require API keys or frameworks.
"""

from src.ch00.eval_compare import score_answer, EvalResult


def test_score_answer_exact_match():
    result = score_answer(
        query="What is 2+2?",
        expected="4",
        actual="4",
    )
    assert result.score == 1.0


def test_score_answer_contains_expected():
    result = score_answer(
        query="What is 2+2?",
        expected="4",
        actual="The answer is 4.",
    )
    assert result.score >= 0.5


def test_score_answer_wrong():
    result = score_answer(
        query="What is 2+2?",
        expected="4",
        actual="The answer is 7.",
    )
    assert result.score == 0.0


def test_score_answer_case_insensitive():
    result = score_answer(
        query="What color is the sky?",
        expected="blue",
        actual="Blue",
    )
    assert result.score >= 0.5


def test_eval_result_fields():
    result = EvalResult(
        query="test",
        expected="expected",
        actual="actual",
        score=0.5,
        tokens=100,
        latency_ms=500.0,
        cost_estimate=0.001,
    )
    assert result.query == "test"
    assert result.score == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ch00/test_eval_compare.py -v`
Expected: FAIL with import errors

- [ ] **Step 3: Implement eval_compare.py**

```python
"""Eval Comparison -- Section 0d code companion.

A simple evaluation harness that runs the same queries against
multiple agent implementations and compares results.

This is not a production eval system. It's the minimum viable eval
that demonstrates the concept: test queries, expected answers,
automated scoring, side-by-side comparison.

Chapter 6 goes deep on production evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvalResult:
    """Result of evaluating a single query against one implementation."""
    query: str
    expected: str
    actual: str
    score: float  # 0.0 to 1.0
    tokens: int
    latency_ms: float
    cost_estimate: float


def score_answer(query: str, expected: str, actual: str) -> EvalResult:
    """Score an answer against the expected answer.

    Simple substring matching -- not production-grade, but enough
    to demonstrate the concept. Production eval uses rubrics and
    LLM judges (see Chapter 6).
    """
    expected_lower = expected.lower().strip()
    actual_lower = actual.lower().strip()

    if expected_lower == actual_lower:
        score = 1.0
    elif expected_lower in actual_lower:
        score = 0.8
    else:
        score = 0.0

    return EvalResult(
        query=query,
        expected=expected,
        actual=actual,
        score=score,
        tokens=0,
        latency_ms=0.0,
        cost_estimate=0.0,
    )


# Test queries shared across all three implementations
TEST_QUERIES = [
    {
        "query": "What is 15 * 7?",
        "expected": "105",
    },
    {
        "query": "How many words are in 'the quick brown fox jumps over the lazy dog'?",
        "expected": "9",
    },
    {
        "query": "Search for agentic AI and tell me the first result.",
        "expected": "Wikipedia article about agentic AI",
    },
    {
        "query": "What is 100 / 4 + 10?",
        "expected": "35",
    },
    {
        "query": "Search for machine learning and count the words in the first result title.",
        "expected": "Wikipedia article about machine learning",
    },
]


def print_comparison(results: dict[str, list[EvalResult]]) -> None:
    """Print a side-by-side comparison table."""
    implementations = list(results.keys())

    print(f"\n{'='*80}")
    print("EVALUATION COMPARISON")
    print(f"{'='*80}")

    # Per-query results
    for i, test in enumerate(TEST_QUERIES):
        print(f"\nQuery {i+1}: {test['query']}")
        print(f"Expected: {test['expected']}")
        for impl_name in implementations:
            if i < len(results[impl_name]):
                r = results[impl_name][i]
                print(f"  {impl_name:>12}: score={r.score:.1f}  tokens={r.tokens:>5}  "
                      f"latency={r.latency_ms:>6.0f}ms  cost=${r.cost_estimate:.5f}")

    # Summary
    print(f"\n{'-'*80}")
    print("SUMMARY")
    print(f"{'-'*80}")
    header = f"{'Implementation':>15} | {'Avg Score':>10} | {'Total Tokens':>12} | {'Avg Latency':>12} | {'Total Cost':>10}"
    print(header)
    print("-" * len(header))

    for impl_name in implementations:
        impl_results = results[impl_name]
        if not impl_results:
            continue
        avg_score = sum(r.score for r in impl_results) / len(impl_results)
        total_tokens = sum(r.tokens for r in impl_results)
        avg_latency = sum(r.latency_ms for r in impl_results) / len(impl_results)
        total_cost = sum(r.cost_estimate for r in impl_results)
        print(f"{impl_name:>15} | {avg_score:>10.2f} | {total_tokens:>12} | {avg_latency:>10.0f}ms | ${total_cost:>9.5f}")


# --- Runnable demo ---

if __name__ == "__main__":
    import asyncio
    import os
    import time
    from dotenv import load_dotenv
    from src.shared.model_client import create_client
    from src.ch00.raw_agent import Agent
    from src.ch00.tool_use import create_default_registry
    from src.ch00.llm_basics import estimate_cost

    load_dotenv()

    async def main():
        provider = os.getenv("MODEL_PROVIDER", "openai")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
        model = os.getenv("MODEL_NAME", "gpt-4o")
        client = create_client(provider=provider, api_key=api_key, model_name=model)
        registry = create_default_registry()

        # Run raw agent against all test queries
        raw_results: list[EvalResult] = []
        agent = Agent(client=client, registry=registry, max_steps=5)

        print("Running raw agent evaluation...")
        for test in TEST_QUERIES:
            result = await agent.run(test["query"])
            scored = score_answer(test["query"], test["expected"], result.answer or "")
            scored.tokens = result.total_tokens
            scored.latency_ms = result.elapsed_ms
            scored.cost_estimate = estimate_cost(
                result.total_tokens // 2, result.total_tokens // 2, model
            )
            raw_results.append(scored)

        print_comparison({"raw": raw_results})
        print("\nTo compare with ADK and LangChain, run with --all flag")
        print("(requires: pip install -e '.[foundations]')")

    asyncio.run(main())
```

- [ ] **Step 4: Implement adk_agent.py (stub with documentation)**

```python
"""ADK Agent -- Section 0d code companion.

The same research agent rebuilt with Google ADK.
~40 lines vs ~100 lines raw.

Requires: pip install -e ".[foundations]"

What ADK gives you:
- Tool registration with decorators
- Agent loop management
- Built-in tracing and observability
- Eval integration

What ADK hides:
- Context assembly details
- The observe-think-act loop internals
- Token management
"""

from __future__ import annotations

# ADK import -- requires the foundations extra
try:
    from google.adk.agents import Agent as ADKAgent
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


def calculator(operation: str, a: float, b: float) -> str:
    """Perform arithmetic: add, subtract, multiply, divide."""
    ops = {"add": a + b, "subtract": a - b, "multiply": a * b, "divide": a / b if b != 0 else None}
    result = ops.get(operation)
    if result is None:
        return f"Error: unknown operation or division by zero"
    return str(result)


def word_count(text: str) -> str:
    """Count words in text."""
    return f"{len(text.split())} words"


def search(query: str) -> str:
    """Search for information on a topic."""
    return (
        f"Search results for '{query}':\n"
        f"1. Wikipedia article about {query}\n"
        f"2. Research paper: 'A Survey of {query}'\n"
        f"3. Blog post: 'Understanding {query} in Practice'"
    )


def create_adk_agent() -> "ADKAgent | None":
    """Create the research agent using Google ADK."""
    if not ADK_AVAILABLE:
        print("Google ADK not installed. Run: pip install -e '.[foundations]'")
        return None

    agent = ADKAgent(
        name="research_assistant",
        model="gemini-2.0-flash",
        description="A helpful research assistant with calculator, word count, and search tools.",
        instruction=(
            "Use tools when you need to calculate, search, or count words. "
            "When you have enough information, respond with your final answer."
        ),
        tools=[calculator, word_count, search],
    )
    return agent


if __name__ == "__main__":
    if not ADK_AVAILABLE:
        print("Google ADK not installed. Run: pip install -e '.[foundations]'")
        print("Then run this script again.")
    else:
        print("ADK agent created successfully. Use eval_compare.py to run evaluation.")
```

- [ ] **Step 5: Implement langchain_agent.py (stub with documentation)**

```python
"""LangChain Agent -- Section 0d code companion.

The same research agent rebuilt with LangChain.
~35 lines vs ~100 lines raw.

Requires: pip install -e ".[foundations]"

What LangChain gives you:
- Huge ecosystem of integrations
- Chain composition patterns
- Community tools and connectors

What LangChain hides:
- The actual control flow (chains are opaque)
- Token accounting details
- Debugging requires reading framework source
"""

from __future__ import annotations

try:
    from langchain_core.tools import tool as langchain_tool
    from langchain_anthropic import ChatAnthropic
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


if LANGCHAIN_AVAILABLE:
    @langchain_tool
    def calculator(operation: str, a: float, b: float) -> str:
        """Perform arithmetic: add, subtract, multiply, divide."""
        ops = {"add": a + b, "subtract": a - b, "multiply": a * b, "divide": a / b if b != 0 else None}
        result = ops.get(operation)
        if result is None:
            return "Error: unknown operation or division by zero"
        return str(result)

    @langchain_tool
    def word_count(text: str) -> str:
        """Count words in text."""
        return f"{len(text.split())} words"

    @langchain_tool
    def search(query: str) -> str:
        """Search for information on a topic."""
        return (
            f"Search results for '{query}':\n"
            f"1. Wikipedia article about {query}\n"
            f"2. Research paper: 'A Survey of {query}'\n"
            f"3. Blog post: 'Understanding {query} in Practice'"
        )


def create_langchain_agent():
    """Create the research agent using LangChain."""
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not installed. Run: pip install -e '.[foundations]'")
        return None

    import os
    from langchain_anthropic import ChatAnthropic
    from langgraph.prebuilt import create_react_agent

    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )

    tools = [calculator, word_count, search]
    agent = create_react_agent(model, tools)
    return agent


if __name__ == "__main__":
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not installed. Run: pip install -e '.[foundations]'")
        print("Then run this script again.")
    else:
        print("LangChain agent created successfully. Use eval_compare.py to run evaluation.")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/ch00/test_eval_compare.py -v`
Expected: All 5 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/ch00/eval_compare.py src/ch00/adk_agent.py src/ch00/langchain_agent.py tests/unit/ch00/test_eval_compare.py
git commit -m "feat: add section 0d code -- framework agents and eval comparison"
```

---

## Task 6: Section 0a Chapter Text

**Files:**
- Create: `docs/book/00a-how-llms-work.md`

- [ ] **Step 1: Write section 0a chapter text**

Write the full ~3,000 word chapter following the spec:
- Open with "You don't need to understand attention heads..."
- Cover: API contract, tokens, context window, hallucination, temperature, structured output
- Voice: direct, warm, opinionated per spec voice rules
- Include inline code examples referencing `src/ch00/llm_basics.py`
- Include figure references to the 4 SVG diagrams (api-contract.svg, context-window-bucket.svg, token-cost-calculator.svg, hallucination-mental-model.svg)
- Use MkDocs admonition blocks for "what just happened" callouts
- Close with the specified bridge paragraph
- Link to companion project `project/llm-explorer/`

- [ ] **Step 2: Verify markdown renders**

Run: `mkdocs serve` and check http://localhost:8000/book/00a-how-llms-work/
(Diagrams won't exist yet -- verify text renders correctly)

- [ ] **Step 3: Commit**

```bash
git add docs/book/00a-how-llms-work.md
git commit -m "feat: add section 0a chapter text -- How LLMs Actually Work"
```

---

## Task 7: Section 0b Chapter Text

**Files:**
- Create: `docs/book/00b-api-to-tools.md`

- [ ] **Step 1: Write section 0b chapter text**

Write the full ~3,500 word chapter following the spec:
- Open with "In the last section, the model could only talk..."
- Cover: prompting as engineering, few-shot examples, function calling, schema validation, multiple tools, single-turn ceiling
- Include inline code examples referencing `src/ch00/tool_use.py`
- Include figure references to 3 SVGs
- MkDocs admonition callouts
- Close with bridge to 0c
- Link to companion project `project/tool-using-assistant/`

- [ ] **Step 2: Verify markdown renders**

Run: `mkdocs serve` and verify

- [ ] **Step 3: Commit**

```bash
git add docs/book/00b-api-to-tools.md
git commit -m "feat: add section 0b chapter text -- From API Calls to Tool Use"
```

---

## Task 8: Section 0c Chapter Text

**Files:**
- Create: `docs/book/00c-first-agent.md`

- [ ] **Step 1: Write section 0c chapter text**

Write the full ~3,000 word chapter following the spec:
- Open with "You have a system that can call tools..."
- Cover: the loop in 20 lines, step-by-step build, real task demo, failure modes, guardrails, full code
- Include inline code from `src/ch00/raw_agent.py`
- Include figure references to 4 SVGs
- Close with bridge to Chapter 1 (the key bridge in the funnel)
- Link to companion project `project/research-agent/`

- [ ] **Step 2: Verify markdown renders**

Run: `mkdocs serve` and verify

- [ ] **Step 3: Commit**

```bash
git add docs/book/00c-first-agent.md
git commit -m "feat: add section 0c chapter text -- Your First Agent, No Framework"
```

---

## Task 9: Section 0d Chapter Text

**Files:**
- Create: `docs/book/00d-frameworks.md`

- [ ] **Step 1: Write section 0d chapter text**

Write the full ~3,000 word chapter following the spec:
- Open with "You built an agent from scratch..."
- Cover: why frameworks exist, ADK walkthrough, LangChain comparison, three-way comparison table, honest take, eval as mindset
- Include inline code from `src/ch00/adk_agent.py` and `src/ch00/langchain_agent.py`
- Include the comparison table from the spec
- Include figure references to 3 SVGs
- Close with the spec's bridge paragraph to Chapter 1
- Amazon CTA at the end

- [ ] **Step 2: Verify markdown renders**

Run: `mkdocs serve` and verify

- [ ] **Step 3: Commit**

```bash
git add docs/book/00d-frameworks.md
git commit -m "feat: add section 0d chapter text -- The Same Agent, With a Framework"
```

---

## Task 10: SVG Diagrams -- Section 0a (4 diagrams)

**Files:**
- Create: `docs/diagrams/api-contract.svg`
- Create: `docs/diagrams/context-window-bucket.svg`
- Create: `docs/diagrams/token-cost-calculator.svg`
- Create: `docs/diagrams/hallucination-mental-model.svg`

- [ ] **Step 1: Create api-contract.svg**

Simple flow diagram: "You send text -> API -> You get text back." Three boxes, arrows. Layers showing agents/RAG/chains built on top. Match existing diagram style (IBM Plex Sans font, clean lines, blue monotone palette).

- [ ] **Step 2: Create context-window-bucket.svg**

Stacked bar showing context window as a fixed bucket: system prompt, few-shot, retrieved docs, history, tool results. Color-coded segments. Shows overflow zone.

- [ ] **Step 3: Create token-cost-calculator.svg**

Annotated table visual: prompt tokens, completion tokens, cost per call, calls per task. Concrete dollar amounts.

- [ ] **Step 4: Create hallucination-mental-model.svg**

Two-panel: Left "What you think" (checkmark, fact-checking). Right "What actually happens" (dice, predicting next token). Green/red color coding.

- [ ] **Step 5: Commit**

```bash
git add docs/diagrams/api-contract.svg docs/diagrams/context-window-bucket.svg docs/diagrams/token-cost-calculator.svg docs/diagrams/hallucination-mental-model.svg
git commit -m "feat: add section 0a diagrams (4 SVGs)"
```

---

## Task 11: SVG Diagrams -- Section 0b (3 diagrams)

**Files:**
- Create: `docs/diagrams/function-calling-cycle.svg`
- Create: `docs/diagrams/tool-selection-comparison.svg`
- Create: `docs/diagrams/single-turn-ceiling.svg`

- [ ] **Step 1: Create function-calling-cycle.svg**

Circular flow: Your code -> schema + prompt -> Model -> "call this function" JSON -> Your code executes -> result -> Model.

- [ ] **Step 2: Create tool-selection-comparison.svg**

Two-panel: Left (green) model picks correct tool. Right (red) model hallucinates arguments.

- [ ] **Step 3: Create single-turn-ceiling.svg**

Flow diagram with a wall: tool-using system hits "can't iterate" ceiling. Arrow pointing right to "agents start here."

- [ ] **Step 4: Commit**

```bash
git add docs/diagrams/function-calling-cycle.svg docs/diagrams/tool-selection-comparison.svg docs/diagrams/single-turn-ceiling.svg
git commit -m "feat: add section 0b diagrams (3 SVGs)"
```

---

## Task 12: SVG Diagrams -- Sections 0c and 0d (7 diagrams)

**Files:**
- Create: `docs/diagrams/agent-loop-foundations.svg`
- Create: `docs/diagrams/agent-trace-waterfall.svg`
- Create: `docs/diagrams/three-failure-modes.svg`
- Create: `docs/diagrams/before-after-guardrails.svg`
- Create: `docs/diagrams/framework-layers.svg`
- Create: `docs/diagrams/three-way-comparison.svg`
- Create: `docs/diagrams/framework-decision-tree.svg`

- [ ] **Step 1: Create 0c diagrams (4 SVGs)**

Agent loop (circular observe-think-act), trace waterfall (vertical timeline with tokens/cost), three failure modes (3-panel red), before/after guardrails (split green/red).

- [ ] **Step 2: Create 0d diagrams (3 SVGs)**

Framework layers (stacked: raw -> ADK -> LangChain with green/amber), three-way comparison dashboard (metrics cards), decision flowchart (simple tree).

- [ ] **Step 3: Commit**

```bash
git add docs/diagrams/agent-loop-foundations.svg docs/diagrams/agent-trace-waterfall.svg docs/diagrams/three-failure-modes.svg docs/diagrams/before-after-guardrails.svg docs/diagrams/framework-layers.svg docs/diagrams/three-way-comparison.svg docs/diagrams/framework-decision-tree.svg
git commit -m "feat: add sections 0c and 0d diagrams (7 SVGs)"
```

---

## Task 13: Companion Projects

**Files:**
- Create: `project/llm-explorer/README.md`, `project/llm-explorer/src/*.py`
- Create: `project/tool-using-assistant/README.md`, `project/tool-using-assistant/src/*.py`
- Create: `project/research-agent/README.md`, `project/research-agent/src/*.py`, `project/research-agent/evals/*`
- Create: `project/framework-comparison/README.md`, `project/framework-comparison/src/*.py`, `project/framework-comparison/evals/*`
- Create: `docs/projects/llm-explorer.md`, `docs/projects/tool-using-assistant.md`, `docs/projects/research-agent.md`, `docs/projects/framework-comparison.md`

- [ ] **Step 1: Create llm-explorer project**

README with project description, `src/` files implementing token counting experiments, context overflow demo, structured output experiments. Docs page for MkDocs site.

- [ ] **Step 2: Create tool-using-assistant project**

README, `src/` files with multi-tool assistant (calculator, search, file reader), validation examples. Docs page.

- [ ] **Step 3: Create research-agent project**

README, `src/` with expanded agent, `evals/` with test_queries.yaml and run_eval.py. Docs page.

- [ ] **Step 4: Create framework-comparison project**

README, `src/` with all three implementations, `evals/` with shared test queries, rubric, and run_eval.py that outputs comparison table. Docs page.

- [ ] **Step 5: Commit**

```bash
git add project/llm-explorer/ project/tool-using-assistant/ project/research-agent/ project/framework-comparison/ docs/projects/llm-explorer.md docs/projects/tool-using-assistant.md docs/projects/research-agent.md docs/projects/framework-comparison.md
git commit -m "feat: add four companion projects for Foundations sections"
```

---

## Task 14: Site Integration

**Files:**
- Modify: `mkdocs.yml`
- Modify: `docs/index.md`
- Modify: `docs/book/index.md`
- Modify: `README.md`
- Modify: `docs/roadmap.md`

- [ ] **Step 1: Update mkdocs.yml navigation**

Replace the nav section with the updated structure from the spec, adding Foundations sub-section before Chapters, and new project pages under Projects.

- [ ] **Step 2: Update docs/index.md**

Add a "New to agentic AI?" callout at the top pointing to Foundations. Position it before the existing chapters table.

- [ ] **Step 3: Update docs/book/index.md**

Add Foundations section before the chapter list. Brief description of each foundation section with links.

- [ ] **Step 4: Update README.md**

Add "New to agentic AI? Start with the Foundations" section near the top, before the "The Book" section. Link to each foundation section.

- [ ] **Step 5: Update docs/roadmap.md**

Add Foundations as shipped content.

- [ ] **Step 6: Verify site builds**

Run: `mkdocs build --strict`
Expected: Build succeeds with no errors

- [ ] **Step 7: Commit**

```bash
git add mkdocs.yml docs/index.md docs/book/index.md README.md docs/roadmap.md
git commit -m "feat: integrate Foundations into site navigation and landing pages"
```

---

## Task 15: Final Verification

- [ ] **Step 1: Run all tests**

Run: `pytest tests/unit/ch00/ -v`
Expected: All tests pass (22+ tests across 4 test files)

- [ ] **Step 2: Run lint**

Run: `ruff check src/ch00/ && ruff format --check src/ch00/`
Expected: No errors

- [ ] **Step 3: Build site**

Run: `mkdocs build --strict`
Expected: Clean build

- [ ] **Step 4: Manual review**

Run: `mkdocs serve` and verify:
- Foundations sections appear in nav before chapters
- All 4 foundation sections render correctly
- Code examples are properly formatted
- Diagram references point to existing files
- Amazon links work
- Reading path flows: Foundations -> Chapter 1 -> Amazon CTA

- [ ] **Step 5: Final commit if any fixes needed**

```bash
git add -A && git commit -m "fix: final polish for Foundations pre-read"
```
