from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class FaultFamily(StrEnum):
    BAD_DEPLOY = "bad_deploy"
    CONFIG_DRIFT = "config_drift"
    DEPENDENCY_FAILURE = "dependency_failure"
    DATA_ISSUE = "data_issue"


class IncidentBundle(BaseModel):
    logs: list[str]
    metrics: dict[str, float]
    config: dict[str, str]
    diff: str


class Incident(BaseModel):
    id: str
    fault_family: FaultFamily
    bundle: IncidentBundle
    ground_truth_root_cause: str
    ground_truth_remediation: str
    irreversible_action: str


class Hypothesis(BaseModel):
    branch: str
    claim: str
    evidence: str


class Verdict(BaseModel):
    grounded: bool
    reason: str


class Finding(BaseModel):
    incident_id: str
    root_cause: str
    proposed_remediation: str
    proposed_action: str


class RemediationDecision(BaseModel):
    approved: bool
    approver: str = "unknown"


class RunRecord(BaseModel):
    system: str
    incident_id: str
    finding: Finding | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_calls: int = 0
    latency_ms: float = 0.0
    remediation_applied: bool = False
    approved: bool = False
    resumed: bool = False
