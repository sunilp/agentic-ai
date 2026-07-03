"""Lab-002 durability harness: kill the contender at the gate, resume from
SQLite in a fresh process, and prove ADK's dedup skips completed work.

Two `SqliteSessionService` instances point at the same on-disk file across
the two phases. The second one has zero in-memory state and rehydrates
purely from the persisted event log -- that is the crash boundary this
harness measures.
"""

from __future__ import annotations

import time

from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from labs.lab_002.schema import Incident, RemediationDecision, RunRecord
from labs.lab_002.systems import (
    _APP,
    _USER,
    _context_blob,
    _extract_finding,
    _resume,
    _tally,
    build_contender,
)


async def run_with_crash(
    incident: Incident, model, db_path: str
) -> tuple[RunRecord, RunRecord]:
    """Run the contender to the human gate, "crash" it, then resume from a
    fresh SqliteSessionService over the same db file.

    Returns (pre_interrupt, post_resume) RunRecords.
    """
    session_id = f"crash-{incident.id}"

    # --- Phase 1: run to the human gate, then "crash" (drop the runner) ---
    svc1 = SqliteSessionService(db_path=db_path)
    await svc1.create_session(app_name=_APP, user_id=_USER, session_id=session_id)
    wf1 = build_contender(model)
    runner1 = Runner(agent=wf1, app_name=_APP, session_service=svc1)
    content = types.Content(role="user", parts=[types.Part(text=_context_blob(incident))])
    pre = RunRecord(system="contender", incident_id=incident.id)
    interrupt_id: str | None = None
    start = time.monotonic()
    async for event in runner1.run_async(
        session_id=session_id, user_id=_USER, new_message=content
    ):
        _tally(pre, event)
        finding = _extract_finding(event)
        if finding is not None:
            pre.finding = finding
        if event.long_running_tool_ids:
            interrupt_id = next(iter(event.long_running_tool_ids))
    pre.latency_ms = (time.monotonic() - start) * 1000
    del runner1, svc1, wf1  # simulated process death

    # --- Phase 2: fresh process, fresh service over the same db, resume ---
    svc2 = SqliteSessionService(db_path=db_path)
    reloaded = await svc2.get_session(app_name=_APP, user_id=_USER, session_id=session_id)
    wf2 = build_contender(model)
    runner2 = Runner(agent=wf2, app_name=_APP, session_service=svc2)
    post = RunRecord(
        system="contender", incident_id=incident.id, finding=pre.finding, resumed=True
    )
    decision = RemediationDecision(approved=True, approver="sre-oncall")
    start = time.monotonic()
    async for event in _resume(runner2, reloaded, interrupt_id, decision):
        _tally(post, event)
        if event.content and event.content.parts and any(
            "applied" in (part.text or "") for part in event.content.parts
        ):
            post.remediation_applied = True
    post.latency_ms = (time.monotonic() - start) * 1000
    post.approved = True
    return pre, post
