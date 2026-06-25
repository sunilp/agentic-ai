# FN-004: prompted-stop vs enforced-stop loop

Companion code for the Field Note [Loop engineering is a 30-year-old loop with a new hashtag](https://agenticlab.sunilprakash.com/field-notes/004-loop-engineering-30-year-old-loop/).

Two versions of the same point:

- [`loop.py`](loop.py) is a deterministic, no-API-key model of the contrast, the version the tests prove in CI.
- [`langgraph_agent.py`](langgraph_agent.py) is the same contrast with a real LLM agent driving the loop on LangGraph.

## The deterministic version

The same loop runs two ways. The script is identical in both: call a destructive tool, then claim the task is done.

- `run_prompted` trusts the agent's own `Done`. The destructive call executes and the database is deleted.
- `run_enforced` puts three external fences around the loop: a hard iteration cap, a no-progress detector that hashes each call and halts on a repeat, and a capability gate that refuses a destructive tool unless it was approved out of band. The agent cannot delete the database on a hallucinated "done", by construction.

The difference between those two functions is the entire content of the Field Note.

## Run it

```bash
python -m src.fn04.run
```

Expected output:

```
prompted-stop loop
  stop reason : agent_done
  database    : DELETED

enforced-stop loop
  stop reason : agent_done
  blocked     : ['delete_all']
  database    : intact
```

## The real agent (LangGraph)

`langgraph_agent.py` builds an actual ReAct agent with `langgraph` and `ChatAnthropic` over two tools, `read_rows` and a destructive `delete_all`, and runs it two ways:

- `run_prompted_agent` gives the agent the tools ungated. Told to clean up a staging table, a real model will often call `delete_all`, and nothing stops it.
- `run_enforced_agent` wraps `delete_all` in the same capability gate from `loop.py` and caps the loop with `recursion_limit`. Without an out-of-band approval the agent cannot delete, by construction, whatever it decides.

The enforcement is framework-agnostic: the gate lives in `loop.py`; the agent just runs inside it.

```bash
pip install langchain-core langchain-anthropic langgraph
export ANTHROPIC_API_KEY=...
python -m src.fn04.langgraph_agent
```

## Test it

```bash
pytest tests/unit/test_fn04.py -v
```

The tests are the proof, and they run without the frameworks or a key: the prompted loop deletes on a hallucinated done, the enforced loop blocks the destructive call without approval, allows it with an out-of-band grant, halts on the iteration cap and on no progress, and the gated tool refuses the destructive call unless it was approved out of band.
