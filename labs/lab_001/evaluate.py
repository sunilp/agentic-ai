"""Score the recorded runs with an LLM judge and emit results.

Usage:
    python -m labs.lab_001.evaluate                  # 3 judge runs, qwen2.5:14b
    python -m labs.lab_001.evaluate --runs 1         # quick pass
    python -m labs.lab_001.evaluate --judge-model qwen2.5:14b

Reads runs/<system>/<id>.json (agent transcripts) plus queries.json (for the
reference answer), judges each answer against the rubric N times to bound judge
variance, and writes results.json + RESULTS.md. Re-running reproduces the numbers
modulo small local-judge nondeterminism (raw per-run scores are saved).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import time
from pathlib import Path

import yaml

from labs.lab_001 import dataset
from src.shared.model_client import create_client
from src.shared.types import CompletionRequest, Message, Role

HERE = Path(__file__).parent
RUNS_DIR = HERE / "runs"
SYSTEMS = ["router", "hierarchy"]

_JUDGE_SYSTEM = (
    "You are a strict evaluation judge for customer-support answers. Score the answer "
    "on three criteria, each from 0.0 to 1.0:\n"
    "- correctness: does it correctly address the question and match the reference policy?\n"
    "- grounded: is it consistent with the reference and free of invented policy or numbers?\n"
    "- completeness: does it give the customer enough to act on?\n"
    'Reply with strict JSON only: {"correctness": x, "grounded": x, "completeness": x}.'
)


def _clamp(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return 0.0


def _parse_scores(content: str) -> dict[str, float]:
    match = re.search(r"\{.*\}", content or "", re.DOTALL)
    if not match:
        return {"correctness": 0.0, "grounded": 0.0, "completeness": 0.0}
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"correctness": 0.0, "grounded": 0.0, "completeness": 0.0}
    return {k: _clamp(raw.get(k, 0.0)) for k in ("correctness", "grounded", "completeness")}


async def _judge_once(client, query: str, reference: str, answer: str) -> dict[str, float]:
    user = (
        f"Question: {query}\n\nReference answer: {reference}\n\n"
        f"Answer to score: {answer or '(empty)'}"
    )
    resp = await client.complete(
        CompletionRequest(
            messages=[
                Message(role=Role.SYSTEM, content=_JUDGE_SYSTEM),
                Message(role=Role.USER, content=user),
            ],
            temperature=0.0,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
    )
    return _parse_scores(resp.content or "")


def _weighted(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(scores.get(name, 0.0) * w for name, w in weights.items())


def _pctl(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lab-001 evaluate: LLM-judge scoring")
    parser.add_argument("--judge-model", default="qwen2.5:14b")
    parser.add_argument("--runs", type=int, default=3, help="judge passes per answer")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    args = parser.parse_args()

    rubric = yaml.safe_load((HERE / "rubric.yaml").read_text())
    weights = {c["name"]: c["weight"] for c in rubric["criteria"]}
    threshold = rubric.get("pass_threshold", 0.7)

    data = dataset.load()
    refs = {q["id"]: q for q in data["queries"]}
    judge = create_client("local", model_name=args.judge_model, base_url=args.base_url)

    started = time.time()
    per_system: dict[str, dict] = {}

    for system in SYSTEMS:
        records = []
        sys_dir = RUNS_DIR / system
        files = sorted(sys_dir.glob("q*.json"))
        for f in files:
            run = json.loads(f.read_text())
            qid = run["query_id"]
            ref = refs.get(qid, {})
            query = ref.get("query", "")
            reference = ref.get("reference_answer", "")
            answer = run.get("answer", "")

            run_weighted = []
            run_scores = []
            for _ in range(args.runs):
                s = await _judge_once(judge, query, reference, answer)
                run_scores.append(s)
                run_weighted.append(_weighted(s, weights))
            avg_scores = {
                k: statistics.mean(rs[k] for rs in run_scores)
                for k in ("correctness", "grounded", "completeness")
            }
            mean_weighted = statistics.mean(run_weighted)
            records.append(
                {
                    "id": qid,
                    "category_true": run["category_true"],
                    "category_used": run["category_used"],
                    "passed": mean_weighted >= threshold,
                    "weighted": round(mean_weighted, 4),
                    "scores": {k: round(v, 4) for k, v in avg_scores.items()},
                    "run_weighted": [round(x, 4) for x in run_weighted],
                    "model_calls": run["model_calls"],
                    "tool_calls": run["tool_calls"],
                    "total_tokens": run["total_tokens"],
                    "latency_ms": run["latency_ms"],
                    "flags": run.get("flags", {}),
                }
            )
            print(f"  [{system}] {qid} weighted={mean_weighted:.2f} pass={mean_weighted >= threshold}")

        n = len(records)
        passed = sum(1 for r in records if r["passed"])
        misroutes = sum(1 for r in records if r["flags"].get("misroute"))
        variance = statistics.mean(
            statistics.pstdev(r["run_weighted"]) if len(r["run_weighted"]) > 1 else 0.0
            for r in records
        ) if records else 0.0
        per_system[system] = {
            "n": n,
            "accuracy": round(passed / n, 4) if n else 0.0,
            "avg_score": round(statistics.mean(r["weighted"] for r in records), 4) if n else 0.0,
            "avg_tokens": round(statistics.mean(r["total_tokens"] for r in records), 1) if n else 0,
            "avg_model_calls": round(statistics.mean(r["model_calls"] for r in records), 2) if n else 0,
            "p50_latency_ms": round(_pctl([r["latency_ms"] for r in records], 0.5), 1) if n else 0,
            "avg_tool_calls": round(statistics.mean(r["tool_calls"] for r in records), 2) if n else 0,
            "misroute_rate": round(misroutes / n, 4) if n else 0.0,
            "verifier_retry_rate": round(
                sum(1 for r in records if r["flags"].get("verifier_retried")) / n, 4
            ) if n else 0.0,
            "verifier_pass_rate": round(
                sum(1 for r in records if r["flags"].get("verifier_passed")) / n, 4
            ) if n else 0.0,
            "judge_variance": round(variance, 4),
            "records": records,
        }

    results = {
        "judge_model": args.judge_model,
        "judge_runs": args.runs,
        "pass_threshold": threshold,
        "weights": weights,
        "dataset_meta": data["meta"],
        "duration_s": round(time.time() - started, 1),
        "systems": per_system,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2))
    (HERE / "RESULTS.md").write_text(_render_markdown(results))
    print(f"[evaluate] wrote results.json and RESULTS.md ({results['duration_s']}s)")


def _render_markdown(r: dict) -> str:
    ro = r["systems"]["router"]
    hi = r["systems"]["hierarchy"]
    meta = r["dataset_meta"]
    winner = "router" if ro["accuracy"] >= hi["accuracy"] else "hierarchy"
    tok_mult = round(hi["avg_tokens"] / ro["avg_tokens"], 2) if ro["avg_tokens"] else 0
    lat_mult = round(hi["p50_latency_ms"] / ro["p50_latency_ms"], 2) if ro["p50_latency_ms"] else 0

    def row(label: str, key: str, fmt: str = "{}") -> str:
        return f"| {label} | {fmt.format(ro[key])} | {fmt.format(hi[key])} |"

    lines = [
        "# Lab-001 (local reproduction): workflow router vs 3-agent hierarchy",
        "",
        f"Judge: `{r['judge_model']}`, {r['judge_runs']} passes per answer. "
        f"Pass threshold {r['pass_threshold']}. Weights {r['weights']}.",
        f"Dataset: {meta['source']} ({meta['actual_n']} queries, seed {meta['seed']}, "
        f"fallback={meta['used_fallback']}).",
        "",
        "## Results",
        "",
        "| Metric | Router | Hierarchy |",
        "|--------|--------|-----------|",
        row("Accuracy (pass rate)", "accuracy", "{:.1%}"),
        row("Avg weighted score", "avg_score", "{:.3f}"),
        row("Avg tokens / query", "avg_tokens"),
        row("Avg model calls", "avg_model_calls"),
        row("p50 latency (ms)", "p50_latency_ms"),
        row("Avg tool calls", "avg_tool_calls"),
        row("Misroute rate", "misroute_rate", "{:.1%}"),
        row("Verifier retry rate", "verifier_retry_rate", "{:.1%}"),
        row("Verifier pass rate", "verifier_pass_rate", "{:.1%}"),
        row("Judge variance (mean stdev)", "judge_variance", "{:.3f}"),
        "",
        f"**Headline:** {winner} won on accuracy "
        f"({ro['accuracy']:.1%} router vs {hi['accuracy']:.1%} hierarchy). "
        f"The hierarchy used {tok_mult}x the tokens and {lat_mult}x the p50 latency of the router.",
        "",
        "## Read this before quoting the numbers",
        "",
        "1. These are local open models (agents on a small model, judge on a mid model), "
        "not the Claude models the original Lab-001 ran. The numbers are NOT comparable to "
        "the original 87/74, and the direction may differ. This is a fresh experiment.",
        "2. Local inference has no dollar cost, so the cost axis here is tokens and model "
        "calls, not dollars per query.",
        "3. The queries are single-turn support requests, which is the short-horizon regime "
        "the experiment targets.",
        "",
        f"Run duration (judging): {r['duration_s']}s. Raw per-query scores and per-run "
        "judge passes are in results.json.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
