# Hong Kong · bounded finite space–time optimization

These sections follow one common representation and evidence order. Original saved scientific paragraphs, tables and figures are retained directly in their matching sections.

## Case role, scope, and model statistics

Unchanged `HK_TST_JORDAN_10OD_30S_50STEPS_R2_R4` ten-demand case: 100 selected physical nodes/111 links, 30-second steps, 50-step horizon, 11,954 dynamic nodes and 24,910 arcs. Not citywide DTA. [Cross-city finite statistics](../data/three_city_r1/THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS.md).

The current R2 six-panel view appears below. [Historical R1 layout](../assets/three_city_r1/hong_kong_finite_space_time_case_sequence.png) · [R1 source record](../assets/three_city_r1/hong_kong_finite_space_time_case_sequence.source.json).

This page reports the **unchanged** `HK_TST_JORDAN_10OD_30S_50STEPS_R2_R4` finite case, not citywide dynamic assignment. The preregistered core has 111 selected physical links, **11,954 dynamic nodes**, **24,910 arcs**, ten demands, 30-second steps and a 50-step (25-minute) horizon. Physical hourly PCE capacity is scaled by `30/3600` for departure arcs; nonphysical turn/zone access and waiting arcs follow the saved [construction contract](../assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/case/case.json). The original K=1 pool, graph and demand were not rebuilt for R5.

| Independent method or check | Accepted result on this same finite graph |
|---|---|
| Arc-flow reference LP | 75.03632985794819 vehicle-minutes; demand/capacity and physical-ID mapping checks pass |
| Current two-phase CG R5 | Phase I artificial flow **4.350218719795723 → 0** in 12 rounds; Phase II adds three columns and reaches approximately **75.03632985794835** vehicle-minutes |
| Independent full-DAG pricing | Closure passes **10/10** demands at `1e-6`; minimum ungenerated reduced cost is numerical zero; no continuation column is required |
| Lagrangian R3 | Separate restricted-path recovery is feasible at the reference objective; independent duality gap **0.7444%** |
| ADMM R2 | **Gated:** first local commodity QP has 0.082467622 PCE original-unit conservation residual; zero accepted outer iterations and no accepted objective |

Reference-objective agreement and independent pricing closure are distinct statements. The early R5 Phase-II summary predates the separate closure stage and is **not** the final certificate. [Final result matrix](../assets/hong_kong/full_stack_r5/HK_CG_R5_FINAL_RESULT_MATRIX.csv) · [Independent closure certificate](../assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json) · [Closure-by-demand table](../assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_BY_DEMAND.csv).

Panel b contains the specifically approved, model-generated HK10 path excerpt. The [artifact-level disclosure record](../assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json) limits approval to this excerpt and its listed derivatives, not the full pool or observed trajectories.

![hong_kong saved finite-case sequence, separately plotted panels](../assets/three_city_r2/hong_kong_finite_space_time_case_sequence.png)

*Source-matched R2 reconstruction from saved records.* [SVG](../assets/three_city_r2/hong_kong_finite_space_time_case_sequence.svg) · [Exact figure sources](../assets/three_city_r2/hong_kong_finite_space_time_case_sequence.source.json) · [Full caption](../assets/three_city_r2/hong_kong_finite_space_time_case_sequence.caption.md).

## From the physical network to the finite time-expanded graph

**The CG example solves a finite space–time linear flow model with fixed arc costs and explicit capacities.** This is distinct from static BPR/Beckmann assignment. The layered view uses the approved HK10 model-generated column excerpt, separating physical roads from road-entry/exit routing states and zero-time turn connectors.

<p align="center"><img src="../assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png" width="100%" alt="Hong Kong layered finite time-expanded graph: actual HK10 Austin Road excerpt at t26 to t28, zero-time turn, and CG workflow."></p>

