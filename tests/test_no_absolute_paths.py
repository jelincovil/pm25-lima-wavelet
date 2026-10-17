import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ["analysis", "data", "paper", "results", "scripts"]
TEXT_SUFFIXES = {".py", ".csv", ".json", ".tex", ".md", ".yaml", ".yml", ".txt"}
PATTERNS = [re.compile(r"/Users/"), re.compile(r"[A-Za-z]:\\\\(?:Users|Windows|Temp|Program)"), re.compile(r"file://")]


def test_no_absolute_paths_in_versioned_artifacts():
    offenders = []
    for folder in SCAN_DIRS:
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in PATTERNS:
                if pattern.search(text):
                    offenders.append(str(path.relative_to(ROOT)))
                    break
    assert not offenders, f"absolute paths found in: {offenders}"
