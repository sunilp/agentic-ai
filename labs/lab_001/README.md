# Lab-001: workflow router vs 3-agent hierarchy (local, reproducible)

A free, fully local re-run of Lab-001 on short-horizon customer-support queries.
It compares a workflow **router** (a rule-based category switch into one
specialized agent) against a 3-agent **hierarchy** (LLM classifier, worker,
verifier with one re-answer round), on the same queries, tools, and model.

## Read this first (honesty caveats)

1. **Different models from the original.** This run uses local open models via
   Ollama. The numbers are not comparable to the original Claude run's 87/74, and
   the direction may differ. Treat this as a fresh experiment, not a reproduction
   of those figures.
2. **No dollar cost.** Local inference is free, so the cost axis here is tokens
   and model calls, not dollars per query.
3. **Short-horizon regime.** The queries are single-turn support requests from a
   public dataset, which is the regime the experiment targets.

## Reproduce

Requires [Ollama](https://ollama.com) running locally and Python 3.11+ with the
project deps (`pydantic`, `httpx`, `pyyaml`).

```bash
# 1. Pull the models (agents = small, judge = mid).
ollama pull llama3.2:3b
ollama pull qwen2.5:14b

# 2. Build the query set (deterministic sample from the Bitext support dataset).
python -m labs.lab_001.dataset 100

# 3. Run both systems and record transcripts under runs/.
python -m labs.lab_001.run

# 4. Score the recorded answers with the LLM judge and write RESULTS.md.
python -m labs.lab_001.evaluate
```

Run from the repository root so `labs` and `src` import correctly.

## What the repo contains vs what you generate

Committed (the reusable harness): the `*.py` modules, `rubric.yaml`, `queries.json`
(the deterministic sample with provenance), and this README. Run the recipe above
and you reproduce the experiment from these.

Generated locally when you run it (not committed): `runs/<system>/<id>.json`
transcripts, `results.json`, and `RESULTS.md`.

## Design

- `dataset.py` — fetches and samples the Bitext customer-support dataset
  (CC-BY 4.0), maps its categories to four router buckets, balanced sample,
  seed 42. Labeled synthetic fallback if the dataset is unreachable.
- `tools.py` — deterministic mock tools (kb lookup, account lookup, create
  ticket). The experiment isolates agent architecture, not tool backends.
- `systems.py` — the router and the hierarchy, both built on the provider-neutral
  `src/shared` model client and types.
- `run.py` — runs both systems, records transcripts.
- `evaluate.py` — LLM-judge scoring against `rubric.yaml`
  (correctness 0.4, grounded 0.3, completeness 0.3, pass at 0.7), N judge passes
  to bound variance.

## Determinism

Models run at temperature 0, but local-model output is not perfectly
deterministic across hardware and quantization. The committed transcripts and
per-run judge scores make the reported numbers inspectable and closely
reproducible; re-running may vary slightly.