*Source-grounded local excerpt; one time step is 30 seconds. Highlighted movements are arc_308368_t26 and arc_667532_t27, joined by the saved zero-time turn. The full path arrives at t37; its sink at t50 is bookkeeping. This is a model-generated path, not an observed trajectory.* [Editable SVG](../assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.svg) · [Source record](../assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.source.json) · [Displayed arcs](../assets/cg_layered_companions_r1/hong_kong_display_edges.csv) · [Exact HK10 derived disclosure record](../assets/cg_layered_companions_r1/HK10_LAYERED_COMPANION_DISCLOSURE.json).

![hong_kong saved physical and dynamic arc construction](../assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.png)

*Source-matched R2 reconstruction from saved records.* [SVG](../assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.svg) · [Exact figure sources](../assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.source.json) · [Full caption](../assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.caption.md).

![Hong Kong source-grounded local physical-link to time-indexed-arc cutaway](../assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.png)

*Two connected Austin Road physical links are shown with their saved turn-aware node-time movement, zero-time turn and waiting arcs over indices 0–3. Layout coordinates are schematic; link IDs, state IDs, arc types and times come from the unchanged 30-second finite graph. The highlighted permitted chain is **not** an exported CG column or observed trajectory. Physical hourly capacity becomes departure-arc PCE per 30-second step on the full graph; this construction is separate from static BPR assignment.* [Editable SVG](../assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.svg) · [Source record and exact IDs](../assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.source.json) · [Earlier aggregate construction graphic](../assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_physical_to_time_expanded.png).

## A generated column as a time-indexed path

The next figure shows the specifically approved **model-generated** HK10 column, not an observed UrbanNav/GPS trajectory. [Exact file-level approval and provenance](../assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json).

![hong_kong accepted generated column and ordered dynamic arcs](../assets/three_city_r2/hong_kong_generated_column_time_indexed_path.png)

*Source-matched R2 reconstruction from saved records.* [SVG](../assets/three_city_r2/hong_kong_generated_column_time_indexed_path.svg) · [Exact figure sources](../assets/three_city_r2/hong_kong_generated_column_time_indexed_path.source.json) · [Full caption](../assets/three_city_r2/hong_kong_generated_column_time_indexed_path.caption.md).

[Historical R1 generated-column layout](../assets/three_city_r1/hong_kong_generated_column_time_indexed_path.png) · [R1 source record](../assets/three_city_r1/hong_kong_generated_column_time_indexed_path.source.json). The R2 figure above is the current view of the same approved model-generated column.

One **actual positive-flow Phase-II R5 model-generated column**, `ORACLE_R1_HK10_K1`, carries 0.8352150831808043 PCE. It contains 77 ordered arcs: 37 movement, 36 turn, two zone, one source and one sink. The [specifically approved excerpt](../assets/three_city_r1/data/hong_kong_selected_generated_column.csv) and [source record](../assets/three_city_r1/data/hong_kong_selected_generated_column.source.json) are available; full pools, dual/state arrays and raw observations remain excluded.

## Phase I restores feasibility

Artificial flow 4.350218719795723 PCE reaches zero after 12 rounds. [Total](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.png) and [by-demand](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_by_demand.png) traces remain below.

![Hong Kong R5 Phase-I total artificial-flow trace](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.png)

*Exact-DAG pricing clears 4.350218719795723 artificial PCE by round 12 on the original ten-demand case.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.svg) · [Source record](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.source.json).

![Hong Kong R5 Phase-I artificial flow by demand](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_by_demand.png)

*All ten demands have zero final Phase-I artificial flow; the initial deficit was concentrated in three demands.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_by_demand.svg) · [Saved trace](../assets/hong_kong/full_stack_r5/cg_run/full_cg_v1_phase_i_artificial_flow_trace.csv).

## Shared capacity couples different OD demands

**Not demonstrated** as a specific before/after cross-OD shared-capacity event in the accepted R5 public record. The complete LP and CG still share capacity constraints; no event is invented for symmetry.

## Phase II improves the real-path objective

The real-only restricted master falls from 75.075236 to approximately 75.036330 vehicle-minutes after three added columns. [Saved trace](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.png).

![Hong Kong R5 Phase-II objective trace](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.png)

*The real-only restricted master falls from 75.075236 to 75.036330 vehicle-minutes after three added columns. The horizontal reference is the unchanged arc-flow LP on this graph.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.svg) · [Source record](../assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.source.json).

