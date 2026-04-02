# LLM Explorer

Hands-on experiments for understanding how language models work at the token and cost level. Companion to Section 0a of "Agentic AI for Serious Engineers."

## What it does

- Estimates token counts using the character approximation from `llm_basics.py`
- Compares estimates against tiktoken (if installed) across multiple models
- Projects cost for batch workloads across different model tiers
- Demonstrates context overflow: how quality degrades as the context window fills
- Shows three structured output patterns: JSON mode, schema enforcement, extraction with validation

## What's inside

```
src/
  token_counter.py     Batch token estimation, tiktoken comparison, cost projections
  context_overflow.py  Progressive context fill experiment with quality scoring
  structured_output.py Three structured output patterns with validation
```

## Running

```bash
# Install dependencies
make install

# Token counting and cost projection
python project/llm-explorer/src/token_counter.py

# Context overflow experiment
python project/llm-explorer/src/context_overflow.py

# Structured output patterns
python project/llm-explorer/src/structured_output.py
```

All three modules use `MockClient` for reproducibility -- no API key required.

## What you'll see

`token_counter.py` prints a table comparing character-based estimates against tiktoken
counts (if installed), then projects the cost of processing a 10,000-document corpus
across four model tiers from cheapest to most expensive.

`context_overflow.py` fills a mock context window in 10% increments from 10% to 100%
full and shows how the simulated quality score degrades. The demo makes the abstract
concept of context limits tangible.

`structured_output.py` shows three practical patterns:
1. JSON mode: parse JSON directly from model output
2. Schema enforcement: validate output against a Pydantic model
3. Extraction with fallback: extract a specific field with a default on failure

## Connection to the book

Section 0a covers how models process text as token sequences, why context windows are
finite, and how to estimate cost before committing to an architecture. These experiments
let you run the numbers yourself rather than trust the prose.
