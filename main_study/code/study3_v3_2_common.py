#!/usr/bin/env python3
"""Shared, outcome-blind utilities for Study 3 Protocol v3.2."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "study3_v3_2"
CONFIG = STUDY / "config/study3_v3_2.json"
GATES = STUDY / "status/gates.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    atomic_write(
        path,
        "".join(
            json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
    )


def set_gate(
    stage: str,
    status: str,
    evidence: Sequence[Path],
    metrics: Mapping[str, Any],
) -> None:
    registry = read_json(GATES)
    registry["updated_at_utc"] = utc_now()
    registry["gates"][stage] = {
        "status": status,
        "evidence": [str(path.relative_to(ROOT)) for path in evidence],
        "metrics": dict(metrics),
    }
    registry["formal_execution_authorized"] = False
    write_json(GATES, registry)


def require_prior_gates(stage_number: int) -> None:
    registry = read_json(GATES)
    missing = [
        f"P{number}"
        for number in range(stage_number)
        if registry["gates"][f"P{number}"]["status"] != "PASS"
    ]
    if missing:
        raise RuntimeError("Required prior gates not PASS: " + ", ".join(missing))
