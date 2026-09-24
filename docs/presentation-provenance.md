# Framework and case presentation: source and layout notes

The root introduction is deliberately city-neutral. Its framework image is conceptual, not empirical. Boston and Sioux Falls start at explicitly named case sections, each with its scope and missing capabilities. Underlying code availability is not treated as evidence that a case ran it.

## Source identities

The Boston scalable handoff actually supplied in this review is **59,092,215 bytes**, SHA-256 `dc9a2908c0a9ce9a37755562d5d4db7854a3995295af9a25be5ee1567ccf8b29`. It includes `FIGURE_LAYOUT_REVISION.md` and 1,532 verified payload records. Its size/hash differs from the earlier completion message; no silent substitution was made. The included note records a map-layout-only revision, and the actual included `SCALE_RESULTS.csv` is the source of displayed status/values.

The supplied Sioux Phase-I handoff is SHA-256 `13019b0406093571f38171a722916d87b4689929d7c4a54d75cb4d28e8ca962e`. All 57 listed member checksums match. Its observations describe two saved runs, not experiments executed in this presentation task.

## Figure types

- `framework_overview`: city-neutral conceptual diagram. No empirical results.
- `boston_method_comparison`: composition of the five existing small-control PNGs. The shared scales, numeric legends and source data remain unchanged; empty margins and duplicate titles are removed. It is not the all-OD result.
- `sioux_space_time_construction`: schematic display of a real local time-network slice. Node IDs, arc endpoints/times and the selected XS170 path come from saved records. It omits the full source/sink horizon.
- `sioux_capacity_exchange`: saved before/after capacity accounting; no newly simulated counterfactual.
- `sioux_phase_i_pair`: layout-only combination of the two supplied phase traces. The individual PNG/SVG originals remain available.

[Exact display-source hashes](assets/presentation_r3/FIGURE_PROVENANCE.json) and [public display model](assets/presentation_r3/DISPLAY_MODEL.json) support reproduction with `python -B tools/visuals/render_presentation_r3.py`. Source figures and data keep their existing terms; a figure does not grant redistribution rights to an entire historical receiver archive. No raw GPS archive, official report cache, private solver log or unsent email is published by these display additions.

Run `python -B tools/build_case_presentation.py` after the normal complete documentation build. It reads the root README and the explicit case sources and updates the matched homepage. The original complete build can retain its other pages; it must not overwrite this homepage afterward with a stale hard-coded narrative.

No new FW, IPOPT, full-path, CG, pricing, SVD, mode estimation, GPS matching or external data collection ran during the redesign. Saved checks/CLI help were inspected separately from any claim of fresh scientific validation.
