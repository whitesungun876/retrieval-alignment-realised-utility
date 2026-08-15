#!/usr/bin/env python3
"""Frozen target-level analysis functions for Study 3 Protocol v3.2."""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


PRIMARY_SEED = 202607301001
BOOTSTRAP_RESAMPLES = 10_000
SIGN_FLIP_RESAMPLES = 10_000


def target_condition_means(
    episode_rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Average valid repetitions; unresolved technical failures remain missing."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in episode_rows:
        if bool(row.get("technical_failure")):
            continue
        grouped[str(row["target_id"])][str(row["condition"])].append(
            float(bool(row["terminal_success"]))
        )
    return {
        target: {condition: float(np.mean(values)) for condition, values in arms.items() if values}
        for target, arms in grouped.items()
    }


def paired_differences(
    means: Mapping[str, Mapping[str, float]], left: str, right: str
) -> tuple[list[str], np.ndarray]:
    targets = sorted(
        target for target, arms in means.items() if left in arms and right in arms
    )
    return targets, np.array(
        [float(means[target][left] - means[target][right]) for target in targets],
        dtype=float,
    )


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
    for start in range(0, resamples, 1000):
        batch = min(1000, resamples - start)
        signs = rng.choice((-1.0, 1.0), size=(batch, values.size))
        statistics = np.abs(np.mean(signs * values, axis=1))
        extreme += int(np.sum(statistics >= observed - 1e-15))
    return (extreme + 1) / (resamples + 1)


def cluster_bootstrap_ci(
    differences: Sequence[float],
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = PRIMARY_SEED + 1,
) -> tuple[float, float]:
    values = np.asarray(differences, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    estimates = np.empty(resamples, dtype=float)
    for start in range(0, resamples, 1000):
        batch = min(1000, resamples - start)
        indices = rng.integers(0, values.size, size=(batch, values.size))
        estimates[start : start + batch] = values[indices].mean(axis=1)
    low, high = np.quantile(estimates, (0.025, 0.975))
    return float(low), float(high)


def comparison(
    means: Mapping[str, Mapping[str, float]],
    left: str,
    right: str,
    seed: int,
) -> dict[str, Any]:
    targets, differences = paired_differences(means, left, right)
    low, high = cluster_bootstrap_ci(differences, seed=seed + 1)
    return {
        "contrast": f"{left}-{right}",
        "targets": len(targets),
        "risk_difference": float(np.mean(differences)) if differences.size else None,
        "risk_difference_percentage_points": (
            float(np.mean(differences) * 100) if differences.size else None
        ),
        "bootstrap_95_ci": [low, high],
        "bootstrap_95_ci_percentage_points": [low * 100, high * 100],
        "sign_flip_p_two_sided": sign_flip_pvalue(differences, seed=seed),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "sign_flip_resamples": SIGN_FLIP_RESAMPLES,
    }


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


def mixed_model_sensitivity(episode_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """MAP logistic random-intercept sensitivity model using statsmodels."""
    import pandas as pd
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    valid = [row for row in episode_rows if not bool(row.get("technical_failure"))]
    data = pd.DataFrame(
        {
            "success": [int(bool(row["terminal_success"])) for row in valid],
            "condition": [str(row["condition"]) for row in valid],
            "target_id": [str(row["target_id"]) for row in valid],
        }
    )
    model = BinomialBayesMixedGLM.from_formula(
        "success ~ C(condition, Treatment(reference='R'))",
        {"target_random_intercept": "0 + C(target_id)"},
        data,
    )
    fit = model.fit_map()
    names = list(model.exog_names)
    coefficients = []
    for index, name in enumerate(names):
        estimate = float(fit.params[index])
        standard_error = float(fit.fe_sd[index])
        z = estimate / standard_error if standard_error > 0 else float("nan")
        p = float(2 * (0.5 * math.erfc(abs(z) / math.sqrt(2))))
        coefficients.append(
            {
                "term": name,
                "log_odds": estimate,
                "standard_error": standard_error,
                "z": z,
                "p_two_sided": p,
            }
        )
    return {
        "model": "BinomialBayesMixedGLM MAP logistic random intercept",
        "target_random_intercept": True,
        "valid_episodes": len(valid),
        "coefficients": coefficients,
        "converged_assessment": str(getattr(fit, "optim_retvals", {})),
    }


def analyze(
    episode_rows: Sequence[Mapping[str, Any]],
    retrieval_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    means = target_condition_means(episode_rows)
    primary = comparison(means, "H", "R", PRIMARY_SEED)
    secondary = [
        comparison(means, "R", "N", PRIMARY_SEED + 10),
        comparison(means, "D", "R", PRIMARY_SEED + 20),
        comparison(means, "H", "D", PRIMARY_SEED + 30),
    ]
    adjusted = holm_adjust(
        {row["contrast"]: float(row["sign_flip_p_two_sided"]) for row in secondary}
    )
    for row in secondary:
        row["holm_adjusted_p"] = adjusted[row["contrast"]]
    return {
        "primary": primary,
        "secondary": secondary,
        "mixed_model_sensitivity": mixed_model_sensitivity(episode_rows),
        "retrieval_counts": {
            "targets": len(retrieval_rows),
            "H_R_same_source": sum(bool(row["R_H_same_source"]) for row in retrieval_rows),
            "H_R_different_source": sum(not bool(row["R_H_same_source"]) for row in retrieval_rows),
        },
        "missing_data_rule": (
            "Unresolved technical failures are missing. A target-condition mean uses "
            "all available repetitions; a contrast omits a target only if either "
            "condition has zero valid repetitions."
        ),
    }


__all__ = [
    "analyze",
    "cluster_bootstrap_ci",
    "comparison",
    "holm_adjust",
    "paired_differences",
    "sign_flip_pvalue",
    "target_condition_means",
]
