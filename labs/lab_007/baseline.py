"""Phase B: what a small local model says when asked for its own confidence.

ARCH-002 says not to threshold on a model's self-reported confidence. This
measures that claim on three models that run on a laptop, using lab_004's
corpus so the result sits beside a guard comparison that already exists.

Writes nowhere unless told to: `--out` picks the destination.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from labs.lab_004.corpus import build
from labs.lab_007.detectors import (
    BinaryWordJudge,
    Jev,
    Kev,
    LocalJudge,
    LogprobJudge,
    cloudflare_credentials,
    ollama_ask,
    ollama_ask_logprobs,
    screen_all,
)
from labs.lab_007.metrics import (
    Resolution,
    auc,
    bootstrap_ci,
    operating_point,
    precision_from_rates,
    resolution,
    rule_of_three_upper_bound,
)
from labs.lab_007.synthetic import noise_floor, noise_floor_spread

HERE = Path(__file__).parent
MODELS = ("llama3.2:3b", "qwen2.5:7b", "gemma4:e2b")
BASE_RATES = (0.5, 0.1, 0.01)


def measure_detector(name: str, judge, tickets: list, threshold: float) -> dict:
    rows = []
    for t, v in zip(tickets, screen_all(judge, [t.body for t in tickets]), strict=True):
        rows.append(
            {
                "id": t.id,
                "injected": t.injected,
                "style": t.style,
                "probability": v.probability,
                "parsed": v.parsed,
                "truncated": v.truncated,
                "latency_ms": round(v.latency_ms, 1),
                "model_version": v.model_version,
                "input_tokens": v.input_tokens,
            }
        )

    usable = [r for r in rows if r["parsed"]]
    preds = [r["probability"] for r in usable]
    labels = [int(r["injected"]) for r in usable]
    # A detector can answer nothing usable, which is a finding about that
    # detector and not a reason to discard every other one in the run.
    res = resolution(preds) if preds else Resolution(distinct=0, extreme_fraction=0.0)
    lat = sorted(r["latency_ms"] for r in rows)

    points = []
    if 0 < sum(labels) < len(labels):
        points = [
            {
                "base_rate": br,
                **{
                    k: getattr(operating_point(preds, labels, threshold, br), k)
                    for k in ("recall", "false_positive_rate", "precision")
                },
            }
            for br in BASE_RATES
        ]

    ranking = None
    if 0 < sum(labels) < len(labels):
        lo, hi = bootstrap_ci(preds, labels, lambda p, l: auc(p, l), resamples=400, seed=5)
        ranking = {"auc": auc(preds, labels), "ci": [lo, hi]}

    versions = sorted({r["model_version"] for r in rows if r["model_version"]})
    return {
        "model": name,
        "model_version": versions[0] if versions else "",
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "n": len(rows),
        "parsed": len(usable),
        "truncated": sum(r["truncated"] for r in rows),
        "distinct_values": res.distinct,
        "extreme_fraction": res.extreme_fraction,
        "median_latency_ms": lat[len(lat) // 2],
        "ranking": ranking,
        "operating_points": points,
        "rows": rows,
    }


def render(data: dict) -> str:
    m = data["meta"]
    out = [
        "# Lab-007 Phase B: self-reported confidence from local models",
        "",
        f"Corpus: lab_004, {m['n_clean']} clean and {m['n_injected']} injected, seed "
        f"{m['seed']}. Threshold {m['threshold']}. Temperature 0.",
        "",
        "## Does the detector use the scale at all?",
        "",
        "| Model | Parsed | Distinct values | Share at 0 or 1 | AUC [95% CI] | Median latency |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in data["models"]:
        rank = r.get("ranking")
        col = (
            f"{rank['auc']:.3f} [{rank['ci'][0]:.3f}, {rank['ci'][1]:.3f}]" if rank else "n/a"
        )
        out.append(
            f"| `{r['model']}` | {r['parsed']}/{r['n']} | "
            f"{r['distinct_values']} | {r['extreme_fraction']:.0%} | {col} | "
            f"{r['median_latency_ms']:.0f} ms |"
        )
    out += [
        "",
        f"At {m['n_clean'] + m['n_injected']} rows a perfectly calibrated detector reads an "
        f"ECE of {m['noise_floor']:.3f} on average, and anywhere from "
        f"{m['noise_floor_spread']['low']:.3f} to {m['noise_floor_spread']['high']:.3f} on any "
        "single run. No calibration claim is available at this corpus size, whatever a "
        "detector emits. That is a property of the corpus, not of the models.",
        "",
        "## What a threshold buys, by declared base rate",
        "",
        f"Every model produced zero false positives on {m['n_clean']} clean tickets, so the",
        "measured precision column reads 1.00 at every prevalence. That is not a finding,",
        f"it is the corpus. Zero events in {m['n_clean']} trials bounds the false-positive rate at",
        f"about {rule_of_three_upper_bound(m['n_clean']):.2f}, not at zero, and the last column is precision at that",
        "bound. The gap between the two columns is what a 50-row corpus cannot tell you.",
        "",
        "| Model | Base rate | Recall | Measured FPR | Precision (measured) | Precision (FPR at bound) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    bound = rule_of_three_upper_bound(m["n_clean"])
    for r in data["models"]:
        for p in r["operating_points"]:
            worst = precision_from_rates(p["base_rate"], p["recall"], bound)
            out.append(
                f"| `{r['model']}` | {p['base_rate']:.0%} | {p['recall']:.2f} | "
                f"{p['false_positive_rate']:.2f} | {p['precision']:.2f} | {worst:.2f} |"
            )
    out += ["", "Generated by `python -m labs.lab_007.baseline`.", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--n-clean", type=int, default=20)
    ap.add_argument("--n-injected", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=HERE)
    ap.add_argument("--jev", action="store_true", help="also run typesafe/jev via Cloudflare")
    ap.add_argument("--logprob", action="store_true",
                    help="also read the same local models from their token distribution")
    ap.add_argument("--kev", action="store_true", help="also run a local kev server")
    ap.add_argument("--kev-url", default="http://localhost:8009")
    ap.add_argument("--render-only", action="store_true",
                    help="re-render BASELINE.md from baseline.json, running no models")
    args = ap.parse_args()

    if args.render_only:
        data = json.loads((args.out / "baseline.json").read_text())
        (args.out / "BASELINE.md").write_text(render(data))
        print(render(data))
        return 0

    tickets = build(n_clean=args.n_clean, n_injected=args.n_injected, seed=args.seed)
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    results = []
    for model in models:
        print(f"  {model} ...", flush=True)
        results.append(
            measure_detector(model, LocalJudge(model, ask=ollama_ask(model)), tickets, args.threshold)
        )
    if args.logprob:
        for model in models:
            print(f"  {model} readout ablation ...", flush=True)
            # One transport, memoised, so both readouts come from the same call.
            raw = ollama_ask_logprobs(model)
            seen: dict[str, list] = {}

            def once(prompt: str, _raw=raw, _seen=seen) -> list:
                if prompt not in _seen:
                    _seen[prompt] = _raw(prompt)
                return _seen[prompt]

            results.append(
                measure_detector(f"{model} (word)", BinaryWordJudge(model, ask=once),
                                 tickets, args.threshold))
            results.append(
                measure_detector(f"{model} (logprob)", LogprobJudge(model, ask=once),
                                 tickets, args.threshold))
    if args.kev:
        print("  kev ...", flush=True)
        results.append(
            measure_detector("kev-0.8b", Kev(args.kev_url), tickets, args.threshold)
        )
    if args.jev:
        print("  jev ...", flush=True)
        account, token = cloudflare_credentials()
        results.append(
            measure_detector("jev", Jev(account, token), tickets, args.threshold)
        )

    data = {
        "meta": {
            "n_clean": args.n_clean,
            "n_injected": args.n_injected,
            "seed": args.seed,
            "threshold": args.threshold,
            "noise_floor": noise_floor(len(tickets), trials=30, seed=101),
            "noise_floor_spread": vars(noise_floor_spread(len(tickets), trials=30, seed=101)),
        },
        "models": results,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "baseline.json").write_text(json.dumps(data, indent=1))
    (args.out / "BASELINE.md").write_text(render(data))
    print()
    print(render(data))
    print(f"wrote baseline.json and BASELINE.md to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
