from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_formal_scales_and_methods():
    df = pd.read_csv(ROOT / "results/inference/adaptive_results.csv").set_index("scale_j")
    assert list(df.index) == list(range(1, 10))
    expected = {
        1: "Permutacao-blocos",
        2: "Permutacao-blocos",
        3: "Permutacao-blocos",
        4: "Permutacao-blocos",
        5: "ANOVA-RM",
        6: "Permutacao-blocos",
        7: "Permutacao-blocos",
        8: "Friedman",
        9: "Friedman",
    }
    assert df["selected_method"].to_dict() == expected


def test_effect_sizes_and_pvalues():
    df = pd.read_csv(ROOT / "results/inference/adaptive_results.csv").set_index("scale_j")
    assert df.loc[4, "effect_size"] == pytest.approx(0.6881, abs=1e-4)
    assert df.loc[4, "raw_p"] == pytest.approx(1.0e-4, abs=1e-12)
    assert df.loc[5, "raw_p"] == pytest.approx(1.406e-11, rel=1e-2)
    assert df.loc[8, "raw_p"] == pytest.approx(0.007892, abs=1e-6)
    assert df.loc[8, "p_bonferroni"] == pytest.approx(0.07103, abs=1e-5)
    assert not bool(df.loc[8, "sig_bonferroni"])
    assert df.loc[9, "raw_p"] == pytest.approx(0.184702, abs=1e-6)
    assert not bool(df.loc[9, "sig_bonferroni"])


def test_block_structure_is_reported():
    df = pd.read_csv(ROOT / "results/inference/adaptive_results.csv").set_index("scale_j")
    assert df.loc[1:6, "n_temporal_blocks"].eq(19).all()
    assert df.loc[7, "n_temporal_blocks"] == 20
    assert df.loc[8, "n_temporal_blocks"] == 40
    assert df.loc[9, "n_temporal_blocks"] == 20
    assert df.loc[1, "coefficient_block_size"] == 256
    assert df.loc[8, "coefficient_block_size"] == 1
    assert df.loc[9, "coefficient_block_size"] == 1
