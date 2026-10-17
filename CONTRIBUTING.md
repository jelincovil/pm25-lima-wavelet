# Contributing

This repository accompanies a manuscript under review. Small, well-scoped
contributions are welcome.

## Reporting an issue

Please open an issue with:

- the command you ran;
- the expected and observed result;
- your Python and TeX versions;
- the relevant file or table.

## Pull requests

1. Create a branch from `main`.
2. Keep scientific parameters unchanged unless the change is explicitly about
   methodology; document the rationale in `docs/DECISIONS.md`.
3. Run `make verify` and, if the pipeline changed, `make analysis`.
4. Do not commit generated LaTeX build artefacts or virtual environments.
5. Do not add absolute paths, credentials or personal data.

## Scope

The repository is a reproducibility package, not a general-purpose wavelet
library. Changes that alter the manuscript's numerical results require a
corresponding entry in `docs/NUMBER_REGISTRY.csv` and a new release tag.
