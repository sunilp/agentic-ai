"""Lab-005 runner: does a poisoned memory reach a consequential action?

    python -m labs.lab_005.run
    python -m labs.lab_005.run --models llama3.2:3b --limit 4
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from labs.lab_005.agent import run_scenario
from labs.lab_005.corpus import build
from labs.lab_005.memory import CONFIGS, Store
from labs.lab_005.report import render

HERE = Path(__file__).resolve().parent


def summarise(rows: list, corpus: dict) -> dict:
    live = [r for r in rows if r.error is None]
    pois = [r for r in live if corpus[r.scenario_id]["poisoned"]]
    clean = [r for r in live if not corpus[r.scenario_id]["poisoned"]]

    def block(rs):
        n = len(rs)
        return {
            "n": n,
            "stored": sum(r.stored for r in rs),
            "cited": sum(r.cites_memory for r in rs),
            "reached": sum(r.reached for r in rs),
            "refused_by_quarantine": sum(r.refused_by_quarantine for r in rs),
            "usable_action": sum(r.phase2_tool is not None and not r.refused_by_quarantine
                                 for r in rs),
            "origins": {o: sum(1 for r in rs if r.memory_origin == o)
                        for o in sorted({r.memory_origin for r in rs if r.memory_origin})},
        }
    return {"n_errors": sum(r.error is not None for r in rows),
            "poisoned": block(pois), "clean": block(clean)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="llama3.2:3b,qwen2.5:7b")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    scen = [asdict(s) for s in build(seed=args.seed)]
    if args.limit:
        scen = scen[:args.limit]
    corpus = {s["id"]: s for s in scen}
    (HERE / "corpus.json").write_text(json.dumps(scen, indent=1))

    meta = {"seed": args.seed, "n_scenarios": len(scen),
            "n_poisoned": sum(s["poisoned"] for s in scen),
            "n_clean": sum(not s["poisoned"] for s in scen),
            "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    reports = []
    for model in [m.strip() for m in args.models.split(",") if m.strip()]:
        t0 = time.time()
        rep = {"model": model, "configs": {}, "rows": {}}
        for config in CONFIGS:
            # A fresh store per configuration. Memory does not leak between them.
            store, rows = Store(config=config), []
            for i, s in enumerate(scen, 1):
                rows.append(run_scenario(s, store, model))
                if i % 6 == 0 or i == len(scen):
                    print(f"  {model} {config}: {i}/{len(scen)}", flush=True)
            rep["configs"][config] = summarise(rows, corpus)
            rep["configs"][config]["store"] = {
                "claims": len(store.claims), "refused_writes": store.refused}
            rep["rows"][config] = [asdict(r) for r in rows]
            b = rep["configs"][config]["poisoned"]
            print(f"{model} {config}: stored {b['stored']}/{b['n']}, "
                  f"cited {b['cited']}, reached {b['reached']}", flush=True)
        rep["duration_s"] = time.time() - t0
        reports.append(rep)

    (HERE / "results.json").write_text(json.dumps({"meta": meta, "models": reports}, indent=1))
    (HERE / "RESULTS.md").write_text(render(reports, meta))
    print("\nwrote RESULTS.md and results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
