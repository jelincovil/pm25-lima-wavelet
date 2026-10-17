# Environment

## Tested environment

| Component | Version |
|---|---|
| Python | 3.12.12 |
| pandas | 2.3.3 |
| NumPy | 2.5.1 |
| statsmodels | 0.15.0 |
| PyWavelets | 1.8.0 |
| SciPy | 1.18.0 |
| pingouin | 0.7.0 |
| Matplotlib | 3.11.1 |
| seaborn | 0.13.2 |
| PyYAML | 6.0.3 |
| PyMuPDF | 1.28.2 |
| pytest | 9.1.1 |
| TeX Live | 2025 (pdfTeX 3.141592653-2.6-1.40.27) |

## Notes

- The committed artefacts were produced by the original local pipeline. The
  reproducibility package is tested with the versions above.
- The full analysis is stochastic only through the permutation test; seed 2026
  is fixed in `analysis/config.yaml`.
- Figures may differ at the pixel level across Matplotlib/font versions. The
  numerical CSV/JSON outputs are authoritative.
- The manuscript uses `pdflatex`, not XeLaTeX, because the original XeLaTeX
  build produced a PDF without extractable text on the author's system.