## From time-expanded flows back to final physical-link movement flow

![hong_kong movement-only physical-link flow audit](../assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.png)

*Source-matched R2 reconstruction from saved records.* [SVG](../assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.svg) · [Exact figure sources](../assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.source.json) · [Full caption](../assets/three_city_r2/hong_kong_time_expanded_to_physical_link_flow.caption.md).

[Historical R1 physical-link aggregation layout](../assets/three_city_r1/hong_kong_time_expanded_to_physical_link_flow.png) · [R1 source record](../assets/three_city_r1/hong_kong_time_expanded_to_physical_link_flow.source.json). The R2 figure above is the current view of the same projection.

Accepted movement-arc flow maps to all 111 selected physical-link IDs, with 69 positive modeled flows. [Public R5 physical map](../assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png). Nonphysical turn/zone/source/sink arcs are not road flow.

![Hong Kong R5 final physical-link movement flow](../assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png)

*Time-indexed movement is aggregated onto the 111 original physical-link IDs; 69 carry positive **modeled** flow. This is not an observed count map.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.svg) · [Source record](../assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.source.json).

## Reference-objective agreement

CG 75.03632985794835 and same-graph arc-flow LP 75.03632985794819 vehicle-minutes agree within numerical tolerance. This is distinct from Hong Kong's static turn-aware BPR/Beckmann objective.

## Independent pricing closure

Independent full-DAG pricing closure passes 10/10 demands at `1e-6`; final public RMP has 25 columns. [Certificate](../assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json) and [by-demand table](../assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_BY_DEMAND.csv).

![Hong Kong R5 independent pricing closure by demand](../assets/hong_kong/full_stack_r5/figures/hk_cg_pricing_closure.png)

*All ten demands pass the minimum ungenerated reduced-cost gate. The independent complete-DAG evaluator makes no optimizer call.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_cg_pricing_closure.svg) · [Redacted certificate](../assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json) · [Solver-free public verifier](../assets/hong_kong/full_stack_r5/verify_receiver_r5.py).

The final public RMP has 25 columns. A solver-free audit reconstructs objective **75.03632985794826** vehicle-minutes and checks zero demand/capacity residual within `1e-6`, model/seed signatures, result lineage and original physical-link projection. Private route sequences, full generated pools and dual arrays are excluded from the public projection. [Public verifier](../assets/hong_kong/full_stack_r5/verify_receiver_r5.py) · [Model freeze](../assets/hong_kong/full_stack_r5/HK_CG_R5_CASE_FREEZE.json).

## Reproduction, evidence boundary, and limits

The frozen ADMM transfer is **Gated** before an accepted outer iteration; no ADMM objective is a peer here. Source provider archives, private point-level data, full CG pool and duals remain excluded. No optimizer was rerun for this rendering.

![Hong Kong same-graph LP, CG and Lagrangian comparison](../assets/hong_kong/full_stack_r5/figures/hk_same_graph_method_comparison.png)

*LP, current CG and the separately recovered Lagrangian feasible primal agree at the same reference objective. ADMM has no accepted objective and is not plotted as a numerical peer.* [SVG](../assets/hong_kong/full_stack_r5/figures/hk_same_graph_method_comparison.svg) · [Lagrangian evaluation](../assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/lagrangian_evaluation.json).

The frozen ADMM R2 transfer remains gated at its **first** original-unit local conservation check, before accepted outer iterations. Its [saved gate figure](../assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_admm_residuals_and_feasibility.png) and [result record](../assets/hong_kong/full_stack_r5/r2r4_baseline/phase_c/admm_run/result.json) are historical and were not converted into an accepted run.

The earlier R2–R4 CG enumerator limit and its figures are preserved under `r2r4_baseline/` as **superseded history only**. They do not describe current R5 CG. Static Beckmann and finite fixed-cost vehicle-minute objectives cannot be compared numerically. [Case landing](hong-kong.md) · [Evidence contract and no-solver checks](../methods/hong-kong-evidence-contract.md).
