# Framework Comparison

Side-by-side comparison of three agent implementations: raw (no framework), Google ADK,
and LangChain. Companion to Section 0d of "Agentic AI for Serious Engineers."

## What it does

- Runs identical queries through three implementations of the same agent
- Reports accuracy, token usage, latency, and cost per implementation
- Handles missing optional dependencies gracefully (ADK or LangChain not installed = skipped column)
- Uses the eval rubric from `evals/rubric.yaml` for scoring

## What's inside

```
src/
  raw_agent.py        Thin wrapper importing Agent from src/ch00/raw_agent
  adk_agent.py        Thin wrapper importing create_adk_agent from src/ch00/adk_agent
  langchain_agent.py  Thin wrapper importing create_langchain_agent from src/ch00/langchain_agent
  compare.py          Runs all three against shared test queries, prints comparison table
evals/
  test_queries.yaml   Five benchmark queries with expected answers
  rubric.yaml         Scoring rules and reported metrics
  run_eval.py         Full eval runner with per-implementation results and summary
```

## Prerequisites

The raw agent works with no extra dependencies. To include framework comparisons:

```bash
pip install -e ".[foundations]"        # installs the book's base dependencies
pip install google-adk                 # optional: enables ADK column
pip install langchain-core langchain-anthropic langgraph  # optional: enables LangChain column
```

## Running

```bash
# Run the comparison (available implementations only)
python project/framework-comparison/src/compare.py

# Run the full eval with scoring
python project/framework-comparison/evals/run_eval.py
```

## What you'll see

```
Framework Comparison -- 5 queries
=======================================================================
Implementation   Avg Score   Total Tokens   Avg Latency ms   Total Cost USD
-----------------------------------------------------------------------
raw_agent             0.92            725             42.3         0.000580
adk_agent          skipped (google-adk not installed)
langchain_agent    skipped (langchain-core not installed)
```

When all three are installed, the table shows all columns and lets you compare the
overhead each framework adds for identical functionality.

## Connection to the book

Section 0d evaluates three agent frameworks against the same task to answer a practical
question: what does a framework actually buy you, and at what cost? This project makes
the comparison empirical rather than rhetorical. The data in the comparison table drives
the framework selection framework introduced in Section 0d.
