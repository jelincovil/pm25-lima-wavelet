#!/usr/bin/env python3
"""F3 — DWT Symmlet-7, pad, Parseval, central coeffs, multiscale energy. Local only."""
from __future__ import annotations

import importlib.util
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pywt

_setup = Path(__file__).resolve().parent / "00_setup_paths.py"
spec = importlib.util.spec_from_file_location("setup_paths", _setup)
setup_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_paths)
load_config = setup_paths.load_config
resolve_paths = setup_paths.resolve_paths
ensure_dirs = setup_paths.ensure_dirs


def mirror_pad(x, left, right):
    return np.pad(np.asarray(x, dtype=float), pad_width=(left, right), mode="reflect")


def load_base(path: Path, stations):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df[stations].astype(float)


def run_dwt(base: pd.DataFrame, stations, cfg_w):
    wavelet = cfg_w["family"]
    N = int(cfg_w["pad_to"])
    j_desc = int(cfg_w["j_descriptive"])
    min_blocks = int(cfg_w["min_blocks"])
    n_original = len(base)
    if n_original > N:
        raise ValueError(f"n={n_original} > pad_to={N}")
    diff = N - n_original
    pad_left = diff // 2
    pad_right = diff - pad_left

    wobj = pywt.Wavelet(wavelet)
    j_seguro = pywt.dwt_max_level(data_len=N, filter_len=wobj.dec_len)

    padded = {st: mirror_pad(base[st].to_numpy(), pad_left, pad_right) for st in stations}
    coeffs = {}
    details = {}
    for st in stations:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coeffs[st] = pywt.wavedec(padded[st], wavelet=wavelet, level=j_desc, mode="periodization")
        details[st] = {j: np.asarray(coeffs[st][-j]) for j in range(1, j_desc + 1)}

    # QC
    rows = []
    for st in stations:
        recon = pywt.waverec(coeffs[st], wavelet=wavelet, mode="periodization")[:N]
        emax = float(np.max(np.abs(recon - padded[st])))
        e_sig = float(np.sum(padded[st] ** 2))
        e_c = float(sum(np.sum(c ** 2) for c in coeffs[st]))
        rows.append({
            "station": st,
            "max_reconstruction_error": emax,
            "relative_parseval_error": abs(e_sig - e_c) / e_sig,
        })
    qc = pd.DataFrame(rows).set_index("station")

    energy = pd.DataFrame({
        st: {j: float(np.sum(details[st][j] ** 2)) for j in range(1, j_desc + 1)}
        for st in stations
    })
    energy.index.name = "scale_j"
    energy_frac = energy.div(energy.sum(axis=0), axis=1)

    # central masks
    inicio = pad_left
    fim = pad_left + n_original
    central_masks = {}
    scale_info = []
    for j in range(1, j_desc + 1):
        n_coeffs = len(details[stations[0]][j])
        passo = N / n_coeffs
        centros = (np.arange(n_coeffs) + 0.5) * passo
        mask = (centros >= inicio) & (centros < fim)
        central_masks[j] = mask
        n_c = int(mask.sum())
        scale_info.append({
            "scale_j": j,
            "period_low_h": 2 ** j,
            "period_high_h": 2 ** (j + 1),
            "n_coefficients_total": n_coeffs,
            "n_coefficients_central": n_c,
            "within_pywt_max_level": j <= j_seguro,
            "enough_central_coefficients": n_c >= min_blocks,
            "eligible_for_inference": (j <= j_seguro) and (n_c >= min_blocks),
        })
    scale_information = pd.DataFrame(scale_info)

    meta = {
        "n_original": n_original,
        "N": N,
        "pad_left": pad_left,
        "pad_right": pad_right,
        "wavelet": wavelet,
        "j_descriptive": j_desc,
        "j_seguro": int(j_seguro),
        "min_blocks": min_blocks,
    }
    return {
        "padded": padded,
        "coeffs": coeffs,
        "details": details,
        "qc": qc,
        "energy": energy,
        "energy_frac": energy_frac,
        "central_masks": central_masks,
        "scale_information": scale_information,
        "meta": meta,
        "stations": stations,
    }


def main():
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    stations = list(cfg["stations"])
    base_path = paths["processed"] / "datos_lima_limpieza_conservadora.csv"
    if not base_path.is_file():
        raise SystemExit(f"Missing Base B: {base_path}. Run 01 first.")
    base = load_base(base_path, stations)
    print("Base B:", base.shape, base_path)

    out = run_dwt(base, stations, cfg["wavelet"])
    print("\nDWT QC:")
    print(out["qc"])
    print("\nJ_seguro:", out["meta"]["j_seguro"])
    print("\nScale eligibility:")
    print(out["scale_information"].to_string(index=False))

    # save tables
    out["qc"].to_csv(paths["inference"] / "dwt_qc.csv")
    out["energy"].to_csv(paths["tables"] / "multiscale_energy.csv")
    out["energy_frac"].to_csv(paths["tables"] / "energy_fraction.csv")
    out["scale_information"].to_csv(paths["tables"] / "scale_eligibility.csv", index=False)
    (paths["inference"] / "wavelet_meta.json").write_text(json.dumps(out["meta"], indent=2), encoding="utf-8")

    # save arrays for F4
    npz = {}
    for st in stations:
        for j, arr in out["details"][st].items():
            npz[f"detail_{st}_j{j}"] = arr
        npz[f"padded_{st}"] = out["padded"][st]
    for j, mask in out["central_masks"].items():
        npz[f"central_mask_j{j}"] = mask.astype(np.uint8)
    np.savez_compressed(paths["inference"] / "wavelet_arrays.npz", **npz)
    print("Saved wavelet_arrays.npz")

    # energy plot
    fig, ax = plt.subplots(figsize=(10, 6))
    for st in stations:
        ax.plot(out["energy"].index, np.log10(out["energy"][st]), marker="o", label=st)
    j_seg = out["meta"]["j_seguro"]
    j_desc = out["meta"]["j_descriptive"]
    ax.axvspan(3.5, 4.5, alpha=0.15, color="gold", label="diurnal band")
    ax.axvspan(5.5, 8.5, alpha=0.10, color="lightgreen", label="synoptic band")
    if j_desc > j_seg:
        ax.axvspan(j_seg + 0.5, j_desc + 0.5, color="gray", alpha=0.18, label="above useful DWT")
    ax.set_xlabel("scale j")
    ax.set_ylabel(r"$\log_{10}(E_j)$")
    ax.set_title("Multiscale energy profiles (Base B conservative)")
    ax.set_xticks(range(1, j_desc + 1))
    ax.legend(ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(paths["figures"] / "multiscale_energy_profiles.png", dpi=200)
    plt.close(fig)

    # energy fraction bar
    fig, ax = plt.subplots(figsize=(10, 6))
    out["energy_frac"].plot(kind="bar", ax=ax)
    ax.set_xlabel("scale j")
    ax.set_ylabel("energy fraction")
    ax.set_title("Energy fraction by scale and station (Base B)")
    fig.tight_layout()
    fig.savefig(paths["figures"] / "energy_fraction_by_scale.png", dpi=200)
    plt.close(fig)

    print("F3 complete.")


if __name__ == "__main__":
    main()
