# Central Boston: the four stages and the GPS feedback

**Follow a saved calculation from household and activity data to road flows.** The four numbered sections show distinct model stages; the separate observation section shows where GPS enters. All figures below read accepted saved results. No new demand estimation, matching, mode calculation or assignment was run to prepare these pages.

[01 Generation](#step-1-trip-generation) · [02 Distribution](#step-2-trip-distribution) · [03 Mode choice](#step-3-mode-choice) · [04 Assignment](#step-4-traffic-assignment) · [GPS feedback](#gps-feedback) · [Run the saved example](#run-the-saved-example)

## Shared foundation, different scopes

[The real-city network](boston-central.md) has 2,852 physical nodes, 5,091 directed roads, 177 H3 r9 zones and nine r7 parents. Zone access, transit, observations and results retain their source IDs and link to this common network. Model access connections are not automatically verified physical paths.

| Scope | What it contains | What it does not mean |
|---|---|---|
| Regional generation | Six transferred purpose totals, approximately 816,054.67 person trips per modeled workday | A measured trip total or the amount assigned in this example |
| Regional distribution | Saved purpose/time-specific PA and directed OD; the illustrated HBW midday total is 22,807.22 person trips | That every trip is included in the downstream panel |
| Fixed feedback panel | 36 HBW OD pairs and three departure samples; 78 eligible OD–time cases | A random population sample or a whole-region assignment |
| Road assignment | S1/S2 private and occupied ride-service inputs, approximately 202 vehicle trips each | Regional background traffic or complete allocation of all modes |

Thirty incomplete panel cases retain 78.079907 person trips in the exclusion ledger. The panel's three departure samples use declared engineering weights, not an observed continuous departure profile.

<a id="step-1-trip-generation"></a>
## 01 · Trip Generation

### How many trips are produced and attracted?

**Input.** Area-allocated ACS household estimates; CTPS TDM23.2.0 effective regional mean rates by purpose; MassGIS nonresidential/mixed assessment activity for attraction weights.

**Calculation.** For each purpose, multiply each zone's estimated households by the corresponding transferred effective mean rate. The saved area allocation yields about **79,537.49 households**. The six rounded report rates sum to **10.26**, yielding approximately **816,054.67 person trips per modeled workday**. The rates are regional summary transfers, not the complete segmented TDM23 generation model.

**Output.** Zonal, purpose-specific productions and attraction margins in [trip_generation_by_purpose.csv](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv). The chart sums the saved production column across zones for each original purpose code; it does not rerun the model.

![01 Trip generation: saved daily productions by six source purpose codes](../assets/boston/four_step_results_r1/step1_generation.png)

[Download the six plotted totals](../assets/boston/four_step_results_r1/data/generation_by_purpose.csv) · [Chart provenance](boston-four-step-sources.md)

The [residential assessment map](boston-central.md#residential-assessment-area-activity-prior) is an **activity input** from the earlier 50,000-person-trip prior. It is not the current generation result or an observed population/trip map. That earlier scenario remains available as a separate baseline.

<a id="step-2-trip-distribution"></a>
## 02 · Trip Distribution

### Where do those trips go?

**Input.** Purpose-specific productions, activity-based attraction weights and the existing zone-to-zone free-flow impedance.

**Calculation.** Gravity/IPF balances the PA matrix. Registered purpose/time factors convert PA into directed OD, including reverse-direction support. The retained friction factor is `exp(-0.08 × time_in_minutes)`; the coefficient remains an engineering assumption. The core is treated as a bounded scenario: outside travel has not been estimated or loaded.

**Output.** The full accepted data asset contains `derived/regional_od_h3.csv`. The chart extracts its **HBW midday** field only, retaining all 177 origin and destination IDs in stable order. Exported cells sum to **22,807.216914 person trips**.

![02 Trip distribution: 177 by 177 saved HBW midday OD values](../assets/boston/four_step_results_r1/step2_distribution.png)

[Download the plotted matrix](../assets/boston/four_step_results_r1/data/hbw_midday_matrix.csv) · [Index-to-H3 table](../assets/boston/four_step_results_r1/data/zone_order.csv)

Color uses `log(1+x)` to expose the spread while the colorbar is labeled in original person-trip units. Blank cells have no exported record; they are not silently treated as observed zeros. This is **modeled demand**, not a GPS-derived passenger OD or a map of traveled paths.

**Selection into later stages.** [validation_panel.csv](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/validation_panel.csv) records the fixed 36 HBW OD pairs. [regional_od_panel_sample.csv](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/regional_od_panel_sample.csv) links those pairs to the regional demand. Only this selected panel, with its declared departure weights and exclusions, proceeds to the feedback calculation.

<a id="step-3-mode-choice"></a>
## 03 · Mode Choice

### How does the service alternative change mode demand?

**Input.** The same panel person-demand weights; scheduled/adjusted itineraries and costs; the registered regional base shares, utility-change coefficients and nested response definition.

**Calculation.** S1 copies regional baseline shares. S2 uses the actual OD-specific service-cost change in a nested pivot response. The release includes multiple declared nest-scale sensitivity branches; the saved FW comparison uses **μ_transit = 1**. This does not estimate an absolute-cost S1 baseline separately for each OD.

**Output.** [od_multimodal_skims.csv](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/od_multimodal_skims.csv) records journey costs and availability; [od_mode_probabilities.csv](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/od_mode_probabilities.csv) records probabilities. The example chart includes all nine source leaves and plots **percentage-point changes**, not relative percentages.

![03 Mode choice: S2 minus S1 response for panel_od_019 at 12:30](../assets/boston/four_step_results_r1/step3_mode_response.png)

[Download the plotted S1/S2 probabilities](../assets/boston/four_step_results_r1/data/selected_mode_response.csv)

For `panel_od_019` at `12:30`, walk-access transit changes from **4.0990% to 4.2246%**, an increase of **0.1256 percentage points**. Unknown alternatives remain explicit. Auto-access transit legs are not assigned; ride service represents occupied movements, with empty repositioning unknown. A zero school-bus response in this panel is a saved model value, not a statement about service availability across Boston.

<a id="step-4-traffic-assignment"></a>
## 04 · Traffic Assignment

### Which roads carry the resulting vehicles?

**Input.** Eligible panel person trips are converted to vehicles under the registered occupancy/loading rules. Both scenarios use the same directed network, effective-capacity interpretation and static Frank–Wolfe implementation.

**Calculation.** The existing static solver distributes private and occupied ride-service demand. This Boston panel does not run the project's separate space–time CG engine, and it does not allocate every mode's passengers to their full network.

| Saved panel result | S1 · planned service | S2 · exploratory adjustment |
|---|---:|---:|
| Vehicle trips | 202.078384 | 202.070733 |
| Road-node demand pairs | 26 | 26 |
| Beckmann objective | 700.850087 | 700.814799 |

![04 Traffic assignment: saved S1 vehicle flow on the Boston network](../assets/boston/visual_release_r1/boston_panel_flow_s1.png)

![Saved S2 minus S1 fixed-panel road-flow difference](../assets/boston/visual_release_r1/boston_panel_flow_delta.png)

The two original maps are preserved byte-for-byte. Seventy-eight links differ above `1e-10` vehicle trips; the largest absolute change is **0.00660264**. There is **no regional background traffic**. Small simulated differences do not establish measured congestion relief or empirical policy effects. [Map sources and units](boston-visual-sources.md).

Saved-output checks covered costs, aggregate node balance and a shortest-path gap at the saved flow. They are computational checks, not a separate full per-OD path decomposition or validation against traffic counts.

<a id="gps-feedback"></a>
## How GPS changes stages 03 and 04

### Two distinct uses: spatial linkage and a service-time input

The [GPS projection map](boston-central.md#one-saved-transit-position-projection) shows one selected quality-qualified segment aligned to road reference lines. That illustration is **not the same segment** as the numeric trace below. It shows spatial linkage; this trace shows the subsequent model use.

For the numeric trace, public record `gps-stop-pair:mbtav:cccdb505033abedc:s01:5-10` refers to MBTA trip **78591067**, route **749**, direction **1**, stop pair **1788 → 5093**. Its derived interval is **86 seconds** versus **180 seconds planned**. Snapshot-derived events are estimates, not exact door-opening/closing observations.

```text
Raw positions → road/service identity → observed interval estimate
                                             ↓
                           exploratory interval adjustment
                                             ↓
GTFS itinerary/time/cost → 03 mode response → vehicle conversion
                                             ↓
                                04 same-network FW → road flow
```

| Same OD–departure: panel_od_019, 12:30 | S1 | S2 |
|---|---:|---:|
| Transit time | 29.052381 min | 27.485714 min |
| Fare | USD 1.70 | USD 1.70 |
| Walk-access transit probability | 4.0990% | 4.2246% |
| Private/occupied ride-service vehicles | 2.164631 | 2.161796 |

The registered factor is approximately `0.477778`. Transferring it to other services in the declared direction/interval is exploratory. **Thirteen adjustments each have one supporting event and are off by default.** Srestore independently disables the overlay and recomputes service costs, probabilities and demand, returning the comparable outputs to S1.

[Follow the full, source-keyed trace](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md) · [Inspect its source row](../../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/feedback_trace.csv)

A road's aggregate response sums multiple OD contributions; it is not solely caused by this one illustrated trace. GPS is **not** used here to estimate the regional household trip total, gravity β, all passenger OD or automobile BPR parameters. No independent AM validation is included.

## Run the saved example

From the repository root:

```bash
python -B examples/boston/run_saved_example.py --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" --output "results/boston_saved_example"
```

Use a new output directory. This rebuilds the compact query database from released CSVs and exports five saved queries. It does not retrieve observations, estimate demand, match GPS, reroute transit or run FW/CG. [Complete command and download guide](../../examples/boston/SAVED_EXAMPLE.md).

The compact component has **26 data tables plus one build-manifest table, two views and 38,800 records**. To use the full English data asset, keep the trusted code in the checkout and point `--data-dir` to the extracted asset's `public_component/` directory. The full regional OD is in that asset's `derived/` directory, not the small panel query table.

## Scope and assumptions

This is a source-backed, bounded four-step **technical example** with exploratory observation feedback. Household rates are transferred regional effective means; attraction, impedance, external travel and discrete departures retain explicit assumptions. Baseline shares are common regional shares, not a local absolute-cost choice model. The service overlay is retrospective midday evidence, not an independently validated AM parameter set.

The original 50,000-person-trip engineering scenarios, MassGIS activity prior, current regional-rate output and fixed feedback panel are distinct versions and scopes. Their charts and totals must not be silently mixed. [Earlier layers and retained maps](boston-central.md).

All source registrations and data terms remain in force. A code license does not replace network, ACS, MassGIS, MBTA or CTPS source terms. Private reviews, correspondence and unnecessary report caches are not required to use this public component.
