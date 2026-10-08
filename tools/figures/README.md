# Saved-result figure rendering

The current figure contract is `docs/assets/figure-contract-r12/FIGURE_TEMPLATE.md`; machine-readable defaults are in `FIGURE_STYLE_CONTRACT.json`. The shared Python renderer is `style.py`. It writes a serif city/title header, PNG at 300 dpi, editable SVG with embedded fonts, PDF, source hashes and a caption. The script never invokes an optimizer.

## Separate responsibilities

- `algorithms/`, `app/`, `examples/` and the existing computational entry points own scientific computation.
- `experiments/catalog.json` and `experiments/inventory.json` bind the historical computational recipes and recorded identities. Do not change these to make a presentation edit appear to be a new successful run.
- `tools/figures/` owns rendering from saved public plot data and traceable vector layout derivatives. `recipes/` contains adapted pure saved-result plotters, accessed through the bounded wrapper; run the wrapper rather than importing arbitrary legacy entry points.
- `docs/assets/figure-contract-r12/` contains the current template, reader explanation, numerical tables and figure derivatives. Original released assets remain at their original paths.

## Re-rendering

From the repository root with Python, NumPy, Matplotlib, Pillow, fontTools and Shapely installed:

```powershell
python -B tools/figures/render_berkeley_saved.py --output regenerated/berkeley
python -B tools/figures/render_gap_progress.py --help
python -B tools/figures/render_city_foundations.py --help
```

Inspect each script's declared public input paths and CLI before running. Scripts needing local archived inputs must state that limitation; a visible plot is not proof that all source geometry or licensed inputs can be redistributed. The vector-transform route preserves original scientific coordinates and data marks and must be labelled as such.

## Renderer input matrix

“Bundled public saved” means the named source files are already in this checkout. “Local archived” means the script also needs separately retained local inputs; these inputs are not supplied by the public checkout or webpage ZIP. No renderer starts a new experiment or acquires missing data.

| Entry point | Input boundary | Exact saved inputs and limitations |
| --- | --- | --- |
| `render_gap_progress.py` | Bundled public saved | Reads hash-bound aggregates under `docs/assets/gap-20261008/` and the released Chicago ADMM history under `docs/assets/algorithm-transfer-r8/`. It joins the saved ADMM histories only after checking their shared state. No private inputs. |
| `render_berkeley_saved.py` | Bundled public saved | Reads Berkeley CSV/JSON and geometry under `docs/assets/berkeley-atlas-r2/data/`, `docs/assets/berkeley-lr-r6/`, and `docs/assets/six-city-r3-1/berkeley/`. Calls the five adapted `recipes/render_*.py` modules through its bounded adapter; use this wrapper instead of running those recipes directly. |
| `render_city_foundations.py` | Local archived plus bundled public records | `--project-root` must contain the separately retained `work/six_city_preflight_r1/cities/` tree and the other archived paths named by the frozen `city-alignment-r3` source records. Those records supply exact hashes; the script verifies them before reading zones, road geometry, transit inputs and saved four-stage outputs. They are **not** all included in the public checkout. Select cities with `--cities`; write to a staging directory with `--output-dir`. Requires pandas and pyproj in addition to the plotting dependencies above. |
| `render_keep_repairs.py` | Bundled public saved; one local archived check for the full run | The five FW map/histogram repairs, Ann Arbor transit repair and Chicago pricing repair read complete public plot-data records under `docs/assets/plot-semantics-r9/` and `docs/assets/city-alignment-r3/`. The UC S72 finite repair also verifies the frozen independent-check member in the separately retained `MCL_C02_Urbana_Algorithm_Transfer_R2_Private_Full.zip` under `--project-root`; this archive is **not** bundled. `--only chicago-pricing` needs only public saved inputs. Requires pyproj and Shapely. |
| `legacy_saved_figures.py` | Bundled public saved or vector-only, selected per manifest entry | Reads `legacy_manifest.json`: public-data entries replot exact saved records; vector-only entries preserve released SVG scientific geometry and apply an outer layout translation and new header. Original outlined labels remain outlines. This is not a raw-data reconstruction of vector-only entries. SVG/PDF conversion also requires svglib, ReportLab and Poppler; see `LEGACY_RENDERING.md`. |
| `project_structure.py` | Bundled presentation definitions | Draws the project-structure diagram from its declared labels, city order and links using `style.py`; it reads no private scientific dataset. Its default output is the current `docs/assets/figure-contract-r12/project-structure/` directory. |
| `style.py`, `embed_serif_fonts.py`, `svg_to_pdf.py` | Rendering helpers | Apply the shared style, embed local font files, or convert a supplied SVG. They do not supply missing experiment inputs or establish numerical acceptance. |

Local archived inputs remain outside the public rendering bundle. Source records retain their hashes or opaque identities; do not copy private inputs into the checkout to make a command appear self-contained. Missing required inputs should stop that renderer, while already generated figures and public source records remain viewable.

## Review before replacing a current figure

1. Fix city, model instance, quantity, unit, state count and the one-sentence conclusion.
2. Verify every input hash; preserve missing values, negative signed gaps and failed stopping gates.
3. Plot every available saved state, including a single point or two real states. State the axis identity; never manufacture intermediate samples or connect method categories as an iteration history. Own-method physical maps remain primary.
4. Use the common style, then inspect the final PNG and editable SVG: top alignment, scientific scales, panel labels, readable legends and no clipped text.
5. Record source/output hashes and the rendering route. Connect the same current asset and table to the homepage and its city-volume anchor. Preserve original scientific bytes in the local archive. Failed attempts are excluded from current reader pages; successful histories retain their early unconverged states.

## Publication boundary

Documentation and computational recipe releases are independent. The preserved computational archive contains 1,106 members and belongs to its recorded historical release; it is not a new-city one-click computation package. Its member hashes remain valid, while a comparison to the live presentation checkout can legitimately differ. Publish no fresh computational PASS from a plotting run. This R11 work is local only; no commit, push or deployment is included.

## R12 saved-data plots

`render_static_r12.py`, `render_short_dynamic_r12.py`, `render_mixed_r12.py` and `render_input_supplement_r12.py` restore graphical presentation from approved saved data. Single-state and two-state figures are allowed. The last script explicitly labels its vector-transform route for the 51-record source plot whose raw row CSV is not public. No solver is invoked.
