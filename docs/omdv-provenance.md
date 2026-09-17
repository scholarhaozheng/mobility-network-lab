# OMDV provenance and integration boundary

The Open Mobility Data Visibility source repository was inspected at Git commit 09575a51973f4289fda7adae85130a10ab554b36. Its accepted release evidence records final-release commit e0c7d2f7ca4e3f72563f14346d96df5f0c04e937. The same-name formal Package A/B files were verified as the later recorded R1.2.4 artifacts; they were not rebuilt.

## Accepted package identities

| Package | Role | SHA-256 | Included here |
|---|---|---|---|
| A | Complete code, no research data · 5,632,290 bytes · 1,173 members | c3e3a3c46a4126e110a6690b21f89e9b2853c0bbf13dedf996d8d2e57189a7bb | No |
| B | Downloadable reproduction package · 11,172,418 bytes · 1,222 members | 565f4edddeb528f2648b3a44e0edba1a1af9bd4eaf81387a31f8a104ad9e83fa | No |

The packages are identities for provenance. Neither archive is redistributed.

## What was integrated

- five selected original implementations: external-city normalization, exact
  municipality/country matching, MobilityDatabase-style catalog normalization
  and schema audit, cleaned-catalog summaries, and GTFS content metrics with a
  streamed stop-times pass;
- a thin MCL adapter and public local-file CLI;
- two controlled example fixtures;
- accepted aggregate city-frame, GTFS, realtime, OSM, and GBFS values;
- a non-geometric 11,422-city projection, all accepted content-city links, and
  explicit source-record/content/city relationships;
- exact source-table hashes and commit identities;
- layer-specific interpretation boundaries;
- a compact, independently authored interoperability catalog;
- tests for direct functions, the public CLI, perturbed inputs, ambiguity,
  unmatched cases, and cross-layer evidence boundaries.

## Selected-copy license scope

The source OMDV LICENSE.md remains an all-rights-reserved repository
placeholder. Hao Zheng separately authorized the selected original files used
here for MIT distribution in Mobility Computation Lab on 2026-09-17. This
file-specific permission does not relicense the complete research repository.

Each admitted file is recorded with its repository-relative source path, last
Git commit, source SHA-256, destination path, destination SHA-256, and
adaptation in
[the authorized-file allowlist](../catalog/omdv-authorized-files.json).
The root MIT license applies to these selected copies and MCL integration glue,
not to external data or unselected repository contents.

## Remaining upstream-only scope

The realtime endpoint probe remains upstream-only because it is coupled to
network access, credentials and versioned research orchestration. The OSM
extractor, GBFS builder and source-layer registry are referenced but not shipped
as executable APIs. The H3 manuscript analysis remains private.

No OMDV figure was selected. Owner permission for original visual design is
confirmed, but no candidate completed a file-specific review of underlying
third-party data and basemap terms.

## Actual public operation

`tools/mcl_data.py` has three bounded operations:

- `query-city` reads the bundled accepted city/relationship projections;
- `catalog-city-match` processes user-supplied local CSV files and writes
  input-dependent exact-match/audit outputs;
- `process-gtfs` inspects one user-supplied local GTFS ZIP with the authorized
  content parser.

None downloads data, probes realtime endpoints, performs GPS matching, compiles
a city road network, estimates OD demand or runs the optimization models.
