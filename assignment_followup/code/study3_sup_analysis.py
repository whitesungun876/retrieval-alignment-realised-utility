#!/usr/bin/env python3
"""Prospective target-level analysis functions for the supplemental experiment.

This module contains no supplemental outcomes and performs no file discovery.
The one-shot unblinding wrapper will pass episode rows explicitly after SUP-R5.
"""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import stats


PRIMARY_SEED = 202608030701
BOOTSTRAP_RESAMPLES = 10_000
SIGN_FLIP_RESAMPLES = 10_000
ALPHA = 0.05
EQUIVALENCE_MARGIN = 0.05


def target_condition_means(
    episode_rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Average available valid repetitions within target and condition."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in episode_rows:
        if bool(row.get("technical_failure")):
            continue
        grouped[str(row["target_id"])][str(row["condition"])].append(
            float(bool(row["terminal_success"]))
        )
    return {
        target: {
            condition: float(np.mean(values))
            for condition, values in conditions.items()
            if values
        }
        for target, conditions in grouped.items()
    }


def paired_differences(
    means: Mapping[str, Mapping[str, float]], left: str, right: str
) -> tuple[list[str], np.ndarray]:
    targets = sorted(
        target for target, conditions in means.items()
        if left in conditions and right in conditions
    )
    differences = np.asarray(
        [means[target][left] - means[target][right] for target in targets],
        dtype=float,
    )
    return targets, differences


def sign_flip_pvalue(
    differences: Sequence[float],
    resamples: int = SIGN_FLIP_RESAMPLES,
    seed: int = PRIMARY_SEED,
) -> float:
    values = np.asarray(differences, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan")
    observed = abs(float(values.mean()))
    if observed == 0:
        return 1.0
    rng = np.random.default_rng(seed)
    extreme = 0
    for start in range(0, resamples, 1_000):
        batch = min(1_000, resamples - start)
        signs = rng.choice((-1.0, 1.0), size=(batch, values.size))
        statistics = np.abs(np.mean(signs * values, axis=1))
        extreme += int(np.sum(statistics >= observed - 1e-15))
    return (extreme + 1) / (resamples + 1)


def bootstrap_ci(
    differences: Sequence[float],
    quantiles: tuple[float, float] = (0.025, 0.975),
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = PRIMARY_SEED + 1,
) -> tuple[float, float]:
    values = np.asarray(differences, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates = np.empty(resamples, dtype=float)
    for start in range(0, resamples, 1_000):
        batch = min(1_000, resamples - start)
        indices = rng.integers(0, values.size, size=(batch, values.size))
        estimates[start : start + batch] = values[indices].mean(axis=1)
    low, high = np.quantile(estimates, quantiles)
    return float(low), float(high)


def tost(
    differences: Sequence[float],
    margin: float = EQUIVALENCE_MARGIN,
    alpha: float = ALPHA,
) -> dict[str, Any]:
    """Paired-difference TOST with a two-sided 90% t interval at alpha=.05."""
    values = np.asarray(differences, dtype=float)
    values = values[np.isfinite(values)]
    n = int(values.size)
    if n < 2:
        return {
            "n": n,
            "margin": margin,
            "lower_p_one_sided": None,
            "upper_p_one_sided": None,
            "ci_90": [None, None],
            "equivalent": False,
        }
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    se = sd / math.sqrt(n)
    if se == 0:
        lower_p = 0.0 if mean > -margin else 1.0
        upper_p = 0.0 if mean < margin else 1.0
        low = high = mean
    else:
        lower_t = (mean + margin) / se
        upper_t = (mean - margin) / se
        lower_p = float(stats.t.sf(lower_t, df=n - 1))
        upper_p = float(stats.t.cdf(upper_t, df=n - 1))
        critical = float(stats.t.ppf(1 - alpha, df=n - 1))
        low, high = mean - critical * se, mean + critical * se
    equivalent = lower_p < alpha and upper_p < alpha
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "standard_error": se,
        "margin": margin,
        "alpha_one_sided": alpha,
        "lower_p_one_sided": lower_p,
        "upper_p_one_sided": upper_p,
        "ci_90": [low, high],
        "equivalent": equivalent,
    }


def comparison(
    means: Mapping[str, Mapping[str, float]],
    left: str,
    right: str,
    seed: int,
) -> dict[str, Any]:
    targets, differences = paired_differences(means, left, right)
    low, high = bootstrap_ci(differences, seed=seed + 1)
    result = {
        "contrast": f"{left}-{right}",
        "targets": len(targets),
        "risk_difference": float(differences.mean()) if differences.size else None,
        "risk_difference_percentage_points": (
            float(differences.mean() * 100) if differences.size else None
        ),
        "bootstrap_95_ci": [low, high],
        "bootstrap_95_ci_percentage_points": [low * 100, high * 100],
        "sign_flip_p_two_sided": sign_flip_pvalue(differences, seed=seed),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "sign_flip_resamples": SIGN_FLIP_RESAMPLES,
    }
    if left == "R2" and right == "P":
        result["tost"] = tost(differences)
    return result


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * value)
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def analyze(episode_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    means = target_condition_means(episode_rows)
    primary = comparison(means, "R2", "P", PRIMARY_SEED)
    secondary = [
        comparison(means, "P", "N2", PRIMARY_SEED + 10),
        comparison(means, "R2", "N2", PRIMARY_SEED + 20),
    ]
    adjusted = holm_adjust(
        {row["contrast"]: float(row["sign_flip_p_two_sided"]) for row in secondary}
    )
    for row in secondary:
        row["holm_adjusted_p"] = adjusted[row["contrast"]]
    return {
        "schema_version": "study3_sup_analysis_v1",
        "primary": primary,
        "secondary": secondary,
        "missing_data_rule": (
            "Unresolved technical failures are missing. Target-condition means use "
            "available valid repetitions; a contrast omits a target only when either "
            "condition has zero valid repetitions."
        ),
        "independent_unit": "target",
    }


__all__ = [
    "analyze",
    "bootstrap_ci",
    "comparison",
    "holm_adjust",
    "paired_differences",
    "sign_flip_pvalue",
    "target_condition_means",
    "tost",
]

