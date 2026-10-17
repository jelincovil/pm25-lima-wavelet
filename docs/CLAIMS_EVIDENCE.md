# Claims–evidence matrix

Every quantitative statement in the manuscript must map to an artefact and a
command. The machine-readable version is `docs/NUMBER_REGISTRY.csv`.

| ID | Claim in the manuscript | Level | Evidence | Status |
|---|---|---|---|---|
| C1 | Conservative cleaning replaces 69–110 h per station (0.68–1.08%) | Observed | `data/audit/resumen_deteccion_atipicos.csv` | Verified |
| C2 | STL+3×IQR would replace 793–1,342 points (8–13%) | Observed | `data/audit/comparacion_metodos_outlier.csv` | Verified |
| C3 | The hourly grid has 10,176 rows; 244–693 values imputed per station | Observed | `data/audit/preprocess_run_meta.json` | Verified |
| C4 | DWT uses Symmlet-7, pad 16,384, `j = 1…9` formal | Observed | `results/inference/wavelet_meta.json`, `results/tables/scale_eligibility.csv` | Verified |
| C5 | DWT reconstruction error ~1e-10; Parseval error ~1e-13 | Observed | `results/inference/dwt_qc.csv` | Verified |
| C6 | Bonferroni-significant differences at `j = 1–7` | Observed | `results/inference/adaptive_results.csv`, Table 2 | Verified |
| C7 | Largest effect at `j = 4`, Kendall `W = 0.69` | Observed | `results/inference/adaptive_results.csv` | Verified |
| C8 | `j = 8` nominal but not Bonferroni; `j = 9` not significant | Observed | `results/inference/adaptive_results.csv` | Verified |
| C9 | Diurnal energy 20.4% (SJL) vs 12.4% (SBJ) | Observed | `results/tables/diurnal_energy_fraction_j4_baseB.csv` | Verified |
| C10 | A≡B in Bonferroni decisions; C flags `j = 8` | Observed | `results/sensitivity/significance_matrix_bonferroni.csv`, `docs/SENSITIVITY.md` | Verified |
| C11 | Blocks: 19–20 at `j = 1–7`, 40 at `j = 8`, 20 at `j = 9` | Observed | `results/inference/adaptive_results.csv` | Verified |
| C12 | Decision matrix: prioritise `j = 1–4` in SJL/STA; do not infer multi-week redundancy | Recommendation | C6–C11, Table 3 | Derived; conditional on the five-station, 14-month record |

## Rules

- **Observed** claims are direct numerical outputs and must be reproducible from the repository.
- **Inferred** claims use cautious language (“consistent with”, “suggests”) and are not presented as causal.
- **Recommendation** claims are conditional engineering implications, not statistical tests.
- If a number changes, update the registry, the manuscript and the relevant test in the same commit.
