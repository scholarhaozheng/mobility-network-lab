# Boston saved population/household allocation tables

These three released CSVs are the source statistics, source-to-H3 contribution crosswalk and H3 aggregate attributes used by the accepted Boston four-stage branch. They are **not** raw county API/geometry files or a new population estimate. Their fields, source versions, allocation formula, preserved raw snapshot hashes and limits are documented in the [public data card](../../../docs/datasets/boston-population-households.md) and [source registry](../../../catalog/boston-population-sources.json).

The matching [generation table](../behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv) and [outside-core spatial ledger](../behavior_feedback_r1_semantic_fix_r1/data/external_flow_ledger.csv) already exist in the public component. From the repository root, verify these saved relationships without a solver:

```powershell
python -B tools/population/verify_saved_allocation.py `
  --data-dir examples/boston/population_r1/data `
  --generation examples/boston/behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv `
  --ledger examples/boston/behavior_feedback_r1_semantic_fix_r1/data/external_flow_ledger.csv
```

This is a saved-arithmetic check, not a new ACS download, geometric overlay, trip-generation estimate or external-trip measurement.
