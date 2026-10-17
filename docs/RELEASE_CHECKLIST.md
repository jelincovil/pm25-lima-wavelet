# Release checklist (GitHub + Zenodo)

**Status 2026-10-17:** the repository is public at
<https://github.com/jelincovil/pm25-lima-wavelet> and release `v1.0.1` exists.
Steps 1–4 are complete; the Zenodo DOI (step 5) is pending an account/token.
Complete the remaining checks before submission.

## 1. Create the empty GitHub repository

- Name: `pm25-lima-wavelet`
- Visibility: public (or private during review; see below)
- Do **not** initialise with README/LICENSE; the local history already exists.

## 2. Push

```bash
cd pm25-lima-wavelet
git branch -M main
git remote add origin git@github.com:jelincovil/pm25-lima-wavelet.git
git push -u origin main
git push origin --tags
```

## 3. Set repository metadata

- Description: “Reproducible wavelet multiscale analysis of the Lima PM2.5 monitoring network (REDIN submission)”.
- Topics: `air-quality`, `pm25`, `wavelet`, `environmental-monitoring`, `lima`, `peru`, `reproducibility`.
- Enable Actions.
- Add branch protection for `main` (require CI).
- Add the repository URL to `README.md`, `CITATION.cff` (`repository-code`) and `.zenodo.json` (`related_identifiers` if desired).

## 4. First release

```bash
git tag -a v1.0.0 -m "REDIN v2 submission candidate"
git push origin v1.0.0
```

The `release` workflow builds the PDF and a release zip. Check that the GitHub
Release contains `pm25-lima-wavelet-release.zip`.

## 5. Zenodo DOI

1. Link the GitHub repository to Zenodo.
2. Archive the `v1.0.0` release.
3. Copy the DOI into:
   - `README.md` (badge and citation section);
   - `CITATION.cff` (`doi`);
   - `paper/article_REDIN.tex` Data Availability statement;
   - `paper/SUBMISSION_PACKAGE_REDIN.md`.
4. Recompile the PDF (`make paper`) and re-run `make verify`.
5. Commit the DOI update and tag `v1.0.1` if the PDF changes.

## 6. If the journal requires anonymous review

- Use a temporary anonymous repository or an anonymised Zenodo record.
- Remove author names from the repository README/CITATION in the anonymous
  mirror only; the manuscript itself already contains author names, so confirm
  the journal’s policy first.
- Keep the public repository private until the decision, then publish.

## 7. Final pre-submission checks

```bash
make verify
make paper
```

- [ ] CI green on `main`.
- [ ] PDF 12 pp; figures on pp. 6, 7, 9.
- [ ] DOI and repository URL in the manuscript.
- [ ] ORCID and affiliations confirmed.
- [ ] Cover letter signed.
- [ ] `paper/SUBMISSION_PACKAGE_REDIN.md` checklist complete.
