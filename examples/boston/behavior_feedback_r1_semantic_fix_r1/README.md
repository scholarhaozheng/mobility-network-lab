# Central Boston: Four-Step Modeling and Transit Observation Feedback

Explore a compact Central Boston example that links GMNS-compatible roads and H3 zones with activity and household inputs, public transit services, and static traffic assignment. A fixed home-based-work panel demonstrates how an observation-based change in transit service can propagate through travel costs, mode shares, vehicle demand, and road flows.

[Quick start](#quick-start) · [Four-step workflow](#four-step-workflow) · [Feedback walkthrough](FEEDBACK_TRACE.md) · [Data dictionary](SCHEMA.md) · [Scope and assumptions](#scope-and-assumptions)

## What you can use

Rebuild a queryable SQLite database from the supplied CSV files. Inspect scenario-specific journeys and costs, trace model parameters to their sources, examine mode and vehicle-demand changes, and compare the saved road-assignment results. The package includes records of unavailable alternatives and excluded cases, alongside the results that enter the calculation.

The query database contains 26 data tables and one build-manifest table, two views, and 38,800 data records. Identifier fields remain text, including codes with leading zeros.

## Quick start

Use the current Boston component at:

```text
examples/boston/behavior_feedback_r1_semantic_fix_r1/
```

The commands below use Python's standard library. They rebuild and query the supplied results; they do not rerun traffic assignment, fit parameters, or retrieve new observations.

From the repository root:

```powershell
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/build_public_database.py
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/validate_public.py
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py trace
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py response
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py unavailable
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py transfers
python -B examples/boston/behavior_feedback_r1_semantic_fix_r1/query_behavior_feedback.py parameters
```

The builder reads `data/public_table_manifest.csv`, verifies the CSV hashes and row counts, and creates `boston_central_public.sqlite` beside the scripts. A prebuilt database is not required. It creates indexes and views and checks SQLite integrity.

With a standalone copy of this component, open its directory and run the same script names without the repository-relative prefix.

Keep the complete component layout when extracting a data download. Missing required CSVs are not replaced by a demonstration subset. The upstream scripts under `pipeline/` require the separately acquired Boston network, transit inputs, and authorized source data; this CSV-to-database workflow is not an internet-source acquisition pipeline.

## Four-step workflow

| Stage | Implemented calculation | Interpretation |
|---|---|---|
| Trip generation | Household estimates combined with transferred regional effective average rates by trip purpose | A regional-rate transfer, not an observed local trip total or a full TDM23 generation model |
| Trip distribution | Activity-based attraction weights, gravity balancing, and purpose/time-specific PA-to-directed-OD conversion | An explicitly bounded demand scenario with retained attraction and impedance assumptions |
| Mode choice | Multimodal journey costs and a nested response around regional baseline shares | OD-specific responses to service changes; the baseline shares are not independently estimated from each OD's absolute costs |
| Traffic assignment | Static Frank-Wolfe assignment of the selected private/occupied-vehicle demand on a common road network | A small conditional panel, without regional background traffic or complete assignment of every mode |

The generation layer produces approximately 816,054.67 person trips per modeled workday from household estimates and transferred effective average rates. That figure is not the amount assigned by this component. The feedback panel contains 36 fixed home-based-work OD pairs and three midday departure samples; 78 complete OD-time cases enter the conditional response calculation. The remaining cases and their person-demand weights are retained in the exclusion records.

## Transit observation feedback

The scenario chain is:

```text
Transit observation
    -> interval-specific service adjustment
    -> permitted transit itinerary and travel cost
    -> mode-share response
    -> person-to-vehicle conversion
    -> static road assignment
```

**S1** is the scheduled-service reference. **S2** applies the exploratory observation-based service overlay. **Srestore** disables that overlay and independently reconstructs the affected service-cost and demand calculations.

The overlay is disabled by default. Its 13 registered interval adjustments each use one observed event. Applying an adjustment to other services in the same declared scope is an exploratory assumption, not an independently validated prediction.

[Read the complete feedback walkthrough](FEEDBACK_TRACE.md) to follow an observation through its parameter, itinerary, mode response, vehicle demand, and link-flow records.

## Saved panel results

The table below describes the existing semantic-fix result set. It is not a new solve performed by the quick-start commands.

| Quantity | S1: scheduled service | S2: exploratory service adjustment |
|---|---:|---:|
| Assigned vehicle trips | 202.078384 | 202.070733 |
| Road-node demand pairs | 26 | 26 |
| Beckmann objective | 700.850087 | 700.814799 |

Seventy-eight road links have an absolute flow difference greater than `1e-10` vehicle trips. The maximum absolute difference is approximately `0.006603` vehicle trips. This is a model-internal response in the fixed panel, not a measured citywide effect or evidence of predictive improvement.

Saved-output checks covered costs, aggregate node balance, and a shortest-path gap at the saved flow. These checks do not constitute a separate complete per-OD path-flow decomposition certificate or an independent validation against observed road traffic.

## Explore the data

| Question | Public entry |
|---|---|
| How does a transit observation affect road flows? | `query_behavior_feedback.py trace` and [FEEDBACK_TRACE.md](FEEDBACK_TRACE.md) |
| How does the representative OD respond? | `query_behavior_feedback.py response` |
| Which alternatives cannot be evaluated or are unavailable? | `query_behavior_feedback.py unavailable` |
| Which transit journeys include transfers? | `query_behavior_feedback.py transfers` |
| Where do the parameters come from? | `query_behavior_feedback.py parameters` |
| What does each table mean? | [SCHEMA.md](SCHEMA.md) |
| Which source records are registered? | [data/source_registry.csv](data/source_registry.csv) |
| Which scenarios and exclusions are represented? | [data/feedback_scenario_registry.csv](data/feedback_scenario_registry.csv) and [data/mode_choice_exclusions.csv](data/mode_choice_exclusions.csv) |

## Scope and assumptions

This example supports reproducible inspection of a limited four-step workflow and an exploratory transit-feedback calculation. It is not an official CTPS forecast, a complete TDM23 reproduction, or a calibrated citywide multimodal model.

The baseline uses common regional shares. The reported assignment follows the `mu_transit=1` sensitivity branch; unavailable official nest scales are not fabricated. Attraction weights, impedance parameters, external traffic, and the panel's discrete departure weights retain their documented limitations.

Only private and occupied ride-service vehicle movements represented by this panel are loaded onto roads. Empty ride-service repositioning is unknown and excluded, not assumed to be zero; transit-auto access legs are not assigned. The saved capacity interpretation remains an explicit engineering assumption where the original Boston generator's basis has not been independently established.

The observation overlay is retrospective and uses limited midday evidence. It does not estimate all passenger OD, calibrate automobile congestion parameters, or establish independent morning-peak performance. The restoration scenario verifies a computational dependency; it is not an empirical validation experiment.

## Data sources and reuse

Use the registered source and parameter records to identify the contributing network, household, activity, transit, and regional-model materials. Preserve their individual attribution and reuse conditions. A code license does not replace data-source terms.

This public component does not require private review archives, unpublished correspondence, or local copies of third-party reports. Additional source inputs needed for a complete upstream rebuild must be obtained and used under their respective permissions.
