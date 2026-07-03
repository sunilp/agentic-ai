"""Lab-002 systems: baseline static ADK agent (Task 7) and contender (Task 8)."""

from __future__ import annotations

import time

from google.adk import Agent, Context, Event, Workflow
from google.adk.events import RequestInput
from google.adk.runners import Runner
from google.adk.workflow import node

# Private ADK module: no public re-export exists for the resume-response helper in
# 2.3.0. Verified against google-adk 2.3.0; pyproject pins ~=2.3.0 to keep this path
# stable. If a later ADK release relocates it, update this import.
from google.adk.workflow.utils._workflow_hitl_utils import create_request_input_response
from google.genai import types

from labs.lab_002 import tools
from labs.lab_002.gate import ApprovalToken
from labs.lab_002.schema import (
    Finding,
    Hypothesis,
    Incident,
    RemediationDecision,
    RunRecord,
    Verdict,
)

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


# --- Contender: dynamic Workflow graph with a human-in-the-loop gate (Task 8) ---

_MAX_RETRY = 2
_BRANCHES = ("deploy", "config", "dependency", "data")

_INVESTIGATOR_INSTR = (
    "You are investigating one angle of an incident. The input starts with a "
    "'branch: <name>' line naming which angle to investigate, followed by the "
    "incident context. Given that, return a Hypothesis: branch (echo the branch "
    "name given to you), claim (what you think happened on this branch), and "
    "evidence (the specific log/metric/config/diff lines that support it)."
)
_VERIFIER_INSTR = (
    "You are a strict verifier. Given a Hypothesis and the original incident "
    "context, judge whether the hypothesis's claim is actually grounded in the "
    "evidence present in the incident context. Return a Verdict: grounded "
    "(true only if the evidence genuinely supports the claim) and reason."
)
_SYNTHESIZER_INSTR = (
    "Combine the confirmed hypotheses (if any) and the incident context into "
    "one Finding: incident_id (copy the incident_id line verbatim), root_cause, "
    "proposed_remediation, and proposed_action (copy the candidate action id "
    "line verbatim). If no hypotheses were confirmed, use the incident context "
    "directly to produce your best-effort Finding."
)


def build_contender(model) -> Workflow:
    """Dynamic investigator/verifier fan-out, synthesized into a Finding that
    pauses at a human approval gate before the irreversible remediation runs.
    """
    investigator = Agent(
        name="investigator", model=model, output_schema=Hypothesis,
        output_key="hypothesis", instruction=_INVESTIGATOR_INSTR)
    verifier = Agent(
        name="verifier", model=model, output_schema=Verdict, output_key="verdict",
        instruction=_VERIFIER_INSTR)
    synthesizer = Agent(
        name="synthesizer", model=model, output_schema=Finding,
        output_key="finding", instruction=_SYNTHESIZER_INSTR)

    @node(rerun_on_resume=True)
    async def investigate(ctx: Context, node_input: str):
        confirmed: list[Hypothesis] = []
        for branch in _BRANCHES:
            for _ in range(_MAX_RETRY):
                h = Hypothesis.model_validate(await ctx.run_node(
                    investigator, node_input=f"branch: {branch}\n{node_input}"))
                v = Verdict.model_validate(await ctx.run_node(
                    verifier, node_input=f"{h.model_dump_json()}\n\n"
                                         f"incident context:\n{node_input}"))
                if v.grounded:
                    confirmed.append(h)
                    break
        synth_input = (
            "confirmed hypotheses:\n"
            + ("\n".join(h.model_dump_json() for h in confirmed)
               if confirmed else "(none confirmed)")
            + f"\n\nincident context:\n{node_input}"
        )
        finding = Finding.model_validate(
            await ctx.run_node(synthesizer, node_input=synth_input))
        yield finding

    def gate(finding: Finding):
        # Returning a RequestInput pauses the workflow until a human responds.
        return RequestInput(
            interrupt_id="remediation_approval",
            message="Approve remediation before it touches prod.",
            payload=finding, response_schema=RemediationDecision)

    def apply(finding: Finding, node_input: RemediationDecision):
        if node_input.approved:
            tok = ApprovalToken(action=finding.proposed_action, approver=node_input.approver)
            tools.apply_remediation(finding.proposed_action, tok)
            text = f"applied {finding.proposed_action}"
        else:
            text = "remediation denied"
        yield Event(content=types.Content(role="model", parts=[types.Part(text=text)]))

    return Workflow(name="contender", edges=[("START", investigate, gate, apply)])


def _tally(rec: RunRecord, event: Event) -> None:
    """Accumulate model-call/token counters from a run event, in place."""
    if event.usage_metadata:
        rec.model_calls += 1
        rec.prompt_tokens += event.usage_metadata.prompt_token_count or 0
        rec.completion_tokens += event.usage_metadata.candidates_token_count or 0


def _extract_finding(event: Event) -> Finding | None:
    """Try to parse a Finding out of any text part of the event."""
    if not (event.content and event.content.parts):
        return None
    for part in event.content.parts:
        if part.text:
            try:
                return Finding.model_validate_json(part.text)
            except Exception:
                pass
    return None


async def _resume(runner: Runner, session, interrupt_id: str, decision: RemediationDecision):
    """Resume a paused run by answering the given interrupt on the same session."""
    part = create_request_input_response(interrupt_id, decision.model_dump())
    content = types.Content(role="user", parts=[part])
    async for event in runner.run_async(
            session_id=session.id, user_id=_USER, new_message=content):
        yield event


async def run_contender(workflow: Workflow, incident: Incident, session_service,
                         *, auto_approve: bool) -> RunRecord:
    session = await session_service.create_session(
        app_name=_APP, user_id=_USER, session_id=f"cont-{incident.id}")
    runner = Runner(agent=workflow, app_name=_APP, session_service=session_service)
    content = types.Content(role="user",
                             parts=[types.Part(text=_context_blob(incident))])
    start = time.monotonic()
    rec = RunRecord(system="contender", incident_id=incident.id)
    interrupt_id: str | None = None
    async for event in runner.run_async(
            session_id=session.id, user_id=_USER, new_message=content):
        _tally(rec, event)
        finding = _extract_finding(event)
        if finding is not None:
            rec.finding = finding
        if event.long_running_tool_ids:
            interrupt_id = next(iter(event.long_running_tool_ids))
    if auto_approve and interrupt_id and rec.finding is not None:
        decision = RemediationDecision(approved=True, approver="sre-oncall")
        async for event in _resume(runner, session, interrupt_id, decision):
            _tally(rec, event)
            if event.content and event.content.parts and any(
                    "applied" in (part.text or "") for part in event.content.parts):
                rec.remediation_applied = True
        rec.approved = True
        rec.resumed = True
    rec.latency_ms = (time.monotonic() - start) * 1000
    return rec
