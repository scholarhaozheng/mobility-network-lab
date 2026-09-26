# Data licenses and publication boundaries

## Static Algorithm B selected derived evidence

The accepted classic Sioux and Central Boston B1 aggregate physical-link flows, evaluation JSONs and eight figures under [`algorithms/origin_based_algorithm_b/`](algorithms/origin_based_algorithm_b/README.md) are selected derived public candidates, not redistributed raw benchmark or Boston input tables. Boston geography traces to GMNS Plus `21_Boston`, Apache-2.0, commit `116447ab641cca1ed34797d019c8e704063393c3`. Its B1 demand is a modeled conditional HBW-midday cohort rather than observed citywide traffic. Native executables, upstream source trees, original demand tables, private logs and path-level run archives are excluded. The project MIT notice covers original adapter/evaluator code only; upstream TAPLab and tap-b retain their own MIT terms.

## Hong Kong bounded GMNS/data pilot

The compact official-derived pilot tables and figures under `examples/hong-kong/gmns_pilot_r1/` retain Hong Kong SAR Government, DATA.GOV.HK, CSDI, Transport Department, Census and Statistics Department and Lands Department attribution. [Exact source/download records](examples/hong-kong/gmns_pilot_r1/SOURCE_REGISTER.csv), [attribution](examples/hong-kong/gmns_pilot_r1/ATTRIBUTION.md) and [rights review](examples/hong-kong/gmns_pilot_r1/RIGHTS_AND_REDISTRIBUTION_REPORT.md) govern reuse. Provider archives are absent. The UrbanNav reference trajectory and all point-level derivatives remain private pending exact-file rights confirmation. The root MIT software license does not relicense these third-party datasets.

## Distributed-method benchmark evidence

The selected public Sioux Lagrangian R2, earlier ADMM R1, and cross-city ADMM R2_S source, authored fixtures, summaries and figures are bounded algorithmic evidence. The ADMM R2 Sioux maps are project-authored schematic derivatives of already-public topology; Sioux per-link numerical comparison CSVs are excluded. The 125-row Boston ADMM/LP physical-link comparison table and its derived figures are released under the user's explicit approval, joined only to previously public GMNS Plus `21_Boston` identifiers and geometry, with Apache-2.0 attribution retained. Private dynamic arcs, demand, raw reference flows, full state arrays, run logs and handoff archives are excluded. No historical Sioux raw input table or upstream provider archive is copied. Existing benchmark-data rights caveats below continue to apply. [ADMM R2 scope and provenance](docs/methods/admm-space-time.md).

## Selected OMDV software and fixtures

Hao Zheng explicitly authorized five selected original OMDV implementations
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

## OMDV-derived public result projections

The public evidence area contains compact aggregate values plus selected,
non-geometric fields from accepted OMDV result tables:

- all 11,422 accepted city-frame rows with identifiers, labels, country codes,
  accepted population values and selected catalog/GTFS/realtime states;
- all 12,442 accepted content-hash/city links;
- 14,328 accepted source-record/content/city relations, with explicit rows for
  source/content records that have no accepted city link.

The projection does not contain raw feeds, city geometry, coordinates, endpoint
or provider URLs, credentials, source archives, SEDAC fields or manuscript
tables. Field-level lineage and exact source hashes are documented in
[open-data sources](docs/open-data-sources.md) and the machine-readable schemas.
Blank source values remain blank; unmatched and no-evidence states are not
converted into a claim that transport data do not exist.

These outputs do not grant a separate license for absent source datasets. The
root MIT License applies to project software and selected authorized original
OMDV code, not automatically to upstream data fields. GHSL-origin fields remain
subject to the European Commission reuse terms referenced by the source
manifest; GTFS/catalog source providers retain their own terms.

## External source boundaries

| Source family | Included material | Excluded material |
|---|---|---|
| GHSL | Selected non-geometric city-frame identifiers, labels, country codes, accepted population values and aggregate count | Geometry, coordinates, source archive |
| MobilityDatabase / Transitland | Selected source registry/record IDs, content hashes and accepted catalog states | Provider URLs, endpoint URLs, raw provider metadata |
| GTFS / GTFS-Realtime | Accepted content/city relationships, counts and historical snapshot classifications | Feed archives, payloads, credentials, live endpoint state |
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
