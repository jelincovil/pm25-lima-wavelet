from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STATIONS = ["SBJ", "STA", "VMT", "SJL", "SMP"]


def test_preprocess_counts_match_manuscript():
    df = pd.read_csv(ROOT / "data/audit/resumen_deteccion_atipicos.csv").set_index("estacao")
    assert list(df.index) == STATIONS
    assert (df["n_total"] == 10176).all()
    assert df["n_imputados"].to_dict() == {
        "SBJ": 693,
        "STA": 570,
        "VMT": 404,
        "SJL": 500,
        "SMP": 244,
    }
    assert df["candidatos_finais"].to_dict() == {
        "SBJ": 69,
        "STA": 81,
        "VMT": 88,
        "SJL": 72,
        "SMP": 110,
    }
    assert df["sinalizados_3IQR"].to_dict() == {
        "SBJ": 1342,
        "STA": 1152,
        "VMT": 793,
        "SJL": 895,
        "SMP": 1118,
    }


def test_processed_bases_are_complete():
    for name in [
        "datos_lima_solo_imputados.csv",
        "datos_lima_limpieza_conservadora.csv",
        "datos_lima_limpieza_agresiva_stl3iqr.csv",
    ]:
        df = pd.read_csv(ROOT / "data/processed" / name, index_col=0, parse_dates=True)
        assert list(df.columns) == STATIONS
        assert len(df) == 10176
        assert not df.isna().any().any()


def test_outlier_counts_are_order_of_magnitude_smaller_than_aggressive():
    summary = pd.read_csv(ROOT / "data/audit/resumen_deteccion_atipicos.csv")
    for _, row in summary.iterrows():
        assert row["candidatos_finais"] < 0.02 * row["n_total"]
        assert row["candidatos_finais"] * 8 < row["sinalizados_3IQR"]
