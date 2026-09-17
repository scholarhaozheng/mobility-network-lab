# Data licenses and publication boundaries

## Selected OMDV software and fixtures

Hao Zheng explicitly authorized four selected original OMDV implementations
and two bounded example fixtures for distribution in this repository under the
root MIT License. The exact source paths, commits, source hashes, destination
paths, destination hashes, and adaptations are recorded in
[the authorized-file allowlist](catalog/omdv-authorized-files.json).

This selected-copy authorization does not change the license of the complete
OMDV research repository. It does not cover third-party code, external data,
basemaps, coauthor material, or other rights the maintainer does not control.

The two `examples/data-tools/` CSV files are controlled fixtures used to test
schema normalization and exact matching. Their URLs use `example.com` and they
are not raw provider catalogs or bundled transit feeds.

## OMDV-derived aggregate evidence

The public evidence catalog also contains compact aggregate values re-expressed
from tracked accepted OMDV summaries. It does not contain source rows, raw
feeds, city geometries, endpoint lists, provider archives, or analytical source
tables. These summaries are provenance-bound factual aggregates and do not
grant a separate data license for absent source datasets. Consult
[OMDV provenance](docs/omdv-provenance.md).

## External source boundaries

| Source family | Included material | Excluded material |
|---|---|---|
| GHSL | Aggregate analytical-frame count | Geometry, attributes, or source download |
| MobilityDatabase / Transitland | Aggregate catalog-scenario values | Feed registry rows, endpoints, raw metadata |
| GTFS / GTFS-Realtime | Aggregate content and snapshot classifications | Feed archives, payloads, endpoint URLs |
| OpenStreetMap / Geofabrik | Aggregate bounded-sample evidence | PBF extracts, feature rows, cached downloads |
| GBFS | Aggregate registry summary | Registry rows, live system feeds |
| SEDAC and manuscript analyses | None | Raw or derived analytical tables and figures |

Every source retains its own terms. The root MIT license does not apply to external data.

## Bundled synthetic inputs

The following directories contain small synthetic regression fixtures created for this project:

- `app/cases/capacity_zone_probe/`
- `app/cases/external_auto_4node/`
- `examples/data-tools/` (selected controlled metadata examples)

They contain no observed trips, GPS traces, personal data, downloaded feed
payloads, or city network extract. They are distributed as original software
test materials under the root MIT License.

## Results-only benchmark records

The catalog contains documentation and summary metadata for three historical Sioux Falls experiments:

- `sioux-200od`
- `sioux-250od`
- `sioux-static-fw`

No historical road-network table, OD table, private reconstruction evidence or upstream dataset snapshot is included. These entries are results-only records and must not be used to infer a license for the absent source data. Obtain any source dataset independently and follow the provider's current license, citation and access terms.

## Derived benchmark figures

The PNG files under `docs/assets/benchmarks/` are project-authored summary visualizations generated from previously verified historical results. They may be redistributed as part of this repository's result documentation. They do not include or license the historical source tables, reconstructed raw flow CSVs, private evidence or upstream dataset snapshots.

The physical-link figures encode aggregate result summaries for the selected OD subsets. Their inclusion does not grant permission to redistribute the absent historical inputs or imply that a separately obtained Sioux Falls dataset is covered by the root software license.

## Data and evidence excluded from publication

The upload excludes generated local runs, private evidence, raw external data, local runtimes and machine-specific logs. In particular, none of the following are included:

- `results/` and `outputs/`
- `external_data/`, `private_data/` and `private_audit/`
- historical private Sioux Falls input tables or evidence volumes
- teacher or course materials
- GPS trajectories, observed OD data or transit feeds
- downloaded third-party repositories, packages, binaries or portable runtimes

## Adding data later

Every future dataset contribution must identify its provider, exact version or retrieval date, license or access terms, permitted redistribution scope, transformations and checksums. If redistribution rights are unknown, publish only a source link and reproducible acquisition instructions; do not copy the data into this repository.
