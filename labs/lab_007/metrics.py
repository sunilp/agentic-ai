"""Calibration metrics for detector verdicts.

A detector that says 0.8 should be right 80% of the time. These functions
measure whether that holds.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Bin:
    """One occupied bucket of a reliability curve."""

    lower: float
    upper: float
    count: int
    mean_pred: float
    observed_rate: float

    @property
    def gap(self) -> float:
        return abs(self.mean_pred - self.observed_rate)


def _bin_index(p: float, bins: int) -> int:
    """Bin for probability p. The top edge belongs to the last bin."""
    return min(int(p * bins), bins - 1)


def _check(preds: Sequence[float], labels: Sequence[int]) -> None:
    if len(preds) != len(labels):
        raise ValueError("preds and labels must be the same length")
    if not preds:
        raise ValueError("no predictions")


def reliability_curve(
    preds: Sequence[float], labels: Sequence[int], bins: int = 10
) -> list[Bin]:
    """Per-bin stated probability against observed rate, low bin first.

    Empty bins are omitted rather than reported as zero, because a bin with no
    observations carries no evidence either way.
    """
    _check(preds, labels)

    buckets: dict[int, list[tuple[float, int]]] = {}
    for p, y in zip(preds, labels, strict=True):
        buckets.setdefault(_bin_index(p, bins), []).append((p, y))

    width = 1.0 / bins
    return [
        Bin(
            lower=idx * width,
            upper=(idx + 1) * width,
            count=len(rows),
            mean_pred=sum(p for p, _ in rows) / len(rows),
            observed_rate=sum(y for _, y in rows) / len(rows),
        )
        for idx, rows in sorted(buckets.items())
    ]


def expected_calibration_error(
    preds: Sequence[float], labels: Sequence[int], bins: int = 10
) -> float:
    """Weighted mean gap between stated probability and observed rate."""
    curve = reliability_curve(preds, labels, bins)
    total = len(preds)
    return sum((b.count / total) * b.gap for b in curve)


def precision_from_rates(
    base_rate: float, recall: float, false_positive_rate: float
) -> float:
    """Precision implied by a detector's rates at a declared prevalence."""
    flagged = base_rate * recall + (1.0 - base_rate) * false_positive_rate
    return (base_rate * recall / flagged) if flagged > 0 else 0.0


def rule_of_three_upper_bound(trials: int) -> float:
    """Roughly the 95% upper bound on a rate after zero events in `trials`.

    Observing no false positive in 20 clean items does not establish that the
    false-positive rate is zero. It establishes that it is probably under 3/20.
    At a rare base rate the difference between those two decides whether the
    detector is usable.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    return 3.0 / trials


@dataclass(frozen=True)
class OperatingPoint:
    """What a threshold buys at a declared base rate.

    Recall and false-positive rate are properties of the detector and do not
    move with prevalence. Precision does, which is the whole point of
    reporting a band rather than one number.
    """

    threshold: float
    base_rate: float
    recall: float
    false_positive_rate: float
    precision: float


def operating_point(
    preds: Sequence[float],
    labels: Sequence[int],
    threshold: float,
    base_rate: float,
) -> OperatingPoint:
    """Precision, recall and FPR at `threshold`, reweighted to `base_rate`.

    Recall and FPR are measured on the corpus as given, since each is
    conditioned on the true class and so is unaffected by prevalence.
    Precision is then recomputed at the declared base rate. There is
    deliberately no default: inheriting whatever mix the corpus happened to
    have is the error this lab exists to measure.
    """
    _check(preds, labels)
    if not 0.0 <= base_rate <= 1.0:
        raise ValueError("base_rate must be between 0 and 1")

    positives = [p for p, y in zip(preds, labels, strict=True) if y == 1]
    negatives = [p for p, y in zip(preds, labels, strict=True) if y == 0]
    if not positives or not negatives:
        raise ValueError("need both positive and negative examples")

    recall = sum(p >= threshold for p in positives) / len(positives)
    fpr = sum(p >= threshold for p in negatives) / len(negatives)

    precision = precision_from_rates(base_rate, recall, fpr)

    return OperatingPoint(
        threshold=threshold,
        base_rate=base_rate,
        recall=recall,
        false_positive_rate=fpr,
        precision=precision,
    )


def bootstrap_ci(
    preds: Sequence[float],
    labels: Sequence[int],
    statistic: Callable[[Sequence[float], Sequence[int]], float],
    resamples: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap interval for `statistic`, resampling pairs.

    Seeded, so a published interval can be reproduced exactly. Resamples that
    the statistic cannot score, such as a draw with only one class, are
    skipped rather than counted as zero.
    """
    _check(preds, labels)
    rng = random.Random(seed)
    n = len(preds)

    values: list[float] = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        try:
            values.append(statistic([preds[i] for i in idx], [labels[i] for i in idx]))
        except ValueError:
            continue

    if not values:
        raise ValueError("no resample could be scored")

    values.sort()
    lo = values[int((alpha / 2) * len(values))]
    hi = values[min(int((1 - alpha / 2) * len(values)), len(values) - 1)]
    return lo, hi


@dataclass(frozen=True)
class Resolution:
    """How much of a probability scale a detector actually uses."""

    distinct: int
    extreme_fraction: float


def resolution(preds: Sequence[float], tolerance: float = 1e-9) -> Resolution:
    """Distinct values emitted, and the share sitting at 0 or 1.

    Calibration assumes a detector has an interior: that 0.7 means something
    different from 0.9. A detector that answers only 0 and 1 has stated a label,
    not a probability, and no reliability curve can be drawn through it however
    many rows the corpus has.
    """
    if not preds:
        raise ValueError("no predictions")
    extreme = sum(p <= tolerance or p >= 1.0 - tolerance for p in preds)
    return Resolution(distinct=len(set(preds)), extreme_fraction=extreme / len(preds))
