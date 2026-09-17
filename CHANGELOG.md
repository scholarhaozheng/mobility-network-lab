# Changelog

## 2.0.0 candidate — 2026-09-17

- Renamed the public product to Mobility Computation Lab.
- Added a compact, non-additive open-mobility evidence catalog with current accepted OMDV values.
- Added an authorized executable OMDV subset: catalog normalization, schema
  auditing, city-table standardization, exact city/country matching, catalog
  summaries, and an input-dependent quality report.
- Added a public `mcl_data.py catalog-city-match` command, controlled fixtures,
  isolated data-tool dependencies, direct/CLI tests, and a selected-file MIT
  allowlist with source and destination hashes.
- Retained exact OMDV source, package, commit, and SHA-256 provenance without
  copying raw research data.
- Added a four-layer architecture, interoperability catalog, publication gate, and evidence tests.
- Preserved the existing external-network workflow, static Frank–Wolfe code, solver-free verifier, and verified 200-OD / 250-OD benchmark records.

## Source and documentation assembly

- English public README, data catalog, user documentation and static project website.
- User-facing source entry point for input validation, finite-network runs and saved-result verification.
- Selected numerical source retained from GMNS-CG 0.3.0-rc5 with per-file hashes.
- Two runnable synthetic reference inputs, separate from the road benchmark result catalog.
- Data-access notices and extension metadata for new network contributions.

The existing Windows engine ZIP is an independent artifact. This source/documentation assembly does not silently replace or re-tag it.
