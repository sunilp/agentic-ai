"""Lab-006 runner: record transcripts for all five arms.

    python -m labs.lab_006.run --limit 5      # smoke
    python -m labs.lab_006.run                # full 100-query set
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from labs.lab_001 import dataset
from labs.lab_006.arms import ARMS, run_arm
from src.shared.model_client import create_client

HERE = Path(__file__).parent
RUNS_DIR = HERE / "runs"


async def main() -> None:
    ap = argparse.ArgumentParser(description="Lab-006: factorial ablation of Lab-001")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--agent-model", default="llama3.2:3b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    args = ap.parse_args()

    data = dataset.load()
    queries = data["queries"]
    if args.limit:
        queries = queries[: args.limit]

    client = create_client("local", model_name=args.agent_model, base_url=args.base_url)
    RUNS_DIR.mkdir(exist_ok=True)
    for arm in ARMS:
        (RUNS_DIR / arm).mkdir(exist_ok=True)

    started, errors = time.time(), 0
    print(f"[run] {len(queries)} queries x {len(ARMS)} arms, model = {args.agent_model}",
          flush=True)
    for i, q in enumerate(queries):
        qid, query, cat = q["id"], q["query"], q["category"]
        line = []
        for arm in ARMS:
            try:
                r = await run_arm(arm, client, query, qid, cat)
            except Exception as exc:
                errors += 1
                print(f"  [{i + 1}] {qid} {arm} ERROR: {exc}", flush=True)
                continue
            (RUNS_DIR / arm / f"{qid}.json").write_text(r.model_dump_json(indent=2))
            line.append(f"{arm}={r.model_calls}c")
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i + 1}/{len(queries)}] {qid} " + " ".join(line), flush=True)

    manifest = {
        "agent_model": args.agent_model, "arms": list(ARMS),
        "n_queries": len(queries), "errors": errors,
        "dataset_meta": data["meta"],
        "duration_s": round(time.time() - started, 1),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (RUNS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[run] done in {manifest['duration_s']}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
