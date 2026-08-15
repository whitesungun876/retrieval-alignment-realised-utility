#!/usr/bin/env python3
"""Freeze and execute the one-time SUP-R6 supplemental analysis.

The `freeze` command creates the final SHA-256 bundle without reading formal
outcomes. The `analyze` command verifies that bundle, reveals the sealed arm map,
derives episode rows, invokes the SUP-R0-frozen analysis entry point exactly once,
and preserves the first output plus provenance.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from study3_v3_2_common import (  # noqa: E402
    read_json,
    read_jsonl,
    sha256_path,
    utc_now,
    write_json,
)


SUP = ROOT / "study3_supplemental_random_baseline"
GATES = SUP / "status/gates.json"
R0_FREEZE = SUP / "reports/sup_r0_freeze_report.json"
R1_REPORT = SUP / "reports/sup_r1_construction_report.json"
R5_REPORT = SUP / "reports/sup_r5_blind_technical_acceptance.json"
R5_INDEX = SUP / "formal/sup_r5_record_index.jsonl"
PUBLIC = SUP / "formal/formal_manifest.jsonl"
BINDINGS = SUP / "sealed/sealed_execution_bindings.jsonl"
CONDITION_MAP = SUP / "sealed/sealed_condition_map.json"
LEDGER = SUP / "formal/parallel_state_rec001/budget_ledger_v1.json"
RAW = SUP / "formal/raw_records"
MAPPING = SUP / "retrieval/r2_p_mapping.jsonl"
TARGETS = SUP / "materials/selected_targets.jsonl"
SOURCES = SUP / "materials/selected_sources.jsonl"
ANALYSIS_CODE = ROOT / "experiments/study3_sup_analysis.py"
FAILURE_RULES = SUP / "analysis/failure_taxonomy_v1.json"
OVERLAP_RULES = SUP / "analysis/overlap_strata_v1.json"
DEVIATION = SUP / "protocol/sup_r6_preanalysis_deviation_01_premature_map_display_20260805.md"

BUNDLE = SUP / "reports/sup_r6_final_analysis_bundle_sha256.json"
FREEZE_REPORT = SUP / "reports/sup_r6_analysis_freeze_report.json"
RESULTS = SUP / "results"
FIRST_ANALYSIS = RESULTS / "sup_r6_confirmatory_analysis_first.json"
EPISODE_OUTCOMES = RESULTS / "sup_r6_episode_outcomes_first.jsonl"
CONDITION_TABLE = RESULTS / "sup_r6_condition_descriptives.csv"
CONTRAST_TABLE = RESULTS / "sup_r6_contrasts.csv"
RETRIEVAL_DIAGNOSTICS = RESULTS / "sup_r6_retrieval_diagnostics.json"
OVERLAP_TABLE = RESULTS / "sup_r6_overlap_diagnostics.csv"
FAILURE_TABLE = RESULTS / "sup_r6_failure_taxonomy.csv"
PROVENANCE = SUP / "reports/sup_r6_first_analysis_provenance.json"
UNBLIND_REPORT = SUP / "reports/sup_r6_unblinding_report.json"

PLANNED_EPISODES = 4800
PLANNED_TARGETS = 800
EXPECTED_CONDITIONS = {"N2", "P", "R2"}


def fail(message: str) -> None:
    raise RuntimeError(message)


def exclusive_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if path.exists() and path.stat().st_size == 0:
            path.unlink()
        raise


def exclusive_json(path: Path, value: Any) -> None:
    exclusive_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def exclusive_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    exclusive_text(
        path,
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
    )


def csv_text(rows: list[Mapping[str, Any]], fieldnames: list[str] | None = None) -> str:
    if not rows and not fieldnames:
        return ""
    names = fieldnames or list(rows[0])
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def output_paths() -> tuple[Path, ...]:
    return (
        FIRST_ANALYSIS,
        EPISODE_OUTCOMES,
        CONDITION_TABLE,
        CONTRAST_TABLE,
        RETRIEVAL_DIAGNOSTICS,
        OVERLAP_TABLE,
        FAILURE_TABLE,
        PROVENANCE,
        UNBLIND_REPORT,
    )


def bundle_inputs() -> tuple[Path, ...]:
    return (
        ANALYSIS_CODE,
        FAILURE_RULES,
        OVERLAP_RULES,
        R0_FREEZE,
        R1_REPORT,
        R5_REPORT,
        R5_INDEX,
        PUBLIC,
        BINDINGS,
        CONDITION_MAP,
        LEDGER,
        MAPPING,
        TARGETS,
        SOURCES,
        DEVIATION,
        Path(__file__).resolve(),
    )


def freeze() -> dict[str, Any]:
    if BUNDLE.exists() or FREEZE_REPORT.exists():
        fail("SUP-R6 freeze output already exists; refusing to overwrite it.")
    if any(path.exists() for path in output_paths()):
        fail("A SUP-R6 analysis output already exists; freeze is prohibited.")
    gates = read_json(GATES)
    r0 = read_json(R0_FREEZE)
    r1 = read_json(R1_REPORT)
    r5 = read_json(R5_REPORT)
    expected_analysis_hash = str(r0["freeze_hashes"]["experiments/study3_sup_analysis.py"])
    expected_map_hash = str(r1["hashes"]["study3_supplemental_random_baseline/sealed/sealed_condition_map.json"])
    checks = {
        "sup_r5_gate_pass": gates["gates"]["SUP-R5"]["status"] == "PASS",
        "sup_r6_gate_pending": gates["gates"]["SUP-R6"]["status"] == "PENDING",
        "supplemental_outcomes_not_unblinded": gates.get("supplemental_outcomes_unblinded") is False,
        "r5_report_pass": r5.get("decision") == "PASS",
        "analysis_code_matches_sup_r0": sha256_path(ANALYSIS_CODE) == expected_analysis_hash,
        "failure_rules_match_sup_r0": sha256_path(FAILURE_RULES) == r0["freeze_hashes"][str(FAILURE_RULES.relative_to(ROOT))],
        "overlap_rules_match_sup_r0": sha256_path(OVERLAP_RULES) == r0["freeze_hashes"][str(OVERLAP_RULES.relative_to(ROOT))],
        "condition_map_matches_sup_r1": sha256_path(CONDITION_MAP) == expected_map_hash,
        "r5_index_matches_r5_report": sha256_path(R5_INDEX) == r5["hashes"]["record_index"],
        "public_manifest_matches_r5_report": sha256_path(PUBLIC) == r5["hashes"]["public_manifest"],
        "sealed_bindings_match_r5_report": sha256_path(BINDINGS) == r5["hashes"]["sealed_bindings"],
        "ledger_matches_r5_report": sha256_path(LEDGER) == r5["hashes"]["authoritative_ledger"],
        "premature_map_display_deviation_recorded": DEVIATION.is_file(),
        "analysis_outputs_absent": not any(path.exists() for path in output_paths()),
    }
    if not all(checks.values()):
        fail("SUP-R6 freeze preflight failed; analysis remains locked.")
    files = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_path(path),
            "bytes": path.stat().st_size,
        }
        for path in bundle_inputs()
    ]
    bundle = {
        "schema_version": "study3_sup_r6_final_analysis_bundle_sha256_v1",
        "created_at_utc": utc_now(),
        "status": "FROZEN_BEFORE_OUTCOME_ANALYSIS",
        "files": files,
        "frozen_analysis_entry_point": "study3_sup_analysis.analyze",
        "planned_invocations_on_supplemental_outcomes": 1,
        "condition_map_prematurely_displayed": True,
        "terminal_outcomes_inspected_before_freeze": False,
        "effect_estimates_computed_before_freeze": False,
    }
    exclusive_json(BUNDLE, bundle)
    report = {
        "schema_version": "study3_sup_r6_analysis_freeze_report_v1",
        "created_at_utc": utc_now(),
        "decision": "PASS",
        "checks": checks,
        "bundle_manifest_sha256": sha256_path(BUNDLE),
        "bundle_file_count": len(files),
        "analysis_code_sha256": expected_analysis_hash,
        "condition_map_sha256": expected_map_hash,
        "condition_mapping_displayed_before_bundle_freeze": True,
        "scientific_outcomes_read_for_inference": False,
    }
    exclusive_json(FREEZE_REPORT, report)
    gates["study_status"] = "SUP_R6_FROZEN_READY_FOR_SINGLE_ANALYSIS"
    gates["gates"]["SUP-R6"]["freeze_status"] = "PASS"
    gates["gates"]["SUP-R6"]["freeze_evidence"] = [
        str(BUNDLE.relative_to(ROOT)),
        str(FREEZE_REPORT.relative_to(ROOT)),
        str(DEVIATION.relative_to(ROOT)),
    ]
    write_json(GATES, gates)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return report


def verify_bundle() -> dict[str, str]:
    if not BUNDLE.exists() or not FREEZE_REPORT.exists():
        fail("SUP-R6 bundle has not been frozen.")
    if any(path.exists() for path in output_paths()):
        fail("A first SUP-R6 output already exists; refusing to rerun or overwrite it.")
    gates = read_json(GATES)
    if gates["gates"]["SUP-R5"]["status"] != "PASS":
        fail("SUP-R5 is not PASS; unblinding is prohibited.")
    if gates["gates"]["SUP-R6"]["status"] != "PENDING":
        fail("SUP-R6 is not PENDING; analysis cannot be invoked.")
    freeze_report = read_json(FREEZE_REPORT)
    if freeze_report.get("decision") != "PASS":
        fail("SUP-R6 freeze report is not PASS.")
    if sha256_path(BUNDLE) != freeze_report["bundle_manifest_sha256"]:
        fail("SUP-R6 bundle-manifest hash mismatch.")
    bundle = read_json(BUNDLE)
    observed: dict[str, str] = {}
    for entry in bundle["files"]:
        path = ROOT / str(entry["path"])
        digest = sha256_path(path)
        if digest != str(entry["sha256"]) or path.stat().st_size != int(entry["bytes"]):
            fail(f"Frozen SUP-R6 input drift: {path}")
        observed[str(entry["path"])] = digest
    return observed


def derive_episode_rows(arm_to_condition: Mapping[str, str]) -> list[dict[str, Any]]:
    index_rows = read_jsonl(R5_INDEX)
    rows: list[dict[str, Any]] = []
    logical_keys: set[tuple[str, str, int]] = set()
    for index in index_rows:
        arm = str(index["masked_arm"])
        condition = str(arm_to_condition[arm])
        run_id = str(index["run_id"])
        row = {
            "target_id": str(index["target_id"]),
            "condition": condition,
            "masked_arm": arm,
            "repetition": int(index["repetition"]),
            "selected_record_run_id": run_id,
            "technical_failure": index["technical_state"] != "valid",
            "terminal_success": None,
        }
        key = (row["target_id"], condition, row["repetition"])
        if key in logical_keys:
            fail(f"Duplicate logical supplemental cell: {key}")
        logical_keys.add(key)
        record_path = RAW / f"{run_id}.json"
        if not record_path.exists() or sha256_path(record_path) != str(index["record_sha256"]):
            fail(f"Frozen record missing or changed: {run_id}")
        if not row["technical_failure"]:
            record = read_json(record_path)
            if str(record["run"]["run_id"]) != run_id:
                fail(f"Record run identifier mismatch: {run_id}")
            if str(record["experimental_design"]["pair_id"]) != row["target_id"]:
                fail(f"Record target identifier mismatch: {run_id}")
            row["terminal_success"] = bool(record["run"]["success"])
        rows.append(row)
    if len(rows) != PLANNED_EPISODES or len(logical_keys) != PLANNED_EPISODES:
        fail("SUP-R6 requires exactly 4,800 unique logical cells.")
    counts = Counter(str(row["condition"]) for row in rows)
    if counts != Counter({condition: 1600 for condition in EXPECTED_CONDITIONS}):
        fail(f"Unexpected condition counts after unblinding: {counts}")
    if len({str(row["target_id"]) for row in rows}) != PLANNED_TARGETS:
        fail("SUP-R6 target count is not 800.")
    return rows


def condition_descriptives(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for condition in ("N2", "P", "R2"):
        selected = [row for row in rows if row["condition"] == condition]
        valid = [row for row in selected if not bool(row["technical_failure"])]
        successes = sum(bool(row["terminal_success"]) for row in valid)
        by_target: defaultdict[str, list[float]] = defaultdict(list)
        for row in valid:
            by_target[str(row["target_id"])].append(float(bool(row["terminal_success"])))
        target_means = [float(np.mean(values)) for values in by_target.values()]
        output.append(
            {
                "condition": condition,
                "planned_episodes": len(selected),
                "valid_episodes": len(valid),
                "technical_missing": len(selected) - len(valid),
                "episode_successes": successes,
                "episode_success_rate": successes / len(valid),
                "targets_with_at_least_one_valid_episode": len(target_means),
                "mean_target_success_rate": float(np.mean(target_means)),
            }
        )
    return output


def contrast_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    values = [("primary", result["primary"])] + [("secondary", row) for row in result["secondary"]]
    for status, value in values:
        tost = value.get("tost") or {}
        rows.append(
            {
                "status": status,
                "contrast": value["contrast"],
                "targets": value["targets"],
                "risk_difference_percentage_points": value["risk_difference_percentage_points"],
                "ci_95_low_percentage_points": value["bootstrap_95_ci_percentage_points"][0],
                "ci_95_high_percentage_points": value["bootstrap_95_ci_percentage_points"][1],
                "sign_flip_p_two_sided": value["sign_flip_p_two_sided"],
                "holm_adjusted_p": value.get("holm_adjusted_p"),
                "tost_margin_percentage_points": 100 * tost["margin"] if tost else None,
                "tost_ci_90_low_percentage_points": 100 * tost["ci_90"][0] if tost else None,
                "tost_ci_90_high_percentage_points": 100 * tost["ci_90"][1] if tost else None,
                "tost_lower_p_one_sided": tost.get("lower_p_one_sided"),
                "tost_upper_p_one_sided": tost.get("upper_p_one_sided"),
                "tost_equivalent": tost.get("equivalent"),
            }
        )
    return rows


def operation_multiset(signature: Iterable[Iterable[str]]) -> Counter[str]:
    return Counter(str(operation) for chain in signature for operation in chain)


def overlap_metrics(target: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    target_operations = operation_multiset(target["structure_signature"])
    source_operations = operation_multiset(source["structure_signature"])
    target_count = sum(target_operations.values())
    overlap_count = sum((target_operations & source_operations).values())
    coverage = None if target_count == 0 else overlap_count / target_count
    if target_count == 0:
        stratum = "no_transformation_target"
    elif overlap_count == 0:
        stratum = "zero_overlap"
    elif coverage is not None and coverage < 1:
        stratum = "partial_coverage"
    else:
        stratum = "complete_coverage"
    target_ingredients = {str(value) for value in target["ingredients"]}
    source_ingredients = {str(value) for value in source["ingredients"]}
    union = target_ingredients | source_ingredients
    ingredient_intersection = len(target_ingredients & source_ingredients)
    return {
        "target_required_operation_count": target_count,
        "operation_overlap_count": overlap_count,
        "operation_coverage": coverage,
        "overlap_stratum": stratum,
        "exact_structural_correspondence": sorted(tuple(chain) for chain in target["structure_signature"]) == sorted(tuple(chain) for chain in source["structure_signature"]),
        "ingredient_overlap_count": ingredient_intersection,
        "ingredient_jaccard": ingredient_intersection / len(union) if union else 1.0,
        "ingredient_set_exact": target_ingredients == source_ingredients,
    }


def retrieval_diagnostics(
    rows: list[Mapping[str, Any]], episode_rows: list[Mapping[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    mapping = read_jsonl(MAPPING)
    targets = {str(row["task_id"]): row for row in read_jsonl(TARGETS)}
    sources = {int(row["seed"]): row for row in read_jsonl(SOURCES)}
    from study3_sup_analysis import target_condition_means

    means = target_condition_means(episode_rows)
    detailed: list[dict[str, Any]] = []
    for item in mapping:
        target_id = str(item["target_id"])
        target = targets[target_id]
        for condition in ("P", "R2"):
            source_seed = int(item[f"{condition}_source_seed"])
            metrics = overlap_metrics(target, sources[source_seed])
            expected_match = bool(item[f"{condition}_structural_match"])
            if bool(metrics["exact_structural_correspondence"]) != expected_match:
                fail(f"Frozen structural-match diagnostic disagrees for {target_id} {condition}.")
            detailed.append(
                {
                    "target_id": target_id,
                    "retrieval_condition": condition,
                    "source_seed": source_seed,
                    **metrics,
                    "target_mean_terminal_success": means[target_id][condition],
                }
            )
    summaries: dict[str, Any] = {}
    for condition in ("P", "R2"):
        selected = [row for row in detailed if row["retrieval_condition"] == condition]
        by_stratum: dict[str, Any] = {}
        for stratum in ("no_transformation_target", "zero_overlap", "partial_coverage", "complete_coverage"):
            subset = [row for row in selected if row["overlap_stratum"] == stratum]
            by_stratum[stratum] = {
                "targets": len(subset),
                "mean_target_success_rate": float(np.mean([row["target_mean_terminal_success"] for row in subset])) if subset else None,
                "exact_structural_match_rate": float(np.mean([row["exact_structural_correspondence"] for row in subset])) if subset else None,
            }
        summaries[condition] = {
            "targets": len(selected),
            "exact_structural_match_count": sum(bool(row["exact_structural_correspondence"]) for row in selected),
            "exact_structural_match_rate": float(np.mean([row["exact_structural_correspondence"] for row in selected])),
            "mean_ingredient_jaccard": float(np.mean([row["ingredient_jaccard"] for row in selected])),
            "ingredient_set_exact_count": sum(bool(row["ingredient_set_exact"]) for row in selected),
            "mean_operation_overlap_count": float(np.mean([row["operation_overlap_count"] for row in selected])),
            "mean_operation_coverage_defined_targets": float(np.mean([row["operation_coverage"] for row in selected if row["operation_coverage"] is not None])),
            "overlap_strata": by_stratum,
        }
    r2_sources = Counter(int(row["R2_source_seed"]) for row in mapping)
    p_sources = Counter(int(row["P_source_seed"]) for row in mapping)
    diagnostic = {
        "schema_version": "study3_sup_r6_retrieval_diagnostics_v1",
        "created_at_utc": utc_now(),
        "status": "predeclared_descriptive_diagnostics",
        "retrieval_conditions": summaries,
        "source_assignment": {
            "P_R2_same_source_targets": sum(int(row["P_source_seed"]) == int(row["R2_source_seed"]) for row in mapping),
            "source_multisets_identical": p_sources == r2_sources,
            "unique_P_sources": len(p_sources),
            "unique_R2_sources": len(r2_sources),
        },
        "operation_overlap_rule_sha256": sha256_path(OVERLAP_RULES),
        "ingredient_overlap_status": "descriptive set intersection and Jaccard summaries; no inferential status",
    }
    return diagnostic, detailed


def parse_transformation(action: str) -> tuple[str, str] | None:
    for operation in ("chop", "slice", "dice"):
        prefix = f"{operation} "
        if action.startswith(prefix):
            return operation, action[len(prefix) :]
    if action.startswith("cook ") and " in " in action:
        ingredient, device = action[5:].rsplit(" in ", 1)
        operation = {"stove": "fry", "oven": "roast", "barbeque": "grill"}.get(device, f"cook:{device}")
        return operation, ingredient
    return None


def classify_failure(
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
        "record_run_id": str(outcome["selected_record_run_id"]),
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
                result.update({"ingredient": ingredient, "observed_operation": operation, "expected_next_operation": expected})
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


def failure_diagnostics(episode_rows: list[Mapping[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    targets = {str(row["task_id"]): row for row in read_jsonl(TARGETS)}
    failures: list[dict[str, Any]] = []
    invalid_actions_all: Counter[str] = Counter()
    valid_non_success = 0
    for outcome in episode_rows:
        if bool(outcome["technical_failure"]):
            continue
        record = read_json(RAW / f"{outcome['selected_record_run_id']}.json")
        invalid_actions_all[str(outcome["condition"])] += sum(not bool(step["action_was_admissible"]) for step in record["trajectory"])
        if not bool(outcome["terminal_success"]):
            valid_non_success += 1
        classified = classify_failure(outcome, record, targets[str(outcome["target_id"])])
        if classified is not None:
            failures.append(classified)
    if len(failures) != valid_non_success or any(row["failure_category"] is None for row in failures):
        fail("Frozen failure taxonomy did not classify every valid non-success episode.")
    counts = Counter(str(row["failure_category"]) for row in failures)
    by_condition: dict[str, Any] = {}
    for condition in ("N2", "P", "R2"):
        selected = [row for row in failures if row["condition"] == condition]
        selected_counts = Counter(str(row["failure_category"]) for row in selected)
        by_condition[condition] = {
            "valid_failures": len(selected),
            "category_counts": dict(sorted(selected_counts.items())),
        }
    diagnostic = {
        "status": "predeclared_descriptive_failure_taxonomy",
        "valid_failures": len(failures),
        "classification_coverage": 1.0,
        "category_counts": dict(sorted(counts.items())),
        "category_fractions": {name: count / len(failures) for name, count in sorted(counts.items())} if failures else {},
        "by_condition": by_condition,
        "invalid_action_counts_all_valid_episodes": dict(sorted(invalid_actions_all.items())),
        "failure_rule_sha256": sha256_path(FAILURE_RULES),
    }
    return diagnostic, failures


def analyze_once() -> dict[str, Any]:
    frozen_hashes = verify_bundle()
    condition_payload = read_json(CONDITION_MAP)
    arm_to_condition = dict(condition_payload["arm_to_condition"])
    if set(arm_to_condition) != {"arm_1", "arm_2", "arm_3"} or set(arm_to_condition.values()) != EXPECTED_CONDITIONS:
        fail("Condition map is not a bijection over N2/P/R2.")
    episode_rows = derive_episode_rows(arm_to_condition)

    # Import only after every frozen input hash passes, then invoke exactly once.
    from study3_sup_analysis import analyze

    result = analyze(episode_rows)
    exclusive_json(FIRST_ANALYSIS, result)
    exclusive_jsonl(EPISODE_OUTCOMES, episode_rows)

    descriptives = condition_descriptives(episode_rows)
    contrasts = contrast_rows(result)
    retrieval, overlap_rows = retrieval_diagnostics(read_jsonl(MAPPING), episode_rows)
    failures, failure_rows = failure_diagnostics(episode_rows)
    retrieval["failure_diagnostics"] = failures

    exclusive_text(CONDITION_TABLE, csv_text(descriptives))
    exclusive_text(CONTRAST_TABLE, csv_text(contrasts))
    exclusive_json(RETRIEVAL_DIAGNOSTICS, retrieval)
    exclusive_text(OVERLAP_TABLE, csv_text(overlap_rows))
    failure_fields = [
        "target_id", "condition", "repetition", "record_run_id", "terminal_reason",
        "step_count", "invalid_action_count", "failure_category", "failure_subcategory",
        "first_irreversible_step", "first_irreversible_action", "ingredient",
        "observed_operation", "expected_next_operation",
    ]
    exclusive_text(FAILURE_TABLE, csv_text(failure_rows, failure_fields))

    output_hashes = {
        str(path.relative_to(ROOT)): sha256_path(path)
        for path in (
            FIRST_ANALYSIS,
            EPISODE_OUTCOMES,
            CONDITION_TABLE,
            CONTRAST_TABLE,
            RETRIEVAL_DIAGNOSTICS,
            OVERLAP_TABLE,
            FAILURE_TABLE,
        )
    }
    provenance = {
        "schema_version": "study3_sup_r6_first_analysis_provenance_v1",
        "created_at_utc": utc_now(),
        "decision": "PASS",
        "sup_r5_verified_pass_before_analysis": True,
        "final_bundle_verified_before_analysis": True,
        "condition_mapping_revealed": True,
        "condition_mapping_had_been_prematurely_displayed_before_freeze": True,
        "protocol_deviation_sha256": sha256_path(DEVIATION),
        "arm_to_condition": arm_to_condition,
        "frozen_analysis_invocations_on_supplemental_outcomes": 1,
        "first_analysis_preserved": True,
        "input_hashes": frozen_hashes,
        "output_hashes": output_hashes,
        "counts": {
            "logical_episode_cells": len(episode_rows),
            "valid_episode_records": sum(not row["technical_failure"] for row in episode_rows),
            "preregistered_technical_missing": sum(bool(row["technical_failure"]) for row in episode_rows),
            "targets": len({row["target_id"] for row in episode_rows}),
        },
        "software_versions": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "evidence_status": {
            "primary_and_secondary": "prospectively frozen confirmatory",
            "retrieval_and_overlap": "predeclared descriptive diagnostics",
            "failure_taxonomy": "predeclared descriptive diagnostic",
            "ingredient_jaccard": "descriptive only; no inferential status",
        },
    }
    exclusive_json(PROVENANCE, provenance)
    unblind = {
        "schema_version": "study3_sup_r6_unblinding_report_v1",
        "created_at_utc": utc_now(),
        "decision": "PASS",
        "condition_mapping": arm_to_condition,
        "primary": result["primary"],
        "secondary": result["secondary"],
        "condition_descriptives": descriptives,
        "retrieval_diagnostics": retrieval["retrieval_conditions"],
        "failure_diagnostics": failures,
        "first_analysis_sha256": sha256_path(FIRST_ANALYSIS),
        "provenance_sha256": sha256_path(PROVENANCE),
    }
    exclusive_json(UNBLIND_REPORT, unblind)

    gates = read_json(GATES)
    gates["gates"]["SUP-R6"] = {
        "status": "PASS",
        "evidence": [
            str(FIRST_ANALYSIS.relative_to(ROOT)),
            str(PROVENANCE.relative_to(ROOT)),
            str(UNBLIND_REPORT.relative_to(ROOT)),
            str(CONTRAST_TABLE.relative_to(ROOT)),
            str(RETRIEVAL_DIAGNOSTICS.relative_to(ROOT)),
            str(FAILURE_TABLE.relative_to(ROOT)),
        ],
        "metrics": {
            "targets": result["primary"]["targets"],
            "valid_episodes": provenance["counts"]["valid_episode_records"],
            "technical_missing": provenance["counts"]["preregistered_technical_missing"],
            "primary_contrast": result["primary"]["contrast"],
            "primary_risk_difference_percentage_points": result["primary"]["risk_difference_percentage_points"],
            "primary_sign_flip_p_two_sided": result["primary"]["sign_flip_p_two_sided"],
            "primary_tost_equivalent": result["primary"]["tost"]["equivalent"],
            "first_analysis_sha256": sha256_path(FIRST_ANALYSIS),
        },
    }
    gates["study_status"] = "SUP_R6_PASS_READY_FOR_REPORTING"
    gates["supplemental_outcomes_unblinded"] = True
    gates["supplemental_analysis_invocations"] = 1
    write_json(GATES, gates)
    printed = {
        "decision": "PASS",
        "primary": result["primary"],
        "secondary": result["secondary"],
        "condition_descriptives": descriptives,
        "retrieval_diagnostics": retrieval["retrieval_conditions"],
        "failure_diagnostics": failures,
    }
    print(json.dumps(printed, ensure_ascii=False, indent=2, sort_keys=True))
    return printed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("freeze", "analyze"))
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    else:
        analyze_once()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SUP-R6 ERROR: {error}", file=sys.stderr)
        raise
