# Manuscript source

`article_REDIN.tex` is the REDIN submission candidate. It compiles with
`pdflatex` (twice), not XeLaTeX.

```bash
cd paper
pdflatex -interaction=nonstopmode -halt-on-error article_REDIN.tex
pdflatex -interaction=nonstopmode -halt-on-error article_REDIN.tex
```

or, from the repository root:

```bash
make paper
```

## Figures

The manuscript uses `\graphicspath{{figures/}}` and explicit paths:

| Figure | File |
|---|---|
| Fig. 1 | `figures/figure_1.png` |
| Fig. 2 | `figures/figure_4.png` |
| Fig. 3 | `figures/figure_2.png` |

The names follow the original analysis outputs; the mapping is intentional.
Do not add duplicate copies in `paper/` — the tests fail if a stale copy is
present outside `figures/`.

## Layout

- 12 pt, letter paper, 2.5 cm margins, single column, line numbers.
- Figure widths 0.80`\textwidth`; all figures must appear before the reference
  list (`scripts/check_pdf.py`).
- Tables use `booktabs`; the full test table is Table 2 and the decision matrix
  is Table 3.

## Bibliography

The bibliography is embedded with `thebibliography` in IEEE numeric style.
Every `\bibitem` is cited; the claim registry checks the numbers, not the
references. If you migrate to BibTeX, verify that all keys resolve and that
the numeric order is preserved.

## Before submission

- Confirm author affiliations, corresponding author and ORCID.
- Insert the public repository URL and Zenodo DOI in the Data Availability
  statement once the release exists.
- Recompile twice and run `python scripts/check_pdf.py`.
