import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_effect_cis_are_consistent():
    df = pd.read_csv(ROOT / "results/inference/effect_ci.csv").set_index("scale_j")
    assert list(df.index) == list(range(1, 10))
    for j, row in df.iterrows():
        assert 0 <= row.ci_low <= row.kendall_w <= row.ci_high <= 1
    assert df.loc[4, "kendall_w"] == 0.6881 or abs(df.loc[4, "kendall_w"] - 0.6881) < 1e-4
    assert df.loc[4, "ci_low"] < 0.60 < df.loc[4, "ci_high"]
    assert df.loc[4, "ci_low"] < 0.69 < df.loc[4, "ci_high"]


def test_diurnal_cis_contain_estimates_and_separate_sjl_sbj():
    df = pd.read_csv(ROOT / "results/tables/diurnal_energy_fraction_ci.csv").set_index("station")
    assert list(df.index) == ["SBJ", "STA", "VMT", "SJL", "SMP"]
    for station, row in df.iterrows():
        assert row.ci_low <= row.pct_E_j4 <= row.ci_high
    assert df.loc["SJL", "ci_low"] > df.loc["SBJ", "ci_high"]


def test_posthoc_is_secondary_and_complete():
    df = pd.read_csv(ROOT / "results/inference/posthoc_pairwise.csv")
    assert len(df) == 90
    assert set(df.scale_j) == set(range(1, 10))
    assert (df.p_holm >= df.p_raw - 1e-15).all()
    j4 = df[df.scale_j == 4]
    assert int(j4.sig_holm.sum()) == 8
    assert not bool(j4[j4.pair == "STA-SJL"].sig_holm.iloc[0])
    assert not bool(j4[j4.pair == "SBJ-SMP"].sig_holm.iloc[0])


def test_uncertainty_summary():
    summary = json.loads((ROOT / "results/inference/uncertainty_summary.json").read_text())
    assert summary["seed"] == 2026
    assert summary["n_boot_effect"] == 2000
    assert summary["n_boot_diurnal"] == 1000
    assert summary["posthoc_pairs"] == 90
