# pm25-lima-wavelet

Reproducible wavelet multiscale analysis of hourly PM2.5 at five REMCA stations in Lima, Peru.

**Manuscript:** *Multiscale Heterogeneity of an Urban PM2.5 Monitoring Network: Wavelet-Based Functional Inference for Lima, Peru*  
**Target journal:** Revista Facultad de Ingeniería, Universidad de Antioquia (REDIN)  
**Status:** submission candidate. Code, processed data, audit trail, figures and LaTeX source are released for review and reuse.

## What this repository contains

This is the reproducibility package for a study that asks a practical monitoring question: **at which timescales do PM2.5 stations provide distinct information?** The analysis couples a conservative preprocessing protocol with assumption-checked wavelet inference and translates the results into a scale-to-objective decision matrix.

Key findings (Base B, conservative preprocessing):

- Inter-station differences are Bonferroni-significant at wavelet scales `j = 1–7` (about 2 h to 11 days).
- The largest rank-based effect is in the diurnal band `j = 4` (16–32 h), Kendall `W = 0.69`.
- `j = 8` is nominally significant but does not survive Bonferroni; `j = 9` shows no evidence of difference, and `j ≥ 10` is not formally testable with this record length.
- Diurnal energy is 20.4% (95% CI 17.4–22.9) at San Juan de Lurigancho versus 12.4% (10.3–16.5) at San Borja.
- At `j = 4`, 8 of 10 secondary pairwise tests differ; SJL–STA and SBJ–SMP do not.
- Conservative cleaning replaces 0.68–1.08% of hours, compared with 8–13% under STL+3×IQR.

## Repository layout

```
analysis/              Python pipeline (00–05), config.yaml
data/raw/              Raw REMCA CSV (see data/README.md)
data/processed/        Base A, B and C
data/audit/            Row-level audit and preprocessing summary
results/tables/        Tables 1–2, decision inputs, key numbers
results/inference/     Adaptive test results, DWT QC, wavelet metadata
results/sensitivity/   A/B/C sensitivity matrices
paper/                 LaTeX source, compiled PDF, final figures
docs/                  Claims registry, reproduction guide, decisions, data dictionary
tests/                 Fast regression tests on committed artefacts
scripts/               Claim, PDF and style checks
```

## Quick start

```bash
git clone https://github.com/jelincovil/pm25-lima-wavelet.git
cd pm25-lima-wavelet

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

make verify     # tests + claims + PDF checks (fast, uses committed artefacts)
make paper      # recompile paper/article_REDIN.pdf
```

## Reproduce the analysis

The full pipeline uses `N_PERM = 9,999` and takes longer than the verification target. It overwrites files in `results/`.

```bash
make analysis
```

Pipeline order:

1. `analysis/01_preprocess_agamaz.py` — Base A/B/C and audit.
2. `analysis/02_wavelet_diagnostics.py` — Symmlet-7 DWT, padding, Parseval checks, energy.
3. `analysis/03_inference_adaptive.py` — assumption-checked tests, `N_PERM = 9,999`, seed 2026.
4. `analysis/04_sensitivity.py` — A/B/C sensitivity.
5. `analysis/05_figures_tables.py` — paper figures, tables and registry.

The paper uses Base B. Raw REMCA data are public; processed bases and the row-level audit are included so that the preprocessing can be inspected without re-downloading the source.

## Reproducibility contract

- All parameters are in [`analysis/config.yaml`](analysis/config.yaml): stations, pad length, wavelet family, formal scales, Hampel settings, seed, permutations and multiplicity.
- `results/tables/f6_paper_numbers.json` is the single source for the manuscript's descriptive numbers.
- `docs/NUMBER_REGISTRY.csv` maps each manuscript token to a value, artefact and command.
- `tests/` checks the counts, wavelet QC, test choices, figure sizes, absence of absolute paths and claim registry.
- `scripts/check_claims.py` fails if a registered token is missing from the LaTeX source.
- `scripts/check_pdf.py` checks that figures appear before the reference list and that figure files stay below 500 KB.

Environment: Python ≥3.10 (tested with 3.12) and a TeX Live installation with `pdflatex`, `booktabs`, `natbib`, `siunitx`, `lineno` and `authblk`.

See [`docs/REPRODUCING.md`](docs/REPRODUCING.md) for the full protocol and expected outputs, and [`docs/UNCERTAINTY.md`](docs/UNCERTAINTY.md) for the bootstrap and post-hoc analyses.

## Data and code availability

- Raw hourly PM2.5: SENAMHI REMCA, <https://www.senamhi.gob.pe>.
- Processed bases and audit: included in `data/`.
- Code: MIT License (`LICENSE`).
- Manuscript and figures: CC BY 4.0 (`LICENSE-PAPER`).
- Data terms: see `DATA_LICENSE.md`.

## Citation

If you use this repository, please cite the manuscript and the archived release. Metadata are in [`CITATION.cff`](CITATION.cff). A Zenodo DOI will be added when the release is archived.

## Contact

Henry S. Aquino-Mosquera — henry.aquino@ciencia.org.pe

## Acknowledgments

We thank SENAMHI for maintaining the REMCA network and for making the hourly data publicly available.
