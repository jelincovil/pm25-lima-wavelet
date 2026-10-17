import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_registered_token_appears_in_manuscript():
    tex = (ROOT / "paper/article_REDIN.tex").read_text(encoding="utf-8")
    with (ROOT / "docs/NUMBER_REGISTRY.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows, "registry is empty"
    missing = [(row["claim_id"], row["paper_token"]) for row in rows if row["paper_token"] not in tex]
    assert not missing, f"tokens absent from manuscript: {missing}"


def test_registry_artifacts_exist():
    with (ROOT / "docs/NUMBER_REGISTRY.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [row["artifact"] for row in rows if not (ROOT / row["artifact"]).exists()]
    assert not missing, f"artifacts absent: {missing}"


def test_registry_ids_are_unique():
    with (ROOT / "docs/NUMBER_REGISTRY.csv").open(newline="", encoding="utf-8") as f:
        ids = [row["claim_id"] for row in csv.DictReader(f)]
    assert len(ids) == len(set(ids))
