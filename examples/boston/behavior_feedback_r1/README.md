# Central Boston behavior-feedback pilot

This directory preserves the historical `behavior_feedback_r1` result. The [current semantic-fix component](../behavior_feedback_r1_semantic_fix_r1/README.md) corrects transit routing, fare handling, directed OD conversion and restoration testing. The numbers below belong only to the earlier run.

This public component is one bounded, real-data technical pilot. It combines ACS 2024 five-year block-group estimates, transferred CTPS TDM23.2.0 regional parameters, actual OSM walking/cycling ways, the archived MBTA Fall 2026 GTFS feed, pre-qualified MBTA vehicle observations, and the existing directed GMNS/FW implementation.

It is not a full TDM23 reproduction, a calibrated local behavior model, a representative Boston congestion run, or an independently validated forecast. The public CTPS report did not provide numeric nested-logit scale parameters or the full zonal inputs; the code therefore preserves the published tree, reports a `mu_transit` sensitivity grid, and labels the `mu=1` FW interface as a boundary diagnostic. The 2026-09-21 midday GPS overlay is disabled by default and does not validate the existing 07:00–09:00 AM configuration.

## Rebuild and query

From the repository root:

```powershell
python examples/boston/behavior_feedback_r1/build_public_database.py
python examples/boston/behavior_feedback_r1/query_behavior_feedback.py trace
python examples/boston/behavior_feedback_r1/query_behavior_feedback.py response
python examples/boston/behavior_feedback_r1/query_behavior_feedback.py unavailable
python examples/boston/behavior_feedback_r1/validate_public.py
```

The builder verifies manifest row counts, preserves identifier text, creates unique indexes and views, and runs SQLite integrity checking. See [SCHEMA.md](SCHEMA.md), [FEEDBACK_TRACE.md](FEEDBACK_TRACE.md), and [acceptance_queries.sql](queries/acceptance_queries.sql).

The executed upstream adapters are retained under `pipeline/`. They require the full local Boston source layout (including licensed/source archives that are not bundled) and accept `--root <boston-work-root>` where applicable. The public SQLite rebuild above is the clean-room path supported entirely by packaged files; it does not pretend to reacquire restricted or version-drifting sources.

## Executed scope

- 177 H3 r9 zones; 171,049.52 area-weighted ACS residents and 79,537.49 households.
- 816,054.67 transferred average-weekday person trips across six purposes. Attractions and gravity distribution remain documented proxies; external travel is unknown, not zero.
- 36 frozen HBW midday OD pairs and three departure instants, covering 1.4568% of the pilot HBW midday demand.
- 864 modal skim rows: real directed GMNS drive paths, OSM walk/bike paths, and time-dependent GTFS paths with access, waiting, in-vehicle, transfer and egress components.
- 13 exact-trip GPS stop-pair observations; all are same-sample exploratory evidence and the overlay is off by default.
- 78 OD-departure rows enter the conditional sensitivity; 30 incomplete-access rows remain in an explicit exclusion ledger with positive demand rather than being set to zero.
- Exactly two panel-only FW runs on an identical network. The S1/S2 input vehicle totals are 202.078384 and 202.033061; 87 link volumes change. These are model-internal responses with no background traffic.
- 23 targeted checks pass, including a leg-level time-account identity and a leading-zero SQLite fixture.

Third-party data remain governed by their source terms. The component contains derived/tabular evidence and a small true panel; source archives such as the MBTA GTFS ZIP and OSM extract are not silently relicensed here.
