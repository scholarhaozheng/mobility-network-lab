# Visual results: four stages, observations, static assignment and CG

This gallery links saved-result figures for Boston and Sioux Falls. It does not rerun optimization or invent new observations. The existing Sioux Falls **selected-OD** figures remain unchanged; the separate Boston CG figures are from one accepted bounded pilot.

For the separate real-city example, see the [Central Boston five-map gallery](datasets/boston-central.md#boston-visual-gallery): network and zones, the MassGIS residential-area prior, one qualified GPS projection, and saved S1 and S2−S1 fixed-panel flows. Its source credits and units are documented alongside each map.

## Central Boston: read results in calculation order

The [four-step walkthrough](datasets/boston-behavior-feedback.md) links actual data to each stage. [Generation](datasets/boston-behavior-feedback.md#step-1-trip-generation), [OD distribution](datasets/boston-behavior-feedback.md#step-2-trip-distribution), [mode response](datasets/boston-behavior-feedback.md#step-3-mode-choice) and [road assignment](datasets/boston-behavior-feedback.md#step-4-traffic-assignment) have separate result figures. The [GPS feedback](datasets/boston-behavior-feedback.md#gps-feedback) explains where observations enter; the [original five-map gallery](datasets/boston-central.md#boston-visual-gallery) remains available as spatial context and saved outputs.

The [Boston bounded space–time CG gallery](cases/boston-space-time.md) gives the corresponding scientific figure families: final physical flow, actual time-network cutaway, Phase-I total and per-demand clearance, a saved cross-OD binding-arc event, Phase-II objective/reference, final validation, and Boston-only independent pricing closure. It is **90 nodes / 125 links / 10 ODs**, not a citywide or second-scale Boston solve. [Composed summary](assets/boston/space_time_cg_r4/boston_cg_summary_panel.png) · [all source/figure hashes](assets/boston/space_time_cg_r4/figure_manifest.json).


## Executed finite space–time CG at a glance

![Executed finite space-time CG overview: one bounded Boston pilot and two historical Sioux Falls selected-OD runs](assets/presentation_r4/cg_experiments_overview.png)

This presentation composite uses saved public figures only; no optimizer or pricing oracle was rerun. Boston is one bounded real-city pilot with independent full-DAG closure for 10/10 demands. Sioux Falls retains separate 200-OD and 250-OD historical selected subsets whose objectives match their own same-subset arc-flow references; independent pricing closure is not established for those runs. [Composite-source manifest](assets/presentation_r4/CG_EXPERIMENTS_OVERVIEW_SOURCES.json).

## Boston bounded CG figure family

<table>
<tr><th>Single-pilot summary</th><th>Physical-to-space–time construction</th></tr>
<tr><td width="50%"><a href="cases/boston-space-time.md"><img src="assets/boston/space_time_cg_r4/boston_cg_summary_panel.png" width="100%" alt="Boston bounded CG summary: final physical flow, Phase-I clearance, Phase-II reference match and independent closure"></a></td><td width="50%"><a href="cases/boston-space-time.md#network-and-construction-physical-geography-versus-time-states"><img src="assets/boston/space_time_cg_r4/boston_space_time_construction.png" width="100%" alt="Actual Boston B07 physical path and time-indexed dynamic arc sequence"></a></td></tr>
<tr><th>Phase-I feasibility restoration</th><th>Phase-II objective and reference</th></tr>
<tr><td><a href="cases/boston-space-time.md#phase-i-total-feasibility-and-od-level-coupling"><img src="assets/boston/space_time_cg_r4/boston_phase_i_artificial_flow.png" width="100%" alt="Boston artificial flow falls to zero at Phase-I round 90"></a></td><td><a href="cases/boston-space-time.md#phase-i-total-feasibility-and-od-level-coupling"><img src="assets/boston/space_time_cg_r4/boston_phase_ii_objective.png" width="100%" alt="Boston Phase-II objective reaches the identical-graph arc-flow LP reference"></a></td></tr>
<tr><th>R4 continuation</th><th>Independent by-demand pricing closure</th></tr>
<tr><td><a href="cases/boston-space-time.md#r4-independent-pricing-closure-and-final-validation"><img src="assets/boston/space_time_cg_r4/boston_pricing_closure_continuation.png" width="100%" alt="Boston R4 adds 15 zero-final-flow certificate columns over five degenerate continuation rounds"></a></td><td><a href="cases/boston-space-time.md#r4-independent-pricing-closure-and-final-validation"><img src="assets/boston/space_time_cg_r4/boston_pricing_closure_by_demand.png" width="100%" alt="All ten Boston demands pass independent full-DAG pricing closure at tolerance 1e-6"></a></td></tr>
</table>

The remaining Boston counterparts—final physical-link flow, OD-level Phase-I clearance, shared-capacity event and final validation—are collected on the [full Boston CG case page](cases/boston-space-time.md).

## Separate historical Sioux Falls benchmarks

These 200/250-OD records agree with their own saved same-subset arc-flow LP objectives; independent full-DAG pricing closure is **not established**. Boston's R4 certificate is not transferred to them.

## Physical-link flow views

<table>
<tr><th>200 OD · 64 selected links</th><th>250 OD · 69 selected links</th></tr>
<tr>
<td width="50%"><a href="datasets/sioux-200od.md"><img src="assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%" alt="200-OD physical-link movement-flow view"></a></td>
<td width="50%"><a href="datasets/sioux-250od.md"><img src="assets/benchmarks/sioux_250od_final_physical_link_flow.png" width="100%" alt="250-OD physical-link movement-flow view"></a></td>
</tr>
</table>

Line width encodes final movement flow aggregated across modelled time. These are schematic network views: opposite directions may overlap, and colours are not a quantitative colour scale. Do not read them as observed traffic, static V/C, precise road-shape GIS or a full 528-OD assignment.

## Phase-II objective trajectories

<table>
<tr><th>200 OD</th><th>250 OD</th></tr>
<tr>
<td width="50%"><img src="assets/benchmarks/sioux_200od_phase2_objective_trace.png" width="100%" alt="200-OD saved Phase-II solved-pool objectives"></td>
<td width="50%"><img src="assets/benchmarks/sioux_250od_phase2_objective_trace.png" width="100%" alt="250-OD saved Phase-II solved-pool objectives"></td>
</tr>
</table>

Each curve is compared with its own same-model arc-flow reference. Different OD selections define different optimization instances; do not interpret the difference between their objective values as an algorithmic improvement.

## Phase-I artificial-flow clearance

<table>
<tr><th>200 OD</th><th>250 OD</th></tr>
<tr>
<td width="50%"><img src="assets/benchmarks/sioux_200od_phase1_artificial_flow.png" width="100%" alt="200-OD successful-run Phase-I artificial-flow trace"></td>
<td width="50%"><img src="assets/benchmarks/sioux_250od_phase1_artificial_flow.png" width="100%" alt="250-OD successful-run Phase-I artificial-flow trace"></td>
</tr>
</table>

Artificial flow is an algorithmic feasibility device, not an observed queue or discarded trip demand. Its progression belongs to the successful solve and is retained for interpretation.

## Data cards and numerical scope

The [200-OD record](datasets/sioux-200od.md) and [250-OD record](datasets/sioux-250od.md) explain saved versus uniquely reconstructed final path flows, objective checks and remaining certificate boundaries. Full raw inputs and reconstruction evidence are not redistributed here. The [static FW record](datasets/sioux-static-fw.md) is a separate approximate static model, not another point on these CG curves.

[Network catalog](datasets.md) · [Outputs and verification](outputs.md) · [City workflow](city-workflow.md)
