SHELL := /bin/bash
PYTHON ?= python3

.PHONY: help setup test claims paper pdfcheck analysis verify all clean

help:
	@echo "Targets:"
	@echo "  setup     create .venv and install pinned dependencies"
	@echo "  test      run fast regression tests"
	@echo "  claims    check manuscript tokens against docs/NUMBER_REGISTRY.csv"
	@echo "  paper     compile paper/article_REDIN.pdf with pdflatex (twice)"
	@echo "  pdfcheck  verify figure order and file sizes"
	@echo "  analysis  run the full pipeline (N_PERM=9999; overwrites results/)"
	@echo "  verify    test + claims + pdfcheck (fast, uses committed artefacts)"
	@echo "  all       analysis + paper + verify"
	@echo "  clean     remove LaTeX build artefacts"

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

claims:
	$(PYTHON) scripts/check_claims.py

paper:
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error article_REDIN.tex && \
		pdflatex -interaction=nonstopmode -halt-on-error article_REDIN.tex

pdfcheck:
	$(PYTHON) scripts/check_pdf.py

analysis:
	$(PYTHON) analysis/00_setup_paths.py
	$(PYTHON) analysis/01_preprocess_agamaz.py
	$(PYTHON) analysis/02_wavelet_diagnostics.py
	$(PYTHON) analysis/03_inference_adaptive.py
	$(PYTHON) analysis/04_sensitivity.py
	$(PYTHON) analysis/05_figures_tables.py

verify: test claims pdfcheck

all: analysis paper verify

clean:
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.synctex.gz
