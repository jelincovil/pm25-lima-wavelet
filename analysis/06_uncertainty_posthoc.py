#!/usr/bin/env python3
"""
F7 — Secondary uncertainty and post-hoc analyses (no changes to primary tests).

Outputs:
  results/inference/posthoc_pairwise.csv
  results/inference/effect_ci.csv
  results/tables/diurnal_energy_fraction_ci.csv
  results/inference/uncertainty_summary.json

The primary inference is unchanged. Pairwise Wilcoxon tests are secondary and
Holm-adjusted within each scale; bootstrap CIs use a fixed seed and are
reported as descriptive uncertainty.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pywt
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
STATIONS = ["SBJ", "STA", "VMT", "SJL", "SMP"]
J_FORMAL = list(range(1, 10))
N_BOOT_EFFECT = 2000
N_BOOT_DIURNAL = 1000
SEED = 2026
DIURNAL_BLOCK_H = 168  # 7-day blocks for the energy-fraction bootstrap
PAD = 3104
N_PAD = 16384
WAVELET = "sym7"
J_DESC = 13


def aggregate_blocks(x: np.ndarray, block_size: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n_blocks = len(x) // block_size
    if n_blocks < 1:
        raise ValueError("block too large")
    return x[: n_blocks * block_size].reshape(n_blocks, block_size).mean(axis=1)


def friedman_w(x: np.ndarray) -> float:
    """Kendall W from a block x station matrix, with tie correction."""
    x = np.asarray(x, dtype=float)
    n, k = x.shape
    ranks = np.vstack([stats.rankdata(row, method="average") for row in x])
    tie_sum = 0
    for row in x:
        _, counts = np.unique(row, return_counts=True)
        tie_sum += np.sum(counts**3 - counts)
    denom = n * k * (k**2 - 1)
    tie_correction = 1 - tie_sum / denom if denom > 0 else 1.0
    q = 12 / (n * k * (k + 1)) * np.sum(ranks.sum(axis=0) ** 2) - 3 * n * (k + 1)
    if tie_correction > 0:
        q /= tie_correction
    return float(q / (n * (k - 1)))


def load_block_matrices() -> dict[int, pd.DataFrame]:
    npz = np.load(ROOT / "results/inference/wavelet_arrays.npz")
    adaptive = pd.read_csv(ROOT / "results/inference/adaptive_results.csv").set_index("scale_j")
    matrices: dict[int, pd.DataFrame] = {}
    for j in J_FORMAL:
        mask = npz[f"central_mask_j{j}"].astype(bool)
        block_size = int(adaptive.loc[j, "coefficient_block_size"])
        columns = {}
        for station in STATIONS:
            detail = npz[f"detail_{station}_j{j}"][mask]
            columns[station] = aggregate_blocks(detail**2, block_size)
        lengths = {len(v) for v in columns.values()}
        if len(lengths) != 1:
            raise ValueError(f"inconsistent block lengths at j={j}: {lengths}")
        matrices[j] = pd.DataFrame(columns).apply(np.log1p)
    return matrices


def pairwise_posthoc(matrices: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for j, wide in matrices.items():
        pairs = list(combinations(STATIONS, 2))
        pvals = []
        local = []
        for a, b in pairs:
            diff = wide[a].to_numpy() - wide[b].to_numpy()
            try:
                stat, p = stats.wilcoxon(diff, alternative="two-sided", method="auto")
            except ValueError:
                stat, p = stats.wilcoxon(diff, alternative="two-sided", method="approx")
            pvals.append(float(p))
            local.append((a, b, float(np.median(diff)), float(stat), float(p)))
        _, p_holm, _, _ = multipletests(pvals, method="holm")
        for (a, b, median_diff, stat, p), ph in zip(local, p_holm):
            rows.append(
                {
                    "scale_j": j,
                    "pair": f"{a}-{b}",
                    "median_diff_log_energy": median_diff,
                    "wilcoxon_stat": stat,
                    "p_raw": p,
                    "p_holm": float(ph),
                    "sig_holm": bool(ph < 0.05),
                    "n_blocks": len(wide),
                }
            )
    return pd.DataFrame(rows)


def effect_ci(matrices: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    for j, wide in matrices.items():
        x = wide[STATIONS].to_numpy()
        observed = friedman_w(x)
        boots = []
        for _ in range(N_BOOT_EFFECT):
            idx = rng.integers(0, len(x), len(x))
            boots.append(friedman_w(x[idx]))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rows.append(
            {
                "scale_j": j,
                "kendall_w": observed,
                "ci_low": float(lo),
                "ci_high": float(hi),
                "n_boot": N_BOOT_EFFECT,
                "n_blocks": len(x),
            }
        )
    return pd.DataFrame(rows)


def diurnal_fraction_ci() -> pd.DataFrame:
    base = pd.read_csv(
        ROOT / "data/processed/datos_lima_limpieza_conservadora.csv",
        index_col=0,
        parse_dates=True,
    )
    values = base[STATIONS].to_numpy(dtype=float)
    n = len(values)
    rng = np.random.default_rng(SEED)
    draws = {station: [] for station in STATIONS}
    n_starts = int(np.ceil(n / DIURNAL_BLOCK_H))
    for _ in range(N_BOOT_DIURNAL):
        starts = rng.integers(0, n - DIURNAL_BLOCK_H, size=n_starts)
        idx = np.concatenate([np.arange(s, s + DIURNAL_BLOCK_H) for s in starts])[:n]
        for col, station in enumerate(STATIONS):
            x = values[idx, col]
            padded = np.pad(x, (PAD, PAD), mode="reflect")
            coeffs = pywt.wavedec(padded, wavelet=WAVELET, level=J_DESC, mode="periodization")
            energies = np.array([np.sum(coeffs[-j] ** 2) for j in range(1, J_DESC + 1)])
            draws[station].append(100.0 * energies[3] / energies.sum())

    observed = {}
    for col, station in enumerate(STATIONS):
        padded = np.pad(values[:, col], (PAD, PAD), mode="reflect")
        coeffs = pywt.wavedec(padded, wavelet=WAVELET, level=J_DESC, mode="periodization")
        energies = np.array([np.sum(coeffs[-j] ** 2) for j in range(1, J_DESC + 1)])
        observed[station] = 100.0 * energies[3] / energies.sum()

    rows = []
    for station in STATIONS:
        lo, hi = np.percentile(draws[station], [2.5, 97.5])
        rows.append(
            {
                "station": station,
                "pct_E_j4": observed[station],
                "ci_low": float(lo),
                "ci_high": float(hi),
                "n_boot": N_BOOT_DIURNAL,
                "block_h": DIURNAL_BLOCK_H,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    out_inf = ROOT / "results/inference"
    out_tab = ROOT / "results/tables"
    out_inf.mkdir(parents=True, exist_ok=True)
    out_tab.mkdir(parents=True, exist_ok=True)

    matrices = load_block_matrices()
    posthoc = pairwise_posthoc(matrices)
    posthoc.to_csv(out_inf / "posthoc_pairwise.csv", index=False)

    effects = effect_ci(matrices)
    effects.to_csv(out_inf / "effect_ci.csv", index=False)

    diurnal = diurnal_fraction_ci()
    diurnal.to_csv(out_tab / "diurnal_energy_fraction_ci.csv", index=False)

    summary = {
        "seed": SEED,
        "n_boot_effect": N_BOOT_EFFECT,
        "n_boot_diurnal": N_BOOT_DIURNAL,
        "diurnal_block_h": DIURNAL_BLOCK_H,
        "j4_w": float(effects.loc[effects.scale_j == 4, "kendall_w"].iloc[0]),
        "j4_ci": [
            float(effects.loc[effects.scale_j == 4, "ci_low"].iloc[0]),
            float(effects.loc[effects.scale_j == 4, "ci_high"].iloc[0]),
        ],
        "diurnal_ci": {
            row.station: [row.ci_low, row.ci_high] for row in diurnal.itertuples()
        },
        "posthoc_pairs": int(len(posthoc)),
        "posthoc_significant_pairs": int(posthoc["sig_holm"].sum()),
    }
    (out_inf / "uncertainty_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("Post-hoc pairs:", len(posthoc), "significant:", int(posthoc["sig_holm"].sum()))
    print("Effect CIs:")
    print(effects.to_string(index=False))
    print("Diurnal fraction CIs:")
    print(diurnal.to_string(index=False))


if __name__ == "__main__":
    main()
