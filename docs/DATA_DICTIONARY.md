# Data dictionary

## `data/raw/datos_lima_raw_mp2.5.csv`

Raw REMCA extract. Columns:

| Column | Meaning |
|---|---|
| `date` | Date in `d/m/yyyy` format |
| `HORA` | Hour in `H:MM:SS` format |
| `SBJ`, `STA`, `VMT`, `SJL`, `SMP` | Hourly PM2.5 (µg m⁻³) at the five study stations |
| `CDM`, `CRS`, `CRB`, `PPD` | Additional stations/columns present in the source; not used in the manuscript |

Source: SENAMHI REMCA, <https://www.senamhi.gob.pe>. SHA-256:
`74007b6e1914579eaadbe74fbde1ac7f994a4b6f0c59fd2117131edff856635f`.

## `data/processed/`

| File | Description | SHA-256 |
|---|---|---|
| `datos_lima_solo_imputados.csv` | Base A: time-interpolated missing values only | `dee1aca225a46a49d0f5284aaa616ddac0a72dbabc72a595054fbb34fa686d3a` |
| `datos_lima_limpieza_conservadora.csv` | Base B: primary analysis (conservative cleaning) | `7b8b8bdccce1e864ed0d286d1c82655e936605fc1971bb592b3c27ab52a56591` |
| `datos_lima_limpieza_agresiva_stl3iqr.csv` | Base C: contrast arm (STL+3×IQR) | `df7a35d70a723e23b32577b49ee4539199d813c01db495988cc1c1526fd182fb` |

All processed files have a `datetime` index (hourly, 10,176 rows) and five
station columns in µg m⁻³.

## `data/audit/`

| File | Description |
|---|---|
| `resumen_deteccion_atipicos.csv` | Per-station counts and detection summary |
| `candidatos_fuertes_revision.csv` | Row-level audit of replaced hours (timestamp, station, value, replacement, residual, Hampel score, run length, corroboration) |
| `comparacion_metodos_outlier.csv` | Conservative vs aggressive replacement counts |
| `preprocess_run_meta.json` | Run configuration and counts |

## `results/`

| Folder | Contents |
|---|---|
| `tables/` | Descriptives, scale tests, energy fractions, correlations, preprocess impact, `f6_paper_numbers.json` |
| `inference/` | Adaptive results, block attempts, DWT QC, wavelet metadata, arrays |
| `sensitivity/` | A/B/C p-value, significance, method and energy matrices |

## Units and identifiers

- PM2.5: µg m⁻³.
- Wavelet scale `j`: period band `2^j`–`2^{j+1}` hours.
- `E_j`: sum of squared detail coefficients at scale `j`.
- `W`: Kendall's coefficient of concordance.
- `η²_G`: generalised eta squared.
