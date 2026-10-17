# Reviewer objections and prepared responses

| Objection | Response | Evidence |
|---|---|---|
| “Five stations cannot support network design.” | The study is a case-specific audit, not a universal design rule. The decision matrix is explicitly conditional on five stations and 14 months. | Table 3; Limitations |
| “Fourteen months cannot capture seasonal variability.” | The record spans two winters and two summers in part; the paper does not claim seasonal equality and labels multi-week scales as not formally testable. | Methods; Results 3.3; Limitations |
| “The preprocessing is still subjective.” | The protocol is explicit and auditable: dual residual flags, maximum one-hour runs, cross-station non-corroboration, and row-level audit. A/B/C sensitivity shows the main pattern is robust. | `data/audit/`; `docs/SENSITIVITY.md` |
| “There are multiple comparisons.” | The family is pre-specified as `M = 9`; Bonferroni controls FWER and Holm values are reported. No post-hoc fishing is used for the main claims. | Methods 2.4; Table 2 |
| “The wavelet choice is arbitrary.” | `sym7` is a standard smooth wavelet for environmental series; DWT QC is reported; the choice is fixed in `config.yaml` and documented as a robustness target. | Methods 2.3; `docs/DECISIONS.md` |
| “The permutation p-values are at the floor.” | The floor is reported explicitly as `1/(9,999+1) = 1.0×10⁻⁴`; effects and block counts are reported alongside p-values. | Table 2; Results 3.3 |
| “Wavelet coefficients are not independent.” | Dependence is diagnosed with Ljung–Box; blocks are aggregated before testing; block permutation is used when dependence persists. Block counts and durations are reported. | Methods 2.4; Results 3.3 |
| “The analysis is observational; causal language is unwarranted.” | The paper uses observational language and presents physical mechanisms as plausible, not as attribution. No source apportionment is claimed. | Discussion 3.5; Limitations |
| “What is new relative to previous Lima studies?” | Previous Lima work focuses on spatial means, exceedances and exposure mapping; this study adds a scale-resolved, assumption-checked audit and a scale-to-objective decision matrix. | Introduction; Comparison 3.8 |
| “Where are the data and code?” | Raw data are public; processed bases, audit, code and manuscript source are in this repository, with a claims registry and tests. | README; `docs/REPRODUCING.md` |

## Language guardrails

- “No evidence of difference” is not “no difference”.
- “Not formally testable” is not “equal”.
- “Consistent with” is not “caused by”.
- Recommendations are conditional on the monitoring objective and the evidence base.
