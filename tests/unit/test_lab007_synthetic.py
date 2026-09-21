"""Lab-007 instrument validation.

An instrument that cannot recover a calibration it was handed has nothing to
say about a real detector. These are the gate, not decoration.
"""
from __future__ import annotations

from labs.lab_007.metrics import expected_calibration_error
from labs.lab_007.synthetic import (
    calibrated,
    noise_floor,
    noise_floor_spread,
    overconfident,
)


def test_instrument_separates_a_calibrated_detector_from_an_overconfident_one() -> None:
    honest_preds, honest_labels = calibrated(4000, seed=11)
    liar_preds, liar_labels = overconfident(4000, seed=11, strength=0.35)

    honest_ece = expected_calibration_error(honest_preds, honest_labels)
    liar_ece = expected_calibration_error(liar_preds, liar_labels)

    assert honest_ece < 0.02, f"calibrated detector read as miscalibrated: {honest_ece}"
    assert liar_ece > 0.15, f"overconfident detector read as honest: {liar_ece}"


def test_noise_floor_falls_as_the_corpus_grows() -> None:
    small = noise_floor(200, trials=8, seed=5)
    large = noise_floor(20_000, trials=8, seed=5)

    assert small > large
    # A 200-row corpus cannot certify any detector to an ECE of 0.02, because a
    # perfectly calibrated one does not read that low at 200 rows.
    assert small > 0.02


def test_noise_floor_spread_reports_variability_not_just_a_mean() -> None:
    # The ECE a calibrated detector reads is an expected value with spread, not a
    # lower bound. Reporting only the mean invites reading it as a threshold.
    stats = noise_floor_spread(200, trials=12, seed=3)

    assert stats.low < stats.mean < stats.high
