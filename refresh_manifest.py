#!/usr/bin/env python3
"""Refresh the repository SHA-256 inventory."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    paths = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.name != "MANIFEST.sha256"
    )
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in paths]
    (ROOT / "MANIFEST.sha256").write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {len(lines)} entries")


if __name__ == "__main__":
    main()
