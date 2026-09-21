"""A detector that answers nothing usable is a result, not a crash.

gemma4:e2b emits a reasoning token before any answer, so its word readout parses
zero of fifty. That must be reported, not raised: the run also contains seven
other detectors that were measured successfully.
"""
from __future__ import annotations

from labs.lab_004.corpus import build
from labs.lab_007.baseline import measure_detector
from labs.lab_007.detectors import Verdict


class NeverParses:
    name = "never-parses"

    def screen(self, ticket: str) -> Verdict:
        return Verdict(0.0, 1.0, "reasoning token, no answer", parsed=False)


def test_a_detector_that_parses_nothing_is_reported_rather_than_raising() -> None:
    tickets = build(n_clean=2, n_injected=3, seed=42)

    row = measure_detector("never-parses", NeverParses(), tickets, threshold=0.5)

    assert row["parsed"] == 0
    assert row["n"] == 5
    assert row["distinct_values"] == 0
    assert row["ranking"] is None
    assert row["operating_points"] == []
