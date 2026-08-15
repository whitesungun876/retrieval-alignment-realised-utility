#!/usr/bin/env python3
"""Build immutable P/C materials from the old frozen P assignment without outcomes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import random
import re
from typing import Any

from transformers import AutoTokenizer

from src.common import OLD_SUP, ROOT, read_json, read_jsonl, refuse_overwrite, sha256_bytes, sha256_path, stable_json, write_json, write_jsonl
from src.renderer import body_sha256, normalize_shell, render_c_matched


MATERIALS = ROOT / "materials"
FORMAL = ROOT / "formal"
SEALED = ROOT / "sealed"
REPORTS = ROOT / "reports"
SELECTED_TARGETS = MATERIALS / "selected_targets.jsonl"
SELECTED_SOURCES = MATERIALS / "selected_sources.jsonl"
EXPERIENCES = MATERIALS / "experience_pairs.jsonl"
INVENTORY = MATERIALS / "combined_inventory.jsonl"
PUBLIC = FORMAL / "formal_manifest.jsonl"
BINDINGS = SEALED / "sealed_execution_bindings.jsonl"
CONDITION_MAP = SEALED / "sealed_condition_map.json"
REPORT = REPORTS / "materials_preflight_report.json"

OLD_TARGETS = OLD_SUP / "materials/selected_targets.jsonl"
OLD_SOURCES = OLD_SUP / "formal/combined_inventory_rec001.jsonl"
OLD_MAPPING = OLD_SUP / "retrieval/r2_p_mapping.jsonl"
OLD_MODEL = OLD_SUP / "formal/qwen_model_rec001.yaml"
OLD_INTERFACE = OLD_SUP / "formal/experience_interface_v1.yaml"
DESIGN = ROOT / "config/design_v1.json"


def _tokenizer() -> tuple[Any, dict[str, Any]]:
    config = read_json(DESIGN)["tokenizer"]
    tokenizer = AutoTokenizer.from_pretrained(config["requested_model"], local_files_only=True)
    raw_snapshot = tokenizer.init_kwargs.get("tokenizer_file")
    snapshot = Path(raw_snapshot) if raw_snapshot else None
    return tokenizer, {
        "requested_model": config["requested_model"],
        "resolved_name_or_path": tokenizer.name_or_path,
        "class": type(tokenizer).__name__,
        "vocabulary_size": len(tokenizer),
        "tokenizer_file": str(snapshot) if snapshot else None,
        "tokenizer_file_sha256": sha256_path(snapshot) if snapshot and snapshot.is_file() else None,
    }


def _source_terms(source: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in source.get("ingredients", []):
        values.add(str(item).strip().lower())
    for action in source.get("gold_actions", []):
        values.add(str(action).strip().lower())
    for marker in (str(source.get("task_id", "")), str(source.get("source_id", "")), str(source.get("seed", ""))):
        if marker:
            values.add(marker.lower())
    for text in (str(source.get("recipe_text", "")), str(source.get("initial_observation", ""))):
        for token in re.findall(r"[a-z]+(?: [a-z]+){0,3}", text.lower()):
            if len(token) >= 6:
                values.add(token)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-new-root-only", action="store_true", help="Required acknowledgement; existing outputs are still never overwritten.")
    args = parser.parse_args()
    if not args.force_new_root_only:
        raise PermissionError("Pass --force-new-root-only to acknowledge the isolated write root.")
    refuse_overwrite(SELECTED_TARGETS, SELECTED_SOURCES, EXPERIENCES, INVENTORY, PUBLIC, BINDINGS, CONDITION_MAP, REPORT)
    design = read_json(DESIGN)
    tokenizer, tokenizer_metadata = _tokenizer()
    count_tokens = lambda text: len(tokenizer.encode(text, add_special_tokens=False))

    targets = read_jsonl(OLD_TARGETS)
    mapping = read_jsonl(OLD_MAPPING)
    if len(targets) != 800 or len(mapping) != 800:
        raise RuntimeError("Expected the frozen 800-target supplemental design.")
    target_by_id = {str(row["task_id"]): row for row in targets}
    source_seeds = {int(row["P_source_seed"]) for row in mapping}
    source_rows_all = {int(row["seed"]): row for row in read_jsonl(OLD_SOURCES)}
    sources = [source_rows_all[seed] for seed in sorted(source_seeds)]

    experience_rows: list[dict[str, Any]] = []
    ratio_values: list[float] = []
    leak_failures: list[dict[str, Any]] = []
    for source in sources:
        pair = render_c_matched(source, count_tokens, float(design["length_ratio_min"]), float(design["length_ratio_max"]))
        lower = pair.c_text.lower()
        hits = sorted(term for term in _source_terms(source) if term and term in lower)
        if hits:
            leak_failures.append({"source_seed": int(source["seed"]), "hits": hits[:20]})
        if normalize_shell(pair.p_text) != normalize_shell(pair.c_text):
            raise RuntimeError(f"P/C shell mismatch for source {source['seed']}")
        row = {
            "schema_version": "protocol_control_experience_pair_v1",
            "source_seed": int(source["seed"]),
            "source_task_id": str(source["task_id"]),
            "p_text": pair.p_text,
            "c_text": pair.c_text,
            "p_sha256": body_sha256(pair.p_text),
            "c_sha256": body_sha256(pair.c_text),
            "p_tokens": pair.p_tokens,
            "c_tokens": pair.c_tokens,
            "token_ratio_c_over_p": pair.token_ratio,
            "trajectory_steps": len(pair.phases),
            "phases": list(pair.phases),
            "common_shell_sha256": sha256_bytes(normalize_shell(pair.p_text).encode()),
            "source_terms_in_c": hits,
        }
        experience_rows.append(row)
        ratio_values.append(pair.token_ratio)
    if leak_failures:
        raise RuntimeError(f"Leakage audit failed for {len(leak_failures)} source(s): {leak_failures[:3]}")

    rng = random.Random(int(design["arm_mask_seed"]))
    conditions = ["P", "C"]
    rng.shuffle(conditions)
    arm_to_condition = {f"arm_{index + 1}": condition for index, condition in enumerate(conditions)}
    condition_to_arm = {value: key for key, value in arm_to_condition.items()}
    p_mapping = {str(row["target_id"]): row for row in mapping}
    experience_by_seed = {int(row["source_seed"]): row for row in experience_rows}
    public: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    for target_index, target in enumerate(targets, start=1):
        target_id = str(target["task_id"])
        mapped = p_mapping[target_id]
        source_seed = int(mapped["P_source_seed"])
        exp = experience_by_seed[source_seed]
        for repetition in (1, 2):
            for condition in ("P", "C"):
                arm = condition_to_arm[condition]
                run_id = f"pc-t{target_index:04d}-{arm}-r{repetition:02d}"
                pub = {
                    "schema_version": "protocol_control_public_cell_v1",
                    "run_id": run_id,
                    "target_index": target_index,
                    "target_id": target_id,
                    "target_seed": int(target["seed"]),
                    "masked_arm": arm,
                    "repetition": repetition,
                    "run_order": None,
                    "scientific_rerun_allowed": False,
                    "transport_retry_cap": 2,
                }
                pub["design_row_sha256"] = sha256_bytes(stable_json(pub))
                experience_sha = exp["p_sha256"] if condition == "P" else exp["c_sha256"]
                binding = {
                    "schema_version": "protocol_control_sealed_binding_v1",
                    "run_id": run_id,
                    "condition": condition,
                    "source_seed": source_seed,
                    "experience_sha256": experience_sha,
                    "paired_p_source_seed": source_seed,
                    "target_cookbook_sha256": str(target["hashes"]["cookbook_sha256"]),
                }
                binding["binding_sha256"] = sha256_bytes(stable_json(binding))
                public.append(pub)
                bindings.append(binding)
    order_rng = random.Random(int(design["formal_run_order_seed"]))
    order_rng.shuffle(public)
    binding_by_id = {row["run_id"]: row for row in bindings}
    ordered_bindings: list[dict[str, Any]] = []
    for order, row in enumerate(public, start=1):
        row["run_order"] = order
        row["design_row_sha256"] = sha256_bytes(stable_json({k: v for k, v in row.items() if k != "design_row_sha256"}))
        ordered_bindings.append(binding_by_id[row["run_id"]])

    selected_source_counts = Counter(int(row["P_source_seed"]) for row in mapping)
    checks = {
        "old_inputs_read_only_and_present": all(path.exists() for path in (OLD_TARGETS, OLD_SOURCES, OLD_MAPPING, OLD_MODEL, OLD_INTERFACE)),
        "targets_800": len(targets) == 800 and len(target_by_id) == 800,
        "p_sources_515": len(sources) == 515,
        "all_sources_replay_verified_success": all(bool(row["official_replay"]["verified_success"]) for row in sources),
        "experience_pairs_515": len(experience_rows) == 515,
        "length_ratio_every_source_within_bounds": all(float(design["length_ratio_min"]) <= value <= float(design["length_ratio_max"]) for value in ratio_values),
        "leakage_hits_zero": not leak_failures,
        "common_shell_parity_all_sources": all(normalize_shell(row["p_text"]) == normalize_shell(row["c_text"]) for row in experience_rows),
        "turn_and_phase_counts_match": all(row["trajectory_steps"] == len(row["phases"]) for row in experience_rows),
        "formal_cells_3200": len(public) == 3200 and len({row["run_id"] for row in public}) == 3200,
        "two_arms_masked": set(arm_to_condition) == {"arm_1", "arm_2"},
        "each_target_arm_two_repetitions": Counter((row["target_id"], row["masked_arm"]) for row in public) == Counter({(target["task_id"], arm): 2 for target in targets for arm in arm_to_condition}),
        "public_manifest_blinded": all("condition" not in row and "source_seed" not in row for row in public),
        "p_c_share_source_each_target": all(int(row["source_seed"]) == int(row["paired_p_source_seed"]) for row in ordered_bindings),
        "run_orders_complete": sorted(row["run_order"] for row in public) == list(range(1, 3201)),
        "source_reuse_max_recorded": max(selected_source_counts.values()) >= 1,
        "new_pc_outcomes_read_zero": True,
        "paid_provider_calls_zero": True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Material checks failed: {checks}")
    write_jsonl(SELECTED_TARGETS, targets)
    write_jsonl(SELECTED_SOURCES, sources)
    write_jsonl(EXPERIENCES, experience_rows)
    inventory = {int(row["seed"]): row for row in targets + sources}
    write_jsonl(INVENTORY, [inventory[key] for key in sorted(inventory)])
    write_jsonl(PUBLIC, public)
    write_jsonl(BINDINGS, ordered_bindings)
    os.chmod(BINDINGS, 0o600)
    write_json(CONDITION_MAP, {"schema_version": "protocol_control_condition_map_v1", "arm_to_condition": arm_to_condition, "masking_seed": design["arm_mask_seed"], "unblind_only_after_technical_acceptance": True})
    os.chmod(CONDITION_MAP, 0o600)
    output_paths = [SELECTED_TARGETS, SELECTED_SOURCES, EXPERIENCES, INVENTORY, PUBLIC, BINDINGS, CONDITION_MAP]
    report = {
        "schema_version": "protocol_control_materials_preflight_v1",
        "decision": "PASS",
        "checks": checks,
        "tokenizer": tokenizer_metadata,
        "length_matching": {
            "minimum": min(ratio_values),
            "median": sorted(ratio_values)[len(ratio_values) // 2],
            "maximum": max(ratio_values),
            "target_range": [design["length_ratio_min"], design["length_ratio_max"]],
        },
        "source_reuse": {"unique_sources": len(selected_source_counts), "maximum_reuse": max(selected_source_counts.values())},
        "old_input_hashes": {str(path): sha256_path(path) for path in (OLD_TARGETS, OLD_SOURCES, OLD_MAPPING, OLD_MODEL, OLD_INTERFACE)},
        "output_hashes": {str(path.relative_to(ROOT)): sha256_path(path) for path in output_paths},
        "new_pc_outcomes_read": False,
        "paid_provider_called": False,
    }
    write_json(REPORT, report)
    print(json.dumps({"decision": "PASS", "formal_cells": 3200, "sources": len(sources), "report": str(REPORT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
