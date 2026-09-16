# Data licenses and publication boundaries

## Bundled synthetic inputs

The following directories contain small synthetic regression fixtures created for this project:

- `app/cases/capacity_zone_probe/`
- `app/cases/external_auto_4node/`

They contain no observed trips, GPS traces, personal data or city network extract. They are distributed as original software test materials under the root MIT License.

## Results-only benchmark records

The catalog contains documentation and summary metadata for three historical Sioux Falls experiments:

- `sioux-200od`
- `sioux-250od`
- `sioux-static-fw`

No historical road-network table, OD table, private reconstruction evidence or upstream dataset snapshot is included. These entries are results-only records and must not be used to infer a license for the absent source data. Obtain any source dataset independently and follow the provider's current license, citation and access terms.

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
