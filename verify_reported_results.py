#!/usr/bin/env python3
"""Recompute principal target-weighted point estimates from public outcomes."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def target_means(path: Path) -> dict[str, dict[str, float]]:
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in read_jsonl(path):
        missing = bool(row.get("technical_failure", row.get("technical_missing", False)))
        success = row.get("terminal_success")
        if missing or success is None:
            continue
        values[(str(row["target_id"]), str(row["condition"]))].append(float(bool(success)))
    result: dict[str, dict[str, float]] = defaultdict(dict)
    for (target, condition), episodes in values.items():
        result[target][condition] = sum(episodes) / len(episodes)
    return dict(result)


def contrast(means: dict[str, dict[str, float]], left: str, right: str) -> float:
    targets = sorted(target for target, row in means.items() if left in row and right in row)
    if not targets:
        raise RuntimeError(f"No paired targets for {left}-{right}")
    return 100.0 * sum(means[target][left] - means[target][right] for target in targets) / len(targets)


def check(name: str, observed: float, expected: float) -> None:
    if abs(observed - expected) > 1e-9:
        raise RuntimeError(f"{name}: expected {expected}, observed {observed}")
    print(f"{name}: {observed:+.6f} percentage points")


def main() -> None:
    main_means = target_means(ROOT / "main_study/results/p10_episode_outcomes_first.jsonl")
    assignment_means = target_means(ROOT / "assignment_followup/results/sup_r6_episode_outcomes_first.jsonl")
    pc_means = target_means(ROOT / "trajectory_control_followup/results/pc_episode_outcomes_sanitised.jsonl")

    check("main R-N", contrast(main_means, "R", "N"), 20.59259259259259)
    check("main D-R", contrast(main_means, "D", "R"), 0.8888888888888888)
    check("assignment R2-P", contrast(assignment_means, "R2", "P"), 1.375)
    check("assignment P-N2", contrast(assignment_means, "P", "N2"), 21.3125)
    check("assignment R2-N2", contrast(assignment_means, "R2", "N2"), 22.6875)
    check("trajectory P-C", contrast(pc_means, "P", "C"), 20.0625)
    print("All principal point estimates match the frozen reports.")


if __name__ == "__main__":
    main()
