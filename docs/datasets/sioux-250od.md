# Sioux Falls · 250 OD

**Historical road-benchmark result · finite space–time column generation.**

This selected-OD benchmark applies the historical finite space–time path-flow model to a Sioux Falls network subset. **It is not the full 528-OD Sioux Falls assignment.**

| Quantity | Value |
|---|---:|
| Physical nodes | 24 |
| Selected physical links | 69 |
| OD pairs | 250 |
| Dynamic nodes | 1,292 |
| Dynamic arcs | 11,254 |
| Final columns | 567 |
| Recomputed path-flow objective | 1,521,090.83662 |

## Final physical-link flow

![Final physical-link movement flow for the selected 250-OD Sioux Falls benchmark subset](../assets/benchmarks/sioux_250od_final_physical_link_flow.png)

Line width represents **total final movement flow aggregated across the modeled time horizon**. It does not represent static V/C or observed traffic. The map is for this selected 250-OD subset, not a full Sioux Falls assignment or a production-scale DTA result.

The physical-link totals were cross-checked independently from (1) saved final dynamic-arc loads aggregated to physical links and (2) the reconstructed all-column final-flow vector mapped back through dynamic arcs. The maximum absolute aggregation difference was approximately `1.09e-11`.

## Phase-II objective trajectory

![Phase-II objective trajectory for the selected 250-OD Sioux Falls benchmark subset](../assets/benchmarks/sioux_250od_phase2_objective_trace.png)

The preserved Phase-II trace shows the solved restricted-master objectives alongside the independently recomputed arc-flow reference objective. The reported final objective is `1521090.83662`.

## Phase-I artificial-flow trace

![Phase-I artificial-flow clearance for the selected 250-OD Sioux Falls benchmark subset](../assets/benchmarks/sioux_250od_phase1_artificial_flow.png)

The historical Phase-I trace records artificial flow falling to zero before Phase II. It is explanatory evidence from the preserved result, not a new run.

## Verification boundary

Of the 567 final column flows, 255 were directly saved and 312 were uniquely reconstructed from preserved final-flow identities using the saved final arc loads and final path-link incidence. The reconstruction did not constrain the objective to the reference value. Path connectivity, demand conservation, shared capacity, nonnegativity and the objective were checked against saved records; the independently recomputed reference-primal objective agrees within the stated audit tolerance.

No optimization was rerun to produce this page or its figures. This is a recovered historical result, not a rerun of the current source distribution. Conditional recovery of a missing vector does not establish uniqueness of the original LP optimum. Final RMP duals and a separate complete pricing certificate were not preserved.

## Data access

Public access is limited to this result record, its derived summary figures and catalog metadata. Historical raw inputs, reconstructed raw flow CSVs and private reconstruction evidence are not redistributed here. The general Sioux Falls data source is linked under [upstream sources](../integrations.md); a freshly obtained upstream snapshot is not automatically byte-identical to the historical input.

## Reuse

Cite the exact instance and verification scope. To execute a new experiment with the current engine, supply a compatible input profile and record a new run; do not label it as a replay of this historical run without checking model and source identity.
