import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_dwt_qc_thresholds():
    qc = pd.read_csv(ROOT / "results/inference/dwt_qc.csv").set_index("station")
    assert list(qc.index) == ["SBJ", "STA", "VMT", "SJL", "SMP"]
    assert qc["max_reconstruction_error"].max() < 1e-8
    assert qc["relative_parseval_error"].max() < 1e-10


def test_wavelet_metadata():
    meta = json.loads((ROOT / "results/inference/wavelet_meta.json").read_text())
    assert meta["n_original"] == 10176
    assert meta["N"] == 16384
    assert meta["pad_left"] == 3104
    assert meta["pad_right"] == 3104
    assert meta["wavelet"] == "sym7"
    assert meta["j_seguro"] == 10


def test_scale_eligibility():
    df = pd.read_csv(ROOT / "results/tables/scale_eligibility.csv").set_index("scale_j")
    assert df.loc[1:9, "eligible_for_inference"].all()
    assert not df.loc[10:, "eligible_for_inference"].any()
