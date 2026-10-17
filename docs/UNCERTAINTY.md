# Uncertainty and secondary pairwise analyses

**Script:** `analysis/06_uncertainty_posthoc.py`  
**Seed:** 2026  
**Status:** secondary/descriptive; does not replace the primary Bonferroni tests.

## Why these analyses

The primary results report p-values and effect sizes, but a reviewer also needs
to know **how uncertain** the effects are and **which stations** drive the
omnibus differences. This module adds:

1. block-bootstrap confidence intervals for Kendall's `W`;
2. block-bootstrap confidence intervals for the diurnal energy fraction;
3. paired post-hoc Wilcoxon tests (Holm within scale).

## Effect-size uncertainty

For each formal scale, the block-level `log1p` energy matrix (19–20 blocks at
`j = 1–7`, 40 at `j = 8`, 20 at `j = 9`) is resampled with replacement
(2,000 replicates; seed 2026). Kendall's `W` is recomputed for each replicate
and the 2.5–97.5 percentiles are reported.

| Scale | W | 95% CI |
|---|---:|---|
| 1 | 0.608 | 0.487–0.769 |
| 2 | 0.616 | 0.520–0.748 |
| 3 | 0.647 | 0.558–0.778 |
| 4 | 0.688 | 0.596–0.802 |
| 5 | 0.587 | 0.486–0.720 |
| 6 | 0.350 | 0.181–0.598 |
| 7 | 0.447 | 0.332–0.621 |
| 8 | 0.086 | 0.036–0.208 |
| 9 | 0.078 | 0.023–0.293 |

At `j = 5` the primary effect metric is generalised η² (0.21), not `W`; the
`W` column is shown for comparability across scales.

## Diurnal energy fraction

The Base B series is resampled in 7-day blocks (168 h), padded and decomposed
again with the same Symmlet-7 settings (1,000 replicates; seed 2026). The
fraction is `E_4 / ΣE_j`.

| Station | E4 share (%) | 95% CI |
|---|---:|---|
| SBJ | 12.40 | 10.34–16.50 |
| STA | 18.74 | 16.86–21.59 |
| VMT | 13.29 | 11.87–17.04 |
| SJL | 20.44 | 17.43–22.94 |
| SMP | 17.41 | 13.40–19.43 |

The SJL and SBJ intervals do not overlap.

## Post-hoc pairwise tests

For each scale, paired Wilcoxon signed-rank tests compare all 10 station pairs
on the block-level `log1p` energy; p-values are Holm-adjusted **within scale**.
There are 90 tests in total; 45 are significant at 0.05 after Holm.

At `j = 4`, 8 of 10 pairs differ. The exceptions are SJL–STA and SBJ–SMP,
consistent with two groups separated by the diurnal band. VMT is intermediate
and differs from both groups in this band.

These are **secondary** tests. They are reported to describe which stations
drive the omnibus result, not to establish a new primary claim. Pairwise
results at `j = 8–9` are reported for completeness but are not interpreted
because the omnibus Bonferroni decision was negative.

## Files

- `results/inference/effect_ci.csv`
- `results/inference/posthoc_pairwise.csv`
- `results/tables/diurnal_energy_fraction_ci.csv`
- `results/inference/uncertainty_summary.json`

## Reproduce

```bash
python analysis/06_uncertainty_posthoc.py
```

Runtime is about 20 s on the reference machine.
