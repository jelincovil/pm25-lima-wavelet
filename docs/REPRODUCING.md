# Reproducing the analysis

This document describes how to regenerate the committed results and the manuscript.

## Requirements

- Python ≥3.10 (tested with 3.12).
- A TeX Live installation with `pdflatex`, `booktabs`, `natbib`, `siunitx`, `lineno`, `authblk`, `caption`, `subcaption`, `makecell`, `multirow`, `titlesec`, `microtype`, `hyperref` and `mathptmx`.
- About 1 GB of free disk space for the virtual environment and generated artefacts.

## 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the versions used for the committed artefacts. If a
package cannot be installed on your platform, use a Python 3.12 environment;
the numerical results should be unchanged within floating-point tolerance.

## 2. Fast verification (uses committed artefacts)

```bash
make verify
```

This runs:

- `pytest` on the committed CSV/JSON files (counts, DWT QC, test choices, claim registry, figure sizes, absence of absolute paths);
- `scripts/check_claims.py`, which verifies that every token in `docs/NUMBER_REGISTRY.csv` appears in the manuscript and that its artefact exists;
- `scripts/check_pdf.py`, which checks that all figures appear before the reference list, are 8.5–17 cm wide and stay below 500 KB.

To rebuild the PDF:

```bash
make paper
```

The manuscript is compiled from `paper/` with `pdflatex` twice.

## 3. Full pipeline (regenerates results)

```bash
make analysis
```

Order and outputs:

| Step | Script | Main outputs |
|---|---|---|
| 1 | `analysis/01_preprocess_agamaz.py` | `data/processed/` Bases A/B/C; `data/audit/` |
| 2 | `analysis/02_wavelet_diagnostics.py` | `results/inference/` DWT QC, arrays, metadata; `results/tables/` energy and eligibility |
| 3 | `analysis/03_inference_adaptive.py` | `results/inference/adaptive_results.csv`; Fig. 3 |
| 4 | `analysis/04_sensitivity.py` | `results/sensitivity/`; `docs/SENSITIVITY.md` |
| 5 | `analysis/05_figures_tables.py` | paper figures, Tables 1–2, `f6_paper_numbers.json`, registry update |
| 6 | `analysis/06_uncertainty_posthoc.py` | bootstrap CIs, pairwise post-hoc table |

Table 2 in the manuscript is typeset from `results/inference/adaptive_results.csv`; the `results/tables/table2_scale_tests.tex` fragment is a raw generator output and is not the final table. The full run uses `N_PERM = 9,999` and seed `2026`. Runtime depends on the
machine; the permutation step is the slowest. The scripts write to the
committed result folders, so run the full pipeline in a scratch copy if you
want to preserve the published artefacts.

## 4. Expected checks

After `make analysis`, the following should hold:

- 10,176 hourly rows per station in each processed base.
- 244–693 imputed hours per station.
- 69–110 conservative replacements per station (0.68–1.08%).
- 793–1,342 replacements under STL+3×IQR (8–13%).
- DWT reconstruction error < 1e-8 and Parseval error < 1e-10.
- Formal scales `j = 1…9`; `j ≥ 10` not eligible.
- Bonferroni threshold `0.05/9 ≈ 0.00556`.

These are encoded in `tests/`. Uncertainty outputs are documented in `docs/UNCERTAINTY.md`.

## 5. Determinism and platform notes

- All random operations use seed `2026`.
- Permutation p-values at the resolution limit are exactly `1/(9,999+1) = 1.0×10⁻⁴`.
- Figures may differ slightly across Matplotlib/font versions; the numerical tables are the authoritative output.
- The manuscript uses `\graphicspath{{figures/}}`, so it must be compiled from `paper/`.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `pdflatex: command not found` | Install TeX Live or use the CI workflow |
| `figure_1.png` not found | Compile from `paper/`; figures live in `paper/figures/` |
| `ModuleNotFoundError: pywt` | Activate the virtual environment and `pip install -r requirements.txt` |
| `check_pdf.py` says figure after references | Recompile; check that figure widths are ≤0.85`\textwidth` |
| Results differ in the last decimals | Check BLAS/OS and package versions; report in an issue |
