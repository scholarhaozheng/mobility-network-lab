# Saved legacy figure presentation

`legacy_saved_figures.py` reads only unchanged released SVGs and public saved plot data. It imports no experiment entry point, model builder, downloader or solver.

Run from the repository root with Python containing Matplotlib, NumPy, Pillow, fontTools, svglib and ReportLab, and Poppler `pdftoppm` on PATH:

```text
python tools/figures/legacy_saved_figures.py --output output/legacy
```

`--indices 15,36` limits a presentation-only run. `--manifest` selects another manifest with public repository-relative sources and exact SHA-256 bindings. `--pdf-python`, `--pdf-package-dir` and `--pdftoppm` select an existing local rendering runtime; they do not change scientific data.

The manifest contains 24 assets: six public-data replots and eighteen vector layout derivatives. Each asset produces SVG, PDF, a 300 dpi PNG, a `.source.json` record and a figure caption. Original assets are never overwritten.

For the vector route, figure-level city/title/prose is placed by the shared `style.py`; scientific axes, data marks, maps, scales, legends and numeric labels retain their original geometry. An outer translation crops unused canvas. Original long notes are recorded verbatim in `removed_figure_text` and relevant explanation is moved to the caption. Rights notices belong to each page's shared notice, while complete original provenance remains in the source record.

New city and title labels are editable SVG text with embedded DejaVu Serif webfonts and TrueType PDF fonts. Original outlined legacy labels remain outlines where the release supplied only glyph paths; `all_labels_editable` is false in those records. Do not claim such assets are raw-data replots or wholly editable text. Existing body colors and projection geometry remain the approved source's values. The PDF adapter expands SVG `use` references without changing their geometry and registers the exact serif font files, preventing missing numeric glyphs or font fallback.

The two ADMM final-state heatmaps remain final spatial states, with the original four-commodity by 35-node values, color floor and stopping gate. They are not iteration-history heatmaps. The old Chicago pure-LR run retains all 759 records and has no own feasible upper bound or certified gap; the later accepted hybrid is separate evidence. Compressed Native rank 26/52 remains a diagnostic failure, distinct from the later uncompressed accepted case.
