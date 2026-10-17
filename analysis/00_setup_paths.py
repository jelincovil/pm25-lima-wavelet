"""Resolve Final Henry project root and key paths from config.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

ANALYSIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ANALYSIS_DIR.parent
CONFIG_PATH = ANALYSIS_DIR / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_project_root"] = str(PROJECT_ROOT)
    return cfg


def resolve_paths(cfg: Dict[str, Any] = None) -> Dict[str, Path]:
    cfg = cfg or load_config()
    root = PROJECT_ROOT
    raw_rel = cfg["paths"]["raw"]
    return {
        "root": root,
        "raw": root / raw_rel,
        "processed": root / cfg["paths"]["processed"],
        "audit": root / cfg["paths"]["audit"],
        "results": root / cfg["paths"]["results"],
        "tables": root / cfg["paths"]["results"] / "tables",
        "figures": root / cfg["paths"]["results"] / "figures",
        "inference": root / cfg["paths"]["results"] / "inference",
        "sensitivity": root / cfg["paths"]["results"] / "sensitivity",
        "paper_figures": root / "paper" / "figures",
        "config": CONFIG_PATH,
    }


def ensure_dirs(paths: Dict[str, Path]) -> None:
    for key in (
        "processed",
        "audit",
        "results",
        "tables",
        "figures",
        "inference",
        "sensitivity",
        "paper_figures",
    ):
        paths[key].mkdir(parents=True, exist_ok=True)


def main() -> None:
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    print("project_root:", paths["root"])
    print("raw_exists:", paths["raw"].is_file(), paths["raw"])
    print("stations:", cfg["stations"])
    if not paths["raw"].is_file():
        raise SystemExit(1)
    print("setup OK")


if __name__ == "__main__":
    main()
