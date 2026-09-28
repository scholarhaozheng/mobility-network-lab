# Three-city R2 presentation: saved-data build contract

This directory contains presentation-only outputs. It does not contain a scientific solver, a newly estimated demand model, or observed traffic inferred from a generated column.

## Repeatable inputs and commands

Run from the repository root with a Python installation that has the documented project dependencies:

```bash
python -B tools/visuals/build_three_city_tables.py
python -B tools/visuals/build_three_city_readable_tables_r2.py
python -B tools/visuals/render_three_city_parallel_r2.py
python -B tools/build_site.py
python -B tools/visuals/check_three_city_parallel_presentation.py
python -B tools/visuals/check_three_city_parallel_r2.py
python -B tools/check_repository.py
python -B tools/check_readme_pages.py
```

The first table builder reads frozen city/result records and retains the machine-readable `docs/data/three_city_r1/*.csv` field names. The R2 table builder reads those CSVs and writes four-instance, metric-row Markdown to `docs/data/three_city_r2/`; it does not change their numerical fields. The R2 figure builder reads the small, shipped `data/*_construction_edges.csv` cutaways and already accepted public plot inputs. It writes twelve SVG/PNG families with per-figure source hashes. The site builder derives its public homepage and case HTML from the checked-in Markdown; it has no dependency on an unshipped `../prior_public_sources` file. The R1 one-off `compose_three_city_readme.py` and `compose_three_city_cases.py` are not maintained public builders and are not shipped in this R2 overlay.

Each A-construction edge table records literal arc ID, endpoint state IDs, time indices, arc type and original physical-link ID (if any). Its `evidence_record_sha256` is the frozen dynamic-arc source hash used for the extraction. Boston's selected path arcs are independently present in the public B07 construction-path table; Hong Kong's cutaway arcs can be checked against the public frozen dynamic graph; Sioux's selected/allowed display IDs are identified in the public `presentation_r3/FIGURE_PROVENANCE.json`. The exact extraction audit was performed against accepted read-only saved records; the full Boston/Sioux dynamic graphs are not copied into this presentation package.

All figure panels are model-output illustrations. Original physical links, time-indexed movement arcs, waiting arcs, and nonphysical source/sink/zone/turn connectors remain different objects. Hong Kong's original road intersections differ from its turn-expanded routing states; `data/hong_kong_physical_to_routing_crosswalk.csv` records the two selected physical-road examples. Sink-horizon connectors are bookkeeping, not extra inferred physical waiting. For Sioux, a model time index is shown without inventing an unpublished duration in seconds.

## Publication boundary

The owner has now explicitly approved public disclosure of the **exact HK10 / ORACLE_R1_HK10_K1 model-generated 77-arc excerpt**, its CSV, corresponding R1/R2 B/D figures, captions and necessary provenance. The original `DISCLOSURE_STATUS_R2.json` remains as the historical pending-decision record; the [current file-level approval and hash allowlist](HK10_DISCLOSURE_APPROVAL_CURRENT.json) controls this disclosure. Shared pages and renderers are dependencies, **not blanket authorization for any other data in those files**. The accepted R5 aggregate CG result is separate; no provider trajectories, original observations, full path pool, dual/state arrays or scientific model runtime bundle are included here. This approval does not itself authorize a commit or push in this task.

The D-family chart uses the saved Boston round-1 B07/B09/B10 deltas and the saved Sioux XS170/XS169 exchange, with category and signed-value labels. Sioux panels c/e display only the 200-OD saved traces; the 250-OD figures remain separately linked in its case page. The D footer states panel-specific instance scope, and an unreported positive-flow count is not rendered as a number.
