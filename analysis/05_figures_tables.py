#!/usr/bin/env python3
"""
F6 — Paper figures and tables from Base B (conservative).

Generates:
  paper/figures/figure_1.png  (preprocessing; paper Fig.1)
  paper/figures/figure_4.png  (diurnal + boxplots; paper Fig.2)
  paper/figures/figure_2.png  (already from F4; multiscale; paper Fig.3) — refresh if needed
  results/tables/table1_descriptives_conservative.csv (refresh)
  results/tables/table2_scale_tests.tex + .csv
  results/tables/table_preprocess_impact.csv
  docs/NUMBER_REGISTRY.csv updates
  docs/FIGURE_NARRATIVE_CHECKLIST.md partial updates

Local only.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image

plt.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 17,
    "axes.labelsize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 11,
})

_setup = Path(__file__).resolve().parent / "00_setup_paths.py"
spec = importlib.util.spec_from_file_location("setup_paths", _setup)
setup_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_paths)
load_config = setup_paths.load_config


def _optimize_png(path: Path) -> None:
    """Convert a Matplotlib PNG to optimized RGB (keeps paper figures <500 KB)."""
    with Image.open(path) as im:
        im.convert("RGB").save(path, optimize=True)
resolve_paths = setup_paths.resolve_paths
ensure_dirs = setup_paths.ensure_dirs


def load_series(path: Path, stations):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df[stations].astype(float)


def figure1_preprocessing(paths, stations, n_ausentes, n_outliers, base_b):
    """Panel A: multi-station series; Panel B: NA vs outlier bars."""
    fig, axes = plt.subplots(
        2, 1, figsize=(10, 7.5), gridspec_kw={"height_ratios": [2.2, 1.0]}
    )
    ax = axes[0]
    colors = {"SBJ": "#1f77b4", "STA": "#d62728", "VMT": "#2ca02c", "SJL": "#9467bd", "SMP": "#ff7f0e"}
    for st in stations:
        ax.plot(base_b.index, base_b[st], lw=0.35, color=colors.get(st, "gray"), label=st, alpha=0.9)
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("A. Hourly PM2.5 after conservative preprocessing (n = {:,})".format(len(base_b)), pad=30)
    ax.legend(ncol=5, fontsize=11, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              frameon=False, handlelength=1.5, columnspacing=1.0, handletextpad=0.4)
    ax.grid(axis="y", alpha=0.3)

    axb = axes[1]
    x = np.arange(len(stations))
    w = 0.38
    nas = [int(n_ausentes[st]) for st in stations]
    outs = [int(n_outliers[st]) for st in stations]
    bars1 = axb.bar(x - w / 2, nas, w, color="#4DB6AC", edgecolor="black", lw=0.4, label="Missing values imputed")
    bars2 = axb.bar(x + w / 2, outs, w, color="#E57373", edgecolor="black", lw=0.4, label="Values replaced (conservative)")
    axb.set_xticks(x)
    axb.set_xticklabels(stations)
    axb.set_ylabel("Count")
    axb.set_title("B. Values modified per station")
    axb.legend(fontsize=10)
    axb.grid(axis="y", alpha=0.3)
    # annotate means of replaced points if we have diagnostics
    for i, st in enumerate(stations):
        axb.text(x[i] - w / 2, nas[i], str(nas[i]), ha="center", va="bottom", fontsize=9)
        axb.text(x[i] + w / 2, outs[i], str(outs[i]), ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    out = paths["paper_figures"] / "figure_1.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    _optimize_png(out)
    fig.savefig(paths["figures"] / "figure1_conservative_preprocessing.png", dpi=300, bbox_inches="tight")
    fig.savefig(paths["figures"] / "figure1_conservative_preprocessing.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


def figure_diurnal_box(paths, stations, base_b):
    """Paper Fig.2 (file figure_4.png): mean diurnal cycle + boxplots."""
    df = base_b.copy()
    df["hour"] = df.index.hour
    diurnal = df.groupby("hour")[stations].mean()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    ax = axes[0]
    colors = {"SBJ": "#1f77b4", "STA": "#d62728", "VMT": "#2ca02c", "SJL": "#9467bd", "SMP": "#ff7f0e"}
    for st in stations:
        ax.plot(diurnal.index, diurnal[st], marker="o", ms=3, lw=1.5, color=colors[st], label=st)
    city = diurnal.mean(axis=1)
    ax.plot(diurnal.index, city, color="black", lw=2.2, ls="--", label="city mean")
    peak_h = int(city.idxmax())
    trough_h = int(city.idxmin())
    ax.axhline(50, color="red", ls=":", lw=1, alpha=0.7, label="WHO 50 µg/m³")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Mean PM2.5 (µg/m³)")
    ax.set_title("A. Mean diurnal cycle", pad=46)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(fontsize=10, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              frameon=False, handlelength=1.5, columnspacing=1.0, handletextpad=0.4)
    ax.grid(alpha=0.3)

    axb = axes[1]
    long = df[stations].melt(var_name="station", value_name="pm25")
    sns.boxplot(data=long, x="station", y="pm25", ax=axb, showfliers=False, palette=colors)
    # light fliers sample
    sns.stripplot(data=long.sample(min(5000, len(long)), random_state=2026),
                  x="station", y="pm25", ax=axb, size=1, color="0.3", alpha=0.15, jitter=0.25)
    axb.axhline(50, color="red", ls="--", lw=1.2, label="WHO 50 µg/m³")
    axb.set_ylabel("PM2.5 (µg/m³)")
    axb.set_title("B. Hourly distributions by station")
    axb.legend(fontsize=10)
    axb.grid(axis="y", alpha=0.3)

    fig.suptitle("Diurnal cycle and distributional properties (Base B conservative)", y=1.02)
    fig.tight_layout()
    out = paths["paper_figures"] / "figure_4.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    _optimize_png(out)
    fig.savefig(paths["figures"] / "figure_diurnal_boxplots.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    stats_diurnal = {
        "city_peak_hour": peak_h,
        "city_peak_value": float(city.loc[peak_h]),
        "city_trough_hour": trough_h,
        "city_trough_value": float(city.loc[trough_h]),
        "station_peak_09": {st: float(diurnal.loc[9, st]) if 9 in diurnal.index else float(diurnal.loc[peak_h, st]) for st in stations},
        "station_mean_at_city_peak": {st: float(diurnal.loc[peak_h, st]) for st in stations},
    }
    return out, stats_diurnal, diurnal


def table1(base_b, n_ausentes, n_outliers, stations):
    rows = {}
    for st in stations:
        s = base_b[st]
        rows[st] = {
            "Mean": s.mean(),
            "SD": s.std(ddof=1),
            "CV (%)": 100 * s.std(ddof=1) / s.mean(),
            "Min": s.min(),
            "P50": s.quantile(0.50),
            "P99": s.quantile(0.99),
            "Max": s.max(),
            "NAs imputed": int(n_ausentes[st]),
            "Outliers replaced": int(n_outliers[st]),
        }
    ordem = ["Mean", "SD", "CV (%)", "Min", "P50", "P99", "Max", "NAs imputed", "Outliers replaced"]
    return pd.DataFrame(rows).loc[ordem, stations]


def table2_from_inference(inf_path: Path):
    r = pd.read_csv(inf_path)
    cols = [
        "scale_j", "period_low_h", "period_high_h", "selected_method",
        "statistic", "raw_p", "p_bonferroni", "sig_bonferroni",
        "effect_name", "effect_size", "independence_ok", "normality_ok",
    ]
    cols = [c for c in cols if c in r.columns]
    t = r[cols].sort_values("scale_j")
    # LaTeX fragment
    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Scale-wise inter-station tests after assumption checking (Base B). Bonferroni over $M=9$ scales.}",
        r"\label{tab:tests}",
        r"\small",
        r"\begin{tabular}{rrrlrrrl}",
        r"\toprule",
        r"$j$ & Period (h) & Method & Stat. & $p$ & $p_{\mathrm{Bonf}}$ & Sig. & Effect \\",
        r"\midrule",
    ]
    for _, row in t.iterrows():
        per = f"{int(row['period_low_h'])}--{int(row['period_high_h'])}"
        method_map = {
            "Permutacao-blocos": "Block perm.",
            "ANOVA-RM": "ANOVA-RM",
            "ANOVA-RM-GG": "ANOVA-RM (GG)",
            "Friedman": "Friedman",
        }
        method = method_map.get(str(row["selected_method"]), str(row["selected_method"])).replace("_", r"\_")
        p = row["raw_p"]
        pb = row["p_bonferroni"]
        p_s = f"{p:.2e}" if p < 0.001 else f"{p:.4f}"
        pb_s = f"{pb:.2e}" if pb < 0.001 else f"{pb:.4f}"
        sig = "yes" if row["sig_bonferroni"] else "no"
        eff = f"{row['effect_size']:.3f}"
        lines.append(
            f"{int(row['scale_j'])} & {per} & {method} & {row['statistic']:.3f} & {p_s} & {pb_s} & {sig} & {eff} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return t, "\n".join(lines)


def main():
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    stations = list(cfg["stations"])

    base_b = load_series(paths["processed"] / "datos_lima_limpieza_conservadora.csv", stations)
    resumen = pd.read_csv(paths["audit"] / "resumen_deteccion_atipicos.csv")
    n_ausentes = dict(zip(resumen["estacao"], resumen["n_imputados"]))
    n_outliers = dict(zip(resumen["estacao"], resumen["candidatos_finais"]))
    # fallback
    for st in stations:
        n_ausentes.setdefault(st, 0)
        n_outliers.setdefault(st, 0)

    print("Fig.1 ...")
    f1 = figure1_preprocessing(paths, stations, n_ausentes, n_outliers, base_b)
    print(" ", f1)

    print("Fig.2 (figure_4.png) diurnal...")
    f4, diurnal_stats, diurnal = figure_diurnal_box(paths, stations, base_b)
    print(" ", f4, diurnal_stats)

    # ensure Fig.3 exists
    f3 = paths["paper_figures"] / "figure_2.png"
    if not f3.is_file():
        src = paths["figures"] / "figure3_assumption_checked.png"
        if src.is_file():
            import shutil
            shutil.copy(src, f3)
            print(" copied Fig.3 from results")
    else:
        print(" Fig.3 already at", f3)

    print("Tables...")
    t1 = table1(base_b, n_ausentes, n_outliers, stations)
    t1.round(4).to_csv(paths["tables"] / "table1_descriptives_conservative.csv")
    # LaTeX table1
    t1r = t1.round(2)
    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Descriptive statistics of hourly PM2.5 ($\mu$g/m$^3$) after conservative preprocessing ($n = 10{,}176$).}",
        r"\label{tab:descriptive}",
        r"\small",
        r"\begin{tabular}{l" + "r" * len(stations) + "}",
        r"\toprule",
        " & " + " & ".join(stations) + r" \\",
        r"\midrule",
    ]
    for idx in t1r.index:
        vals = []
        for st in stations:
            v = t1r.loc[idx, st]
            if idx in ("NAs imputed", "Outliers replaced"):
                vals.append(str(int(v)))
            else:
                vals.append(f"{v:.2f}")
        lines.append(f"{idx} & " + " & ".join(vals) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (paths["tables"] / "table1_descriptives_conservative.tex").write_text("\n".join(lines), encoding="utf-8")

    t2, t2tex = table2_from_inference(paths["inference"] / "adaptive_results.csv")
    t2.to_csv(paths["tables"] / "table2_scale_tests.csv", index=False)
    (paths["tables"] / "table2_scale_tests.tex").write_text(t2tex, encoding="utf-8")

    # impact comparison
    comp = pd.read_csv(paths["audit"] / "comparacion_metodos_outlier.csv")
    comp.to_csv(paths["tables"] / "table_preprocess_impact.csv", index=False)

    # diurnal energy j4 from sensitivity B
    energy = pd.read_csv(paths["tables"] / "multiscale_energy.csv", index_col=0)
    energy.index = energy.index.astype(int)
    frac_j4 = (energy.loc[4] / energy.sum(axis=0) * 100)
    frac_j4.to_csv(paths["tables"] / "diurnal_energy_fraction_j4_baseB.csv", header=["pct_E_j4"])

    # correlations
    corr = base_b.corr()
    corr.to_csv(paths["tables"] / "station_pearson_corr.csv")

    root = paths["root"]
    meta = {
        "figure_1": str(f1.relative_to(root)),
        "figure_2_paper_file": str((paths["paper_figures"] / "figure_4.png").relative_to(root)),
        "figure_3_paper_file": str((paths["paper_figures"] / "figure_2.png").relative_to(root)),
        "diurnal": diurnal_stats,
        "frac_j4_pct": {st: float(frac_j4[st]) for st in stations},
        "n_hours": int(len(base_b)),
        "outliers": n_outliers,
        "nas": n_ausentes,
        "corr_min": float(corr.where(~np.eye(len(stations), dtype=bool)).min().min()),
        "corr_max": float(corr.where(~np.eye(len(stations), dtype=bool)).max().max()),
    }
    (paths["tables"] / "f6_paper_numbers.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # update NUMBER_REGISTRY
    reg_path = paths["root"] / "docs" / "NUMBER_REGISTRY.csv"
    if reg_path.is_file():
        rows = list(csv.DictReader(reg_path.open()))
        if not rows or "new_value" not in rows[0]:
            print("  registry uses claim-token schema; leaving it unchanged")
            rows = []
        updates = {
            "outliers_range": (
                f"{min(n_outliers.values())}-{max(n_outliers.values())} "
                f"({100*min(n_outliers.values())/len(base_b):.2f}-{100*max(n_outliers.values())/len(base_b):.2f}%)",
                "data/audit",
                "updated_F6",
            ),
            "n_hours": (str(len(base_b)), "data/processed", "updated_F6"),
            "diurnal_SJL_frac": (f"{frac_j4['SJL']:.1f}%", "tables/diurnal_energy_fraction_j4_baseB.csv", "updated_F6"),
            "diurnal_SBJ_frac": (f"{frac_j4['SBJ']:.1f}%", "tables/diurnal_energy_fraction_j4_baseB.csv", "updated_F6"),
            "peak_09h_city": (
                f"{diurnal_stats['city_peak_value']:.1f} at h={diurnal_stats['city_peak_hour']}",
                "f6_paper_numbers.json",
                "updated_F6",
            ),
            "trough_17h_city": (
                f"{diurnal_stats['city_trough_value']:.1f} at h={diurnal_stats['city_trough_hour']}",
                "f6_paper_numbers.json",
                "updated_F6",
            ),
            "seasonal_claim": (
                "no formal inference j>=10; j=9 n.s.; do not claim seasonal indistinguishability",
                "adaptive_results + Agamaz",
                "updated_F6",
            ),
        }
        if rows:
            for row in rows:
                if row["claim_id"] in updates:
                    row["new_value"], row["source_file"], row["status"] = updates[row["claim_id"]]
            with reg_path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)

    # narrative checklist
    chk = paths["root"] / "docs" / "FIGURE_NARRATIVE_CHECKLIST.md"
    chk.write_text(f"""# Checklist narrativa de figuras — Henry (REDIN)

