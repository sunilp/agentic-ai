"""Lab-007 calibration instrument."""
from __future__ import annotations

import random

import pytest

from labs.lab_007.metrics import (
    bootstrap_ci,
    precision_from_rates,
    resolution,
    rule_of_three_upper_bound,
    expected_calibration_error,
    operating_point,
    reliability_curve,
)


def test_ece_is_zero_when_every_bin_matches_its_empirical_rate() -> None:
    # Ten predictions at 0.2, two of which are positive. Ten at 0.8, eight positive.
    preds = [0.2] * 10 + [0.8] * 10
    labels = [1, 1] + [0] * 8 + [1] * 8 + [0, 0]

    assert expected_calibration_error(preds, labels, bins=10) == pytest.approx(0.0, abs=1e-12)


def test_reliability_curve_reports_one_row_per_occupied_bin() -> None:
    preds = [0.15] * 4 + [0.85] * 4
    labels = [1, 0, 0, 0] + [1, 1, 1, 0]

    rows = reliability_curve(preds, labels, bins=10)

    assert [r.count for r in rows] == [4, 4]
    assert [r.observed_rate for r in rows] == [0.25, 0.75]
    assert rows[0].mean_pred == pytest.approx(0.15)
    assert rows[1].mean_pred == pytest.approx(0.85)


def _detector_90_recall_10_fpr() -> tuple[list[float], list[int]]:
    """100 positives, 100 negatives. 90% of positives and 10% of negatives score high."""
    preds = [0.9] * 90 + [0.1] * 10 + [0.9] * 10 + [0.1] * 90
    labels = [1] * 100 + [0] * 100
    return preds, labels


def test_precision_collapses_when_reweighted_to_a_rare_base_rate() -> None:
    preds, labels = _detector_90_recall_10_fpr()

    # 0.9 recall and 0.1 false-positive rate, but only 1 in 100 inputs is an attack.
    point = operating_point(preds, labels, threshold=0.5, base_rate=0.01)

    # (0.01 * 0.9) / (0.01 * 0.9 + 0.99 * 0.1)
    assert point.precision == pytest.approx(0.0833333, abs=1e-6)
    assert point.recall == pytest.approx(0.9)


def _calibrated_sample(n: int, rng: random.Random) -> tuple[list[float], list[int]]:
    """A detector whose stated probability is its true hit rate."""
    preds = [rng.choice([0.05, 0.25, 0.45, 0.65, 0.85, 0.95]) for _ in range(n)]
    labels = [int(rng.random() < p) for p in preds]
    return preds, labels


def test_bootstrap_interval_narrows_as_the_sample_grows() -> None:
    rng = random.Random(7)
    small_preds, small_labels = _calibrated_sample(60, rng)
    large_preds, large_labels = _calibrated_sample(6000, rng)

    lo_s, hi_s = bootstrap_ci(
        small_preds, small_labels, expected_calibration_error, resamples=400, seed=1
    )
    lo_l, hi_l = bootstrap_ci(
        large_preds, large_labels, expected_calibration_error, resamples=400, seed=1
    )

    assert (hi_l - lo_l) < (hi_s - lo_s)


def test_resolution_reports_a_near_binary_detector_as_having_no_interior() -> None:
    # What the local models actually do: almost every answer is 0.0 or 1.0.
    preds = [0.0] * 36 + [1.0] * 9 + [0.5] * 5

    r = resolution(preds)

    assert r.distinct == 3
    assert r.extreme_fraction == pytest.approx(0.9)


def test_rule_of_three_bounds_a_rate_after_seeing_no_failures() -> None:
    # Zero false positives in 20 clean tickets does not mean the rate is zero.
    assert rule_of_three_upper_bound(20) == pytest.approx(0.15)


def test_an_unobserved_false_positive_rate_destroys_precision_at_a_rare_base_rate() -> None:
    # 0.47 recall, and an FPR we cannot show is below 0.15, at 1% prevalence.
    assert precision_from_rates(
        base_rate=0.01, recall=0.47, false_positive_rate=0.15
    ) == pytest.approx(0.0307, abs=1e-4)
