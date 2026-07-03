from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from labs.lab_002.schema import FaultFamily, Incident, IncidentBundle

_PATH = Path(__file__).parent / "incidents.json"

# Per-family templates: (root_cause, remediation, action_prefix, service pool)
_TEMPLATES = {
    FaultFamily.BAD_DEPLOY: (
        "bad deploy of {svc} {ver}", "rollback {svc} to previous version",
        "rollback_deploy", ["svc-checkout", "svc-payments", "svc-search"]),
    FaultFamily.CONFIG_DRIFT: (
        "config drift on {svc}: {key} changed", "revert {key} on {svc}",
        "revert_config", ["svc-auth", "svc-orders", "svc-inventory"]),
    FaultFamily.DEPENDENCY_FAILURE: (
        "{svc} dependency {dep} timing out", "restart {svc} and fail over {dep}",
        "restart_service", ["svc-notify", "svc-ledger", "svc-catalog"]),
    FaultFamily.DATA_ISSUE: (
        "stale cache serving bad data on {svc}", "purge cache for {svc}",
        "purge_cache", ["svc-profile", "svc-pricing", "svc-feed"]),
}


def _make(idx: int, family: FaultFamily, rng: random.Random) -> Incident:
    root, remed, prefix, svcs = _TEMPLATES[family]
    svc = rng.choice(svcs)
    ver = f"v1.{rng.randint(0, 9)}.{rng.randint(0, 9)}"
    key = rng.choice(["replicas", "timeout_ms", "max_conns"])
    dep = rng.choice(["redis", "postgres", "kafka"])
    err = round(rng.uniform(0.3, 0.95), 2)
    root_cause = root.format(svc=svc, ver=ver, key=key, dep=dep)
    return Incident(
        id=f"inc-{idx:03d}",
        fault_family=family,
        bundle=IncidentBundle(
            logs=[f"[error] {svc} 5xx spike", f"[warn] {dep} latency high"],
            metrics={"err_rate": err, "p99_ms": round(rng.uniform(200, 4000), 1)},
            config={key: str(rng.randint(1, 9)), "region": rng.choice(["eu", "us"])},
            diff=f"- {svc}:{ver}\n+ {svc}:v1.{rng.randint(0, 9)}.{rng.randint(0, 9)}",
        ),
        ground_truth_root_cause=root_cause,
        ground_truth_remediation=remed.format(svc=svc, key=key, dep=dep),
        irreversible_action=f"{prefix}:{svc}@{ver}",
    )


def generate(n: int, seed: int = 42) -> list[Incident]:
    """Deterministic, family-balanced synthetic incidents."""
    rng = random.Random(seed)
    families = list(FaultFamily)
    out: list[Incident] = []
    for idx in range(n):
        family = families[idx % len(families)]
        out.append(_make(idx, family, rng))
    return out


def load(path: str | Path = _PATH) -> list[Incident]:
    data = json.loads(Path(path).read_text())
    return [Incident.model_validate(d) for d in data]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    items = generate(n, seed=42)
    _PATH.write_text(json.dumps([i.model_dump() for i in items], indent=2) + "\n")
    print(f"wrote {len(items)} incidents to {_PATH}")
