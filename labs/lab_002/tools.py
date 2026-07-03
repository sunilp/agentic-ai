from __future__ import annotations

from labs.lab_002.gate import ApprovalToken, require_approval
from labs.lab_002.schema import Incident


def log_search(incident: Incident, query: str = "") -> str:
    hits = [ln for ln in incident.bundle.logs if query.lower() in ln.lower()] \
        if query else incident.bundle.logs
    return "\n".join(hits) or "no matching log lines"


def metric_query(incident: Incident, name: str = "") -> str:
    m = incident.bundle.metrics
    if name and name in m:
        return f"{name}={m[name]}"
    return ", ".join(f"{k}={v}" for k, v in m.items())


def config_read(incident: Incident) -> str:
    return "\n".join(f"{k}={v}" for k, v in incident.bundle.config.items())


def diff_read(incident: Incident) -> str:
    return incident.bundle.diff


def apply_remediation(action: str, token: ApprovalToken | None) -> str:
    """The single irreversible action. Gated by an out-of-band approval token."""
    require_approval(action, token)
    return f"remediation applied: {action}"
