#!/usr/bin/env python3
"""
F5 — Sensitivity: Base A (imputed only) vs B (conservative) vs C (STL+3×IQR).

Compares multiscale energy profiles and adaptive inference patterns.
- Arm B reuses F3/F4 artifacts when present.
- Arms A/C recompute DWT + inference.

Local only. Permutation count for A/C defaults to config inference.n_permutations
but can be overridden with env SENS_N_PERM (e.g. 1999 for faster draft).
"""
from __future__ import annotations

import importlib.util
import json
import os
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_root_analysis = Path(__file__).resolve().parent


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # ensure __file__ for nested imports
    mod.__file__ = str(path)
    spec.loader.exec_module(mod)
    return mod


setup_paths = _load_mod("setup_paths", _root_analysis / "00_setup_paths.py")
mod02 = _load_mod("wavelet02", _root_analysis / "02_wavelet_diagnostics.py")
# load 03 without running main
src03 = (_root_analysis / "03_inference_adaptive.py").read_text()
src03 = src03.replace('if __name__ == "__main__":\n    main()\n', "")
ns03 = {"__file__": str(_root_analysis / "03_inference_adaptive.py"), "__name__": "inf03"}
exec(compile(src03, "03_inference_adaptive.py", "exec"), ns03)

load_config = setup_paths.load_config
resolve_paths = setup_paths.resolve_paths
ensure_dirs = setup_paths.ensure_dirs
run_dwt = mod02.run_dwt
load_base = mod02.load_base


def run_inference_for_arm(dwt_out, stations, cfg, n_perm, seed, alpha, min_blocks):
    details = dwt_out["details"]
    central_masks = dwt_out["central_masks"]
    scale_info = dwt_out["scale_information"]
    formal = scale_info.loc[scale_info["eligible_for_inference"], "scale_j"].astype(int).tolist()

    records = []
    for j in formal:
        mask = central_masks[j]
        squared = np.column_stack([details[st][j][mask] ** 2 for st in stations])
        selected = ns03["select_temporal_block_size"](
            squared, stations, min_blocks=min_blocks, alpha=alpha
        )
        wide_log = selected["wide_log"]
        independence = selected["independence"]
        n_blocks = len(wide_log)
        normality = ns03["check_normality"](wide_log, stations, alpha=alpha, seed=seed + j)

        if independence["independence_ok"]:
            if normality["normality_ok"]:
                try:
                    test_result = ns03["run_rm_anova"](wide_log, stations, alpha=alpha)
                except Exception:
                    test_result = ns03["run_friedman"](wide_log, stations, n_blocks)
            else:
                test_result = ns03["run_friedman"](wide_log, stations, n_blocks)
        else:
            print(f"    j={j}: block perm n={n_perm}...")
            test_result = ns03["block_permutation_friedman"](
                wide_log[stations], n_permutations=n_perm, seed=seed + j
            )

        records.append({
            "scale_j": j,
            "period_low_h": 2 ** j,
            "period_high_h": 2 ** (j + 1),
            "independence_ok": independence["independence_ok"],
            "normality_ok": normality["normality_ok"],
            "selected_method": test_result["method"],
            "statistic": test_result["statistic"],
            "raw_p": test_result["raw_p"],
            "effect_name": test_result["effect_name"],
            "effect_size": test_result["effect_size"],
            "n_temporal_blocks": n_blocks,
            "coefficient_block_size": selected["block_size"],
        })

    results = pd.DataFrame(records)
    m = results["scale_j"].nunique()
    results["p_bonferroni"] = (results["raw_p"] * m).clip(upper=1.0)
    results["sig_bonferroni"] = results["raw_p"] < (alpha / m)
    return results, formal, m


def diurnal_energy_fraction(energy: pd.DataFrame, j=4) -> pd.Series:
    """Share of detail energy at scale j (default diurnal 16-32h)."""
    if j not in energy.index:
        energy = energy.copy()
        energy.index = energy.index.astype(int)
    total = energy.sum(axis=0)
    return (energy.loc[j] / total * 100)


