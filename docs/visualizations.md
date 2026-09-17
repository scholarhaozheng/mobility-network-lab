# Road benchmark visualizations

These figures summarize saved, independently checked historical Sioux Falls **selected-OD** experiments. They are the same approved image assets shipped with the preceding release; this gallery does not rerun optimization or invent new observations.

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
