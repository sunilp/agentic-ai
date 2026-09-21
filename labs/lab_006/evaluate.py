"""Lab-006 evaluation: judge all five arms and report the factorial contrasts.

Reuses Lab-001's judge prompt, rubric, weights and pass threshold without modification,
imported rather than copied, so the arms are scored exactly as the original comparison
was. Re-scoring the two replicated arms in the same session is deliberate: it means the
contrasts are internal to one run and do not depend on the older numbers being
reproducible.

    python -m labs.lab_006.evaluate --runs 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import yaml

from labs.lab_001 import dataset
from labs.lab_001.evaluate import _judge_once, _weighted
from labs.lab_006.arms import ARMS
from labs.lab_006.report import render
from src.shared.model_client import create_client

HERE = Path(__file__).parent
LAB1 = HERE.parent / "lab_001"
RUNS_DIR = HERE / "runs"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="qwen2.5:14b")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    args = ap.parse_args()

    rubric = yaml.safe_load((LAB1 / "rubric.yaml").read_text())
    weights = {c["name"]: c["weight"] for c in rubric["criteria"]}
    threshold = rubric.get("pass_threshold", 0.7)

    data = dataset.load()
    refs = {q["id"]: q for q in data["queries"]}
    judge = create_client("local", model_name=args.judge_model, base_url=args.base_url)

    started = time.time()
    systems: dict[str, dict] = {}

    for arm in ARMS:
        files = sorted((RUNS_DIR / arm).glob("q*.json"))
        records = []
        for f in files:
            run = json.loads(f.read_text())
            qid = run["query_id"]
            ref = refs.get(qid, {})
            per_pass = [
                await _judge_once(judge, ref.get("query", ""),
                                  ref.get("reference_answer", ""), run.get("answer", ""))
                for _ in range(args.runs)
            ]
            weighted = [_weighted(s, weights) for s in per_pass]
            mean_weighted = statistics.mean(weighted)
            records.append({
                "id": qid,
                "category_true": run["category_true"],
                "category_used": run["category_used"],
                "passed": mean_weighted >= threshold,
                "weighted": round(mean_weighted, 4),
                "run_weighted": [round(w, 4) for w in weighted],
                "model_calls": run["model_calls"],
                "total_tokens": run["total_tokens"],
                "latency_ms": run["latency_ms"],
                "flags": run["flags"],
            })
        n = len(records) or 1
        systems[arm] = {
            "n": len(records),
            "accuracy": round(sum(r["passed"] for r in records) / n, 4),
            "avg_score": round(statistics.mean(r["weighted"] for r in records), 4) if records else 0,
            "avg_tokens": round(statistics.mean(r["total_tokens"] for r in records), 1) if records else 0,
            "avg_model_calls": round(statistics.mean(r["model_calls"] for r in records), 2) if records else 0,
            "p50_latency_ms": round(statistics.median(r["latency_ms"] for r in records), 1) if records else 0,
            "misroute_rate": round(sum(r["flags"]["misroute"] for r in records) / n, 4),
            "retry_rate": round(sum(bool(r["flags"].get("retried")) for r in records) / n, 4),
            "records": records,
        }
        s = systems[arm]
        print(f"{arm:16} pass={s['accuracy']:.1%} score={s['avg_score']:.3f} "
              f"calls={s['avg_model_calls']} misroute={s['misroute_rate']:.0%}", flush=True)

    manifest = json.loads((RUNS_DIR / "manifest.json").read_text())
    out = {
        "judge_model": args.judge_model,
        "judge_runs": args.runs,
        "pass_threshold": threshold,
        "weights": weights,
        "agent_model": manifest.get("agent_model"),
        "dataset_meta": manifest.get("dataset_meta"),
        "run_duration_s": manifest.get("duration_s"),
        "judge_duration_s": round(time.time() - started, 1),
        "systems": systems,
    }
    (HERE / "results.json").write_text(json.dumps(out, indent=1))
    (HERE / "RESULTS.md").write_text(render(out))
    print("\nwrote RESULTS.md and results.json", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
