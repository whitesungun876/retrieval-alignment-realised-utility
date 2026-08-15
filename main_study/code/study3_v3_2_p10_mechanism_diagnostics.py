#!/usr/bin/env python3
"""Post-P10 alignment, mechanism, and deterministic failure diagnostics.

This script does not alter or rerun the preserved P10 confirmatory analysis.
The offline diagnostics were prespecified descriptively in Protocol v3.2
Section 14.6. Subset utility estimates are exploratory mechanism diagnostics.
The failure categories were named in Section 14.6, but the executable decision
rules below were operationalised after unblinding and are labelled accordingly.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import io
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

os.environ.setdefault("MPLCONFIGDIR", "/tmp/study3_v3_2_matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from study3_v3_2_analysis import comparison, target_condition_means
from study3_v3_2_common import ROOT, STUDY, read_json, read_jsonl, sha256_path, utc_now, write_json


OUTCOMES = STUDY / "results/p10_episode_outcomes_first.jsonl"
CONFIRMATORY = STUDY / "results/p10_confirmatory_analysis_first.json"
RETRIEVAL = STUDY / "formal/retrieval_selections.jsonl"
TARGETS = STUDY / "formal/selected_targets.jsonl"
RAW_RECORDS = STUDY / "formal/raw_records"

RESULT_JSON = STUDY / "results/p10_mechanism_diagnostics.json"
CONTRAST_CSV = STUDY / "results/p10_mechanism_contrasts.csv"
FAILURE_CSV = STUDY / "results/p10_failure_taxonomy.csv"
FIGURE = STUDY / "results/p10_alignment_utility_gap.png"
PROVENANCE = STUDY / "reports/p10_mechanism_diagnostics_provenance.json"

EXPECTED_OUTCOME_SHA256 = "b9f65029e91cdb004b631a8eceb95765eb3e89963e94fb3c09b06238c669d444"
EXPECTED_CONFIRMATORY_SHA256 = "6819bf17608dc8a3bc2bd544a4d6fde54115227f8ce3ee0cff8d175309f6638d"
EXPECTED_RETRIEVAL_SHA256 = "cd2e3f715f7f87ecc0256ebc00638558d58659b3d38c982231ba83a3fb1f0afd"


def require_frozen_inputs() -> None:
    if RESULT_JSON.exists() or PROVENANCE.exists():
        raise RuntimeError("Mechanism diagnostic output already exists; refusing to overwrite it.")
    expected = {
        OUTCOMES: EXPECTED_OUTCOME_SHA256,
        CONFIRMATORY: EXPECTED_CONFIRMATORY_SHA256,
        RETRIEVAL: EXPECTED_RETRIEVAL_SHA256,
    }
    for path, digest in expected.items():
        if sha256_path(path) != digest:
            raise RuntimeError(f"Frozen input hash mismatch: {path}")


def exact_binomial_two_sided_all_one(discordant: int) -> float:
    """Exact McNemar/binomial p when all discordant pairs favour H."""
    return math.ldexp(1.0, 1 - discordant)


def alignment_bootstrap_difference(
    retrieval_rows: list[Mapping[str, Any]], seed: int = 202608030201
) -> list[float]:
    differences = np.array(
        [
            float(bool(row["H_structural_match"]))
            - float(bool(row["R_structural_match"]))
            for row in retrieval_rows
        ],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    estimates = np.empty(10_000, dtype=float)
    for start in range(0, 10_000, 1_000):
        indices = rng.integers(0, len(differences), size=(1_000, len(differences)))
        estimates[start : start + 1_000] = differences[indices].mean(axis=1)
    return [float(value) for value in np.quantile(estimates, (0.025, 0.975))]


def parse_transformation(action: str) -> tuple[str, str] | None:
    for operation in ("chop", "slice", "dice"):
        prefix = f"{operation} "
        if action.startswith(prefix):
            return operation, action[len(prefix) :]
    if action.startswith("cook ") and " in " in action:
        ingredient, device = action[5:].rsplit(" in ", 1)
        operation = {"stove": "fry", "oven": "roast", "barbeque": "grill"}.get(
            device, f"cook:{device}"
        )
        return operation, ingredient
    return None


def classify_episode_failure(
    outcome: Mapping[str, Any], record: Mapping[str, Any], target: Mapping[str, Any]
) -> dict[str, Any] | None:
    if bool(outcome["technical_failure"]) or bool(outcome["terminal_success"]):
        return None

    chains = {str(name): [str(op) for op in chain] for name, chain in target["chains"].items()}
    progress = {name: 0 for name in chains}
    invalid_actions = sum(not bool(step["action_was_admissible"]) for step in record["trajectory"])
    result: dict[str, Any] = {
        "target_id": str(outcome["target_id"]),
        "condition": str(outcome["condition"]),
        "repetition": int(outcome["repetition"]),
        "selected_record_run_id": str(outcome["selected_record_run_id"]),
        "terminal_reason": str(record["run"]["terminal_reason"]),
        "step_count": int(record["run"]["step_count"]),
        "invalid_action_count": int(invalid_actions),
        "failure_category": None,
        "failure_subcategory": None,
        "first_irreversible_step": None,
        "first_irreversible_action": None,
        "ingredient": None,
        "observed_operation": None,
        "expected_next_operation": None,
    }

    for step in record["trajectory"]:
        action = str(step["chosen_action"])
        parsed = parse_transformation(action)
        if bool(step["task_failure"]):
            result["first_irreversible_step"] = int(step["step"])
            result["first_irreversible_action"] = action
            if parsed is not None:
                operation, ingredient = parsed
                chain = chains.get(ingredient, [])
                position = progress.get(ingredient, 0)
                expected = chain[position] if position < len(chain) else None
                other_expected = {
                    other_chain[progress[name]]
                    for name, other_chain in chains.items()
                    if name != ingredient and progress[name] < len(other_chain)
                }
                result.update(
                    {
                        "ingredient": ingredient,
                        "observed_operation": operation,
                        "expected_next_operation": expected,
                    }
                )
                if operation in chain[position + 1 :]:
                    result["failure_category"] = "within_chain_order_error"
                    result["failure_subcategory"] = "later_required_operation_executed_early"
                else:
                    result["failure_category"] = "operation_to_ingredient_error"
                    if expected is None:
                        subtype = "operation_on_nonrequired_or_completed_ingredient"
                    elif operation in other_expected:
                        subtype = "operation_allocated_to_wrong_ingredient_role"
                    else:
                        subtype = "wrong_operation_for_ingredient"
                    result["failure_subcategory"] = subtype
            elif action.startswith("eat ") and action != "eat meal":
                result["failure_category"] = "premature_ingredient_consumption"
                result["failure_subcategory"] = "ingredient_eaten_before_meal_completion"
                result["ingredient"] = action[4:]
            elif action == "prepare meal":
                result["failure_category"] = "premature_prepare_meal"
                result["failure_subcategory"] = "meal_prepared_before_recipe_completion"
            else:
                result["failure_category"] = "other_irreversible_recipe_error"
                result["failure_subcategory"] = "environment_task_failure_unclassified_action"
            return result

        if parsed is not None:
            operation, ingredient = parsed
            chain = chains.get(ingredient, [])
            position = progress.get(ingredient, 0)
            if position < len(chain) and operation == chain[position]:
                progress[ingredient] = position + 1

    if str(record["run"]["terminal_reason"]) == "max_steps":
        result["failure_category"] = "navigation_or_step_limit_failure"
        result["failure_subcategory"] = "step_limit_without_irreversible_recipe_error"
    else:
        result["failure_category"] = "other_nonterminal_failure"
        result["failure_subcategory"] = "non_success_without_environment_task_failure"
    return result


def target_level_contrast(
    means: Mapping[str, Mapping[str, float]],
    target_ids: Iterable[str],
    left: str,
    right: str,
    seed: int,
) -> dict[str, Any]:
    subset = {target_id: means[target_id] for target_id in target_ids}
    return comparison(subset, left, right, seed)


def csv_text(rows: list[Mapping[str, Any]]) -> str:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def make_figure(
    alignment: Mapping[str, float], target_success: Mapping[str, float], path: Path
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(9.4, 4.3), constrained_layout=True)
    methods = ["R", "D", "H"]
    colors = ["#777777", "#4593B8", "#1261A0"]
    values = [100 * alignment[name] for name in methods]
    axes[0].bar(methods, values, color=colors)
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Exact anonymous-chain match (%)")
    axes[0].set_title("Offline retrieval alignment")
    for index, value in enumerate(values):
        axes[0].text(index, value + 1.5, f"{value:.1f}", ha="center")

    conditions = ["N", "R", "D", "H"]
    values = [100 * target_success[name] for name in conditions]
    axes[1].bar(conditions, values, color=["#BBBBBB"] + colors)
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("Mean target terminal success (%)")
    axes[1].set_title("Online realised utility")
    for index, value in enumerate(values):
        axes[1].text(index, value + 1.5, f"{value:.1f}", ha="center")
    figure.suptitle("Study 3 retrieval–execution gap")
    figure.savefig(path, dpi=220)
    plt.close(figure)


def main() -> None:
    require_frozen_inputs()
    retrieval = read_jsonl(RETRIEVAL)
    outcomes = read_jsonl(OUTCOMES)
    confirmatory = read_json(CONFIRMATORY)
    targets = {str(row["task_id"]): row for row in read_jsonl(TARGETS)}
    means = target_condition_means(outcomes)

    alignment_counts = {
        method: sum(bool(row[f"{method}_structural_match"]) for row in retrieval)
        for method in ("R", "D", "H")
    }
    alignment_rates = {method: count / len(retrieval) for method, count in alignment_counts.items()}
    h_match_r_mismatch = sum(
        bool(row["H_structural_match"]) and not bool(row["R_structural_match"])
        for row in retrieval
    )
    r_match_h_mismatch = sum(
        bool(row["R_structural_match"]) and not bool(row["H_structural_match"])
        for row in retrieval
    )
    alignment_ci = alignment_bootstrap_difference(retrieval)

    strict_rows = [
        row
        for row in retrieval
        if not bool(row["R_structural_match"])
        and bool(row["H_structural_match"])
        and not bool(row["R_H_same_source"])
    ]
    disagreement_rows = [row for row in retrieval if not bool(row["R_H_same_source"])]
    strict_ids = [str(row["target_id"]) for row in strict_rows]
    disagreement_ids = [str(row["target_id"]) for row in disagreement_rows]
    strict_hr = target_level_contrast(means, strict_ids, "H", "R", 202608030301)
    strict_rn = target_level_contrast(means, strict_ids, "R", "N", 202608030311)
    disagreement_hr = target_level_contrast(
        means, disagreement_ids, "H", "R", 202608030321
    )

    failure_rows: list[dict[str, Any]] = []
    invalid_actions_all = Counter()
    for outcome in outcomes:
        if bool(outcome["technical_failure"]):
            continue
        record_path = RAW_RECORDS / f"{outcome['selected_record_run_id']}.json"
        record = read_json(record_path)
        invalid_actions_all[str(outcome["condition"])] += sum(
            not bool(step["action_was_admissible"]) for step in record["trajectory"]
        )
        failure = classify_episode_failure(outcome, record, targets[str(outcome["target_id"])])
        if failure is not None:
            failure_rows.append(failure)

    failure_counts = Counter(str(row["failure_category"]) for row in failure_rows)
    failure_subcounts = Counter(str(row["failure_subcategory"]) for row in failure_rows)
    failure_by_condition: dict[str, dict[str, int]] = {}
    for condition in ("N", "R", "D", "H"):
        selected = [row for row in failure_rows if row["condition"] == condition]
        counts = Counter(str(row["failure_category"]) for row in selected)
        failure_by_condition[condition] = {
            "failures": len(selected),
            **{category: counts.get(category, 0) for category in sorted(failure_counts)},
        }
    if len(failure_rows) != 1_129 or sum(failure_counts.values()) != 1_129:
        raise RuntimeError("Failure classifier did not cover exactly all 1,129 valid failures.")
    if failure_counts.get("other_nonterminal_failure", 0) or failure_counts.get(
        "other_irreversible_recipe_error", 0
    ):
        raise RuntimeError("Unexpected unclassified failure remained.")

    condition_target_success = {
        condition: float(np.mean([arms[condition] for arms in means.values()]))
        for condition in ("N", "R", "D", "H")
    }
    result = {
        "schema_version": "study3_v3_2_p10_mechanism_diagnostics_v1",
        "created_at_utc": utc_now(),
        "analysis_status": {
            "confirmatory_output_unchanged": True,
            "offline_alignment": "prespecified descriptive diagnostic (Protocol v3.2 Section 14.6)",
            "strict_correction_subset": "exploratory mechanism diagnostic; does not replace the all-target primary result",
            "failure_taxonomy": "categories prespecified in Section 14.6; executable priority rules operationalised after unblinding",
        },
        "offline_alignment": {
            "definition": "exact equality of anonymous multisets of ordered ingredient transformation chains",
            "targets": len(retrieval),
            "match_counts": alignment_counts,
            "match_rates": alignment_rates,
            "H_minus_R_percentage_points": 100 * (alignment_rates["H"] - alignment_rates["R"]),
            "H_minus_R_target_bootstrap_95_ci_percentage_points": [100 * x for x in alignment_ci],
            "paired_discordance": {
                "H_match_R_mismatch": h_match_r_mismatch,
                "R_match_H_mismatch": r_match_h_mismatch,
                "exact_mcnemar_two_sided_p": exact_binomial_two_sided_all_one(
                    h_match_r_mismatch
                ),
            },
            "D_H_same_source": sum(bool(row["D_H_same_source"]) for row in retrieval),
        },
        "mechanism_subsets": {
            "strict_correction_definition": "R structural mismatch, H structural match, and different selected source",
            "strict_correction_targets": len(strict_ids),
            "strict_correction_H_minus_R": strict_hr,
            "strict_correction_R_minus_N": strict_rn,
            "H_R_source_disagreement_targets": len(disagreement_ids),
            "disagreement_H_minus_R": disagreement_hr,
        },
        "failure_diagnostics": {
            "valid_failures": len(failure_rows),
            "category_counts": dict(sorted(failure_counts.items())),
            "category_fractions_of_failures": {
                key: value / len(failure_rows) for key, value in sorted(failure_counts.items())
            },
            "subcategory_counts": dict(sorted(failure_subcounts.items())),
            "by_condition": failure_by_condition,
            "invalid_action_counts_all_valid_episodes": dict(invalid_actions_all),
            "classification_coverage": 1.0,
            "within_chain_order_errors_observed": failure_counts.get(
                "within_chain_order_error", 0
            ),
        },
        "condition_target_success_rates": condition_target_success,
        "confirmatory_primary_for_reference": confirmatory["primary"],
    }

    contrast_rows = []
    for label, status, value in (
        ("strict-correction H-R", "exploratory mechanism", strict_hr),
        ("strict-correction R-N", "exploratory mechanism", strict_rn),
        ("source-disagreement H-R", "exploratory mechanism", disagreement_hr),
    ):
        contrast_rows.append(
            {
                "analysis": label,
                "status": status,
                "targets": value["targets"],
                "risk_difference_percentage_points": value[
                    "risk_difference_percentage_points"
                ],
                "ci_95_low_percentage_points": value[
                    "bootstrap_95_ci_percentage_points"
                ][0],
                "ci_95_high_percentage_points": value[
                    "bootstrap_95_ci_percentage_points"
                ][1],
                "sign_flip_p_two_sided": value["sign_flip_p_two_sided"],
            }
        )

    write_json(RESULT_JSON, result)
    CONTRAST_CSV.write_text(csv_text(contrast_rows), encoding="utf-8")
    FAILURE_CSV.write_text(csv_text(failure_rows), encoding="utf-8")
    make_figure(alignment_rates, condition_target_success, FIGURE)
    write_json(
        PROVENANCE,
        {
            "schema_version": "study3_v3_2_p10_mechanism_diagnostics_provenance_v1",
            "created_at_utc": utc_now(),
            "confirmatory_analysis_rerun": False,
            "input_hashes": {
                str(path.relative_to(ROOT)): sha256_path(path)
                for path in (OUTCOMES, CONFIRMATORY, RETRIEVAL, TARGETS)
            },
            "output_hashes": {
                str(path.relative_to(ROOT)): sha256_path(path)
                for path in (RESULT_JSON, CONTRAST_CSV, FAILURE_CSV, FIGURE)
            },
            "script_sha256": sha256_path(Path(__file__)),
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"MECHANISM DIAGNOSTICS ERROR: {error}", file=sys.stderr)
        raise
