"""Run baseline vs contender over the incident set, plus the durability harness.

Usage:
    LAB002_MODEL=ollama_chat/llama3.2:3b python -m labs.lab_002.run   # full set
    LAB002_LIMIT=5 python -m labs.lab_002.run                          # smoke test

Env:
    LAB002_MODEL   Agent model, default "ollama_chat/llama3.2:3b" (wrapped in
                   LiteLlm, routed to Ollama). A `gemini*` prefix switches to
                   native Gemini (no LiteLlm, ADK talks to it directly) -- see
                   the guard in `_build_model`. No Gemini API key is configured
                   in this environment, so that path is untested here; it
                   exists so a future paid run only has to set the env var.
    LAB002_LIMIT   int; if set, only the first N incidents are processed. Lets
                   the whole pipeline (this script + evaluate.py) be smoke
                   tested cheaply before committing to a full run.

Records one JSON transcript per (system, incident) under runs/<system>/<id>.json,
a fixed durability subset under runs/durability/<id>.json, an aggregate
results.json, and a human-readable RESULTS.md covering the four axes: success
rate, cost multiple, latency multiple, durability savings. evaluate.py is a
separate, slower stage that re-scores the recorded findings with an LLM judge
and folds those numbers into results.json + RESULTS.md.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from pathlib import Path

from google.adk.sessions.in_memory_session_service import InMemorySessionService

from labs.lab_002 import dataset, durability, metrics
from labs.lab_002.schema import Incident, RunRecord
from labs.lab_002.systems import build_baseline, build_contender, run_baseline, run_contender

HERE = Path(__file__).parent
RUNS_DIR = HERE / "runs"

_DEFAULT_MODEL = "ollama_chat/llama3.2:3b"
_DURABILITY_SUBSET_N = 5


def _build_model(model_name: str):
    """Wrap the configured model for ADK.

    Gemini models run native (no LiteLlm, ADK resolves the string directly).
    Everything else -- Ollama and other OpenAI-compatible local models -- goes
    through LiteLlm. This is the local floor for now: no Gemini key exists in
    this environment.
    """
    if model_name.startswith("gemini"):
        return model_name
    from google.adk.models.lite_llm import LiteLlm

    return LiteLlm(model=model_name)


def _pctl(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _aggregate(records: list[RunRecord], incidents_by_id: dict[str, Incident]) -> dict:
    n = len(records)
    if n == 0:
        return {
            "n": 0,
            "success_rate": 0.0,
            "avg_prompt_tokens": 0,
            "avg_completion_tokens": 0,
            "avg_total_tokens": 0,
            "avg_model_calls": 0,
            "p50_latency_ms": 0,
            "remediation_rate": 0.0,
            "records": [],
        }
    sr = metrics.success_rate(records, incidents_by_id)
    per_record = [
        {
            "incident_id": r.incident_id,
            "finding": json.loads(r.finding.model_dump_json()) if r.finding else None,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "model_calls": r.model_calls,
            "latency_ms": round(r.latency_ms, 1),
            "remediation_applied": r.remediation_applied,
            "approved": r.approved,
            "resumed": r.resumed,
            "heuristic_score": round(
                metrics.score_finding(r.finding, incidents_by_id[r.incident_id]), 4
            ),
        }
        for r in records
    ]
    return {
        "n": n,
        "success_rate": round(sr, 4),
        "avg_prompt_tokens": round(statistics.mean(r.prompt_tokens for r in records), 1),
        "avg_completion_tokens": round(
            statistics.mean(r.completion_tokens for r in records), 1
        ),
        "avg_total_tokens": round(
            statistics.mean(r.prompt_tokens + r.completion_tokens for r in records), 1
        ),
        "avg_model_calls": round(statistics.mean(r.model_calls for r in records), 2),
        "p50_latency_ms": round(_pctl([r.latency_ms for r in records], 0.5), 1),
        "remediation_rate": round(
            sum(1 for r in records if r.remediation_applied) / n, 4
        ),
        "records": per_record,
    }


def _aggregate_durability(pairs: list[tuple[str, RunRecord, RunRecord]]) -> dict:
    n = len(pairs)
    if n == 0:
        return {
            "n": 0,
            "avg_tokens_saved": 0,
            "avg_model_calls_saved": 0,
            "avg_latency_ms_saved": 0,
            "avg_frontier_calls": 0,
            "records": [],
        }
    savings = [metrics.durability_savings(pre, post) for _, pre, post in pairs]
    per_record = [
        {"incident_id": iid, "savings": sv}
        for (iid, _pre, _post), sv in zip(pairs, savings, strict=True)
    ]
    return {
        "n": n,
        "avg_tokens_saved": round(statistics.mean(s["tokens_saved"] for s in savings), 1),
        "avg_model_calls_saved": round(
            statistics.mean(s["model_calls_saved"] for s in savings), 2
        ),
        "avg_latency_ms_saved": round(
            statistics.mean(s["latency_ms_saved"] for s in savings), 1
        ),
        "avg_frontier_calls": round(statistics.mean(s["frontier_calls"] for s in savings), 2),
        "records": per_record,
    }


async def main() -> None:
    model_name = os.environ.get("LAB002_MODEL", _DEFAULT_MODEL)
    limit_env = os.environ.get("LAB002_LIMIT")
    limit = int(limit_env) if limit_env else 0

    incidents = dataset.load()
    if limit:
        incidents = incidents[:limit]
    incidents_by_id = {i.id: i for i in incidents}

    model = _build_model(model_name)

    RUNS_DIR.mkdir(exist_ok=True)
    for system in ("baseline", "contender", "durability"):
        (RUNS_DIR / system).mkdir(exist_ok=True)

    session_service = InMemorySessionService()
    baseline_agent = build_baseline(model)
    contender_workflow = build_contender(model)

    started = time.time()
    print(f"[run] {len(incidents)} incidents, agent model = {model_name}")

    baseline_records: list[RunRecord] = []
    contender_records: list[RunRecord] = []
    errors = 0
    for i, incident in enumerate(incidents):
        try:
            base = await run_baseline(baseline_agent, incident, session_service)
            cont = await run_contender(
                contender_workflow, incident, session_service, auto_approve=True
            )
        except Exception as exc:  # one bad incident must not abort an unattended batch
            errors += 1
            print(f"  [{i + 1}/{len(incidents)}] {incident.id} ERROR: {exc}")
            continue
        baseline_records.append(base)
        contender_records.append(cont)
        (RUNS_DIR / "baseline" / f"{incident.id}.json").write_text(
            base.model_dump_json(indent=2)
        )
        (RUNS_DIR / "contender" / f"{incident.id}.json").write_text(
            cont.model_dump_json(indent=2)
        )
        print(
            f"  [{i + 1}/{len(incidents)}] {incident.id} "
            f"base={base.model_calls}c/{base.prompt_tokens + base.completion_tokens}t "
            f"cont={cont.model_calls}c/{cont.prompt_tokens + cont.completion_tokens}t "
            f"resumed={cont.resumed}"
        )

    # --- Durability: crash + resume over a fixed subset ---
    durability_subset = incidents[: min(_DURABILITY_SUBSET_N, len(incidents))]
    db_path = str(RUNS_DIR / "durability.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    durability_pairs: list[tuple[str, RunRecord, RunRecord]] = []
    durability_skipped = 0
    for incident in durability_subset:
        try:
            pre, post = await durability.run_with_crash(incident, model, db_path)
        except Exception as exc:
            # Task 9 review flagged run_with_crash lacks an interrupt guard: if the
            # gate is never reached (e.g. the investigator/synthesizer failed to
            # produce a valid Finding on a weak local model), resuming can raise.
            # One bad incident must not abort the whole durability batch.
            print(f"  [durability] {incident.id} ERROR: {exc}")
            durability_skipped += 1
            continue
        if pre.finding is None:
            # Ran without raising but never reached the gate with a usable
            # finding -- nothing meaningful to resume, so skip it too.
            print(f"  [durability] {incident.id} skipped: gate not reached (no pre-crash finding)")
            durability_skipped += 1
            continue
        durability_pairs.append((incident.id, pre, post))
        (RUNS_DIR / "durability" / f"{incident.id}.json").write_text(
            json.dumps(
                {
                    "incident_id": incident.id,
                    "pre": json.loads(pre.model_dump_json()),
                    "post": json.loads(post.model_dump_json()),
                    "savings": metrics.durability_savings(pre, post),
                },
                indent=2,
            )
        )
        print(
            f"  [durability] {incident.id} pre={pre.model_calls}c "
            f"post={post.model_calls}c resumed={post.resumed}"
        )

    baseline_agg = _aggregate(baseline_records, incidents_by_id)
    contender_agg = _aggregate(contender_records, incidents_by_id)
    durability_agg = _aggregate_durability(durability_pairs)

    cost_multiple = (
        round(contender_agg["avg_total_tokens"] / baseline_agg["avg_total_tokens"], 2)
        if baseline_agg["avg_total_tokens"]
        else 0.0
    )
    latency_multiple = (
        round(contender_agg["p50_latency_ms"] / baseline_agg["p50_latency_ms"], 2)
        if baseline_agg["p50_latency_ms"]
        else 0.0
    )

    results = {
        "agent_model": model_name,
        "n_incidents": len(incidents),
        "limit": limit or None,
        "errors": errors,
        "durability_subset": [inc.id for inc in durability_subset],
        "durability_skipped": durability_skipped,
        "started": started,
        "finished": time.time(),
        "duration_s": round(time.time() - started, 1),
        "systems": {"baseline": baseline_agg, "contender": contender_agg},
        "cost_multiple": cost_multiple,
        "latency_multiple": latency_multiple,
        "durability": durability_agg,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2))
    (HERE / "RESULTS.md").write_text(_render_markdown(results))
    print(f"[run] done in {results['duration_s']}s; wrote results.json and RESULTS.md")


def _render_markdown(r: dict) -> str:
    base = r["systems"]["baseline"]
    cont = r["systems"]["contender"]
    dur = r["durability"]
    limit_note = f" (limited to first {r['limit']})" if r.get("limit") else ""
    lines = [
        "# Lab-002 (local reproduction): static baseline vs durable contender",
        "",
        f"Agent model: `{r['agent_model']}`. {r['n_incidents']} incidents{limit_note}, "
        f"{r['errors']} errors during the main run.",
        "",
        "## Results (heuristic scoring)",
        "",
        "Success rate here is `metrics.score_finding`: keyword overlap between the "
        "recorded finding and the incident's ground truth. Run "
        "`python -m labs.lab_002.evaluate` for an independent LLM-judge cross-check.",
        "",
        "| Metric | Baseline | Contender |",
        "|--------|----------|-----------|",
        f"| Success rate | {base['success_rate']:.1%} | {cont['success_rate']:.1%} |",
        f"| Avg total tokens / incident | {base['avg_total_tokens']} | {cont['avg_total_tokens']} |",
        f"| Avg model calls | {base['avg_model_calls']} | {cont['avg_model_calls']} |",
        f"| p50 latency (ms) | {base['p50_latency_ms']} | {cont['p50_latency_ms']} |",
        f"| Remediation applied rate | {base['remediation_rate']:.1%} | {cont['remediation_rate']:.1%} |",
        "",
        f"**Cost multiple (contender / baseline avg tokens):** {r['cost_multiple']}x. "
        f"**Latency multiple (contender / baseline p50):** {r['latency_multiple']}x.",
        "",
        "## Durability (crash + resume over a fixed subset)",
        "",
        f"{dur['n']} of {len(r['durability_subset'])} incidents in the subset reached "
        f"the human gate and were crash-tested ({r['durability_skipped']} skipped: no "
        "finding reached the gate, or the resume errored).",
        "",
    ]
    if dur["n"]:
        lines += [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Avg tokens saved on resume | {dur['avg_tokens_saved']} |",
            f"| Avg model calls saved on resume | {dur['avg_model_calls_saved']} |",
            f"| Avg latency (ms) saved on resume | {dur['avg_latency_ms_saved']} |",
            f"| Avg frontier-only calls after resume | {dur['avg_frontier_calls']} |",
            "",
        ]
    else:
        lines += [
            "No incidents in the durability subset reached the gate; no savings computed.",
            "",
        ]
    lines += [
        "## Read this before quoting the numbers",
        "",
        "1. Local open models only (agent on the model above, judge on qwen2.5:14b "
        "via evaluate.py). No Gemini key is configured in this environment, so "
        "`LAB002_MODEL=gemini-2.0-flash` is an untested path here, not a claim made "
        "by this run.",
        "2. Local inference has no dollar cost. The cost axis is tokens and model "
        "calls per incident, not dollars.",
        "3. Success rate above is the cheap heuristic. Run "
        "`python -m labs.lab_002.evaluate` for the LLM-judge cross-check, a "
        "separate, slower pass over these same recorded findings.",
        "",
        f"Run duration: {r['duration_s']}s. Per-incident transcripts are under `runs/`; "
        "full per-incident detail is in results.json.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
