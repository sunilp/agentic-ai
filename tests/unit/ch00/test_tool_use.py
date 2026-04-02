"""Tests for the tool use module (Section 0b)."""

import pytest
from pydantic import ValidationError

from src.ch00.tool_use import (
    CalculatorInput,
    ToolRegistry,
    calculator,
    execute_tool_call,
    word_count,
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
