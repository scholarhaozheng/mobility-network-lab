# Central Boston demand and transit feedback

The current [Central Boston example](boston-central.md) connects GMNS-compatible roads and H3 zones with household and activity inputs, a four-step demand workflow, transit service observations, and static road assignment. Its public CSVs rebuild a queryable SQLite database; the upstream research inputs are documented separately.

[Open the current component](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/README.md) · [Follow one observation to a road flow](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md) · [Explore the data dictionary](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/SCHEMA.md)

## Four-step workflow

1. **Trip generation:** area-weighted ACS household estimates and transferred CTPS TDM23.2.0 effective average rates produce approximately 816,054.67 modeled daily person trips. This is a generation result, not the panel's assigned traffic.
2. **Trip distribution:** activity-based attraction proxies and a gravity/IPF calculation produce a production-attraction matrix. Purpose and time factors convert it to directed OD. External traffic remains unknown and is not loaded.
3. **Mode choice:** scheduled and observation-adjusted transit journeys enter a nested response around regional baseline mode shares. These shares are not estimated separately from each OD's absolute costs. Official numerical nest scales are unavailable; the reported assignment uses the declared `mu_transit=1` sensitivity branch.
4. **Traffic assignment:** selected private and occupied ride-service vehicles enter the existing static Frank-Wolfe solver on the same road network. The result is a conditional panel calculation without regional background traffic.

The fixed panel has 36 home-based-work OD pairs at three midday departure times. Seventy-eight complete OD-time cases enter the response; exclusions and their person-demand weights remain in the public records. Thirteen registered service-interval adjustments each derive from one observed event. They are disabled by default and have no independent morning-peak validation.

## Inspect the saved scenarios

S1 is scheduled service. S2 applies the exploratory transit observation overlay. Srestore independently turns it off and recomputes the affected itinerary, cost, probability and demand calculations. This checks the computational connection to the service input.

| Saved result | S1 | S2 |
|---|---:|---:|
| Assigned vehicle trips | 202.0783842283045 | 202.07073267183475 |
| Road-node demand pairs | 26 | 26 |

Seventy-eight links change by more than `1e-10` vehicle trips. The maximum absolute link-flow change is about `0.006602639856733816`. These are panel-only model responses, not measured citywide traffic effects. The [feedback walkthrough](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md) gives the source observation, selected itinerary, mode response, vehicle conversion and one aggregate road-link result.

From the repository root, rebuild and inspect the saved data:

```bash
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/build_public_database.py
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/validate_public.py
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py trace
```

The component provides 26 CSV data tables, one build-manifest table, two views and 38,800 data records. These commands reconstruct and query the supplied derived results. They do not acquire all source data or rerun the model.

For one command that rebuilds the same query database and exports five saved queries, follow the [saved-result example guide](../../examples/boston/SAVED_EXAMPLE.md):

```bash
python -B examples/boston/run_saved_example.py --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" --output "results/boston_saved_example"
```

Here `--data-dir` is the compact component included in the checkout. If using the separately downloaded full public data ZIP, extract it first and instead point `--data-dir` at its `public_component/` subdirectory; keep the trusted builder and query code beside `run_saved_example.py` in the checkout. This inspects saved outputs only and does not rerun demand, matching, mode choice or assignment.

## Model scope and data reuse

The household rates are a regional transfer, attraction weights and impedance include declared assumptions, and the GPS overlay is a same-sample midday sensitivity. Empty ride-service repositioning is unknown and excluded; transit-auto access legs are not assigned. The results do not imply CTPS endorsement, a complete TDM23 reproduction, a calibrated full-city model or independently validated prediction.

Source and parameter registers accompany the data. The project code license does not replace the individual network, ACS, MassGIS, MBTA, OSM and regional-report terms. The public package omits private receiver archives, correspondence and raw transit feeds.
