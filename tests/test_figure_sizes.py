from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ["figure_1.png", "figure_4.png", "figure_2.png"]


def test_paper_figures_exist_and_are_small_enough():
    for name in FIGURES:
        path = ROOT / "paper/figures" / name
        assert path.is_file(), f"missing figure: {name}"
        assert path.stat().st_size <= 500 * 1024, f"{name} exceeds 500 KB"
        with Image.open(path) as im:
            assert im.width >= 1000 and im.height >= 1000
            assert im.mode in {"RGB", "RGBA", "L", "P"}


def test_no_stale_figure_copies_outside_figures_dir():
    paper = ROOT / "paper"
    for name in FIGURES:
        assert not (paper / name).exists(), f"stale duplicate at paper/{name}"