def main():
    cfg = load_config()
    paths = resolve_paths(cfg)
    ensure_dirs(paths)
    sens_dir = paths["sensitivity"]
    sens_dir.mkdir(parents=True, exist_ok=True)

    stations = list(cfg["stations"])
    alpha = float(cfg["inference"]["alpha"])
    seed = int(cfg["inference"]["seed"])
    min_blocks = int(cfg["wavelet"]["min_blocks"])
    n_perm_full = int(cfg["inference"]["n_permutations"])
    n_perm = int(os.environ.get("SENS_N_PERM", str(n_perm_full)))

    arms = {
        "A_imputed_only": paths["processed"] / "datos_lima_solo_imputados.csv",
        "B_conservative": paths["processed"] / "datos_lima_limpieza_conservadora.csv",
        "C_aggressive_stl3iqr": paths["processed"] / "datos_lima_limpieza_agresiva_stl3iqr.csv",
    }

    all_inf = []
    all_energy = []
    all_diurnal = []
    methods_summary = {}

    for arm_name, csv_path in arms.items():
        print(f"\n######## ARM {arm_name} ########")
        if not csv_path.is_file():
            raise SystemExit(f"Missing {csv_path}")

        # Reuse B from F4 if available and matching
        if arm_name == "B_conservative":
            res_path = paths["inference"] / "adaptive_results.csv"
            en_path = paths["tables"] / "multiscale_energy.csv"
            if res_path.is_file() and en_path.is_file():
                print("  reusing F3/F4 artifacts for Base B")
                results = pd.read_csv(res_path)
                energy = pd.read_csv(en_path, index_col=0)
                energy.index = energy.index.astype(int)
                m = results["scale_j"].nunique()
                # ensure columns
                if "sig_bonferroni" not in results.columns:
                    results["sig_bonferroni"] = results["raw_p"] < (alpha / m)
                results["arm"] = arm_name
                energy_out = energy.copy()
                energy_out.insert(0, "arm", arm_name)
                frac = diurnal_energy_fraction(energy, j=4)
                all_inf.append(results)
                all_energy.append(energy.assign(arm=arm_name).reset_index().melt(
                    id_vars=["arm", "scale_j"] if "scale_j" in energy.reset_index().columns else ["arm"],
                    var_name="station", value_name="energy"
                ) if False else None)
                # simpler energy long form later
                energy_long = energy.reset_index().melt(id_vars=energy.index.name or "scale_j", var_name="station", value_name="E_j")
                if energy_long.columns[0] != "scale_j":
                    energy_long = energy_long.rename(columns={energy_long.columns[0]: "scale_j"})
                energy_long["arm"] = arm_name
                all_energy.append(energy_long)
                all_diurnal.append(pd.DataFrame({"arm": arm_name, "station": frac.index, "pct_energy_j4": frac.values}))
                methods_summary[arm_name] = results["selected_method"].value_counts().to_dict()
                results.to_csv(sens_dir / f"inference_{arm_name}.csv", index=False)
                energy.to_csv(sens_dir / f"energy_{arm_name}.csv")
                continue

        base = load_base(csv_path, stations)
        print("  shape", base.shape, "running DWT...")
        dwt_out = run_dwt(base, stations, cfg["wavelet"])
        energy = dwt_out["energy"]
        energy.index = energy.index.astype(int)
        print("  inference (N_PERM=%d)..." % n_perm)
        results, formal, m = run_inference_for_arm(
            dwt_out, stations, cfg, n_perm=n_perm, seed=seed, alpha=alpha, min_blocks=min_blocks
        )
        results["arm"] = arm_name
        results.to_csv(sens_dir / f"inference_{arm_name}.csv", index=False)
        energy.to_csv(sens_dir / f"energy_{arm_name}.csv")
        print(results[["scale_j", "selected_method", "raw_p", "sig_bonferroni", "effect_size"]].to_string(index=False))

        energy_long = energy.reset_index().melt(id_vars="scale_j", var_name="station", value_name="E_j")
        energy_long["arm"] = arm_name
        all_energy.append(energy_long)
        all_inf.append(results)
        frac = diurnal_energy_fraction(energy, j=4)
        all_diurnal.append(pd.DataFrame({"arm": arm_name, "station": frac.index, "pct_energy_j4": frac.values}))
        methods_summary[arm_name] = results["selected_method"].value_counts().to_dict()

    inf_all = pd.concat(all_inf, ignore_index=True)
    energy_all = pd.concat(all_energy, ignore_index=True)
    diurnal = pd.concat(all_diurnal, ignore_index=True)

    inf_all.to_csv(sens_dir / "inference_all_arms.csv", index=False)
    energy_all.to_csv(sens_dir / "energy_all_arms_long.csv", index=False)
    diurnal.to_csv(sens_dir / "diurnal_energy_fraction_j4.csv", index=False)

    # significance pattern matrix
    sig_mat = inf_all.pivot_table(index="scale_j", columns="arm", values="sig_bonferroni", aggfunc="first")
    p_mat = inf_all.pivot_table(index="scale_j", columns="arm", values="raw_p", aggfunc="first")
    method_mat = inf_all.pivot_table(index="scale_j", columns="arm", values="selected_method", aggfunc="first")
    effect_mat = inf_all.pivot_table(index="scale_j", columns="arm", values="effect_size", aggfunc="first")
    sig_mat.to_csv(sens_dir / "significance_matrix_bonferroni.csv")
    p_mat.to_csv(sens_dir / "pvalue_matrix.csv")
    method_mat.to_csv(sens_dir / "method_matrix.csv")
    effect_mat.to_csv(sens_dir / "effect_matrix.csv")

    # agreement A vs B vs C on Bonferroni calls
    arms_list = list(sig_mat.columns)
    agreement = {}
    if len(arms_list) >= 2:
        for i, a in enumerate(arms_list):
            for b in arms_list[i + 1 :]:
                same = (sig_mat[a].astype(bool) == sig_mat[b].astype(bool)).mean()
                agreement[f"{a}_vs_{b}"] = float(same)

    # diurnal ranking stability
    diurnal_wide = diurnal.pivot(index="station", columns="arm", values="pct_energy_j4")
    diurnal_wide.to_csv(sens_dir / "diurnal_j4_pct_by_arm.csv")

    # Figure: -log10 p by arm
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    for ax, arm in zip(axes, arms.keys()):
        sub = inf_all[inf_all["arm"] == arm].sort_values("scale_j")
        if sub.empty:
            ax.set_title(arm)
            continue
        y = -np.log10(np.clip(sub["raw_p"].to_numpy(), 1e-300, 1))
        ax.bar(sub["scale_j"], y, color="#4c72b0", edgecolor="black", lw=0.4)
        m_arm = sub["scale_j"].nunique()
        ax.axhline(-np.log10(alpha / m_arm), ls=":", color="dimgray", label="Bonferroni")
        ax.axhline(-np.log10(alpha), ls="--", color="black", label="α=0.05")
        ax.set_title(arm.replace("_", " "), fontsize=10)
        ax.set_xlabel("j")
        ax.set_xticks(range(1, 10))
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel(r"$-\log_{10}(p)$")
    axes[0].legend(fontsize=7)
    fig.suptitle("Sensitivity: scale-wise significance by preprocessing arm", y=1.02)
    fig.tight_layout()
    fig.savefig(paths["figures"] / "sensitivity_minus_log_p_by_arm.png", dpi=200, bbox_inches="tight")
    fig.savefig(sens_dir / "sensitivity_minus_log_p_by_arm.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # energy profile overlay j=1..13 mean log10 across stations
    fig, ax = plt.subplots(figsize=(9, 5))
    for arm in arms.keys():
        sub = energy_all[energy_all["arm"] == arm]
        if sub.empty:
            continue
        mean_e = sub.groupby("scale_j")["E_j"].mean()
        ax.plot(mean_e.index, np.log10(mean_e), marker="o", label=arm)
    ax.set_xlabel("scale j")
    ax.set_ylabel(r"mean $\log_{10}(E_j)$ across stations")
    ax.set_title("Sensitivity: multiscale energy (mean over stations)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(paths["figures"] / "sensitivity_energy_profiles.png", dpi=200)
    fig.savefig(sens_dir / "sensitivity_energy_profiles.png", dpi=200)
    plt.close(fig)

    # Verdict logic
    # Core pattern: j=1-7 Bonf significant, j=8 weak/no, j=9 no — on primary arm B
    def pattern(sig_series):
        s = sig_series.reindex(range(1, 10))
        return {
            "j1_7_all_sig": bool(s.loc[1:7].astype(bool).all()) if s.loc[1:7].notna().all() else False,
            "j8_sig": bool(s.loc[8]) if pd.notna(s.loc[8]) else None,
            "j9_sig": bool(s.loc[9]) if pd.notna(s.loc[9]) else None,
            "n_sig": int(s.astype(bool).sum()),
        }

    patterns = {arm: pattern(sig_mat[arm]) for arm in sig_mat.columns}
    b_pat = patterns.get("B_conservative", {})
    a_pat = patterns.get("A_imputed_only", {})
    c_pat = patterns.get("C_aggressive_stl3iqr", {})

    same_core_ab = (
        a_pat.get("j1_7_all_sig") == b_pat.get("j1_7_all_sig")
        and a_pat.get("j9_sig") == b_pat.get("j9_sig")
    )
    same_core_bc = (
        c_pat.get("j1_7_all_sig") == b_pat.get("j1_7_all_sig")
        and c_pat.get("j9_sig") == b_pat.get("j9_sig")
    )

    if same_core_ab and same_core_bc:
        verdict = "robustas"
        verdict_detail = (
            "El patrón cualitativo principal (heterogeneidad fuerte en j=1–7; "
            "sin evidencia en j=9) se mantiene en A, B y C. "
            "Las conclusiones del paper no dependen críticamente del tratamiento de atípicos."
        )
    elif same_core_ab:
        verdict = "robustas_con_matices"
        verdict_detail = (
            "A (solo imputados) y B (conservador) coinciden en el patrón principal; "
            "C (agresivo) muestra matices. Preferir B como principal y reportar A como sensibilidad."
        )
    else:
        verdict = "dependientes_del_preproceso"
        verdict_detail = (
            "A y B divergen en escalas clave. Revisar claims del paper y no sobreafirmar robustez."
        )

    # Write SENSITIVITY.md
    md = []
    md.append("# Sensibilidad preproceso — Henry\n")
    md.append(f"**Estado:** completado (F5 local)\n")
    md.append(f"**N_PERM (A/C):** {n_perm}  \n")
    md.append(f"**N_PERM (B, F4):** {n_perm_full if 'B_conservative' in methods_summary else 'n/a'}  \n")
    md.append(f"**Seed:** {seed}\n")
    md.append("\n## Brazos\n")
    md.append("| Brazo | Descripción | Fuente |\n|-------|-------------|--------|\n")
    md.append("| A | Solo imputados | `datos_lima_solo_imputados.csv` |\n")
    md.append("| B | Conservador Agamaz (principal) | `datos_lima_limpieza_conservadora.csv` + F4 |\n")
    md.append("| C | STL+3×IQR agresivo (contraste) | `datos_lima_limpieza_agresiva_stl3iqr.csv` |\n")
    md.append("\n## Patrón de significancia Bonferroni (M=9)\n\n")
    md.append(sig_mat.to_markdown() if hasattr(sig_mat, "to_markdown") else sig_mat.to_string())
    md.append("\n\n## Métodos elegidos por escala\n\n")
    md.append(method_mat.to_string())
    md.append("\n\n## Efectos (Kendall W o η²_G)\n\n")
    md.append(effect_mat.round(4).to_string())
    md.append("\n\n## Fracción de energía en j=4 (diurna, % del total de detalle)\n\n")
    md.append(diurnal_wide.round(2).to_string())
    md.append("\n\n## Acuerdo de llamadas Bonferroni entre brazos\n\n")
    for k, v in agreement.items():
        md.append(f"- **{k}:** {v:.0%} de escalas con la misma decisión sig/no-sig\n")
    md.append("\n## Veredicto\n\n")
    md.append(f"**{verdict}**\n\n")
    md.append(verdict_detail + "\n")
    md.append("\n## Implicación para el paper\n\n")
    md.append("- Método principal del manuscrito: **Base B (conservador)**.\n")
    md.append("- Reportar en Methods/Limitations la sensibilidad A vs B (y opcionalmente C).\n")
    md.append("- No reintroducir limpieza 8–13% como análisis principal.\n")
    md.append("\n## Artefactos\n\n")
    md.append("- `results/sensitivity/inference_all_arms.csv`\n")
    md.append("- `results/sensitivity/significance_matrix_bonferroni.csv`\n")
    md.append("- `results/figures/sensitivity_minus_log_p_by_arm.png`\n")
    md.append("- `results/figures/sensitivity_energy_profiles.png`\n")

    text_md = "".join(md)
    # to_markdown may fail on older pandas - fix if needed
    try:
        sig_md = sig_mat.to_markdown()
    except Exception:
        sig_md = "```\n" + sig_mat.to_string() + "\n```"
    text_md = text_md  # already used to_string fallback above carefully
    # rewrite cleanly without to_markdown dependency
    text_md = f"""# Sensibilidad preproceso — Henry

**Estado:** completado (F5 local)  
**N_PERM (A/C):** {n_perm}  
**N_PERM (B principal, F4):** {n_perm_full}  
**Seed:** {seed}

## Brazos

| Brazo | Descripción | Fuente |
|-------|-------------|--------|
| A | Solo imputados | `datos_lima_solo_imputados.csv` |
| B | Conservador Agamaz (principal) | `datos_lima_limpieza_conservadora.csv` + artefactos F4 |
| C | STL+3×IQR agresivo (contraste) | `datos_lima_limpieza_agresiva_stl3iqr.csv` |

## Patrón de significancia Bonferroni (M=9)

```
{sig_mat.to_string()}
```

## Métodos elegidos por escala

```
{method_mat.to_string()}
```

## Tamaños de efecto

```
{effect_mat.round(4).to_string()}
```

## Fracción de energía en j=4 (banda diurna, % del total de detalle)

```
{diurnal_wide.round(2).to_string()}
```

## Acuerdo de decisiones Bonferroni entre brazos

"""
    for k, v in agreement.items():
        text_md += f"- **{k}:** {v:.0%} de escalas con la misma decisión\n"
    text_md += f"""

## Veredicto

**{verdict}**

{verdict_detail}

### Patrones resumidos

```
{json.dumps(patterns, indent=2)}
```

## Implicación para el paper

- Análisis principal del manuscrito: **Base B (conservador)**.
- En Methods/Limitations: mencionar sensibilidad A vs B (y C como contraste con la versión Raw).
- No reintroducir la limpieza 8–13% como método principal.
- Figuras del paper (Fig.1, Fig.3, Tab.1–2) se basan en B; F5 documenta robustez.

## Artefactos

- `results/sensitivity/inference_all_arms.csv`
- `results/sensitivity/significance_matrix_bonferroni.csv`
- `results/sensitivity/pvalue_matrix.csv`
- `results/sensitivity/diurnal_j4_pct_by_arm.csv`
- `results/figures/sensitivity_minus_log_p_by_arm.png`
- `results/figures/sensitivity_energy_profiles.png`
- `docs/SENSITIVITY.md` (este archivo)
"""
    (paths["root"] / "docs" / "SENSITIVITY.md").write_text(text_md, encoding="utf-8")
    (sens_dir / "SENSITIVITY.md").write_text(text_md, encoding="utf-8")
    (sens_dir / "verdict.json").write_text(
        json.dumps({"verdict": verdict, "detail": verdict_detail, "patterns": patterns, "agreement": agreement, "n_perm_ac": n_perm}, indent=2),
        encoding="utf-8",
    )
    print("\n==== VERDICT:", verdict, "====")
    print(verdict_detail)
    print("F5 complete.")


if __name__ == "__main__":
    main()
