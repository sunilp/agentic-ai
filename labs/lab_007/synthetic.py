"""Detectors whose calibration is known in advance.

The instrument is pointed at these before it is pointed at anything real. If it
cannot tell one of these apart from another, its reading on a live detector is
not evidence.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

# True hit rates a synthetic detector is allowed to hold. Coarse on purpose, so
# each value lands in its own bin and a gap can be worked out by hand.
GRID = (0.05, 0.25, 0.45, 0.65, 0.85, 0.95)


def _draw(n: int, seed: int) -> tuple[list[float], list[int]]:
    """Ground truth: a real hit rate per item, and an outcome drawn from it."""
    if n <= 0:
        raise ValueError("n must be positive")
    rng = random.Random(seed)
    true_rates = [rng.choice(GRID) for _ in range(n)]
    labels = [int(rng.random() < p) for p in true_rates]
    return true_rates, labels


def calibrated(n: int, seed: int) -> tuple[list[float], list[int]]:
    """States exactly the rate at which it is right."""
    true_rates, labels = _draw(n, seed)
    return true_rates, labels


def overconfident(
    n: int, seed: int, strength: float = 0.35
) -> tuple[list[float], list[int]]:
    """Right as often as `calibrated`, but pushes every claim toward 0 or 1."""
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be between 0 and 1")
    true_rates, labels = _draw(n, seed)
    preds = [
        min(1.0, p + strength) if p >= 0.5 else max(0.0, p - strength)
        for p in true_rates
    ]
    return preds, labels


def noise_floor(n: int, bins: int = 10, trials: int = 20, seed: int = 0) -> float:
    """The ECE a perfectly calibrated detector reads on a corpus of `n` rows.

    Expected calibration error is biased upward on finite samples: each bin's
    observed rate carries sampling noise, and the metric takes the absolute
    value of every gap, so noise cannot cancel. A measured ECE is only evidence
    of miscalibration if it clears this floor.
    """
    from labs.lab_007.metrics import expected_calibration_error

    if trials <= 0:
        raise ValueError("trials must be positive")
    scores = [
        expected_calibration_error(*calibrated(n, seed=seed + i), bins=bins)
        for i in range(trials)
    ]
    return sum(scores) / len(scores)


@dataclass(frozen=True)
class FloorStats:
    """What a perfectly calibrated detector reads, and how much it varies.

    Reported as a mean with a range because it is an expected finite-sample
    value, not a lower bound. A single run can land either side of the mean,
    so quoting the mean alone invites reading it as a threshold.
    """

    mean: float
    low: float
    high: float


def noise_floor_spread(
    n: int, bins: int = 10, trials: int = 20, seed: int = 0
) -> FloorStats:
    """Mean and observed range of a calibrated detector's ECE at `n` rows."""
    from labs.lab_007.metrics import expected_calibration_error

    if trials <= 1:
        raise ValueError("need at least two trials to report a range")
    scores = [
        expected_calibration_error(*calibrated(n, seed=seed + i), bins=bins)
        for i in range(trials)
    ]
    return FloorStats(mean=sum(scores) / len(scores), low=min(scores), high=max(scores))
