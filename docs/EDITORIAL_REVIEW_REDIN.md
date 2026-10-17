# Informe editorial — REDIN v2.1

**Fecha:** 2026-10-17  
**Manuscrito:** `paper/article_REDIN.tex` / `paper/article_REDIN.pdf`  
**Alcance:** calidad de texto, consistencia editorial, figuras, tablas y referencias.  
**Restricción:** no se modificaron datos, métodos, resultados ni conclusiones científicas.

---

## 1. Diagnóstico de partida

El manuscrito era científicamente sólido, pero presentaba defectos de producto que un editor o revisor detecta en la primera lectura:

| Área | Problema | Riesgo |
|---|---|---|
| Título | Corte manual que dejaba “Network:” o “Peru” aislados | Aspecto descuidado en la primera página |
| Abstract | Frases densas, “strong” sin precisión, “j≥10 was not testable” | Legibilidad y precisión |
| Resumen ES | “no fue testeable”, “faltantes”, “pierden soporte Bonferroni” | Anglicismos y registro informal |
| Introducción | REMCA, SENAMHI, WHO e IQR sin desarrollar; una cita wavelet-FANOVA poco precisa | Accesibilidad y rigor |
| Métodos | “fitted”, “run length”, “log(1+·)”, “block + station”, umbrales sin nota | Prosa técnica mejorable |
| Resultados | “29.7” para un valor de 29.64; “confirming”; “simple decision rule” | Precisión y tono |
| Discusión | “Comparison with previous work” al final, después de limitaciones | Flujo narrativo |
| Tablas | “NAs imputed”; abreviaturas sin nota; caption de Tabla 2 demasiado cargado | Legibilidad |
| Figuras | Texto pequeño; leyenda “Permutacao-blocos” en inglés; títulos redundantes | Calidad visual y coherencia idiomática |
| Referencias | Numeración no seguía el orden de primera cita; una cita no sostenía la frase | Cumplimiento IEEE |
| Declaraciones | “Statistical analysis” no es rol CRediT; “Correspondence” | Precisión editorial |

---

## 2. Cambios aplicados

### 2.1 Título y primera página

- Se eliminó el corte que aislaba “Network:” y se recompuso el título en tres líneas equilibradas.
- Se mantuvo el título en inglés y el título en español, ambos dentro del límite de palabras.
- Se conservó el bloque de autores y afiliaciones, sin inventar datos.

### 2.2 Abstract y Resumen

- Abstract reescrito a **228 palabras** (límite 230), con estructura problema → brecha → datos/método → resultados → implicación.
- “strong” sustituido por **“Bonferroni-significant”**.
- “stations provide distinct information” → **“stations behave differently”** (más concreto).
- “no evidence of difference” → **“no evidence of a difference”**.
- Se añadió “per station” a la imputación y “wavelet transform” a Symmlet-7.
- Resumen en español reescrito: “valores faltantes”, “enfoque wavelet”, “dejan de serlo tras la corrección de Bonferroni”, “no pudo evaluarse formalmente”, “señales de varias semanas”.

### 2.3 Introducción

- PM2.5 presentado como **factor de riesgo ambiental**, no solo “burden”.
- **SENAMHI** y **REMCA** desarrollados en su primera aparición.
- **WHO** desarrollado como Organización Mundial de la Salud.
- **IQR** definido en la primera mención de STL+3×IQR.
- Se eliminó la cita `abramovich2004` de la frase de wavelet-FANOVA, porque no sostenía ese uso; la referencia se retiró de la bibliografía.
- Se mantuvo la estructura de tres contribuciones y el roadmap.

### 2.4 Métodos

- “was fit” → **“was fitted”**.
- “run length” → **“number of consecutive flagged hours”**.
- **STL** y **MAD** desarrollados.
- “block + station” → **“additive model with block and station effects”**.
- “log(1+·)” → **“log-transformed block means, $\log(1+x)$”**.
- Umbrales de normalidad explícitos (Shapiro–Wilk ≥ 0.05, |skewness| < 1, |excess kurtosis| < 2).
- “Holm p-values in supplementary tables” → **“in the reproducibility materials”**, para no remitir a un suplemento inexistente.
- Se aclaró la diferencia 10 178 → 10 176: **ocho timestamps duplicados promediados**.
- Se describe la imputación como **interpolación lineal en el tiempo**.
- Software: se eliminó la promesa de disponibilidad “from the corresponding author” y se remite al repositorio y a la declaración de datos.

### 2.5 Resultados y discusión

