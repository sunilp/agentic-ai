"""Lab-002 systems: baseline static ADK agent (Task 7) and contender (Task 8)."""

from __future__ import annotations

import time

from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

from labs.lab_002 import tools
from labs.lab_002.gate import ApprovalToken
from labs.lab_002.schema import Finding, Incident, RunRecord

_APP = "lab002"
_USER = "sre"

_BASELINE_INSTR = (
    "You are an incident responder. Given the incident context, output the single "
    "most likely root cause, a remediation, and the exact irreversible action to "
    "take, as JSON matching the Finding schema. Do not take the action yourself."
)


def build_baseline(model) -> Agent:
    """A single static ADK agent: one pass, one Finding, no runtime decomposition."""
    return Agent(
        name="baseline_responder",
        model=model,
        instruction=_BASELINE_INSTR,
        output_schema=Finding,
        output_key="finding",
    )


def _context_blob(incident: Incident) -> str:
    return (
        f"incident_id: {incident.id}\n"
        f"logs:\n{tools.log_search(incident)}\n"
        f"metrics: {tools.metric_query(incident)}\n"
        f"config:\n{tools.config_read(incident)}\n"
        f"diff:\n{tools.diff_read(incident)}\n"
        f"candidate action id: {incident.irreversible_action}"
    )


async def run_baseline(agent: Agent, incident: Incident, session_service) -> RunRecord:
    session = await session_service.create_session(
        app_name=_APP, user_id=_USER, session_id=f"base-{incident.id}")
    runner = Runner(agent=agent, app_name=_APP, session_service=session_service)
    content = types.Content(role="user",
                             parts=[types.Part(text=_context_blob(incident))])
    start = time.monotonic()
    finding: Finding | None = None
    calls = prompt_tok = comp_tok = 0
    async for event in runner.run_async(
            session_id=session.id, user_id=_USER, new_message=content):
        if event.usage_metadata:
            calls += 1
            prompt_tok += event.usage_metadata.prompt_token_count or 0
            comp_tok += event.usage_metadata.candidates_token_count or 0
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    try:
                        finding = Finding.model_validate_json(part.text)
                    except Exception:
                        pass
    rec = RunRecord(system="baseline", incident_id=incident.id, finding=finding,
                     prompt_tokens=prompt_tok, completion_tokens=comp_tok,
                     model_calls=calls, latency_ms=(time.monotonic() - start) * 1000)
    # static, fixed gate: apply only if the finding names the sanctioned action
    if finding and finding.proposed_action == incident.irreversible_action:
        tools.apply_remediation(
            incident.irreversible_action,
            ApprovalToken(action=incident.irreversible_action, approver="static-policy"))
        rec.remediation_applied = True
        rec.approved = True
    return rec