Actualizado en F6 (figuras regeneradas desde Base B).

## Fig. 1 — Preprocessing (`figure_1.png`)
- Archivo: `paper/figures/figure_1.png`
- [x] Panel A: series conservadoras n={len(base_b):,}
- [x] Panel B: NA imputados vs outliers (conteos {n_outliers})
- [ ] Integrado en cuerpo LaTeX (F7)
- [ ] Caption actualizado en .tex (F7)
- **Estado:** figura lista; narrativa LaTeX pendiente F7

### Draft caption (EN)
Preprocessing of hourly PM2.5 from five Lima REMCA stations. (A) Complete aligned series after conservative cleaning. (B) Counts of linearly imputed missing values and conservatively replaced isolated instrumental-error candidates (medcouple-adjusted boxplot ∩ Hampel, duration ≤1 h, no cross-station corroboration). Outlier replacements are {min(n_outliers.values())}–{max(n_outliers.values())} per station (~0.7–1.1%), versus 8–13% under the previous STL+3×IQR rule.

## Fig. 2 — Diurnal + boxplots (`figure_4.png`)
- City peak: hour {diurnal_stats['city_peak_hour']} ≈ {diurnal_stats['city_peak_value']:.1f} µg/m³
- City trough: hour {diurnal_stats['city_trough_hour']} ≈ {diurnal_stats['city_trough_value']:.1f} µg/m³
- [x] Figura regenerada Base B
- [ ] Narrativa LaTeX (F7)
- **Estado:** figura lista

## Fig. 3 — Multiscale + inference (`figure_2.png`)
- [x] Regenerada en F4 (assumption-checked)
- j=1–7 Bonf. significant; j=8 no; j=9 no; j≥10 not tested
- Peak effect j=4 Kendall W ≈ 0.69
- [ ] Narrativa LaTeX (F7)
- **Estado:** figura lista

## Números clave F6
- Outliers B: {n_outliers}
- E_j4 fractions (%): { {st: round(float(frac_j4[st]),1) for st in stations} }
- Pearson corr range: {meta['corr_min']:.2f}–{meta['corr_max']:.2f}
""", encoding="utf-8")

    print("\nTable 1:")
    print(t1.round(2).to_string())
    print("\nE_j4 %:")
    print(frac_j4.round(2))
    print("\nF6 complete.")


if __name__ == "__main__":
    main()
