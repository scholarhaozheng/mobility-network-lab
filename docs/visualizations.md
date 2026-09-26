# Visual results: four stages, observations, static assignment and CG

This gallery links saved-result figures for Boston and Sioux Falls and the bounded Hong Kong data pilot. It does not rerun optimization or invent observations. Common finite space–time CG figure families use the same terminology and reading order in both assignment cases; city-specific supplementary figures remain available and are not removed.

The additional [Sioux Lagrangian R2 and earlier ADMM R1 paired figures](methods/distributed-assignment.md) document accepted **selected-OD finite space–time shared-capacity** evidence. That R1 ADMM 250-OD view is drawn from final metrics only; no R1 iteration history was invented. The new R2_S lane below uses its own accepted saved histories. [Hong Kong's five official-derived data-layer SVGs](cases/hong-kong-gmns-pilot.md) have no assignment-flow interpretation.

## ADMM R2 · finite space–time shared capacity

![Verified Sioux and Boston ADMM R2 overview](assets/admm_r2/figures/admm_results_overview.png)

The [ADMM R2 method contract](methods/admm-space-time.md) leads to matched saved-result galleries for [Sioux Falls 200/250 selected ODs](cases/sioux-admm.md) and the [rights-cleared Boston 10-OD frozen holdout](cases/boston-admm.md). Each includes residual and feasibility traces, same-graph LP objective comparison, physical-link scatter and maps. Sioux 200 and Boston 10 also show commodity-level local conservation. The Boston signed map preserves its `4.24e-4`-vehicle maximum and uses only previously public GMNS geometry. All 22 accepted figure families retain individual SVG/PNG files and source sidecars; the 125-row Boston derived table is published without private dynamic inputs. This gallery does not rerun a solver.

## Static Algorithm B / matched saved figure families

![Accepted static Algorithm B evidence: Sioux Falls left and Boston B1 right, four matched evidence rows](assets/algorithm_b_r21/algorithm_b_cross_city_overview.png)

The overview uses display crops of the eight accepted R2 SVGs, ordered as convergence, same-problem FW physical-link comparison, selected-origin flow reconstructed from exported OD paths, and independent verification. The complete panels and explanatory captions remain on the [Sioux Falls](cases/sioux-algorithm-b.md) and [Boston](cases/boston-algorithm-b.md) case pages. Boston's one-point convergence is the saved trace, not an invented sequence; its selected-origin bars are not native Bush internal state or observed traffic. [Editable overview](assets/algorithm_b_r21/algorithm_b_cross_city_overview.svg) · [Crop and source-hash contract](assets/algorithm_b_r21/FIGURE_CONTRACT.md) · [Adapter status](integrations/taplab-tapb.md).

## Central Boston: demand, observations and static assignment

The [four-stage walkthrough](datasets/boston-behavior-feedback.md) links actual data to each stage. [Generation](datasets/boston-behavior-feedback.md#step-1-trip-generation), [OD distribution](datasets/boston-behavior-feedback.md#step-2-trip-distribution), [mode response](datasets/boston-behavior-feedback.md#step-3-mode-choice) and [road assignment](datasets/boston-behavior-feedback.md#step-4-traffic-assignment) have separate result figures. The [GPS feedback](datasets/boston-behavior-feedback.md#gps-feedback) explains where observations enter; the [original five-map gallery](datasets/boston-central.md#boston-visual-gallery) remains available as spatial context and saved outputs.

## Case-parallel finite space–time CG figure families

| Shared figure family | Boston | Sioux Falls |
|---|---|---|
| **From the physical network to time-indexed columns** | [Actual B07 physical-to-time cutaway](cases/boston-space-time.md#1-from-the-physical-network-to-time-indexed-columns) | [Actual XS170 local cutaway](cases/sioux-space-time.md#1-from-the-physical-network-to-time-indexed-columns) |
| **Phase I restores feasibility** | [Total and B01–B10 artificial-flow clearance](cases/boston-space-time.md#2-phase-i-restores-feasibility) | [200/250-OD total and OD-level clearance](cases/sioux-space-time.md#2-phase-i-restores-feasibility) |
| **A new path can help a different OD** | [B07/B09/B10 shared-capacity event](cases/boston-space-time.md#3-a-new-path-can-help-a-different-od) | [XS170/XS169 shared-capacity event](cases/sioux-space-time.md#3-a-new-path-can-help-a-different-od) |
| **Phase II improves the real-path objective** | [Boston Phase-II objective and reference](cases/boston-space-time.md#4-phase-ii-improves-the-real-path-objective) | [200/250-OD Phase-II objectives and references](cases/sioux-space-time.md#4-phase-ii-improves-the-real-path-objective) |
| **Final physical-link movement flow and validation** | [Boston final flow and audit](cases/boston-space-time.md#5-final-physical-link-movement-flow-and-validation) | [200/250-OD final flow and audit](cases/sioux-space-time.md#5-final-physical-link-movement-flow-and-validation) |
| **Independent pricing closure** | [Established for 10/10 demands](cases/boston-space-time.md#6-independent-pricing-closure) | [Not established for the retained historical runs](cases/sioux-space-time.md#6-independent-pricing-closure) |

Both cases have matching six-panel saved-result figures with identical canvas and panel order. The figures use restrained panel letters; explanations and limits sit in the case-page captions rather than in title cards inside the images:

<table><tr><th>Boston · one bounded pilot</th><th>Sioux Falls · two historical selected-OD benchmarks</th></tr><tr><td width="50%"><a href="assets/presentation_r5/boston_cg_case_sequence.png"><img src="assets/presentation_r5/boston_cg_case_sequence.png" width="100%" alt="Boston six-panel CG case sequence ending with independent pricing closure established for 10 of 10 demands"></a></td><td width="50%"><a href="assets/presentation_r5/sioux_cg_case_sequence.png"><img src="assets/presentation_r5/sioux_cg_case_sequence.png" width="100%" alt="Sioux Falls six-panel CG case sequence ending with independent pricing closure not established for the historical runs"></a></td></tr></table>

Display crops retain the plotted curves, axes, maps and time-network geometry while moving explanatory prose outside the composite; the complete originals remain linked in the case pages. No optimizer, pricing routine, demand model or map-matching routine was rerun. [Exact source hashes, crop coordinates and no-solve renderer](assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) · [Boston SVG](assets/presentation_r5/boston_cg_case_sequence.svg) · [Sioux Falls SVG](assets/presentation_r5/sioux_cg_case_sequence.svg).


## Executed finite space–time CG at a glance

![Six-stage executed CG evidence map: one bounded Boston pilot and two historical Sioux Falls selected-OD runs, with distinct independent-pricing-closure status](assets/presentation_r5/boston_sioux_cg_parallel_overview.png)

This compact overview uses the canonical six-stage vocabulary without repeating the detailed case panels. No optimizer or pricing oracle was rerun. Boston is one bounded real-city pilot with independent pricing closure for 10/10 demands. Sioux Falls retains separate 200-OD and 250-OD historical selected-OD benchmarks with reference-objective agreement on their own finite time-expanded graphs; independent pricing closure is not established for those runs. [Current SVG](assets/presentation_r5/boston_sioux_cg_parallel_overview.svg) · [Current source hashes](assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json) · [Earlier saved overview](assets/presentation_r4/cg_experiments_overview.png) and [its source manifest](assets/presentation_r4/CG_EXPERIMENTS_OVERVIEW_SOURCES.json).

## Boston bounded CG figure family

<table>
<tr><th>Single-pilot summary</th><th>Physical-to-space–time construction</th></tr>
<tr><td width="50%"><a href="cases/boston-space-time.md"><img src="assets/boston/space_time_cg_r4/boston_cg_summary_panel.png" width="100%" alt="Boston bounded CG summary: final physical-link movement flow, Phase-I clearance, Phase-II reference-objective agreement and independent pricing closure"></a></td><td width="50%"><a href="cases/boston-space-time.md#1-from-the-physical-network-to-time-indexed-columns"><img src="assets/boston/space_time_cg_r4/boston_space_time_construction.png" width="100%" alt="Actual Boston B07 physical path and time-indexed dynamic arc sequence"></a></td></tr>
<tr><th>Phase-I feasibility restoration</th><th>Phase-II objective and reference</th></tr>
<tr><td><a href="cases/boston-space-time.md#2-phase-i-restores-feasibility"><img src="assets/boston/space_time_cg_r4/boston_phase_i_artificial_flow.png" width="100%" alt="Boston artificial flow falls to zero at Phase-I round 90"></a></td><td><a href="cases/boston-space-time.md#4-phase-ii-improves-the-real-path-objective"><img src="assets/boston/space_time_cg_r4/boston_phase_ii_objective.png" width="100%" alt="Boston Phase-II objective reaches the arc-flow LP reference on the same finite time-expanded graph"></a></td></tr>
<tr><th>R4 continuation</th><th>Independent by-demand pricing closure</th></tr>
<tr><td><a href="cases/boston-space-time.md#6-independent-pricing-closure"><img src="assets/boston/space_time_cg_r4/boston_pricing_closure_continuation.png" width="100%" alt="Boston R4 adds 15 zero-final-flow certificate columns over five degenerate continuation rounds"></a></td><td><a href="cases/boston-space-time.md#6-independent-pricing-closure"><img src="assets/boston/space_time_cg_r4/boston_pricing_closure_by_demand.png" width="100%" alt="All ten Boston demands pass independent full-DAG pricing closure at tolerance 1e-6"></a></td></tr>
</table>

The remaining Boston counterparts—final physical-link flow, OD-level Phase-I clearance, shared-capacity event and final validation—are collected on the [full Boston CG case page](cases/boston-space-time.md).

### Scope and supplementary evidence

The [Boston finite space–time CG page](cases/boston-space-time.md) retains the full scientific figure family: final physical-link movement flow, actual time-indexed column construction, Phase-I total and per-demand clearance, a recorded cross-OD shared-capacity event, Phase-II objective/reference, final validation and the Boston-only independent pricing-closure continuation. It is **90 physical nodes / 125 directed links / 10 ODs**, not a citywide or second-scale Boston solve.

[Composed summary](assets/boston/space_time_cg_r4/boston_cg_summary_panel.png) · [All source/figure hashes](assets/boston/space_time_cg_r4/figure_manifest.json).

## Sioux Falls historical selected-OD benchmarks

The [Sioux Falls finite space–time CG page](cases/sioux-space-time.md) retains two distinct historical benchmark instances: 200 ODs and 250 ODs. They agree with the arc-flow LP objectives on their own selected-OD finite time-expanded graphs; independent pricing closure is **not established**. Boston's R4 certificate is not transferred to them.

### Final physical-link movement flow

<table>
<tr><th>200 OD · 64 selected links</th><th>250 OD · 69 selected links</th></tr>
<tr>
<td width="50%"><a href="datasets/sioux-200od.md"><img src="assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%" alt="200-OD final physical-link movement-flow view"></a></td>
<td width="50%"><a href="datasets/sioux-250od.md"><img src="assets/benchmarks/sioux_250od_final_physical_link_flow.png" width="100%" alt="250-OD final physical-link movement-flow view"></a></td>
</tr>
</table>

Line width encodes final movement flow aggregated across modeled time. These are schematic network views: opposite directions may overlap, and colors are not a quantitative scale. Do not read them as observed traffic, static V/C, precise road-shape GIS or a full 528-OD assignment.

### Phase II improves the real-path objective

<table>
<tr><th>200 OD</th><th>250 OD</th></tr>
<tr>
<td width="50%"><img src="assets/benchmarks/sioux_200od_phase2_objective_trace.png" width="100%" alt="200-OD saved Phase-II solved-pool objective trace"></td>
<td width="50%"><img src="assets/benchmarks/sioux_250od_phase2_objective_trace.png" width="100%" alt="250-OD saved Phase-II solved-pool objective trace"></td>
</tr>
</table>

Each curve is compared with the arc-flow LP on its own selected-OD finite time-expanded graph. Different OD selections define different optimization instances; their objective values are not directly comparable as an algorithmic improvement measure.

### Phase I restores feasibility

<table>
<tr><th>200 OD</th><th>250 OD</th></tr>
<tr>
<td width="50%"><img src="assets/benchmarks/sioux_200od_phase1_artificial_flow.png" width="100%" alt="200-OD successful-run Phase-I artificial-flow trace"></td>
<td width="50%"><img src="assets/benchmarks/sioux_250od_phase1_artificial_flow.png" width="100%" alt="250-OD successful-run Phase-I artificial-flow trace"></td>
</tr>
</table>

Artificial flow is an algorithmic feasibility device, not an observed queue or discarded real demand. Its progression belongs to the successful solve and is retained for interpretation.

## Data cards and numerical scope

The [200-OD record](datasets/sioux-200od.md) and [250-OD record](datasets/sioux-250od.md) explain saved versus uniquely reconstructed final path flows, objective checks and remaining certificate boundaries. Full raw inputs and reconstruction evidence are not redistributed here. The [static FW record](datasets/sioux-static-fw.md) is a separate static model, not another point on these CG curves.

[Network catalog](datasets.md) · [Outputs and verification](outputs.md) · [City workflow](city-workflow.md)