- “29.7” → **“near 30”** para no dar una precisión falsa (SMP = 29.64).
- Se separó la lectura de asimetría de la línea WHO: ahora se explica que la guía es una referencia, no un estándar horario.
- “confirming” → **“showing”** (no se confirma una relación causal).
- “simple engineering decision rule” → **“engineering decision rule”**.
- “additional stations add less independent information” → se suavizó a **“the evidence weakens; a smaller subset may be adequate, but should be tested against the objective”**.
- “This matches a physical partition” → **“is consistent with”**.
- “Several limitations remain” en lugar de “Limitations remain”.
- **“Comparison with previous work” se movió antes de “Practical implications”**: el flujo ahora es interpretación → comparación → implicaciones → limitaciones.
- Conclusiones divididas en dos párrafos: resultados y consecuencias/límites.

### 2.6 Tablas

- Tabla 1: “NAs imputed” → **“Missing values imputed”**; nota con SD, CV, P50/P99.
- Tabla 2: “Kendall W” → **“Kendall's W”**; abreviaturas (Block perm., ANOVA-RM, Sig.) movidas a una nota bajo la tabla; caption más corto y legible.
- Tabla 3: se mantuvo la matriz de decisión; se revisó el tono condicional.

### 2.7 Figuras

- **Figura 1 regenerada** con etiquetas “Missing values imputed” y “Values replaced (conservative)”, título de panel “Values modified per station”, mayor tamaño de fuente y formato PNG optimizado (2400 px, 285 KB).
- **Figura 2 regenerada** con fuentes mayores y leyenda WHO más clara (2400 px, 206 KB).
- **Figura 3 regenerada** con fuentes mayores y leyenda **“Block permutation”** (antes “Permutacao-blocos”), 2400 px, 238 KB.
- Las tres figuras cumplen ≤500 KB y 8.5–17 cm.
- **Leyendas de panel A movidas fuera del área de datos**: se corrigió la superposición con las series en Fig. 2A y Fig. 3A (y se aplicó el mismo criterio a Fig. 1A).
- Se añadieron `\FloatBarrier` después de los párrafos que presentan cada figura para que no se apilen ni caigan al final.

### 2.8 Referencias

- Biblioteca reordenada por **orden de primera cita** (IEEE).
- `\begin{thebibliography}{21}`.
- Eliminada `abramovich2004` (uso no sostenido).
- Añadidos DOI verificables a Daubechies (1992), Mallat (1989) y Nason (2008).
- 21 referencias, todas citadas; sin huérfanas.

### 2.9 Declaraciones y metadatos

- “Statistical analysis” → **“Formal analysis”** (CRediT).
- “Correspondence” → **“Corresponding author”**.
- Data Availability: URL del repositorio y release v1.0.0; DOI se añadirá al archivar.
- Se mantiene la línea de autor de correspondencia, sin pie de página.

---

## 3. Verificación

| Comprobación | Resultado |
|---|---|
| PDF | 12 pp |
| Figuras | pp. 6, 7 y 8, antes de la bibliografía |
| Tamaño de figuras | 285 / 238 / 206 KB |
| Abstract EN | 228 palabras |
| Referencias | 21, todas citadas |
| Citas indefinidas | 0 |
| Overfull >2 pt | 0 |
| Título ES | Presente |
| Palabras clave | 5 EN / 5 ES |

---

## 4. Lo que no se cambió (a propósito)

- Todos los valores numéricos, tests, escalas y conclusiones.
- La Base B como análisis principal y la sensibilidad A/B/C.
- Las afiliaciones y los ORCID: requieren confirmación humana; no se inventaron.
- El DOI de Zenodo: requiere cuenta/token; el manuscrito declara que se añadirá al archivar.

---

## 5. Recomendaciones residuales (post-editorial)

1. **Lectura nativa en inglés** por un editor de lenguaje, centrada en ritmo y concisión; el texto ya es correcto, pero una pasada humana de 1 h elevaría el acabado.
2. **Revisión del resumen en español** por un hispanohablante nativo, especialmente “superaciones” vs “excedencias” según la variante peruana.
3. **Confirmar afiliaciones y ORCID** antes de OJS.
4. **Añadir el DOI de Zenodo** cuando exista y recompilar.
5. **Revisar la prueba de similitud** (Turnitin/iThenticate) tras la reordenación de referencias.
6. **Comprobar el template REDIN** en OJS: tamaños de figura, caption y orden de declaraciones.

---

## 6. Archivos tocados

- `paper/article_REDIN.tex`
- `paper/article_REDIN.pdf`
- `paper/figures/figure_1.png`
- `paper/figures/figure_2.png`
- `paper/figures/figure_4.png`
- `analysis/03_inference_adaptive.py`
- `analysis/05_figures_tables.py`
- `paper/SUBMISSION_PACKAGE_REDIN.md`
- `paper/REDIN_CHANGE_LOG.md`
- `STATUS.md`
- `submission_REDIN/` y `submission_REDIN_2026-10-17.zip`
