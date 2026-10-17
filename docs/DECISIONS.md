# Analysis decisions

This is a lightweight architecture decision record for the scientific and
reproducibility choices that a reviewer is likely to question.

| ID | Decision | Rationale | Alternatives considered | Consequence |
|---|---|---|---|---|
| D01 | Base B (conservative) is the primary analysis | Preserves multi-hour and multi-station pollution episodes; only 0.68–1.08% of hours replaced | Base A (imputation only); Base C (STL+3×IQR) | Conclusions are robust to A; C changes `j = 8` |
| D02 | Symmlet-7 (`sym7`) | Smooth, near-symmetric, seven vanishing moments; adequate for environmental series at this length | Haar, db4, sym8 | Reported as a sensitivity target; sym7 is fixed in `config.yaml` |
| D03 | Mirror padding to 16,384 points | Dyadic DWT requirement; keeps 10,176 original hours centred with 3,104 points per side | Zero padding; truncation | Coarse scales `j ≥ 11` are descriptive only |
| D04 | Formal inference at `j = 1…9` | At least 12 central coefficients per scale; `j = 10` has only 10 | Test all 13 scales | No formal claim at `j ≥ 10`; edge effects acknowledged |
| D05 | Central coefficients only | Removes pure-padding coefficients from inference | All coefficients | Fewer coefficients but no padding artefacts |
| D06 | Block aggregation with Ljung–Box + Holm | Handles temporal dependence before choosing a test | Coefficient-wise tests; no aggregation | Blocks are ~512 h at `j = 1–7`, 256 h at `j = 8`, 512 h at `j = 9` |
| D07 | Adaptive test tree (RM-ANOVA / Friedman / block permutation) | Test assumptions are checked rather than assumed | Always Kruskal–Wallis; always MANOVA | Methods vary by scale; reported in Table 2 |
| D08 | Bonferroni over `M = 9` | Pre-specified family-wise control across formal scales | Holm only; FDR; no correction | Threshold 0.00556; Holm values in the numerical tables |
| D09 | `N_PERM = 9,999`, seed 2026 | Stable permutation p-values; resolution floor 1.0×10⁻⁴ | 1,999; 99,999 | Floor reported explicitly; no over-precision |
| D10 | No claim of seasonal equality | `j ≥ 10` is not formally testable; `j = 9` has low power | Claim “indistinguishable at seasonal scales” | Wording is “no evidence”, not “no difference” |
| D11 | Decision matrix is conditional | Five stations, 14 months, no meteorology/source apportionment | Universal network-design rule | Recommendations are engineering implications, not causal laws |
| D12 | Independent public repository | Avoid exposing the parent project and unrelated documents | Publish the parent repository | Curated package, clean history, MIT/CC BY licensing |

## Reproducibility decisions

- The committed results are the authoritative artefacts; the full pipeline can regenerate them.
- Tests check the committed artefacts, not a fresh stochastic run.
- The paper uses `\graphicspath{{figures/}}` and explicit paths, so stale copies cannot shadow the final figures.
