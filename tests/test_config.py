from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_config_contract():
    cfg = yaml.safe_load((ROOT / "analysis/config.yaml").read_text())
    assert cfg["stations"] == ["SBJ", "STA", "VMT", "SJL", "SMP"]
    assert cfg["wavelet"]["family"] == "sym7"
    assert cfg["wavelet"]["pad_to"] == 16384
    assert cfg["wavelet"]["j_formal_max"] == 9
    assert cfg["wavelet"]["min_blocks"] == 12
    assert cfg["preprocess"]["stl_period"] == 24
    assert cfg["preprocess"]["hampel_window"] == 49
    assert cfg["preprocess"]["hampel_k"] == 4.0
    assert cfg["inference"]["n_permutations"] == 9999
    assert cfg["inference"]["seed"] == 2026
    assert cfg["inference"]["alpha"] == 0.05
