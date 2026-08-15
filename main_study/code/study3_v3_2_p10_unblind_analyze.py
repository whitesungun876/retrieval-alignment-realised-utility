#!/usr/bin/env python3
"""One-time P10 unblinding and confirmatory analysis for Study 3 v3.2.

The script validates all frozen inputs before revealing the condition map, calls
the frozen analysis entry point exactly once, and preserves the first output and
its provenance. It refuses to overwrite a prior P10 confirmatory result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Iterable, Mapping

os.environ.setdefault("MPLCONFIGDIR", "/tmp/study3_v3_2_matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from study3_v3_2_common import (
    GATES,
    ROOT,
    STUDY,
    read_json,
    read_jsonl,
    set_gate,
    sha256_path,
    utc_now,
    write_json,
    write_jsonl,
)


ANALYSIS_CODE = ROOT / "experiments/study3_v3_2_analysis.py"
P7_FREEZE = STUDY / "reports/p7_freeze_report.json"
P9_REPORT = STUDY / "reports/p9_blind_technical_acceptance.json"
P9_ADJUDICATION = STUDY / "reports/p9_blind_technical_acceptance_adjudication_01.json"
P9_INDEX = STUDY / "formal/p9_selected_record_index.jsonl"
CONDITION_MAP = STUDY / "formal/sealed_condition_map.json"
RETRIEVAL_SELECTIONS = STUDY / "formal/retrieval_selections.jsonl"
RAW_RECORDS = STUDY / "formal/raw_records"

RESULTS = STUDY / "results"
REPORTS = STUDY / "reports"
FIRST_ANALYSIS = RESULTS / "p10_confirmatory_analysis_first.json"
EPISODE_OUTCOMES = RESULTS / "p10_episode_outcomes_first.jsonl"
CONDITION_TABLE = RESULTS / "p10_condition_descriptives.csv"
CONTRAST_TABLE = RESULTS / "p10_confirmatory_contrasts.csv"
CONTRAST_FIGURE = RESULTS / "p10_confirmatory_contrasts.png"
PROVENANCE = REPORTS / "p10_first_analysis_provenance.json"
UNBLIND_REPORT = REPORTS / "p10_unblinding_report.json"

EXPECTED_ANALYSIS_SHA256 = "746a2720cad1e556aac7d9b09b967cfd5ab793c2e2dd5ae4c8c3eb70ce7443fe"
EXPECTED_CONDITION_MAP_SHA256 = "adfb0fee90f2e5b0dc44176d64a7a383b98521430d7cabdc8e62536a498e4bc4"
EXPECTED_P9_REPORT_SHA256 = "de31e779c533a05213613c9309c14b83e6aad3fe8cc6068940598260c3476719"
EXPECTED_P9_ADJUDICATION_SHA256 = "eafa114cc5d33d006dbe52cbf9ce25195ccea65c5c4a8e0239ab068e0fd4c588"
EXPECTED_P9_INDEX_SHA256 = "9b6501862e208e5dcec91b2cf4d12287ee16652486e4d5366579682bfaba7b97"
EXPECTED_RETRIEVAL_SHA256 = "cd2e3f715f7f87ecc0256ebc00638558d58659b3d38c982231ba83a3fb1f0afd"


def fail(message: str) -> None:
    raise RuntimeError(message)


def validate_preflight() -> dict[str, str]:
    if FIRST_ANALYSIS.exists() or PROVENANCE.exists():
        fail("P10 first analysis already exists; refusing to rerun or overwrite it.")

    registry = read_json(GATES)
    if registry["gates"]["P9"]["status"] != "PASS":
        fail("P9 is not PASS; P10 unblinding is prohibited.")
    if registry["gates"]["P10"]["status"] != "PENDING":
        fail("P10 gate is not PENDING.")

    p7 = read_json(P7_FREEZE)
    adjudication = read_json(P9_ADJUDICATION)
    if adjudication.get("decision") != "PASS":
        fail("P9 adjudication is not PASS.")
    expected = {
        ANALYSIS_CODE: EXPECTED_ANALYSIS_SHA256,
        CONDITION_MAP: EXPECTED_CONDITION_MAP_SHA256,
        P9_REPORT: EXPECTED_P9_REPORT_SHA256,
        P9_ADJUDICATION: EXPECTED_P9_ADJUDICATION_SHA256,
        P9_INDEX: EXPECTED_P9_INDEX_SHA256,
        RETRIEVAL_SELECTIONS: EXPECTED_RETRIEVAL_SHA256,
    }
    observed = {str(path.relative_to(ROOT)): sha256_path(path) for path in expected}
    for path, digest in expected.items():
        if sha256_path(path) != digest:
            fail(f"Frozen input hash mismatch: {path}")
    if p7["hashes"]["analysis_code"] != EXPECTED_ANALYSIS_SHA256:
        fail("P7 analysis-code hash does not match the frozen constant.")
    if p7["hashes"]["sealed_condition_map"] != EXPECTED_CONDITION_MAP_SHA256:
        fail("P7 condition-map hash does not match the frozen constant.")
    return observed


def derive_episode_rows(
    index_rows: Iterable[Mapping[str, Any]], arm_to_condition: Mapping[str, str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    logical_keys: set[tuple[str, str, int]] = set()
    for index in index_rows:
        arm = str(index["masked_arm"])
        condition = str(arm_to_condition[arm])
        row = {
            "target_id": str(index["target_id"]),
            "condition": condition,
            "masked_arm": arm,
            "repetition": int(index["repetition"]),
            "planned_run_id": str(index["planned_run_id"]),
            "selected_record_run_id": index.get("selected_record_run_id"),
            "selection": str(index["selection"]),
            "technical_failure": False,
            "terminal_success": None,
        }
        key = (row["target_id"], arm, row["repetition"])
        if key in logical_keys:
            fail(f"Duplicate P9 logical cell: {key}")
        logical_keys.add(key)

        if index["selection"] == "preregistered_unresolved_technical_failure":
            row["technical_failure"] = True
        else:
            run_id = str(index["selected_record_run_id"])
            record_path = RAW_RECORDS / f"{run_id}.json"
            if not record_path.exists():
                fail(f"Selected record is missing: {record_path}")
            if sha256_path(record_path) != str(index["selected_record_sha256"]):
                fail(f"Selected record hash mismatch: {run_id}")
            record = read_json(record_path)
            if str(record["run"]["run_id"]) != run_id:
                fail(f"Selected record run_id mismatch: {run_id}")
            if str(record["experimental_design"]["pair_id"]) != row["target_id"]:
                fail(f"Selected record target mismatch: {run_id}")
            row["terminal_success"] = bool(record["run"]["success"])
        rows.append(row)

    if len(rows) != 5_400 or len(logical_keys) != 5_400:
        fail("P10 requires exactly 5,400 unique logical cells.")
    counts = Counter(row["condition"] for row in rows)
    if counts != Counter({"N": 1_350, "R": 1_350, "D": 1_350, "H": 1_350}):
        fail(f"Unexpected condition counts after unblinding: {counts}")
    return rows


def condition_descriptives(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for condition in ("N", "R", "D", "H"):
        selected = [row for row in rows if row["condition"] == condition]
        valid = [row for row in selected if not bool(row["technical_failure"])]
        successes = sum(bool(row["terminal_success"]) for row in valid)
        by_target: dict[str, list[float]] = defaultdict(list)
        for row in valid:
            by_target[str(row["target_id"])].append(float(bool(row["terminal_success"])))
        target_means = [sum(values) / len(values) for values in by_target.values()]
        output.append(
            {
                "condition": condition,
                "planned_episodes": len(selected),
                "valid_episodes": len(valid),
                "technical_missing": len(selected) - len(valid),
                "episode_successes": successes,
                "episode_success_rate": successes / len(valid),
                "targets_with_at_least_one_valid_episode": len(target_means),
                "mean_target_success_rate": sum(target_means) / len(target_means),
            }
        )
    return output


def csv_text(fieldnames: list[str], rows: Iterable[Mapping[str, Any]]) -> str:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def contrast_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for status, value in [("primary", result["primary"])] + [
        ("secondary", row) for row in result["secondary"]
    ]:
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
            }
        )
    return rows


def make_figure(rows: list[Mapping[str, Any]], path: Path) -> None:
    labels = [str(row["contrast"]) for row in rows]
    values = [float(row["risk_difference_percentage_points"]) for row in rows]
    lows = [float(row["ci_95_low_percentage_points"]) for row in rows]
    highs = [float(row["ci_95_high_percentage_points"]) for row in rows]
    positions = list(range(len(rows)))
    colors = ["#1261A0" if row["status"] == "primary" else "#777777" for row in rows]
    figure, axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    axis.axvline(0, color="#222222", linewidth=1, linestyle="--")
    for y, estimate, low, high, color in zip(positions, values, lows, highs, colors):
        axis.errorbar(
            estimate,
            y,
            xerr=[[estimate - low], [high - estimate]],
            fmt="o",
            color=color,
            capsize=4,
            linewidth=1.8,
        )
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Risk difference (percentage points; 95% cluster-bootstrap CI)")
    axis.set_title("Study 3 v3.2 confirmatory contrasts")
    figure.savefig(path, dpi=220)
    plt.close(figure)


def main() -> None:
    frozen_hashes = validate_preflight()

    # The condition map is opened only after P9 and every frozen-input check passes.
    condition_payload = read_json(CONDITION_MAP)
    arm_to_condition = dict(condition_payload["arm_to_condition"])
    if set(arm_to_condition.values()) != {"N", "R", "D", "H"}:
        fail("Condition map is not a bijection over N/R/D/H.")

    index_rows = read_jsonl(P9_INDEX)
    episode_rows = derive_episode_rows(index_rows, arm_to_condition)
    retrieval_rows = read_jsonl(RETRIEVAL_SELECTIONS)
    if len(retrieval_rows) != 675:
        fail("Expected exactly 675 frozen retrieval rows.")
    if {row["target_id"] for row in retrieval_rows} != {
        row["target_id"] for row in episode_rows
    }:
        fail("Retrieval and episode target sets differ.")

    # Import only after verifying the frozen script hash, then invoke exactly once.
    from study3_v3_2_analysis import analyze

    result = analyze(episode_rows, retrieval_rows)
    descriptives = condition_descriptives(episode_rows)
    contrasts = contrast_rows(result)

    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p10-staging-", dir=str(RESULTS)) as temp_name:
        staging = Path(temp_name)
        staged_analysis = staging / FIRST_ANALYSIS.name
        staged_episodes = staging / EPISODE_OUTCOMES.name
        staged_condition_table = staging / CONDITION_TABLE.name
        staged_contrast_table = staging / CONTRAST_TABLE.name
        staged_figure = staging / CONTRAST_FIGURE.name

        write_json(staged_analysis, result)
        write_jsonl(staged_episodes, episode_rows)
        staged_condition_table.write_text(
            csv_text(list(descriptives[0]), descriptives), encoding="utf-8"
        )
        staged_contrast_table.write_text(
            csv_text(list(contrasts[0]), contrasts), encoding="utf-8"
        )
        make_figure(contrasts, staged_figure)

        staged = {
            FIRST_ANALYSIS: staged_analysis,
            EPISODE_OUTCOMES: staged_episodes,
            CONDITION_TABLE: staged_condition_table,
            CONTRAST_TABLE: staged_contrast_table,
            CONTRAST_FIGURE: staged_figure,
        }
        if any(destination.exists() for destination in staged):
            fail("A P10 output appeared during analysis; refusing to overwrite it.")
        for destination, source in staged.items():
            shutil.move(str(source), str(destination))

    provenance = {
        "schema_version": "study3_v3_2_p10_first_analysis_provenance_v1",
        "created_at_utc": utc_now(),
        "decision": "PASS",
        "p9_gate_verified_pass_before_unblinding": True,
        "condition_mapping_revealed": True,
        "arm_to_condition": arm_to_condition,
        "frozen_analysis_invocations": 1,
        "first_analysis_preserved": True,
        "input_hashes": frozen_hashes,
        "output_hashes": {
            str(path.relative_to(ROOT)): sha256_path(path)
            for path in (
                FIRST_ANALYSIS,
                EPISODE_OUTCOMES,
                CONDITION_TABLE,
                CONTRAST_TABLE,
                CONTRAST_FIGURE,
            )
        },
        "counts": {
            "logical_episode_cells": len(episode_rows),
            "valid_episode_records": sum(not row["technical_failure"] for row in episode_rows),
            "preregistered_unresolved_technical_failures": sum(
                bool(row["technical_failure"]) for row in episode_rows
            ),
            "targets": len(retrieval_rows),
        },
    }
    write_json(PROVENANCE, provenance)
    write_json(
        UNBLIND_REPORT,
        {
            "schema_version": "study3_v3_2_p10_unblinding_report_v1",
            "created_at_utc": utc_now(),
            "decision": "PASS",
            "condition_mapping": arm_to_condition,
            "first_analysis_sha256": sha256_path(FIRST_ANALYSIS),
            "first_analysis_provenance_sha256": sha256_path(PROVENANCE),
            "descriptive_condition_rates": descriptives,
        },
    )
    set_gate(
        "P10",
        "PASS",
        [FIRST_ANALYSIS, PROVENANCE, UNBLIND_REPORT, CONDITION_TABLE, CONTRAST_TABLE, CONTRAST_FIGURE],
        {
            "targets": int(result["primary"]["targets"]),
            "valid_episodes": int(provenance["counts"]["valid_episode_records"]),
            "unresolved_technical_failures": int(
                provenance["counts"]["preregistered_unresolved_technical_failures"]
            ),
            "primary_contrast": str(result["primary"]["contrast"]),
            "primary_risk_difference_percentage_points": float(
                result["primary"]["risk_difference_percentage_points"]
            ),
            "primary_sign_flip_p_two_sided": float(result["primary"]["sign_flip_p_two_sided"]),
            "first_analysis_sha256": sha256_path(FIRST_ANALYSIS),
        },
    )
    print(json.dumps({"decision": "PASS", "result": result, "descriptives": descriptives}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"P10 ERROR: {error}", file=sys.stderr)
        raise
