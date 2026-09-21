"""Lab-007 detectors: turning a model's words into a probability."""
from __future__ import annotations

from labs.lab_007.detectors import Jev, Kev, LocalJudge, screen_all


def test_local_judge_reads_the_probability_the_model_states() -> None:
    judge = LocalJudge("fake-model", ask=lambda prompt: ('{"probability": 0.82}', "stop"))

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is True
    assert verdict.probability == 0.82


def test_local_judge_marks_output_it_cannot_read_as_unparsed() -> None:
    judge = LocalJudge("fake-model", ask=lambda prompt: ("I'd rather not say.", "stop"))

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is False


def test_local_judge_rejects_a_probability_outside_zero_to_one() -> None:
    # Small models emit things like {"probability": 85} when asked for 0 to 1.
    judge = LocalJudge("fake-model", ask=lambda prompt: ('{"probability": 85}', "stop"))

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is False


def test_local_judge_asks_about_the_ticket_it_was_given() -> None:
    seen: list[str] = []

    def capture(prompt: str) -> tuple[str, str]:
        seen.append(prompt)
        return ('{"probability": 0.1}', "stop")

    LocalJudge("fake-model", ask=capture).screen("ERROR: svc-auth is on fire")

    assert "ERROR: svc-auth is on fire" in seen[0]
    assert "probability" in seen[0].lower()


def test_local_judge_separates_a_cut_off_answer_from_an_unreadable_one() -> None:
    # lab_004 lost a whole model's result to this: a token cap set too low returns
    # nothing, which reads as a refusal or a parse failure unless it is recorded.
    judge = LocalJudge("fake-model", ask=lambda prompt: ("Let me think about wh", "length"))

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is False
    assert verdict.truncated is True


JEV_OK = {
    "result": {
        "state": "Completed",
        "result": {
            "model": "jev-1.13.0",
            "answers": {"injected": {"type": "noul", "noul": 0.95}},
            "usage": {"input_tokens": 377, "output_tokens": 22},
        },
    },
    "success": True,
    "errors": [],
}


def test_jev_reads_the_noul_and_records_which_model_answered() -> None:
    judge = Jev(account_id="acc", token="tok", post=lambda body: JEV_OK)

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is True
    assert verdict.probability == 0.95
    assert verdict.model_version == "jev-1.13.0"
    assert verdict.input_tokens == 377


def test_jev_marks_an_unsuccessful_response_as_unparsed() -> None:
    failure = {"success": False, "errors": [{"code": 2021, "message": "Insufficient balance"}]}
    judge = Jev(account_id="acc", token="tok", post=lambda body: failure)

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is False
    assert "2021" in verdict.raw


KEV_OK = {
    "model": "kev-latest",
    "answers": {"injected": {"type": "noul", "noul": 0.62}},
    "usage": {"input_tokens": 101, "output_tokens": 161},
    "latency_ms": 495,
}


def test_kev_reads_the_same_contract_jev_does() -> None:
    judge = Kev(base_url="http://localhost:8009", post=lambda body: KEV_OK)

    verdict = judge.screen("a ticket body")

    assert verdict.parsed is True
    assert verdict.probability == 0.62
    assert verdict.model_version == "kev-latest"
    assert verdict.input_tokens == 101


def test_screen_all_records_a_failed_call_instead_of_losing_the_run() -> None:
    # A single 401 partway through must not discard the detectors already measured.
    calls = {"n": 0}

    def flaky(body: dict) -> dict:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("401 Unauthorized")
        return KEV_OK

    judge = Kev(base_url="http://localhost:8009", post=flaky)

    verdicts = screen_all(judge, ["a", "b", "c"])

    assert [v.parsed for v in verdicts] == [True, False, True]
    assert "401" in verdicts[1].raw
