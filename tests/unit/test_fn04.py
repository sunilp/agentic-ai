"""Tests for the FN-004 prompted-stop vs enforced-stop loop.

These tests are the proof behind the Field Note: the same scripted agent,
run two ways. The prompted loop deletes the database on a hallucinated
"done"; the enforced loop cannot, by construction.
"""

from src.fn04.loop import (
    ApprovalGate,
    Database,
    Done,
    LoopResult,
    StopReason,
    Tool,
    ToolCall,
    run_enforced,
    run_prompted,
)


def _delete_tool(db: Database) -> dict[str, Tool]:
    return {
        "read_rows": Tool("read_rows", lambda: list(db.rows)),
        "delete_all": Tool("delete_all", db.delete_all, destructive=True),
    }


def test_prompted_loop_deletes_database_on_hallucinated_done():
    db = Database()
    tools = _delete_tool(db)
    # The agent calls the destructive tool, then claims it is finished.
    agent = iter([ToolCall("delete_all"), Done()])

    result = run_prompted(agent, tools, db)

    assert db.deleted is True
    assert result.stop_reason is StopReason.AGENT_DONE
    assert ToolCall("delete_all") in result.executed_calls


def test_enforced_loop_blocks_destructive_call_without_approval():
    db = Database()
    tools = _delete_tool(db)
    agent = iter([ToolCall("delete_all"), Done()])

    result = run_enforced(agent, tools, db, approval=ApprovalGate())

    assert db.deleted is False
    assert ToolCall("delete_all") in result.blocked_calls
    assert ToolCall("delete_all") not in result.executed_calls


def test_enforced_loop_allows_destructive_call_with_out_of_band_approval():
    db = Database()
    tools = _delete_tool(db)
    call = ToolCall("delete_all")
    gate = ApprovalGate()
    gate.grant(call)  # granted out of band, by a principal the agent is not
    agent = iter([call, Done()])

    result = run_enforced(agent, tools, db, approval=gate)

    assert db.deleted is True
    assert ToolCall("delete_all") in result.executed_calls


def test_enforced_loop_halts_on_iteration_cap():
    db = Database()
    tools = {"noop": Tool("noop", lambda i: i)}

    def runaway():
        i = 0
        while True:
            i += 1
            yield ToolCall("noop", {"i": i})  # distinct each turn, never says done

    result = run_enforced(runaway(), tools, db, max_iterations=5)

    assert result.stop_reason is StopReason.MAX_ITERATIONS
    assert result.iterations == 5


def test_enforced_loop_halts_on_no_progress():
    db = Database()
    tools = {"spin": Tool("spin", lambda: None)}
    # Same call, same args, every turn: no new information, no progress.
    agent = iter([ToolCall("spin"), ToolCall("spin"), ToolCall("spin")])

    result = run_enforced(agent, tools, db, max_iterations=100)

    assert result.stop_reason is StopReason.NO_PROGRESS
    assert result.iterations < 100


def test_loop_result_shape():
    result = LoopResult(
        stop_reason=StopReason.AGENT_DONE,
        iterations=0,
        blocked_calls=[],
        executed_calls=[],
    )
    assert result.stop_reason is StopReason.AGENT_DONE
    assert result.blocked_calls == []
