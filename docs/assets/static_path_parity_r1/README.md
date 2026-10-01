# Static finite-path / L3 paired presentation views

Section 03 rows 12 and 13 show two complementary figure types per city: a
saved physical-link distribution and a saved flow/reconstruction view on the
network. These figures are presentation derivatives, not new assignment runs.
The exact images, SHA-256 values, source records, and model-specific baselines
are listed in [FIGURE_PARITY_MAP.csv](FIGURE_PARITY_MAP.csv); each newly rendered
figure also has a `*.source.json` sidecar and an editable SVG.

Boston uses the 26-OD ABS_PLANNED reference and rank-26 native Diagnostic L3
records. The L3 difference is against the same finite-path reference. Sioux
Falls uses the supplied 24-node/76-directed-link topology in a **schematic**
layout; its row-12 B_BECKMANN link vector is a native candidate on the frozen
2,218-path representation, not an accepted full-network UE. Its row-13 L3
difference is the A_REG001 path-aggregate versus explicit-link residual, not
a comparison with FW. Hong Kong uses the accepted corrected-R2 26-OD H1
finite-path and rank-26 records. Its L3 difference is against its same-instance
H1 FW anchor. None of these local colour scales is comparable across cities.

The Hong Kong network derivatives omit the prior embedded bottom provenance
sentence; the claim boundary remains in the external case-page captions.
Original corrected-R2 PNG/SVG files and their hashes remain unchanged. The
private corrected-R2 H1 arrays and full path pool are not copied here.

Regeneration requires Python with NumPy, Matplotlib, Shapely, and NetworkX,
plus the locally retained accepted corrected-R2 H1 result directory:

```text
python -B tools/visuals/render_static_path_parity_r1.py --hk-h1 <local-accepted-H1-result-directory>
```

This reads saved results only; it does not call a solver, generate new paths,
or recalculate a basis.
