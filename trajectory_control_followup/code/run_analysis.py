#!/usr/bin/env python3
"""Run the authorized, prospectively frozen P/C formal analysis.

This driver performs only deterministic integrity checks and data assembly before
calling ``src.analysis.analyze``.  It does not alter the frozen analysis module.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from src.analysis import analyze, target_condition_means, paired_differences


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "formal/formal_manifest.jsonl"
BINDINGS = ROOT / "sealed/sealed_execution_bindings.jsonl"
CONDITION_MAP = ROOT / "sealed/sealed_condition_map.json"
LEDGER = ROOT / "formal/state_resume_4worker_v1/budget_ledger_v1.json"
RAW = ROOT / "formal/raw_records"
ACCEPTANCE = ROOT / "reports/formal_outcome_blind_technical_acceptance_v1.json"
FROZEN_ANALYSIS = ROOT / "src/analysis.py"
OUT = ROOT / "analysis_formal_v1/results"

EXPECTED_ANALYSIS_SHA256 = "7558648da80f0e788215be3e437ff4bb20f93a7588f9d1a7435510909d3b4a5d"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    acceptance = read_json(ACCEPTANCE)
    if acceptance["decision"] != "PASS":
        raise RuntimeError("Outcome-blind technical acceptance is not PASS.")
    if sha256(FROZEN_ANALYSIS) != EXPECTED_ANALYSIS_SHA256:
        raise RuntimeError("Frozen analysis.py hash drifted.")

    public_rows = read_jsonl(MANIFEST)
    binding_rows = read_jsonl(BINDINGS)
    public = {row["run_id"]: row for row in public_rows}
    bindings = {row["run_id"]: row for row in binding_rows}
    ledger = read_json(LEDGER)
    completed = ledger["completed"]
    consumed = ledger["consumed_without_record"]
    raw_paths = {path.stem: path for path in RAW.glob("*.json")}

    if len(public) != 3200 or len(bindings) != 3200:
        raise RuntimeError("Formal manifest or binding count is not 3,200.")
    if set(public) != set(bindings):
        raise RuntimeError("Manifest and binding IDs differ.")
    if set(raw_paths) != set(completed):
        raise RuntimeError("Raw-record IDs and completed-ledger IDs differ.")
    if set(completed) | set(consumed) != set(public):
        raise RuntimeError("Completed plus consumed IDs do not allocate all formal cells.")
    if set(completed) & set(consumed):
        raise RuntimeError("Completed and consumed IDs overlap.")

    condition_map = read_json(CONDITION_MAP)["arm_to_condition"]
    rows: list[dict[str, Any]] = []
    episode_counts = {"P": 0, "C": 0}
    success_counts = {"P": 0, "C": 0}
    for run_id in sorted(completed):
        path = raw_paths[run_id]
        if sha256(path) != completed[run_id]["record_sha256"]:
            raise RuntimeError(f"Raw-record hash mismatch: {run_id}")
        payload = read_json(path)
        public_row = public[run_id]
        binding = bindings[run_id]
        condition = str(binding["condition"])
        expected_condition = condition_map[public_row["masked_arm"]]
        if condition != expected_condition:
            raise RuntimeError(f"Condition-map mismatch: {run_id}")
        if payload["run"]["run_id"] != run_id:
            raise RuntimeError(f"Raw run ID mismatch: {run_id}")
        if payload["run"].get("error") is not None:
            raise RuntimeError(f"Accepted record has run error: {run_id}")
        success = bool(payload["run"]["success"])
        row = {
            "run_id": run_id,
            "target_id": public_row["target_id"],
            "target_index": public_row["target_index"],
            "condition": condition,
            "repetition": public_row["repetition"],
            "terminal_success": success,
            "technical_failure": bool(completed[run_id]["technical_failure"]),
        }
        rows.append(row)
        episode_counts[condition] += 1
        success_counts[condition] += int(success)

    missing_by_condition = {"P": 0, "C": 0}
    consumed_rows: list[dict[str, Any]] = []
    for run_id in sorted(consumed):
        public_row = public[run_id]
        condition = str(bindings[run_id]["condition"])
        missing_by_condition[condition] += 1
        consumed_rows.append({
            "run_id": run_id,
            "target_id": public_row["target_id"],
            "target_index": public_row["target_index"],
            "condition": condition,
            "repetition": public_row["repetition"],
        })

    primary = analyze(rows)
    means = target_condition_means(rows)
    targets, differences = paired_differences(means)
    if len(targets) != 800:
        raise RuntimeError(f"Expected 800 evaluable targets, got {len(targets)}.")

    # Deterministic worst-case sensitivity: impute every missing P/C episode as
    # either 0 or 1, then repeat the same target-level estimand.
    def imputed_effect(p_value: bool, c_value: bool) -> float:
        expanded = list(rows)
        for item in consumed_rows:
            expanded.append({
                **item,
                "terminal_success": p_value if item["condition"] == "P" else c_value,
                "technical_failure": False,
            })
        expanded_means = target_condition_means(expanded)
        _, expanded_diff = paired_differences(expanded_means)
        return float(expanded_diff.mean())

    lower_bound = imputed_effect(False, True)
    upper_bound = imputed_effect(True, False)
    t_result = stats.ttest_1samp(differences, popmean=0.0)
    target_rates = {
        condition: float(np.mean([value[condition] for value in means.values() if condition in value]))
        for condition in ("P", "C")
    }
    distribution = {
        str(value): int(np.sum(np.isclose(differences, value)))
        for value in (-1.0, -0.5, 0.0, 0.5, 1.0)
    }

    report = {
        "schema_version": "protocol_control_pc_authorized_formal_analysis_v1",
        "authorization": "User explicitly authorized P/C result analysis after outcome-blind technical acceptance.",
        "integrity": {
            "technical_acceptance": acceptance["decision"],
            "frozen_analysis_sha256": sha256(FROZEN_ANALYSIS),
            "completed_records": len(completed),
            "consumed_without_record": len(consumed),
            "evaluable_targets": len(targets),
            "technical_failures": sum(bool(row["technical_failure"]) for row in rows),
        },
        "primary_frozen_analysis": primary,
        "descriptive": {
            "observed_episode_counts": episode_counts,
            "observed_success_counts": success_counts,
            "observed_episode_success_rates": {condition: success_counts[condition] / episode_counts[condition] for condition in ("P", "C")},
            "equally_weighted_target_success_rates": target_rates,
            "target_difference_distribution": distribution,
            "unplanned_paired_t_robustness": {
                "t": float(t_result.statistic),
                "df": len(differences) - 1,
                "p_two_sided": float(t_result.pvalue),
                "label": "unplanned transparent robustness check; not the frozen primary sensitivity",
            },
        },
        "missingness": {
            "missing_by_condition": missing_by_condition,
            "all_800_targets_evaluable_under_frozen_available-repetition_rule": True,
            "worst_case_imputation_P0_C1_risk_difference": lower_bound,
            "worst_case_imputation_P1_C0_risk_difference": upper_bound,
            "worst_case_imputation_percentage_points": [100 * lower_bound, 100 * upper_bound],
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "formal_pc_analysis_v1.json", report)
    with (OUT / "target_level_differences_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["target_id", "P_mean", "C_mean", "P_minus_C"])
        for target in targets:
            writer.writerow([target, means[target]["P"], means[target]["C"], means[target]["P"] - means[target]["C"]])
    write_json(OUT / "consumed_missing_cells_v1.json", consumed_rows)
    write_json(OUT / "result_hashes_v1.json", {
        "formal_pc_analysis_v1.json": sha256(OUT / "formal_pc_analysis_v1.json"),
        "target_level_differences_v1.csv": sha256(OUT / "target_level_differences_v1.csv"),
        "consumed_missing_cells_v1.json": sha256(OUT / "consumed_missing_cells_v1.json"),
    })
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
