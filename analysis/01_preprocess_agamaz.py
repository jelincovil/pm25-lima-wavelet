#!/usr/bin/env python3
"""
F2 — Preprocesamiento conservador Agamaz (Henry / Lima PM2.5). Local only.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.stats.stattools import medcouple
from statsmodels.tsa.seasonal import STL

_setup = Path(__file__).resolve().parent / "00_setup_paths.py"
spec = importlib.util.spec_from_file_location("setup_paths", _setup)
setup_paths = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(setup_paths)
load_config = setup_paths.load_config
resolve_paths = setup_paths.resolve_paths
ensure_dirs = setup_paths.ensure_dirs


def limites_boxplot_ajustado(x, multiplicador=1.5):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    q1, q3 = np.quantile(x, [0.25, 0.75])
    iqr = q3 - q1
    mc = float(medcouple(x))
    if iqr == 0:
        return -np.inf, np.inf, mc
    if mc >= 0:
        lo = q1 - multiplicador * np.exp(-4 * mc) * iqr
        hi = q3 + multiplicador * np.exp(3 * mc) * iqr
    else:
        lo = q1 - multiplicador * np.exp(-3 * mc) * iqr
        hi = q3 + multiplicador * np.exp(4 * mc) * iqr
    return float(lo), float(hi), mc


def hampel_local(residuos, janela=49):
    residuos = pd.Series(residuos, copy=True, dtype=float)
    min_periodos = max(7, janela // 2)
    mediana_local = residuos.rolling(window=janela, center=True, min_periods=min_periodos).median()
    mad_local = residuos.rolling(window=janela, center=True, min_periods=min_periodos).apply(
        lambda x: np.median(np.abs(x - np.median(x))), raw=True
    )
    escala = 1.4826 * mad_local
    escala = escala.replace(0, np.nan)
    escore = (residuos - mediana_local) / escala
    return mediana_local, mad_local, escore


def comprimento_das_sequencias(mascara):
    mascara = pd.Series(mascara).fillna(False).astype(bool)
    grupos = mascara.ne(mascara.shift(fill_value=False)).cumsum()
    comprimentos = mascara.groupby(grupos).transform("sum")
    return comprimentos.where(mascara, 0).astype(int)


def ts_clean_aggressive(series, period=24):
    s = series.copy().astype(float)
    stl = STL(s, period=period, robust=True).fit()
    resid = stl.resid
    q1, q3 = np.nanpercentile(resid, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
    out = (resid < lo) | (resid > hi)
    s_clean = s.copy()
    s_clean[out] = stl.trend[out] + stl.seasonal[out]
    s_clean = s_clean.clip(lower=0)
    return s_clean, int(out.sum())


def load_raw(path, stations):
    df = pd.read_csv(path)
    missing = {"date", "HORA", *stations}.difference(df.columns)
    if missing:
        raise ValueError(f"Columnas ausentes en raw: {sorted(missing)}")
    df["datetime"] = pd.to_datetime(
        df["date"].astype(str).str.strip() + " " + df["HORA"].astype(str).str.strip(),
        dayfirst=True, errors="coerce",
    )
    for st in stations:
        df[st] = pd.to_numeric(df[st], errors="coerce")
    return df


def build_base_a(df, stations):
    dados = (
        df[["datetime"] + stations]
        .dropna(subset=["datetime"])
        .groupby("datetime")[stations]
        .mean()
        .sort_index()
    )
    grade = pd.date_range(start=dados.index.min(), end=dados.index.max(), freq="h")
    dados = dados.reindex(grade)
    dados.index.name = "datetime"
    n_ausentes = dados.isna().sum()
    dados_imputados = dados.interpolate(method="time", limit_direction="both")
    if dados_imputados.isna().any().any():
        dados_imputados = dados_imputados.interpolate(method="linear", limit_direction="both")
    if dados_imputados.isna().any().any():
        raise RuntimeError("Aún hay NA tras interpolación.")
    return dados_imputados, n_ausentes


def conservative_clean(dados_imputados, stations, n_ausentes, cfg_pre):
    periodo = int(cfg_pre["stl_period"])
    k_adj = float(cfg_pre["medcouple_fence"])
    janela = int(cfg_pre["hampel_window"])
    k_hampel = float(cfg_pre["hampel_k"])
    k_conc = float(cfg_pre["concordance_k"])
    max_dur = int(cfg_pre["max_duration_hours"])

    residuos = pd.DataFrame(index=dados_imputados.index, columns=stations, dtype=float)
    componente_esperada = pd.DataFrame(index=dados_imputados.index, columns=stations, dtype=float)
    escores_hampel = pd.DataFrame(index=dados_imputados.index, columns=stations, dtype=float)
    flag_ajustado = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    flag_hampel = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    flag_iqr3 = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    parametros = {}

    for estacao in stations:
        ajuste = STL(dados_imputados[estacao], period=periodo, robust=True).fit()
        residuos[estacao] = ajuste.resid
        componente_esperada[estacao] = ajuste.trend + ajuste.seasonal
        lo, hi, mc = limites_boxplot_ajustado(ajuste.resid, multiplicador=k_adj)
        flag_ajustado[estacao] = (ajuste.resid < lo) | (ajuste.resid > hi)
        _, _, escore = hampel_local(ajuste.resid, janela=janela)
        escores_hampel[estacao] = escore
        flag_hampel[estacao] = escore.abs() > k_hampel
        q1, q3 = np.quantile(ajuste.resid, [0.25, 0.75])
        iqr = q3 - q1
        flag_iqr3[estacao] = (ajuste.resid < q1 - 3 * iqr) | (ajuste.resid > q3 + 3 * iqr)
        parametros[estacao] = {
            "medcouple": mc,
            "limite_inferior_ajustado": lo,
            "limite_superior_ajustado": hi,
        }

    flag_duplo = flag_ajustado & flag_hampel
    flag_isolado = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    flag_corrobora = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    flag_final = pd.DataFrame(False, index=dados_imputados.index, columns=stations)
    duracao = pd.DataFrame(0, index=dados_imputados.index, columns=stations, dtype=int)

    for estacao in stations:
        otras = [x for x in stations if x != estacao]
        duracao[estacao] = comprimento_das_sequencias(flag_duplo[estacao])
        flag_isolado[estacao] = flag_duplo[estacao] & (duracao[estacao] <= max_dur)
        pos = escores_hampel[otras].gt(k_conc).any(axis=1)
        neg = escores_hampel[otras].lt(-k_conc).any(axis=1)
        flag_corrobora[estacao] = ((residuos[estacao] > 0) & pos) | ((residuos[estacao] < 0) & neg)
        flag_final[estacao] = flag_duplo[estacao] & flag_isolado[estacao] & ~flag_corrobora[estacao]

    datos_conservadores = dados_imputados.copy()
    for estacao in stations:
        idx = flag_final[estacao]
        datos_conservadores.loc[idx, estacao] = componente_esperada.loc[idx, estacao]
        datos_conservadores[estacao] = datos_conservadores[estacao].clip(lower=0)

    rows = []
    for estacao in stations:
        rows.append({
            "estacao": estacao,
            "n_total": len(dados_imputados),
            "n_imputados": int(n_ausentes[estacao]),
            "medcouple_residuos": parametros[estacao]["medcouple"],
            "sinalizados_3IQR": int(flag_iqr3[estacao].sum()),
            "sinalizados_boxplot_ajustado": int(flag_ajustado[estacao].sum()),
            "sinalizados_hampel": int(flag_hampel[estacao].sum()),
            "concordancia_dos_dois": int(flag_duplo[estacao].sum()),
            "candidatos_finais": int(flag_final[estacao].sum()),
            "percentual_final": 100 * float(flag_final[estacao].mean()),
        })
    resumo = pd.DataFrame(rows)

    lista = []
    for estacao in stations:
        indices = flag_final.index[flag_final[estacao]]
        if len(indices) == 0:
            continue
        lista.append(pd.DataFrame({
            "datetime": indices,
            "estacao": estacao,
            "valor_imputado": dados_imputados.loc[indices, estacao].to_numpy(),
            "valor_substituto_STL": componente_esperada.loc[indices, estacao].to_numpy(),
            "residuo_STL": residuos.loc[indices, estacao].to_numpy(),
            "escore_hampel": escores_hampel.loc[indices, estacao].to_numpy(),
            "duracao_sequencia": duracao.loc[indices, estacao].to_numpy(),
            "corroborado_por_outra_estacao": flag_corrobora.loc[indices, estacao].to_numpy(),
        }))
    diagnostico = (
        pd.concat(lista, ignore_index=True).sort_values(["datetime", "estacao"])
        if lista else pd.DataFrame()
    )
    extras = {"flag_final": flag_final, "parametros": parametros}
    return datos_conservadores, resumo, diagnostico, extras


def plot_eda_raw(df, stations, out_dir):
    long = []
    for st in stations:
        vals = pd.to_numeric(df[st], errors="coerce").dropna()
        long.append(pd.DataFrame({"station": st, "pm25": vals}))
    long_df = pd.concat(long, ignore_index=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=long_df, x="station", y="pm25", ax=ax, showfliers=True)
    ax.axhline(50, color="red", ls="--", lw=1, label="WHO 50 ug/m3 (ref.)")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.set_title("Raw hourly PM2.5 by station (no imputation / no outlier treatment)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "eda_boxplot_raw.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    for st in stations:
        vals = pd.to_numeric(df[st], errors="coerce").dropna()
        sns.kdeplot(vals, label=f"{st} (n={len(vals):,})", ax=ax)
    ax.set_xlabel("PM2.5 (ug/m3)")
    ax.set_title("Raw PM2.5 density by station")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "eda_density_raw.png", dpi=200)
    plt.close(fig)


def plot_candidates(dados_imputados, flag_final, stations, out_path):
    fig, axes = plt.subplots(len(stations), 1, figsize=(16, 13), sharex=True)
    for ax, st in zip(axes, stations):
        ax.plot(dados_imputados.index, dados_imputados[st], color="0.5", lw=0.4, label="imputed series")
        idx = flag_final.index[flag_final[st]]
        if len(idx):
            ax.scatter(idx, dados_imputados.loc[idx, st], s=12, c="crimson", zorder=3,
                       label=f"final candidates (n={len(idx)})")
        ax.set_ylabel(st)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("datetime")
    fig.suptitle("Conservative strong candidates (isolated dual-flag, non-corroborated)", y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def table1_descriptives(datos, n_ausentes, flag_final, stations):
    rows = {}
    for st in stations:
        s = datos[st]
        rows[st] = {
            "Mean": s.mean(),
            "SD": s.std(ddof=1),
            "CV (%)": 100 * s.std(ddof=1) / s.mean(),
            "Min": s.min(),
            "P50": s.quantile(0.50),
            "P99": s.quantile(0.99),
            "Max": s.max(),
            "NAs imputed": int(n_ausentes[st]),
            "Outliers replaced": int(flag_final[st].sum()),
        }
    ordem = ["Mean", "SD", "CV (%)", "Min", "P50", "P99", "Max", "NAs imputed", "Outliers replaced"]
    return pd.DataFrame(rows).loc[ordem, stations]


def main():
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    stations = list(cfg["stations"])
    pre = cfg["preprocess"]

    print("Loading raw:", paths["raw"])
    df = load_raw(paths["raw"], stations)
    print("raw rows:", len(df))

    plot_eda_raw(df, stations, paths["figures"])
    print("EDA figures written")

    dados_a, n_ausentes = build_base_a(df, stations)
    print("Base A shape:", dados_a.shape)
    print("NAs imputed:\n", n_ausentes)

    dados_b, resumo, diagnostico, extras = conservative_clean(dados_a, stations, n_ausentes, pre)
    flag_final = extras["flag_final"]
    print("\nConservative detection summary:")
    print(resumo.round(3).to_string(index=False))

    cleaned_c = {}
    n_orig = {}
    for st in stations:
        ser, n = ts_clean_aggressive(dados_a[st], period=int(pre["stl_period"]))
        cleaned_c[st] = ser
        n_orig[st] = n
    dados_c = pd.DataFrame(cleaned_c, index=dados_a.index)
    dados_c.index.name = "datetime"

    comparacion = pd.DataFrame({
        "Estacion": stations,
        "STL_3IQR": [n_orig[s] for s in stations],
        "Conservador": [int(flag_final[s].sum()) for s in stations],
    })
    comparacion["Reduccion_abs"] = comparacion["STL_3IQR"] - comparacion["Conservador"]
    comparacion["Reduccion_pct"] = 100 * comparacion["Reduccion_abs"] / comparacion["STL_3IQR"]
    print("\nMethod comparison:")
    print(comparacion.round(2).to_string(index=False))

    t1 = table1_descriptives(dados_b, n_ausentes, flag_final, stations)
    print("\nTable 1 (conservative):")
    print(t1.round(2).to_string())

    dados_a.to_csv(paths["processed"] / "datos_lima_solo_imputados.csv", index_label="datetime")
    dados_b.to_csv(paths["processed"] / "datos_lima_limpieza_conservadora.csv", index_label="datetime")
    dados_c.to_csv(paths["processed"] / "datos_lima_limpieza_agresiva_stl3iqr.csv", index_label="datetime")
    resumo.to_csv(paths["audit"] / "resumen_deteccion_atipicos.csv", index=False)
    diagnostico.to_csv(paths["audit"] / "candidatos_fuertes_revision.csv", index=False)
    comparacion.to_csv(paths["audit"] / "comparacion_metodos_outlier.csv", index=False)
    t1.round(4).to_csv(paths["tables"] / "table1_descriptives_conservative.csv")
    plot_candidates(dados_a, flag_final, stations, paths["figures"] / "diagnostico_candidatos_atipicos.png")

    meta = {
        "stations": stations,
        "n_hours": int(len(dados_a)),
        "n_start": str(dados_a.index.min()),
        "n_end": str(dados_a.index.max()),
        "n_ausentes": {k: int(v) for k, v in n_ausentes.items()},
        "candidatos_finais": {s: int(flag_final[s].sum()) for s in stations},
        "stl3iqr": n_orig,
        "config_preprocess": pre,
    }
    (paths["audit"] / "preprocess_run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("\nWrote Base A/B/C + audit + Table1 + figures under Final Henry/")
    print("F2 complete.")


if __name__ == "__main__":
    main()
