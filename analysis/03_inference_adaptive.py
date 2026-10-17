#!/usr/bin/env python3
"""F4 — Adaptive inference j=1..9 (RM-ANOVA / Friedman / block-permutation). Local only."""
from __future__ import annotations

import importlib.util
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import pywt
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests

try:
    import pingouin as pg
except ImportError:
    pg = None

_setup = Path(__file__).resolve().parent / "00_setup_paths.py"
spec = importlib.util.spec_from_file_location("setup_paths", _setup)
setup_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_paths)
load_config = setup_paths.load_config
resolve_paths = setup_paths.resolve_paths
ensure_dirs = setup_paths.ensure_dirs


def aggregate_nonoverlapping(x, block_size):
    x = np.asarray(x, dtype=float)
    n = x.shape[0]
    n_blocks = n // block_size
    if n_blocks < 1:
        raise ValueError("block too large")
    x_use = x[: n_blocks * block_size]
    return x_use.reshape(n_blocks, block_size, x.shape[1]).mean(axis=1)


def check_block_independence(wide_log, stations, alpha=0.05):
    n_blocks = len(wide_log)
    if n_blocks < 8:
        return {"independence_ok": False, "lag": np.nan, "minimum_adjusted_p": np.nan}
    lag = min(10, max(1, n_blocks // 5))
    raw = {}
    for st in stations:
        values = np.asarray(wide_log[st], dtype=float)
        if len(values) <= lag + 2 or np.std(values) == 0:
            raw[st] = np.nan
        else:
            res = acorr_ljungbox(values, lags=[lag], return_df=True)
            raw[st] = float(res["lb_pvalue"].iloc[0])
    p_array = np.array([raw[st] for st in stations], dtype=float)
    if not np.isfinite(p_array).all():
        return {"independence_ok": False, "lag": lag, "minimum_adjusted_p": np.nan}
    _, adjusted, _, _ = multipletests(p_array, alpha=alpha, method="holm")
    return {
        "independence_ok": bool(np.all(adjusted >= alpha)),
        "lag": lag,
        "minimum_adjusted_p": float(np.min(adjusted)),
    }


def select_temporal_block_size(squared_coefficients, stations, min_blocks=12, alpha=0.05):
    n_coeffs = squared_coefficients.shape[0]
    max_block_size = max(1, n_coeffs // min_blocks)
    powers = range(int(np.floor(np.log2(max_block_size))) + 1)
    candidates = [2 ** p for p in powers]
    attempts = []
    selected = None
    for block_size in candidates:
        aggregated = aggregate_nonoverlapping(squared_coefficients, block_size)
        wide_log = pd.DataFrame(np.log1p(aggregated), columns=stations)
        independence = check_block_independence(wide_log, stations, alpha=alpha)
        attempts.append({
            "block_size": block_size,
            "n_blocks": len(wide_log),
            "independence_ok": independence["independence_ok"],
            "ljung_box_lag": independence["lag"],
            "minimum_adjusted_ljung_p": independence["minimum_adjusted_p"],
        })
        if independence["independence_ok"]:
            selected = {
                "block_size": block_size,
                "aggregated": aggregated,
                "wide_log": wide_log,
                "independence": independence,
                "attempts": attempts,
            }
            break
    if selected is None:
        block_size = candidates[-1]
        aggregated = aggregate_nonoverlapping(squared_coefficients, block_size)
        wide_log = pd.DataFrame(np.log1p(aggregated), columns=stations)
        independence = check_block_independence(wide_log, stations, alpha=alpha)
        selected = {
            "block_size": block_size,
            "aggregated": aggregated,
            "wide_log": wide_log,
            "independence": independence,
            "attempts": attempts,
        }
    return selected


def repeated_measures_residuals(wide):
    x = np.asarray(wide, dtype=float)
    row_means = x.mean(axis=1, keepdims=True)
    column_means = x.mean(axis=0, keepdims=True)
    grand_mean = x.mean()
    return (x - row_means - column_means + grand_mean).ravel()


def check_normality(wide_log, stations, alpha=0.05, seed=2026):
    residuals = repeated_measures_residuals(wide_log[stations])
    residuals = residuals[np.isfinite(residuals)]
    rng = np.random.default_rng(seed)
    residuals_test = residuals if len(residuals) <= 5000 else rng.choice(residuals, size=5000, replace=False)
    shapiro_stat, shapiro_p = stats.shapiro(residuals_test)
    skewness = stats.skew(residuals, bias=False)
    excess_kurtosis = stats.kurtosis(residuals, fisher=True, bias=False)
    normality_ok = (shapiro_p >= alpha) and (abs(skewness) < 1) and (abs(excess_kurtosis) < 2)
    return {
        "normality_ok": bool(normality_ok),
        "shapiro_W": float(shapiro_stat),
        "shapiro_p": float(shapiro_p),
        "residual_skewness": float(skewness),
        "residual_excess_kurtosis": float(excess_kurtosis),
        "residuals": residuals,
    }


def _col(row, names, default=np.nan):
    for n in names:
        if n in row.index and pd.notna(row[n]):
            return row[n]
    return default


def run_rm_anova(wide_log, stations, alpha=0.05):
    if pg is None:
        raise RuntimeError("pingouin not installed")
    wide = wide_log[stations].copy()
    wide["block"] = np.arange(len(wide), dtype=int)
    long = wide.melt(id_vars="block", value_vars=stations, var_name="station", value_name="log_energy")
    anova = pg.rm_anova(
        data=long, dv="log_energy", within="station", subject="block",
        detailed=True, correction=True, effsize="ng2",
    )
    if "Source" in anova.columns:
        sn = anova["Source"].astype(str).str.strip().str.lower()
        rows = anova.loc[sn == "station"]
        linha = rows.iloc[0] if not rows.empty else anova.iloc[0]
    else:
        linha = anova.iloc[0]
    f_stat = float(_col(linha, ["F"]))
    p_unc = float(_col(linha, ["p_unc", "p-unc"]))
    p_gg = _col(linha, ["p_GG_corr", "p-GG-corr"])
    p_gg = float(p_gg) if pd.notna(p_gg) else np.nan
    p_mauchly = _col(linha, ["p_spher", "p-spher"])
    p_mauchly = float(p_mauchly) if pd.notna(p_mauchly) else np.nan
    eta = _col(linha, ["ng2"])
    eta = float(eta) if pd.notna(eta) else np.nan
    sphericity_ok = bool(p_mauchly >= alpha) if np.isfinite(p_mauchly) else np.nan
    if sphericity_ok is False and np.isfinite(p_gg):
        method, p_sel = "ANOVA-RM-GG", p_gg
    else:
        method, p_sel = "ANOVA-RM", p_unc
    return {
        "method": method,
        "statistic": f_stat,
        "raw_p": float(p_sel),
        "uncorrected_p": p_unc,
        "greenhouse_geisser_p": p_gg,
        "sphericity_ok": sphericity_ok,
        "mauchly_p": p_mauchly,
        "effect_name": "generalized_eta_squared",
        "effect_size": eta,
    }


def friedman_stat_from_ranks(rank_sums, n_blocks, n_stations, tie_correction):
    q = 12 / (n_blocks * n_stations * (n_stations + 1)) * np.sum(rank_sums ** 2) - 3 * n_blocks * (n_stations + 1)
    if tie_correction > 0:
        q = q / tie_correction
    return float(q)


def block_permutation_friedman(wide, n_permutations=9999, seed=2026):
    x = np.asarray(wide, dtype=float)
    n_blocks, n_stations = x.shape
    rank_matrix = np.vstack([stats.rankdata(row, method="average") for row in x])
    tie_sum = 0
    for row in x:
        _, counts = np.unique(row, return_counts=True)
        tie_sum += np.sum(counts ** 3 - counts)
    denom = n_blocks * n_stations * (n_stations ** 2 - 1)
    tie_correction = 1 - tie_sum / denom if denom > 0 else 1
    observed_q = friedman_stat_from_ranks(rank_matrix.sum(axis=0), n_blocks, n_stations, tie_correction)
    perm_len = int(np.ceil(n_blocks ** (1 / 3)))
    perm_len = max(2, min(16, perm_len, n_blocks))
    rng = np.random.default_rng(seed)
    greater = 0
    for _ in range(n_permutations):
        perm_sums = np.zeros(n_stations)
        for start in range(0, n_blocks, perm_len):
            end = min(start + perm_len, n_blocks)
            perm = rng.permutation(n_stations)
            perm_sums += rank_matrix[start:end, :][:, perm].sum(axis=0)
        if friedman_stat_from_ranks(perm_sums, n_blocks, n_stations, tie_correction) >= observed_q:
            greater += 1
    p_value = (greater + 1) / (n_permutations + 1)
    kendall_w = observed_q / (n_blocks * (n_stations - 1))
    return {
        "method": "Permutacao-blocos",
        "statistic": observed_q,
        "raw_p": float(p_value),
        "effect_name": "Kendall_W",
        "effect_size": float(kendall_w),
        "permutation_block_length": perm_len,
    }


def run_friedman(wide_log, stations, n_blocks):
    q, p = stats.friedmanchisquare(*[wide_log[st].to_numpy() for st in stations])
    return {
        "method": "Friedman",
        "statistic": float(q),
        "raw_p": float(p),
        "effect_name": "Kendall_W",
        "effect_size": float(q / (n_blocks * (len(stations) - 1))),
        "permutation_block_length": np.nan,
    }


def load_arrays(paths, stations, j_desc):
    npz = np.load(paths["inference"] / "wavelet_arrays.npz")
    details = {st: {} for st in stations}
    for st in stations:
        for j in range(1, j_desc + 1):
            details[st][j] = npz[f"detail_{st}_j{j}"]
    central_masks = {j: npz[f"central_mask_j{j}"].astype(bool) for j in range(1, j_desc + 1)}
    return details, central_masks


def main():
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    stations = list(cfg["stations"])
    j_desc = int(cfg["wavelet"]["j_descriptive"])
    min_blocks = int(cfg["wavelet"]["min_blocks"])
    alpha = float(cfg["inference"]["alpha"])
    n_perm = int(cfg["inference"]["n_permutations"])
    seed = int(cfg["inference"]["seed"])

    scale_info = pd.read_csv(paths["tables"] / "scale_eligibility.csv")
    energy = pd.read_csv(paths["tables"] / "multiscale_energy.csv", index_col=0)
    energy.index = energy.index.astype(int)
    meta = json.loads((paths["inference"] / "wavelet_meta.json").read_text())
    j_seguro = int(meta["j_seguro"])

    details, central_masks = load_arrays(paths, stations, j_desc)
    formal_scales = (
        scale_info.loc[scale_info["eligible_for_inference"], "scale_j"].astype(int).tolist()
    )
    print("Formal scales:", formal_scales)
    print(f"N_PERM={n_perm}, seed={seed}")

    result_records = []
    block_attempt_records = []
    residuals_by_j = {}

    for j in formal_scales:
        print(f"\n=== scale j={j} ===")
        mask = central_masks[j]
        squared = np.column_stack([details[st][j][mask] ** 2 for st in stations])
        selected = select_temporal_block_size(squared, stations, min_blocks=min_blocks, alpha=alpha)
        block_size = selected["block_size"]
        wide_log = selected["wide_log"]
        independence = selected["independence"]
        for att in selected["attempts"]:
            block_attempt_records.append({"scale_j": j, **att})
        n_blocks = len(wide_log)
        normality = check_normality(wide_log, stations, alpha=alpha, seed=seed + j)
        residuals_by_j[j] = normality["residuals"]

        sphericity_ok = np.nan
        mauchly_p = np.nan
        uncorrected_p = np.nan
        greenhouse_geisser_p = np.nan
        perm_block_len = np.nan

        if independence["independence_ok"]:
            if normality["normality_ok"]:
                try:
                    test_result = run_rm_anova(wide_log, stations, alpha=alpha)
                    sphericity_ok = test_result["sphericity_ok"]
                    mauchly_p = test_result["mauchly_p"]
                    uncorrected_p = test_result["uncorrected_p"]
                    greenhouse_geisser_p = test_result["greenhouse_geisser_p"]
                except Exception as err:
                    print("RM-ANOVA failed, fallback Friedman:", err)
                    test_result = run_friedman(wide_log, stations, n_blocks)
            else:
                test_result = run_friedman(wide_log, stations, n_blocks)
        else:
            print(f"  block permutation ({n_perm})...")
            test_result = block_permutation_friedman(
                wide_log[stations], n_permutations=n_perm, seed=seed + j
            )
            perm_block_len = test_result.get("permutation_block_length", np.nan)

        print(f"  method={test_result['method']} p={test_result['raw_p']:.6g} effect={test_result['effect_size']:.4f}")

        result_records.append({
            "scale_j": j,
            "period_low_h": 2 ** j,
            "period_high_h": 2 ** (j + 1),
            "n_central_coefficients": squared.shape[0],
            "coefficient_block_size": block_size,
            "approximate_block_duration_h": block_size * (2 ** j),
            "n_temporal_blocks": n_blocks,
            "ljung_box_lag": independence["lag"],
            "minimum_adjusted_ljung_p": independence["minimum_adjusted_p"],
            "independence_ok": independence["independence_ok"],
            "shapiro_W": normality["shapiro_W"],
            "shapiro_p": normality["shapiro_p"],
            "residual_skewness": normality["residual_skewness"],
            "residual_excess_kurtosis": normality["residual_excess_kurtosis"],
            "normality_ok": normality["normality_ok"],
            "sphericity_ok": sphericity_ok,
            "mauchly_p": mauchly_p,
            "uncorrected_anova_p": uncorrected_p,
            "greenhouse_geisser_p": greenhouse_geisser_p,
            "permutation_block_length": perm_block_len,
            "selected_method": test_result["method"],
            "statistic": test_result["statistic"],
            "raw_p": test_result["raw_p"],
            "effect_name": test_result["effect_name"],
            "effect_size": test_result["effect_size"],
        })

    results = pd.DataFrame(result_records)
    m = results["scale_j"].nunique()
    results["p_bonferroni"] = (results["raw_p"] * m).clip(upper=1.0)
    results["sig_bonferroni"] = results["raw_p"] < (alpha / m)
    # Holm
    order = np.argsort(results["raw_p"].to_numpy())
    holm = np.empty(len(results))
    raw = results["raw_p"].to_numpy()
    for rank, idx in enumerate(order):
        holm[idx] = min(1.0, raw[idx] * (m - rank))
    # enforce monotone
    for i in range(1, len(order)):
        holm[order[i]] = max(holm[order[i]], holm[order[i - 1]])
    results["p_holm"] = holm
    results["sig_holm"] = results["p_holm"] < alpha

    results.to_csv(paths["inference"] / "adaptive_results.csv", index=False)
    pd.DataFrame(block_attempt_records).to_csv(paths["inference"] / "block_attempts.csv", index=False)
    print("\n=== RESULTS ===")
    print(results[["scale_j", "selected_method", "raw_p", "p_bonferroni", "effect_size", "independence_ok", "normality_ok"]].to_string(index=False))
    print(f"\nBonferroni threshold: {alpha/m:.6f} (M={m})")

    # Figure 3
    colors_station = {"SBJ": "#1f77b4", "STA": "#d62728", "VMT": "#2ca02c", "SJL": "#9467bd", "SMP": "#ff7f0e"}
    colors_method = {
        "ANOVA-RM": "#4c72b0", "ANOVA-RM-GG": "#55a868",
        "Friedman": "#c44e52", "Permutacao-blocos": "#8172b2",
    }
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    for st in stations:
        ax1.plot(energy.index, np.log10(energy[st]), marker="o", lw=2, ms=5, color=colors_station[st], label=st)
    ax1.axvspan(3.5, 4.5, alpha=0.15, color="gold", label="diurnal")
    ax1.axvspan(5.5, 8.5, alpha=0.10, color="lightgreen", label="synoptic")
    if j_desc > j_seguro:
        ax1.axvspan(j_seguro + 0.5, j_desc + 0.5, color="gray", alpha=0.18, label="above useful DWT")
    ax1.set_title("A. Multiscale energy profiles", fontweight="bold")
    ax1.set_xlabel("Wavelet detail scale j")
    ax1.set_ylabel(r"$\log_{10}(E_j)$")
    ax1.set_xticks(range(1, j_desc + 1))
    ax1.grid(axis="y", alpha=0.3)
    ax1.legend(ncol=3, fontsize=8, loc="upper left")

    x = results["scale_j"].to_numpy()
    minus_log_p = -np.log10(np.clip(results["raw_p"].to_numpy(), 1e-300, 1))
    bar_colors = [colors_method.get(mth, "gray") for mth in results["selected_method"]]
    ax2.bar(x, minus_log_p, color=bar_colors, edgecolor="black", linewidth=0.5)
    ax2.axhline(-np.log10(alpha), ls="--", color="black", lw=1.2, label=r"$\alpha=0.05$")
    ax2.axhline(-np.log10(alpha / m), ls=":", color="dimgray", lw=1.5, label=f"Bonferroni 0.05/{m}")
    not_tested = [j for j in range(1, j_desc + 1) if j not in formal_scales]
    if not_tested:
        ax2.scatter(not_tested, np.zeros(len(not_tested)), marker="x", color="black", s=40, label="not tested")
    if j_desc > j_seguro:
        ax2.axvspan(j_seguro + 0.5, j_desc + 0.5, color="gray", alpha=0.18)
    ax2.axvspan(3.5, 4.5, alpha=0.15, color="gold")
    ax2.axvspan(5.5, 8.5, alpha=0.10, color="lightgreen")
    ax2.set_title("B. Inter-station differences after assumption checking", fontweight="bold")
    ax2.set_xlabel("Wavelet detail scale j")
    ax2.set_ylabel(r"$-\log_{10}(p)$")
    ax2.set_xticks(range(1, j_desc + 1))
    ax2.grid(axis="y", alpha=0.3)
    used = list(results["selected_method"].unique())
    handles = [
        Patch(facecolor=colors_method[mth], edgecolor="black", label=mth)
        for mth in used if mth in colors_method
    ]
    # threshold lines already labeled via axhline label=
    line_handles, line_labels = ax2.get_legend_handles_labels()
    ax2.legend(handles=handles + line_handles, labels=[h.get_label() for h in handles] + line_labels, fontsize=8, loc="upper right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(paths["figures"] / f"figure3_assumption_checked.{ext}", dpi=300, bbox_inches="tight")
    # paper-ready copy
    fig.savefig(paths["paper_figures"] / "figure_2.png", dpi=300, bbox_inches="tight")  # paper Fig.3 uses figure_2.png
    plt.close(fig)

    # QQ plots
    n_sc = len(formal_scales)
    ncols = 3
    nrows = int(np.ceil(n_sc / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 3.2 * nrows))
    axes = np.atleast_2d(axes)
    for i, j in enumerate(formal_scales):
        ax = axes[i // ncols, i % ncols]
        res = residuals_by_j[j]
        stats.probplot(res, dist="norm", plot=ax)
        ax.set_title(f"j={j}")
    for k in range(n_sc, nrows * ncols):
        axes[k // ncols, k % ncols].axis("off")
    fig.suptitle("RM residual Q–Q plots by scale", y=1.01)
    fig.tight_layout()
    fig.savefig(paths["figures"] / "wavelet_residual_qqplots.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "M_tests": int(m),
        "bonferroni_alpha": alpha / m,
        "n_permutations": n_perm,
        "seed": seed,
        "formal_scales": formal_scales,
        "methods_used": results["selected_method"].value_counts().to_dict(),
    }
    (paths["inference"] / "inference_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nF4 complete. Outputs in results/inference and results/figures.")


if __name__ == "__main__":
    main()
