# Berkeley LR extended diagnostic

Extended LR diagnostic: 300 same-rule cold-start iterations; the original 1% gate is first met at iteration 10. Final best lower 43.66742440801, feasible upper 43.66742440801 PCE·min; certified gap 0.0000000% (bounds close within floating-point precision). The original accepted 10-iteration run remains historical evidence. Independent diagnostic audit passed; original formal-entry replay pending at this export.

The five displayed figure families share the selected receiver-approved run. The original 10-iteration figures, data and code remain in their historical asset folders.

From this asset directory, run `python -X utf8 renderers/render_all_figures.py`. This recreates all five figure families in `regenerated/` from the included `inputs/` files. Dependencies: Python, NumPy, Matplotlib, Pillow, Shapely and fontTools; the font helper embeds the selected serif font. All full input rows and plot sources are retained here. No solver is called during plotting.
