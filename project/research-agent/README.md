# Research Agent

An expanded agent loop with configurable budgets, step-level cost tracking, trace export,
and graceful error recovery. Companion to Section 0c of "Agentic AI for Serious Engineers."

## What it does

- Runs a multi-step agent loop with a configurable step budget
- Logs token usage and estimated cost at each step
- Exports the full execution trace to JSON for inspection
- Recovers gracefully from tool errors without terminating the run
- Provides a CLI runner that takes a query and prints the annotated trace

## What's inside

```
src/
  agent.py   Expanded Agent with per-step logging, trace export, error recovery
  tools.py   search, read_url (simulated), summarize (LLM call), calculator
  run.py     CLI runner: python -m ... "your query here"
evals/
  test_queries.yaml  Five benchmark queries with expected answers
  run_eval.py        Loads YAML, runs agent against each query, prints scored results
```

## Running

```bash
# Install dependencies
make install

# Run a single query
python project/research-agent/src/run.py "What is 15 * 7?"

# Run a single query with trace export
python project/research-agent/src/run.py --export trace.json "What is 100 / 4 + 10?"

# Run the full eval suite
python project/research-agent/evals/run_eval.py
```

## Example queries

```
"What is 15 * 7?"
"Search for agentic AI and summarize what you find."
"How many words are in 'the quick brown fox jumps over the lazy dog'?"
"What is 100 / 4 + 10?"
"Search for machine learning and tell me the first result."
```

## What you'll see

Each run prints a step-by-step trace:

```
[step 1] tool_call  calculator({"operation": "multiply", "a": 15, "b": 7})
         -> 105.0
         tokens: 60  cost: $0.000048
[step 2] response   "15 * 7 = 105"
         tokens: 85  cost: $0.000068

Summary: 2 steps, 145 tokens, $0.000116, 45ms
```

The eval runner prints a score table and overall pass rate.

## Connection to the book

Section 0c introduces the raw agent loop -- the simplest possible implementation where a
model can call tools, observe results, and iterate. This project adds the instrumentation
that makes production agents debuggable: per-step cost visibility, exportable traces, and
error recovery that does not silently swallow failures.
