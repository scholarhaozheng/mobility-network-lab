# Render Central Boston public visuals from saved inputs

`render_boston_public_maps.py` is an optional image renderer, not a data-acquisition or modelling pipeline. It requires Python 3.10+ and Pillow. Viewing the already published images requires neither this script nor its inputs. Running it does not estimate demand, match GPS, execute assignment or download sources.

```sh
python -B tools/visuals/render_boston_public_maps.py --config tools/visuals/render_config.example.json --asset all
```

Replace the example config's `input_dir` and `output_dir` placeholders with explicit local directories first. The output must not overlap an input/source directory. `--input-dir` and `--output-dir` can override the config; `--asset` may select `hero`, `social`, `network`, `activity`, `gps`, `flow_s1` or `flow_delta` individually.

The renderer reads the following **exact filenames** from `input_dir`. A path named below is repository-relative or, for assignment outputs, relative to the extracted full public data ZIP. These are mappings, not a claim that all exact geometry snapshots ship in the repository.

| Input filename | Saved-data mapping / availability |
|---|---|
| `gmns_links.csv`, `zones.geojson`, `core.geojson`, `analysis.geojson` | Exact saved GMNS road and H3/boundary geometry snapshots from the bounded Boston build; not bundled as this renderer's ready-to-run input directory. The repository has related network CSVs and offline maps, but do not substitute them without checking fields, geometry and versions. |
| `parcel_geometries.csv`, `zone_activity_r9.csv` | Saved parcel geometry and selected MassGIS `RES_AREA` zone allocation from activity run `boston_activity_prior_r1_20260922`; the renderer snapshots are not bundled here. The project releases related activity-prior relations under `examples/boston/data/activity_prior_r1/`. |
| `corridor_link.csv` | `examples/boston/data/corridor_link.csv` (ordered member-link relation). |
| `gps_segment_quality.csv`, `gps_point_progress.csv`, `gps_path_links.csv` | Same-named saved derived relations under `examples/boston/data/`; these are not raw MBTA snapshots. |
| `s1_solution.csv`, `s2_solution.csv` | Rename/copy the saved solution CSVs from `assignment_outputs/S1_planned_service/` and `assignment_outputs/S2_exploratory_gps_overlay/` in the full `BOSTON_BEHAVIOR_FEEDBACK_PUBLIC_DATA_EN.zip` asset. Do not rerun FW. |
| `s1_run_summary.json`, `s2_run_summary.json` | Rename/copy each corresponding `run_summary.json` from those same two assignment-output directories. |

Use source-identical saved files when seeking a byte-faithful rerender. Missing optional geometry snapshots do not authorize new data collection or scientific reconstruction. The gallery's [source, license and unit note](../../docs/datasets/boston-visual-sources.md) explains what the existing images actually show.

Input coordinates are WGS84 longitude/latitude (`EPSG:4326`); the renderer transforms them in memory to WGS84 / UTM zone 19N (`EPSG:32619`) for metric display and scale bars. Reciprocal flow links are offset by 2.7 screen pixels for legibility, without altering network geometry. S1 and S2−S1 share a viewport. SVGs contain screen coordinates only and load no remote content. Retain the GMNS Plus Apache-2.0 notice and MassGIS / MassDOT / MBTA credits when reusing outputs.
