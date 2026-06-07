"""Run both systems over the query set and record raw transcripts.

Usage:
    python -m labs.lab_001.run                 # full set
    python -m labs.lab_001.run --limit 20      # first 20 queries (validation pass)
    python -m labs.lab_001.run --agent-model llama3.2:3b

Records one JSON file per (system, query) under runs/<system>/<id>.json plus a
runs/manifest.json describing the configuration. Scoring is a separate stage
(evaluate.py) so it can replay from these committed transcripts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from labs.lab_001 import dataset
from labs.lab_001.systems import run_hierarchy, run_router
from src.shared.model_client import create_client

HERE = Path(__file__).parent
RUNS_DIR = HERE / "runs"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lab-001 run: router vs hierarchy")
    parser.add_argument("--limit", type=int, default=0, help="limit to first N queries (0 = all)")
    parser.add_argument("--agent-model", default="llama3.2:3b")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    args = parser.parse_args()

    data = dataset.load()
    queries = data["queries"]
    if args.limit:
        queries = queries[: args.limit]

    client = create_client("local", model_name=args.agent_model, base_url=args.base_url)

    RUNS_DIR.mkdir(exist_ok=True)
    for system in ("router", "hierarchy"):
        (RUNS_DIR / system).mkdir(exist_ok=True)

    started = time.time()
    print(f"[run] {len(queries)} queries, agent model = {args.agent_model}")
    errors = 0
    for i, q in enumerate(queries):
        qid, query, cat = q["id"], q["query"], q["category"]
        try:
            router = await run_router(client, query, qid, cat)
            hierarchy = await run_hierarchy(client, query, qid, cat)
        except Exception as exc:  # one bad query must not abort an unattended batch
            errors += 1
            print(f"  [{i + 1}/{len(queries)}] {qid} ERROR: {exc}")
            continue
        (RUNS_DIR / "router" / f"{qid}.json").write_text(router.model_dump_json(indent=2))
        (RUNS_DIR / "hierarchy" / f"{qid}.json").write_text(hierarchy.model_dump_json(indent=2))
        print(
            f"  [{i + 1}/{len(queries)}] {qid} {cat:<10} "
            f"router={router.model_calls}c/{router.total_tokens}t "
            f"hier={hierarchy.model_calls}c/{hierarchy.total_tokens}t"
        )

    manifest = {
        "agent_model": args.agent_model,
        "base_url": args.base_url,
        "n_queries": len(queries),
        "errors": errors,
        "limit": args.limit,
        "dataset_meta": data["meta"],
        "started": started,
        "finished": time.time(),
        "duration_s": round(time.time() - started, 1),
    }
    (RUNS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[run] done in {manifest['duration_s']}s; transcripts in {RUNS_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
