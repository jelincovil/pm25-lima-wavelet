# Preprocessing audit

## What was changed

The conservative protocol replaces an hourly value only when **all** of the
following hold:

1. The STL residual is outside a medcouple-adjusted boxplot fence (`k = 1.5`).
2. A centred Hampel filter (49 h, 4 MAD) also flags the residual.
3. The dual-flag run lasts at most one hour.
4. No other station shows a same-direction Hampel excursion (`K_conc = 2.5`)
   at the same time.

Flagged hours are replaced by the STL trend + seasonal component and clipped
at zero.

## Counts

| Station | Imputed (NA) | Conservative replacements | % of series | STL+3×IQR replacements |
|---|---:|---:|---:|---:|
| SBJ | 693 | 69 | 0.68% | 1,342 |
| STA | 570 | 81 | 0.80% | 1,152 |
| VMT | 404 | 88 | 0.86% | 793 |
| SJL | 500 | 72 | 0.71% | 895 |
| SMP | 244 | 110 | 1.08% | 1,118 |

The conservative rule replaces about an order of magnitude fewer hours than
STL+3×IQR. The difference is the point of the protocol: the aggressive rule
removes a large share of the upper tail that may represent real pollution
episodes.

## Files

- `data/audit/resumen_deteccion_atipicos.csv`: per-station detection summary.
- `data/audit/candidatos_fuertes_revision.csv`: one row per replaced hour.
- `data/audit/comparacion_metodos_outlier.csv`: conservative vs aggressive.
- `data/audit/preprocess_run_meta.json`: configuration and totals.

## Reproduce

```bash
python analysis/01_preprocess_agamaz.py
```

The script writes Bases A/B/C and refreshes the audit files.
