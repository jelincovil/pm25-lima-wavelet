# Data

## Raw

`raw/datos_lima_raw_mp2.5.csv` is the REMCA extract used in the study. It is
included to make the preprocessing audit reproducible. Source: SENAMHI REMCA,
<https://www.senamhi.gob.pe>. See `../DATA_LICENSE.md` for terms.

SHA-256: `74007b6e1914579eaadbe74fbde1ac7f994a4b6f0c59fd2117131edff856635f`

The raw file contains columns for other stations (`CDM`, `CRS`, `CRB`, `PPD`)
that are not used in the manuscript. The five study stations are `SBJ`, `STA`,
`VMT`, `SJL` and `SMP`.

## Processed

| File | Base | Description |
|---|---|---|
| `processed/datos_lima_solo_imputados.csv` | A | Time interpolation of missing values only |
| `processed/datos_lima_limpieza_conservadora.csv` | B | Primary analysis; conservative replacement |
| `processed/datos_lima_limpieza_agresiva_stl3iqr.csv` | C | Contrast; STL+3×IQR |

All three have 10,176 hourly rows and five station columns in µg m⁻³.

## Audit

`audit/` contains the per-station summary, the row-level replacement log,
the conservative-vs-aggressive comparison and the run metadata. See
`../docs/AUDIT.md` for the protocol.

## Rebuild

```bash
python analysis/01_preprocess_agamaz.py
```

This overwrites the processed and audit files. The script expects
`data/raw/datos_lima_raw_mp2.5.csv`.
