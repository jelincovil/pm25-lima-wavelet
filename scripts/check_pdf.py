#!/usr/bin/env python3
"""Check manuscript layout: figure order, figure size, page count and image width."""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper" / "article_REDIN.pdf"
FIG_DIR = ROOT / "paper" / "figures"
FIGURES = ["figure_1.png", "figure_4.png", "figure_2.png"]
MAX_PAGES = 14
MIN_CM = 8.5
MAX_CM = 17.0
MAX_BYTES = 500 * 1024


def cm_from_pt(value: float) -> float:
    return value * 2.54 / 72.0


def main() -> int:
    errors: list[str] = []
    if not PDF.is_file():
        print(f"missing PDF: {PDF}")
        return 1

    for name in FIGURES:
        path = FIG_DIR / name
        if not path.is_file():
            errors.append(f"missing figure: {path.relative_to(ROOT)}")
            continue
        if path.stat().st_size > MAX_BYTES:
            errors.append(f"{name} exceeds 500 KB ({path.stat().st_size} bytes)")
        with Image.open(path) as im:
            if im.width < 1000 or im.height < 1000:
                errors.append(f"{name} is below 1000 px on at least one side")

    doc = pymupdf.open(PDF)
    pages = len(doc)
    if pages > MAX_PAGES:
        errors.append(f"PDF has {pages} pages (limit {MAX_PAGES})")

    ref_page = None
    for i, page in enumerate(doc):
        text = page.get_text()
        if "\nReferences\n" in text or text.strip().startswith("References"):
            ref_page = i
            break
    if ref_page is None:
        errors.append("could not locate the References heading")

    image_pages = []
    for i, page in enumerate(doc):
        images = page.get_images(full=True)
        if not images:
            continue
        image_pages.append(i)
        for image in images:
            for rect in page.get_image_rects(image[0]):
                width_cm = cm_from_pt(rect.width)
                if width_cm < MIN_CM or width_cm > MAX_CM:
                    errors.append(
                        f"page {i + 1}: figure width {width_cm:.1f} cm outside "
                        f"{MIN_CM}-{MAX_CM} cm"
                    )
        if ref_page is not None and i >= ref_page:
            errors.append(f"page {i + 1}: figure appears after the References heading")

    if not image_pages:
        errors.append("no figures found in the PDF")

    print(f"pages: {pages}")
    print(f"figure pages: {[p + 1 for p in image_pages]}")
    print(f"references page: {ref_page + 1 if ref_page is not None else 'not found'}")
    if errors:
        print("layout checks failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("layout checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
