#!/usr/bin/env python3
"""Check that every token in docs/NUMBER_REGISTRY.csv appears in the manuscript."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "NUMBER_REGISTRY.csv"
TEX = ROOT / "paper" / "article_REDIN.tex"


def main() -> int:
    if not REGISTRY.is_file():
        print(f"missing registry: {REGISTRY}")
        return 1
    if not TEX.is_file():
        print(f"missing manuscript: {TEX}")
        return 1

    tex = TEX.read_text(encoding="utf-8")
    with REGISTRY.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("registry is empty")
        return 1

    missing_tokens = []
    missing_artifacts = []
    for row in rows:
        if row["paper_token"] not in tex:
            missing_tokens.append((row["claim_id"], row["paper_token"]))
        artifact = ROOT / row["artifact"]
        if not artifact.exists():
            missing_artifacts.append((row["claim_id"], row["artifact"]))

    print(f"claims checked: {len(rows)}")
    if missing_tokens:
        print("tokens absent from manuscript:")
        for claim_id, token in missing_tokens:
            print(f"  - {claim_id}: {token!r}")
    if missing_artifacts:
        print("artifacts absent:")
        for claim_id, artifact in missing_artifacts:
            print(f"  - {claim_id}: {artifact}")

    if missing_tokens or missing_artifacts:
        return 1
    print("all registered tokens and artifacts are present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
