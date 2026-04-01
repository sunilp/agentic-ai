"""Tool use module (Section 0b).

Demonstrates the mechanics of structured tool calling:
how to define tools with Pydantic input validation, register them in a
registry, derive ToolSchema objects for the model, and execute tool calls
with safe argument validation before dispatch.
"""

from __future__ import annotations

import asyncio
import json
from enum import StrEnum
from typing import Any, Callable, Type

from pydantic import BaseModel, Field, ValidationError

from src.shared.model_client import MockClient
from src.shared.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    Role,
    ToolCall,
    ToolParameter,
    ToolSchema,
    TokenUsage,
)


# ---------------------------------------------------------------------------
# Enums and input models
# ---------------------------------------------------------------------------


class Operation(StrEnum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"


class CalculatorInput(BaseModel):
    """Input schema for the calculator tool."""

    operation: Operation
    a: float
    b: float


class WordCountInput(BaseModel):
    """Input schema for the word count tool."""

    text: str


class SearchInput(BaseModel):
    """Input schema for the fake search tool."""

    query: str
    max_results: int = Field(default=3, ge=1, le=10)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def calculator(operation: str, a: float, b: float) -> str:
    """Perform a basic arithmetic operation and return the result as a string.

    Args:
        operation: One of add, subtract, multiply, divide.
        a:         Left operand.
        b:         Right operand.

    Returns:
        The result as a string, or an error message on division by zero.
    """
    op = Operation(operation)
    if op == Operation.ADD:
        return str(float(a + b))
    elif op == Operation.SUBTRACT:
        return str(float(a - b))
    elif op == Operation.MULTIPLY:
        return str(float(a * b))
    elif op == Operation.DIVIDE:
        if b == 0:
            return "Error: division by zero"
        return str(float(a / b))
    # Should be unreachable given Operation enum, but satisfies type checkers.
    return f"Error: unknown operation '{operation}'"  # pragma: no cover


def word_count(text: str) -> str:
    """Count the number of words in *text*.

    Args:
        text: Input text to count.

    Returns:
        A human-readable string with the word count.
    """
    count = len(text.split())
    return f"Word count: {count}"


def fake_search(query: str, max_results: int = 3) -> str:
    """Return fake search results for demonstration purposes.

    Args:
        query:       Search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        A JSON string representing mock search results.
    """
    results = [
        {"title": f"Result {i + 1} for '{query}'", "url": f"https://example.com/{i + 1}"}
        for i in range(max_results)
    ]
    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------


class Tool:
    """An entry in the tool registry.

    Holds the callable function and its associated Pydantic input model so
    arguments can be validated before dispatch.
    """

    def __init__(
        self,
        name: str,
        description: str,
        fn: Callable[..., str],
        input_model: Type[BaseModel],
    ) -> None:
        self.name = name
        self.description = description
        self.fn = fn
        self.input_model = input_model

    def to_schema(self) -> ToolSchema:
        """Derive a ToolSchema from the Pydantic model's field definitions."""
        parameters: list[ToolParameter] = []
        model_fields = self.input_model.model_fields

        for field_name, field_info in model_fields.items():
            annotation = field_info.annotation

            # Resolve the JSON-schema type string.
            type_str = _python_type_to_json_type(annotation)

            # Collect enum values if the annotation is a StrEnum subclass.
            enum_values: list[str] | None = None
            origin = getattr(annotation, "__origin__", None)
            if origin is None and isinstance(annotation, type) and issubclass(annotation, StrEnum):
                enum_values = [e.value for e in annotation]  # type: ignore[attr-defined]

            is_required = field_info.default is field_info.default_factory is None  # type: ignore[comparison-overlap]
            # Simpler: a field is required when it has no default value.
            is_required = field_info.is_required()

            parameters.append(
                ToolParameter(
                    name=field_name,
                    type=type_str,
                    description=field_info.description or field_name,
                    required=is_required,
                    enum=enum_values,
                )
            )

        return ToolSchema(name=self.name, description=self.description, parameters=parameters)


def _python_type_to_json_type(annotation: Any) -> str:
    """Map a Python type annotation to a JSON Schema type string."""
    if annotation is None:
        return "string"
    # Handle Optional / Union types (origin = types.UnionType or typing.Union).
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        # For Optional[X] just use the first non-None arg.
        args = getattr(annotation, "__args__", ())
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_type(non_none[0])
        return "string"

    type_map: dict[Any, str] = {
        int: "integer",
        float: "number",
        bool: "boolean",
        str: "string",
        list: "array",
        dict: "object",
    }
    # StrEnum subclasses are string-valued.
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return "string"
    return type_map.get(annotation, "string")


class ToolRegistry:
    """Registry that maps tool names to Tool entries.

    Usage::

        registry = ToolRegistry()
        registry.register("calc", "A calculator", calculator, CalculatorInput)
        schemas = registry.get_schemas()  # pass to CompletionRequest
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        fn: Callable[..., str],
        input_model: Type[BaseModel],
    ) -> None:
        """Register a tool under *name*.

        Args:
            name:        Unique tool name (used by the model to invoke it).
            description: Short description of what the tool does.
            fn:          The callable to execute.
            input_model: Pydantic BaseModel class used for argument validation.
        """
        self._tools[name] = Tool(name=name, description=description, fn=fn, input_model=input_model)

    def list_tools(self) -> list[str]:
        """Return a list of registered tool names."""
        return list(self._tools.keys())

    def get_schemas(self) -> list[ToolSchema]:
        """Return ToolSchema objects for all registered tools."""
        return [entry.to_schema() for entry in self._tools.values()]

    def get(self, name: str) -> Tool | None:
        """Return the Tool entry for *name*, or None if not registered."""
        return self._tools.get(name)


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------


def execute_tool_call(registry: ToolRegistry, tool_name: str, arguments: dict[str, Any]) -> str:
    """Validate and execute a tool call from the model.

    Looks up the tool by name, validates *arguments* against its Pydantic
    input model, then calls the underlying function.

    Args:
        registry:   The ToolRegistry to look up tools from.
        tool_name:  The name of the tool to call.
        arguments:  Raw argument dict from the model (will be validated).

    Returns:
        The tool's string output, or an error string on failure.
    """
    entry = registry.get(tool_name)
    if entry is None:
        return f"Error: unknown tool '{tool_name}'"

    try:
        validated = entry.input_model.model_validate(arguments)
    except ValidationError as exc:
        return f"Validation error: {exc}"

    try:
        return entry.fn(**validated.model_dump())
    except Exception as exc:  # noqa: BLE001
        return f"Error executing tool '{tool_name}': {exc}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_default_registry() -> ToolRegistry:
    """Create a ToolRegistry pre-populated with the standard demo tools.

    Returns:
        A ToolRegistry with calculator, word_count, and fake_search registered.
    """
    registry = ToolRegistry()
    registry.register(
        name="calculator",
        description="Perform basic arithmetic: add, subtract, multiply, or divide two numbers.",
        fn=calculator,
        input_model=CalculatorInput,
    )
    registry.register(
        name="word_count",
        description="Count the number of words in a piece of text.",
        fn=word_count,
        input_model=WordCountInput,
    )
    registry.register(
        name="search",
        description="Search for information on a topic and return the top results.",
        fn=fake_search,
        input_model=SearchInput,
    )
    return registry


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    """Demo: register tools, derive schemas, simulate a tool call loop."""

    async def _demo() -> None:
        registry = create_default_registry()

        # --- 1. Show registered tool names and their schemas ---
        print("Registered tools:", registry.list_tools())
        print()
        for schema in registry.get_schemas():
            print(f"Tool: {schema.name}")
            print(f"  Description: {schema.description}")
            for p in schema.parameters:
                enum_hint = f" (enum: {p.enum})" if p.enum else ""
                req = "required" if p.required else "optional"
                print(f"  Param: {p.name} [{p.type}] {req}{enum_hint}")
            print()

        # --- 2. Direct tool invocation with validation ---
        print("Direct calculator call:")
        result = execute_tool_call(registry, "calculator", {"operation": "multiply", "a": 6, "b": 7})
        print(f"  6 * 7 = {result}\n")

        print("Division by zero:")
        result = execute_tool_call(registry, "calculator", {"operation": "divide", "a": 10, "b": 0})
        print(f"  {result}\n")

        print("Invalid operation (validation error):")
        result = execute_tool_call(registry, "calculator", {"operation": "modulo", "a": 10, "b": 3})
        print(f"  {result}\n")

        print("Unknown tool:")
        result = execute_tool_call(registry, "nonexistent", {})
        print(f"  {result}\n")

        # --- 3. Simulate a MockClient tool-calling interaction ---
        # The mock returns a canned ToolCall so we can exercise the dispatch loop.
        mock_tool_call = ToolCall(
            id="call_001",
            name="calculator",
            arguments={"operation": "add", "a": 100, "b": 200},
        )
        client = MockClient(
            responses=[
                CompletionResponse(
                    tool_calls=[mock_tool_call],
                    model="mock",
                    usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
                ),
                CompletionResponse(
                    content="The answer is 300.0.",
                    model="mock",
                ),
            ]
        )

        schemas = registry.get_schemas()
        request = CompletionRequest(
            messages=[
                Message(role=Role.USER, content="What is 100 + 200?"),
            ],
            tools=schemas,
        )
        print("Simulated model call with tools:")
        response = await client.complete(request)
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_result = execute_tool_call(registry, tc.name, tc.arguments)
                print(f"  Model requested tool '{tc.name}' -> {tool_result}")
        print()

        # --- 4. Pydantic validation demo ---
        print("Pydantic input validation:")
        try:
            CalculatorInput(operation="modulo", a=1, b=2)  # type: ignore[arg-type]
        except Exception as exc:
            print(f"  Caught expected error: {type(exc).__name__}")

        valid = CalculatorInput(operation="add", a=3, b=4)
        print(f"  Valid input: {valid}")

    asyncio.run(_demo())
