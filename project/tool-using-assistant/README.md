# Tool-Using Assistant

A single-turn assistant that selects and executes tools to answer user queries.
Companion to Section 0b of "Agentic AI for Serious Engineers."

## What it does

- Defines four tools with Pydantic input validation: calculator, word counter, search, file reader
- Builds a tool registry using the shared `ToolRegistry` from `src/ch00/tool_use.py`
- Accepts a query, simulates tool selection, executes the appropriate tool, and returns the result
- Logs tool selections and validation errors to stdout

## What's inside

```
src/
  tools.py      Four tools with Pydantic validation (calculator, word_counter, search, file_reader)
  assistant.py  Single-turn assistant: query -> tool selection -> execution -> response
```

## Running

```bash
# Install dependencies
make install

# Run the tool definitions demo
python project/tool-using-assistant/src/tools.py

# Run the assistant demo
python project/tool-using-assistant/src/assistant.py
```

No API key required. The assistant demo uses `MockClient` to simulate tool call responses
so you can observe the full flow without a live model.

## What you'll see

The tools demo prints each tool's schema as the model would receive it, then exercises
each tool directly with valid and invalid inputs to show Pydantic's validation behaviour.

The assistant demo runs five queries against a scripted mock model. Each query shows:
- Which tool the model selected
- The validated arguments
- The tool result
- The final response

## Connection to the book

Section 0b explains how structured tool calling works: how tools are described to the
model, how the model selects and parameterises them, and why Pydantic validation matters
before execution. This project makes all four steps visible in a single runnable script.
