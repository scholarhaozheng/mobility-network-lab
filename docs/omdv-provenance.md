# OMDV provenance and integration boundary

The Open Mobility Data Visibility source repository was inspected at Git commit 09575a51973f4289fda7adae85130a10ab554b36. Its accepted R1.2.1 release evidence records final-release commit e0c7d2f7ca4e3f72563f14346d96df5f0c04e937.

## Accepted package identities

| Package | Role | SHA-256 | Included here |
|---|---|---|---|
| A | Complete code, no research data | a129bb01fd0a493ca6cfde8ed70512f3944fdd870fe198f840062102920a2693 | No |
| B | Downloadable reproduction package | 256b94d3c14bfc36ae61a210a2ab99b02f3bb054e48e0acc2ff84e805f30c19a | No |

The packages are identities for provenance. Neither archive is redistributed.

## What was integrated

- four selected original implementations: external-city normalization, exact
  municipality/country matching, MobilityDatabase-style catalog normalization
  and schema audit, and cleaned-catalog summaries;
- a thin MCL adapter and public local-file CLI;
- two controlled example fixtures;
- accepted aggregate city-frame, GTFS, realtime, OSM, and GBFS values;
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

The GTFS unique-content parser and realtime endpoint probe remain
`UPSTREAM_LINK_ONLY` / later-refactor items because they are coupled to
versioned caches and research orchestration. The OSM extractor, GBFS builder,
and source-layer registry are referenced but not shipped as executable APIs.
The H3 manuscript analysis remains private.

No OMDV figure was selected. Owner permission for original visual design is
confirmed, but no candidate completed a file-specific review of underlying
third-party data and basemap terms.

## Actual public operation

`tools/mcl_data.py catalog-city-match` processes user-supplied local CSV files.
It produces input-dependent normalized tables, exact city/country matches,
summary/audit tables, ambiguity records, and a quality report. It does not
download data, parse GTFS ZIPs, probe realtime endpoints, perform GPS matching,
or compile a city network.
