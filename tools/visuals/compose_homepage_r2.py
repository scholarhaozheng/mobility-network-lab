#!/usr/bin/env python3
"""Maintain the R3 GitHub-native evidence rows and stage-based case atlas.

Uses only the source-matched R2 row matrix and pre-existing public case art.
The complete site builder subsequently derives docs/index.md and index.html.
"""
from __future__ import annotations

import csv
import html
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MATRIX=ROOT/"docs/assets/homepage_evidence_r2/ROW_TEMPLATE_MATRIX.csv"
ROW15_MAPPING=ROOT/"docs/assets/homepage_evidence_r2/ROW15_REUSE_SOURCE_MAPPING.csv"
HK_STATIC_R2_MAPPING=ROOT/"docs/assets/homepage_evidence_r2/ROW12_13_HK_REUSE_SOURCE_MAPPING.csv"
STATIC_PATH_PARITY=ROOT/"docs/assets/static_path_parity_r1/FIGURE_PARITY_MAP.csv"
README=ROOT/"README.md"
HERO="""# Mobility Computation Lab

**Mobility Computation Lab connects city networks, travel demand, and reproducible network computation.**

This open-source research and learning project is developed by [Hao Zheng](https://scholarhaozheng.github.io/), a recent M.S. graduate from Tsinghua University, under the guidance of **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)**. It brings together documented examples in Boston, Sioux Falls, and Hong Kong to study how city data, demand models, and network algorithms work together.

The repository uses the [General Modeling Network Specification (GMNS)](https://github.com/zephyr-data-specs/GMNS) as its portable network and data contract. Selected static traffic-assignment experiments build on [TAPLab: An Open Laboratory for Reproducible Traffic Assignment Experiments](https://github.com/asu-trans-ai-lab/TAPLab) and the official [tap-b Algorithm B](https://github.com/spartalab/tap-b), with upstream software, methods, and datasets attributed explicitly.

Project-specific work includes assembling and adapting the Boston, Sioux Falls, and Hong Kong cases; connecting city data and four-stage demand models to documented network computations; implementing and evaluating project-specific adapters, workflows, and experiments; and making each result traceable to its actual instance, units, assumptions, and evidence.

**Learning companion.** To make these computational ideas easier to explore, the site includes the [Traffic Assignment Lab](docs/traffic-assignment-lab.html), an interactive demo of assignment, decomposition, spatial hierarchy, and coordinated computation on one teaching network. The demo was developed collaboratively by **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)** and Hao Zheng, with Hao Zheng working under Professor Zhou's guidance and maintaining the web version.

[My contributions and upstream foundations](docs/contributions.md) · [Full technical walkthrough](docs/full-walkthrough.md) · [Start with a saved example](docs/getting-started.md) · [Source and citation](docs/citation.md)

"""
TWO_AXES="""<a id="two-axes"></a><a id="02a-two-axes-of-mobility-computation-lab"></a>
### Two axes of Mobility Computation Lab

**Horizontal axis — documented city cases:**  
Boston · Sioux Falls · Hong Kong

**Vertical axis — computational depth within network assignment:**

- **A · Native assignment** — Frank–Wolfe, official tap-b Algorithm B, finite-path controls, and native L3 reconstruction.
- **B · Decomposition and distributed computation** — column generation, Lagrangian decomposition, and ADMM local or coupled computations.
- **C · Spatial hierarchy and representation** — fine and parent zones, access relationships, turn/time states, and projection back to physical network objects.
- **D · Coordination and verification** — shared capacities, residuals, pricing closure, independent evaluators, and declared result contracts.

**How to read the two axes.**  
The horizontal axis compares how the documented framework is instantiated in Boston, Sioux Falls, and Hong Kong. The vertical axis organizes increasing computational depth inside the network-assignment branch. A–D are not four mandatory execution steps. Source data, GMNS, population and activity preparation, transit and observations, and the four-stage demand workflow remain the common city-model foundation outside A–D.

"""
CITIES=("Boston","Sioux Falls","Hong Kong")
SLUG={"Boston":"boston","Sioux Falls":"sioux-falls","Hong Kong":"hong-kong"}
DISPLAY_SCOPE_REVISIONS={
    "24-node, 76-link supplied directed benchmark; schematic topology, no city zone hierarchy.":
        "24-node, 76-link supplied directed benchmark.",
    "Transferred rate and declared capture sensitivity, not local calibration.":
        "Transferred rate and declared capture sensitivity.",
    "Supplied OD is input, not a modeled distribution stage.":
        "Supplied OD is input.",
    "Modeled one-hour static PCE road flow, not measured traffic.":
        "Modeled one-hour static PCE road flow.",
    "Rank-50 classic static benchmark candidates, not an empirical speedup.":
        "Rank-50 classic static benchmark candidates.",
}
ROW_GROUPS=[
 ("I / City data and model foundations","a--city-data-and-model-foundations",("01","02","03")),
 ("II / Transit and observation evidence","b--transit-and-observation-evidence",("04","05")),
 ("III / Four-stage travel-demand workflow","c--four-stage-travel-demand-workflow",("06","07","08","09")),
 ("IV / Static assignment · BPR/Beckmann","d1--static-assignment--bprbeckmann",("10","11","12","13")),
 ("V / Finite time-expanded · fixed cost, hard capacity","d2--finite-time-expanded--fixed-cost-hard-capacity",("14","15","16","17","18")),
]
STAGES=[
 ("sources","Sources and GMNS"),("population","Population, households and activity"),
 ("transit","Transit and observations"),("generation","Trip generation"),
 ("distribution","Trip distribution"),("mode","Mode choice"),
 ("static","Static assignment methods"),("finite","Optimization on the time-expanded network"),
 ("tools","Tools and reproducibility"),
]
STAGE_ROWS={"sources":("01","02"),"population":("03",),"transit":("04","05"),"generation":("06",),"distribution":("07",),"mode":("08",),"static":("10","11","12","13"),"finite":("14","15","16","17","18")}
COVER={
 "Boston":"docs/assets/boston/visual_release_r1/mcl_boston_hero.png",
 "Sioux Falls":"docs/assets/homepage_evidence_r1/sioux_falls_case_cover.png",
 "Hong Kong":"docs/assets/homepage_evidence_r1/hong_kong_case_cover.png",
}
BOSTON_GPS_PROJECTION="docs/assets/boston/visual_release_r1/boston_gps_projection.png"
HK_REFERENCE_PROJECTION="docs/assets/hong_kong/visual_release_r1/hong_kong_reference_projection.png"
GPS_PAIR_SECONDARY={
 "Boston":(BOSTON_GPS_PROJECTION,
           "docs/datasets/boston-central.md#one-saved-transit-position-projection",
           "Twelve saved Boston vehicle positions, projected points and matched road geometry",
           "Projection figure"),
 "Hong Kong":(HK_REFERENCE_PROJECTION,
              "docs/cases/hong-kong.md#demand-transit-and-observations",
              "Twelve saved UrbanNav reference positions, their projected points and matched Hong Kong roads",
              "Projection figure"),
}
CASE_PAGE={"Boston":"docs/cases/boston.md","Sioux Falls":"docs/cases/sioux-falls.md","Hong Kong":"docs/cases/hong-kong.md"}
FINITE_FIGURES={
 "Boston":{
  "construction":("docs/assets/three_city_r2/boston_physical_to_time_expanded_graph.png","Saved physical-to-finite-graph cutaway"),
  "layered":("docs/assets/cg_layered_companions_r1/boston_layered_space_time_construction.png","B07 excerpt across selected time layers"),
  "path":("docs/assets/boston/space_time_cg_r4/boston_space_time_construction.png","Recorded B07 time-indexed column"),
  "flow":("docs/assets/boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png","Bounded 10-OD final physical-link flow"),
 },
 "Sioux Falls":{
  "construction":("docs/assets/three_city_r2/sioux_physical_to_time_expanded_graph.png","Selected finite-graph cutaway"),
  "layered":("docs/assets/presentation_r3/sioux_space_time_construction.png","XS170 example across selected layers"),
  "path":("docs/assets/three_city_r2/sioux_generated_column_time_indexed_path.png","Saved XS170 route and ordered arcs"),
  "flow":("docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png","200-OD example; 250-OD flow remains in case page"),
 },
 "Hong Kong":{
  "construction":("docs/assets/three_city_r2/hong_kong_physical_to_time_expanded_graph.png","Turn-aware finite-graph cutaway"),
  "layered":("docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png","Approved HK10 excerpt across selected layers"),
  "path":("docs/assets/hong_kong/presentation_r6/hk_physical_to_time_cutaway.png","Permitted local chain; display-only, not an exported CG column"),
  "flow":("docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png","R5 bounded 10-OD final physical-link flow"),
 },
}
FINITE_SLUG={"Boston":"boston","Sioux Falls":"sioux_falls","Hong Kong":"hong_kong"}
ROLE={
 "Boston":"City GMNS, population/demand, MBTA/GPS linkage and separate bounded static and finite computations.",
 "Sioux Falls":"Supplied-OD controlled static benchmark and separate historical selected-OD finite cases; not a four-stage city compiler.",
 "Hong Kong":"Bounded turn-aware GMNS and four-stage engineering scenario with separate ten-OD finite CG evidence.",
}
FACTS={
 "Boston":("2,852 physical nodes; 5,091 directed links; 177 H3 fine zones","B1: 453 ODs / 1,936.238475 PCE in 2 h; expanded FW and 26-OD controls are distinct","90 nodes; 125 links; 10 ODs","MBTA inputs and exploratory GPS matching; no held-out citywide calibration"),
 "Sioux Falls":("24 nodes; 76 directed links; supplied benchmark OD","528 positive OD records; official Algorithm B, historical FW and native controls","24 nodes; 64/69 selected links; 200/250 ODs","No modern city population, GTFS, GPS or detector stage"),
 "Hong Kong":("780 physical nodes; 1,239 directed links; 95 fine zones","8,930 OD pairs; 723.191 modeled PCE in 1 h","100 selected nodes; 111 links; 10 ODs; approved HK10 generated column","Detector/trajectory association is contextual; modeled flow is not observed traffic"),
}

# Each extra card keeps an original, scientifically distinct image visible.
# Tuples: city, stage, label, image, detailed target, method, instance/status.
EXTRAS=[
 ("Boston","sources","Special zones and access","docs/assets/boston/visual_release_r1/boston_network_zones.png","docs/cases/boston.md#gmns-zones-and-source-evidence","GMNS","Central Boston"),
 ("Boston","population","ACS/H3 allocation","docs/assets/boston/population_r1/population_allocation.png","docs/datasets/boston-population-households.md","Population","ACS 2024 five-year"),
 ("Boston","transit","GPS point-to-road projection",BOSTON_GPS_PROJECTION,"docs/datasets/boston-central.md#one-saved-transit-position-projection","GPS map matching","12 saved MBTA positions"),
 ("Boston","generation","Generation by purpose","docs/assets/boston/four_step_results_r1/step1_generation.png","docs/cases/boston.md#stage-01-trip-generation","Trip generation","bounded example"),
 ("Boston","distribution","HBW OD distribution","docs/assets/boston/four_step_results_r1/step2_distribution.png","docs/cases/boston.md#stage-02-trip-distribution","Trip distribution","bounded example"),
 ("Boston","mode","Service-response mode choice","docs/assets/boston/four_step_results_r1/step3_mode_response.png","docs/cases/boston.md#stage-03-mode-choice","Mode choice","S1/S2 sensitivity"),
 ("Boston","static","FW 500-OD tier","docs/assets/boston/scalable_tool_r1/fw_500_flow.png","docs/cases/boston-assignment.md#primary-scale-result-versus-controlled-method-comparison","FW","500-OD tier"),
 ("Boston","static","FW 2,000-OD tier","docs/assets/boston/scalable_tool_r1/fw_2000_flow.png","docs/cases/boston-assignment.md#primary-scale-result-versus-controlled-method-comparison","FW","2,000-OD tier"),
 ("Boston","static","FW expanded tier","docs/assets/boston/scalable_tool_r1/fw_all_flow.png","docs/cases/boston-assignment.md#primary-scale-result-versus-controlled-method-comparison","FW","17,522 loaded ODs"),
 ("Boston","static","Task-local Algorithm B B1","docs/assets/algorithm_b_r21/source_panels/boston_b1_fw_flow.svg","docs/cases/boston-algorithm-b.md#4-physical-link-comparison-with-same-problem-fw","Algorithm B","B1 453-OD; accepted"),
 ("Boston","static","FW anchor for the 130-path control","docs/assets/boston/assignment_methods_r1/boston_abs_planned_fw_flow.png","docs/cases/boston-assignment.md#same-instance-saved-result","FW comparison anchor","ABS_PLANNED 26-OD; not the finite-path solution"),
 ("Boston","static","Native L3 rank 26 difference","docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_minus_fw.png","docs/cases/boston-assignment.md#signed-native-minus-fw-differences","L3","rank 26; numerical candidate"),
 ("Boston","static","Native L3 rank 52 difference","docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank52_minus_fw.png","docs/cases/boston-assignment.md#signed-native-minus-fw-differences","L3","rank 52; numerical candidate"),
 ("Boston","finite","Case-sequence overview","docs/assets/presentation_r5/boston_cg_case_sequence.png","docs/cases/boston-space-time.md#case-role-scope-and-model-statistics","CG","10-OD"),
 ("Boston","finite","Physical to time-expanded graph","docs/assets/cg_layered_companions_r1/boston_layered_space_time_construction.png","docs/cases/boston-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph","CG construction","10-OD"),
 ("Boston","finite","Generated time-indexed column","docs/assets/three_city_r2/boston_generated_column_time_indexed_path.png","docs/cases/boston-space-time.md#a-generated-column-as-a-time-indexed-path","CG column","10-OD"),
 ("Boston","finite","Phase I artificial-flow clearance","docs/assets/boston/space_time_cg_r4/boston_phase_i_artificial_flow.png","docs/cases/boston-space-time.md#phase-i-restores-feasibility","CG Phase I","10-OD"),
 ("Boston","finite","Shared-capacity event","docs/assets/boston/space_time_cg_r4/boston_shared_capacity_event.png","docs/cases/boston-space-time.md#shared-capacity-couples-different-od-demands","CG capacity","10-OD"),
 ("Boston","finite","Phase II objective","docs/assets/boston/space_time_cg_r4/boston_phase_ii_objective.png","docs/cases/boston-space-time.md#phase-ii-improves-the-real-path-objective","CG Phase II","10-OD"),
 ("Boston","finite","Final physical-link movement flow","docs/assets/boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png","docs/cases/boston-space-time.md#from-time-expanded-flows-back-to-final-physical-link-movement-flow","CG flow","10-OD"),
 ("Boston","finite","Independent pricing closure","docs/assets/boston/space_time_cg_r4/boston_pricing_closure_by_demand.png","docs/cases/boston-space-time.md#independent-pricing-closure","CG pricing","10/10"),
 ("Boston","finite","ADMM convergence","docs/assets/admm_r2/figures/convergence_Boston_10OD.png","docs/cases/boston-admm.md#original-saved-convergence-view","ADMM","R2_S 10-OD accepted"),
 ("Boston","finite","ADMM physical flow and LP difference","docs/assets/admm_r2/figures/admm_boston_10od_minus_lp.png","docs/cases/boston-admm.md#physical-link-movement-flow-and-lp-comparison","ADMM","R2_S 10-OD accepted"),
 ("Sioux Falls","sources","Classic network topology","docs/assets/homepage_evidence_r1/sioux_falls_classic_topology.png","docs/cases/sioux-falls.md#gmns-zones-and-source-evidence","Network","24-node / 76-link"),
 ("Sioux Falls","static","Historical FW vs Algorithm B","docs/assets/algorithm_b_r21/presentation/sioux_fw_flow_compact.png","docs/cases/sioux-algorithm-b.md#4-physical-link-comparison-with-same-problem-fw","FW / Algorithm B","528-OD; separate objectives"),
 ("Sioux Falls","static","Official Algorithm B accepted flow","docs/assets/algorithm_b_r21/source_panels/sioux_origin_flow.svg","docs/cases/sioux-algorithm-b.md#5-selected-origin-reconstructed-flow","Algorithm B","official adapter"),
 ("Sioux Falls","static","Native L3 rank-50 saved link flows","docs/assets/homepage_alignment_r3/sioux_native_l3_rank50_link_flows.png","docs/cases/sioux-falls.md#static-assignment","L3","rank 50; diagnostic, not UE"),
 ("Sioux Falls","finite","200/250-OD case overview","docs/assets/presentation_r5/sioux_cg_case_sequence.png","docs/cases/sioux-space-time.md#case-role-scope-and-model-statistics","CG","historical selected ODs"),
 ("Sioux Falls","finite","Physical to time-expanded graph","docs/assets/three_city_r2/sioux_physical_to_time_expanded_graph.png","docs/cases/sioux-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph","CG construction","selected graph"),
 ("Sioux Falls","finite","Generated time-indexed column","docs/assets/three_city_r2/sioux_generated_column_time_indexed_path.png","docs/cases/sioux-space-time.md#a-generated-column-as-a-time-indexed-path","CG column","selected graph"),
 ("Sioux Falls","finite","Phase I 200 OD","docs/assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png","docs/cases/sioux-space-time.md#200-od-pairs","CG Phase I","200-OD"),
 ("Sioux Falls","finite","Phase I 250 OD","docs/assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png","docs/cases/sioux-space-time.md#250-od-pairs","CG Phase I","250-OD"),
 ("Sioux Falls","finite","Shared-capacity reallocation","docs/assets/presentation_r5/sioux_shared_capacity_canonical.png","docs/cases/sioux-space-time.md#recorded-shared-capacity-reallocation-event","CG capacity","200-OD example"),
 ("Sioux Falls","finite","Phase II / own-LP objective","docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png","docs/cases/sioux-space-time.md#phase-ii-improves-the-real-path-objective","CG Phase II","selected 200-OD trace; 250-OD linked"),
 ("Sioux Falls","finite","Final movement flow 200 OD","docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png","docs/cases/sioux-space-time.md#from-time-expanded-flows-back-to-final-physical-link-movement-flow","CG flow","200-OD"),
 ("Sioux Falls","finite","Final movement flow 250 OD","docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png","docs/cases/sioux-space-time.md#from-time-expanded-flows-back-to-final-physical-link-movement-flow","CG flow","250-OD"),
 ("Sioux Falls","finite","Lagrangian accepted recovery","docs/assets/sioux/distributed_r1/Sioux_200OD_P07.png","docs/methods/distributed-assignment.md#lagrangian-capacity-pricing-with-separate-primal-recovery","Lagrangian","selected 200/250-OD"),
 ("Sioux Falls","finite","ADMM 200-OD convergence","docs/assets/admm_r2/figures/convergence_Sioux_200OD.png","docs/cases/sioux-admm.md#original-saved-convergence-views","ADMM","R2_S 200-OD"),
 ("Sioux Falls","finite","ADMM 250-OD physical flow","docs/assets/admm_r2/figures/admm_sioux_250_final_physical_link_flow.png","docs/cases/sioux-admm.md#physical-link-movement-flow","ADMM","R2_S 250-OD"),
 ("Hong Kong","sources","Roads, zones and turns","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_assignment_ready_network.png","docs/cases/hong-kong.md#gmns-zones-and-source-evidence","GMNS","780 nodes / 1,239 links"),
 ("Hong Kong","population","2021 census allocation and activity proxy","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_population_households_activity.png","docs/cases/hong-kong-four-stage.md","Population/proxy","not observed employment"),
 ("Hong Kong","transit","Detector/trajectory association","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_detector_and_trajectory_evidence.png","docs/cases/hong-kong.md#demand-transit-and-observations","Observation linkage","not held-out validation"),
 ("Hong Kong","generation","Production/attraction scenario","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_trip_generation_distribution.png","docs/cases/hong-kong-four-stage.md","Trip generation","engineering scenario"),
 ("Hong Kong","mode","Mode costs and shares","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_mode_choice_costs_and_shares.png","docs/cases/hong-kong-four-stage.md","Mode choice","one-hour AM"),
 ("Hong Kong","static","FW static PCE map","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_static_fw_flow.png","docs/cases/hong-kong-static-assignment.md","FW","8,930 OD / 723.191 modeled PCE"),
 ("Hong Kong","static","Task-local Algorithm B vs FW","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_algorithm_b_vs_fw.png","docs/cases/hong-kong-static-assignment.md","Algorithm B","accepted; not official-adapter parity"),
 ("Hong Kong","finite","Bounded case overview","docs/assets/hong_kong/full_stack_r5/figures/hk_cg_case_sequence.png","docs/cases/hong-kong-space-time.md#case-role-scope-and-model-statistics","CG","R5 10-OD"),
 ("Hong Kong","finite","Physical to time-indexed movement","docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png","docs/cases/hong-kong-space-time.md#from-the-physical-network-to-the-finite-time-expanded-graph","CG construction","R5 10-OD"),
 ("Hong Kong","finite","Approved HK10 77-arc column","docs/assets/three_city_r2/hong_kong_generated_column_time_indexed_path.png","docs/cases/hong-kong-space-time.md#a-generated-column-as-a-time-indexed-path","CG column","model-generated; approved exact excerpt"),
 ("Hong Kong","finite","Phase I artificial flow","docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_i_artificial_flow.png","docs/cases/hong-kong-space-time.md#phase-i-restores-feasibility","CG Phase I","R5 10-OD"),
 ("Hong Kong","finite","Phase II objective","docs/assets/hong_kong/full_stack_r5/figures/hk_cg_phase_ii_objective.png","docs/cases/hong-kong-space-time.md#phase-ii-improves-the-real-path-objective","CG Phase II","R5 10-OD"),
 ("Hong Kong","finite","Final physical-link movement flow","docs/assets/hong_kong/full_stack_r5/figures/hk_cg_final_physical_link_movement_flow.png","docs/cases/hong-kong-space-time.md#from-time-expanded-flows-back-to-final-physical-link-movement-flow","CG flow","R5 10-OD"),
 ("Hong Kong","finite","Independent 10/10 pricing closure","docs/assets/hong_kong/full_stack_r5/figures/hk_cg_pricing_closure.png","docs/cases/hong-kong-space-time.md#independent-pricing-closure","CG pricing","R5 10-OD"),
 ("Hong Kong","finite","Lagrangian certified gap","docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_lagrangian_dual_primal_gap.png","docs/cases/hong-kong-space-time.md#reference-objective-agreement","Lagrangian","bounded accepted 0.7444%"),
 ("Hong Kong","finite","ADMM R3 convergence","docs/assets/admm_r3/hong_kong/hk_admm_r3_residual_convergence.png","docs/cases/hong-kong-space-time.md#admm-r3-bounded-four-od-transfer","ADMM","accepted fresh 4-OD · 165 iterations; separate from gated 10-OD R2"),
 ("Hong Kong","finite","ADMM R3 physical flow vs LP","docs/assets/admm_r3/hong_kong/hk_admm_r3_admm_vs_lp_physical_flow.png","docs/cases/hong-kong-space-time.md#admm-r3-bounded-four-od-transfer","ADMM","accepted fresh 4-OD · 58 positive physical links"),
]

def esc(s):return html.escape(str(s),quote=True)

def load_matrix():
    with MATRIX.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    if len(rows)!=57:raise AssertionError(len(rows))
    # Homepage-only copy edits; retain the accepted matrix and sidecars as provenance.
    for r in rows:
        r["result_scope"]=DISPLAY_SCOPE_REVISIONS.get(r["result_scope"],r["result_scope"])
        if (r["row_id"],r["city"])==("12","Sioux Falls"):
            r["result_scope"]="Frozen 2,218-path representation; B_BECKMANN native candidate, not full-network UE."
    return {(r["row_id"],r["city"]):r for r in rows}

def row_target(r):
    return r["target_page"]+("#"+r["target_anchor"] if r["target_anchor"] else "")

def row15_reuse(rows):
    with ROW15_MAPPING.open(newline="",encoding="utf-8") as f:
        reuse={r["city"]:r for r in csv.DictReader(f)}
    if set(reuse)!=set(CITIES):raise AssertionError("row-15 city mapping")
    for row in rows:
        record=reuse[row["city"]]
        for field,expected in (("original_figure",record["original_figure"]),
                               ("data_or_figure_source",record["source_record"]),
                               ("source_hash",record["source_sha256"]),
                               ("target_page",record["target_page"]),
                               ("target_anchor",record["target_anchor"])):
            if row[field]!=expected:raise AssertionError((row["city"],field))
        if (record["reused_existing_figure"],record["newly_generated_scientific_figure"])!=("true","false"):
            raise AssertionError("row-15 reuse contract")
        path=ROOT/record["original_figure"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record["original_sha256"]:
            raise AssertionError((row["city"],"original figure hash"))
        source_path=ROOT/record["source_record"]
        source_bytes=source_path.read_bytes()
        if record["source_hash_convention"]=="LF-normalized":
            source_bytes=source_bytes.replace(b"\r\n",b"\n")
        elif record["source_hash_convention"]!="exact-bytes":
            raise AssertionError((row["city"],"unknown source hash convention"))
        if hashlib.sha256(source_bytes).hexdigest()!=record["source_sha256"]:
            raise AssertionError((row["city"],"source hash"))
        if (record["display_width_px"],record["image_area_height_px"])!=("220","160"):
            raise AssertionError("row-15 image geometry")
    return reuse

def hk_static_r2_reuse(rows, rid):
    with HK_STATIC_R2_MAPPING.open(newline="",encoding="utf-8") as f:
        records={r["row_id"]:r for r in csv.DictReader(f)}
    if set(records)!={"12","13"}:
        raise AssertionError("corrected R2 Hong Kong static mapping")
    record=records[rid]
    row=next(r for r in rows if r["city"]=="Hong Kong")
    for field,expected in (("original_figure",record["original_figure"]),
                           ("data_or_figure_source",record["source_record"]),
                           ("source_hash",record["source_sha256"]),
                           ("target_page",record["target_page"]),
                           ("target_anchor",record["target_anchor"])):
        if row[field]!=expected:
            raise AssertionError((rid,field))
    if (record["source_package"],record["reused_existing_figure"],
        record["newly_generated_scientific_figure"])!=("corrected_R2","true","false"):
        raise AssertionError("corrected R2 figure contract")
    if not all(s in row["notes"] for s in
               ("reused_existing_figure=true","newly_generated_scientific_figure=false",
                "source_package=corrected_R2")):
        raise AssertionError("corrected R2 matrix contract")
    figure=ROOT/record["original_figure"]
    source=ROOT/record["source_record"]
    if not figure.is_file() or hashlib.sha256(figure.read_bytes()).hexdigest()!=record["original_sha256"]:
        raise AssertionError((rid,"corrected R2 figure hash"))
    source_bytes=source.read_bytes()
    if record["source_hash_convention"]=="LF-normalized":
        source_bytes=source_bytes.replace(b"\r\n",b"\n")
    elif record["source_hash_convention"]!="exact-bytes":
        raise AssertionError("source hash convention")
    if hashlib.sha256(source_bytes).hexdigest()!=record["source_sha256"]:
        raise AssertionError((rid,"corrected R2 source hash"))
    return {"Hong Kong":record}

def static_path_parity(rid):
    with STATIC_PATH_PARITY.open(newline="",encoding="utf-8") as f:
        rows=[r for r in csv.DictReader(f) if r["row_id"]==rid]
    lookup={(r["city"],r["view"]):r for r in rows}
    if set(lookup)!={(city,view) for city in CITIES for view in ("distribution","network")}:
        raise AssertionError((rid,"static path parity coverage"))
    for r in rows:
        for field in ("figure","source_record"):
            if not (ROOT/r[field]).is_file():raise FileNotFoundError(r[field])
        if hashlib.sha256((ROOT/r["figure"]).read_bytes()).hexdigest()!=r["sha256"]:
            raise AssertionError((rid,r["city"],r["view"],"figure hash"))
        if r["original_preserved"]!="yes":raise AssertionError("original figure preservation")
    return lookup

def component_preview_cell(r, rid, reused):
    reuse_record = reused.get(r["city"]) if reused else None
    primary = reuse_record["original_figure"] if reuse_record else r["preview_path"]
    alt = ("Hong Kong accepted bounded ADMM R3 four-OD residual, objective versus LP, and physical-flow preview; historical ten-OD R2 remains gated."
           if rid=="18" and r["city"]=="Hong Kong" else
           r["city"]+" saved physical-to-finite-graph construction preview"
           if rid=="14" else
           r["city"]+" Phase-I artificial-flow and Phase-II objective traces"
           if rid=="16" else
           r["city"]+" Phase-II / CG-RMP objective versus arc-flow LP reference"
           if rid=="15" else
           "Hong Kong saved bounded H1 "+r["row_title"]+" figure"
           if reuse_record else r["city"]+" "+r["row_title"]+" preview")
    paired = rid == "05" and r["city"] in GPS_PAIR_SECONDARY
    cell = ('<td width="266"'+(' height="160" valign="middle"' if reused else '')+
            (' class="gps-evidence-pair"' if paired else '')+
            ' align="center"><a href="'+esc(FINITE_FIGURES[r["city"]]["construction"][0] if rid=="14" else row_target(r))+'"><img'+
            (' class="gps-paired-preview"' if paired else '')+' src="'+esc(primary)+
            '" width="'+('118' if paired else '220')+'" alt="'+esc(alt)+'"></a>')
    if paired:
        figure,target,secondary_alt,_=GPS_PAIR_SECONDARY[r["city"]]
        if not (ROOT/figure).is_file():
            raise FileNotFoundError(figure)
        cell += (' <a href="'+esc(target)+'"><img class="gps-paired-preview" src="'+
                 esc(figure)+'" width="118" alt="'+esc(secondary_alt)+'"></a>')
    return cell+'</td>'

def finite_preview_row(kind, row_class):
    cells=[]
    for city in CITIES:
        original,scope=FINITE_FIGURES[city][kind]
        if not (ROOT/original).is_file():raise FileNotFoundError(original)
        preview=(original if kind=="flow" else
                 'docs/assets/homepage_finite_atlas_r1/'+FINITE_SLUG[city]+'_'+kind+'.png')
        if not (ROOT/preview).is_file():raise FileNotFoundError(preview)
        cells.append('<td width="266" align="center"><a href="'+esc(original)+'"><img src="'+
                     esc(preview)+'" width="220" alt="'+esc(city+' '+scope+ '; open complete source figure')+
                     '"></a></td>')
    return '<tr class="'+row_class+'">'+''.join(cells)+'</tr>'

def static_path_table(rows, rid, title):
    pair=static_path_parity(rid)
    out=['<table class="home-coverage" data-component="'+rid+'" width="100%"><colgroup>'+('<col width="33%">'*3)+'</colgroup>',
         '<thead><tr><th colspan="3" scope="colgroup" width="800">'+esc(title)+'</th></tr>',
         '<tr>'+''.join('<th scope="col" width="266">'+esc(city)+'</th>' for city in CITIES)+'</tr></thead><tbody>',
         '<tr class="coverage-scope">'+''.join('<td width="266" valign="top">'+esc(r["result_scope"])+'</td>' for r in rows)+'</tr>']
    for view in ("distribution","network"):
        out.append('<tr class="coverage-preview static-path-'+view+'">'+''.join(
            '<td width="266" height="'+('160' if view=='distribution' else '130')+'" valign="middle" align="center">'
            '<a href="'+esc(row_target(r))+'"><img src="'+esc(pair[(r["city"],view)]["figure"])+
            '" width="220" alt="'+esc(r["city"]+' '+r["row_title"]+' '+view+' view')+'"></a></td>'
            for r in rows)+'</tr>')
    out.append('<tr class="coverage-caption"><td colspan="3" align="center"><sub>'+esc(
        "finite-path reconstruction panel" if rid=="12" else "L3 reconstruction/difference panel")+
        '</sub></td></tr>')
    out.append('<tr class="coverage-links">')
    for r in rows:
        city_pair={view:pair[(r["city"],view)] for view in ("distribution","network")}
        out.append('<td width="266"><sub><a href="'+esc(row_target(r))+'">Evidence</a> · '+
                   '<a href="'+esc(city_pair["distribution"]["figure"])+'">Distribution</a> · '+
                   '<a href="'+esc(city_pair["network"]["figure"])+'">Network</a> · '+
                   '<a href="'+esc(city_pair["network"]["source_record"])+
                   '">Source</a></sub></td>')
    out+=['</tr></tbody></table>']
    return '\n'.join(out)

def component_table(matrix, rid):
    title=matrix[(rid,"Boston")]["row_title"]
    rows=[matrix[(rid,city)] for city in CITIES]
    reused=(row15_reuse(rows) if rid=="15" else
            hk_static_r2_reuse(rows,rid) if rid in {"12","13"} else None)
    if rid in {"12","13"}:
        return static_path_table(rows,rid,title)
    def scope_cell(r):
        if rid=="18" and r["city"]=="Hong Kong":
            return ('<td width="266" valign="top"><strong>Accepted bounded ADMM R3 transfer</strong><br>'+
                    esc(r["result_scope"])+
                    '<br><sub>Finite 30-s × 50-step shared-capacity case with modeled OD demand; '
                    'not full-territory assignment or empirical traffic validation.</sub></td>')
        return '<td width="266" valign="top">'+esc(r["result_scope"])+'</td>'
    out=['<table class="home-coverage" data-component="'+rid+'" width="100%"><colgroup>'+('<col width="33%">'*3)+'</colgroup>',
         '<thead><tr><th colspan="3" scope="colgroup" width="800">'+esc(title)+'</th></tr>',
         '<tr>'+''.join('<th scope="col" width="266">'+esc(city)+'</th>' for city in CITIES)+'</tr></thead><tbody>',
         '<tr class="coverage-scope">'+''.join(scope_cell(r) for r in rows)+'</tr>',
         '<tr class="coverage-preview">'+''.join(component_preview_cell(r,rid,reused) for r in rows)+'</tr>',
         '<tr class="coverage-caption">'+(
             ''.join('<td width="266" align="center"><sub>'+esc(reused[r["city"]]["caption"] if r["city"] in reused else r["graphic_type"])+'</sub></td>' for r in rows)
             if reused else
             ''.join('<td width="266" align="center"><sub>'+esc({
                 "Boston":"Network association · saved point projection",
                 "Sioux Falls":"Outside the supplied observation benchmark",
                 "Hong Kong":"Detector-link view · saved point projection",
             }[r["city"]])+'</sub></td>' for r in rows)
             if rid=="05" else
             '<td colspan="3" align="center"><sub>Residuals · log10 absolute objective error against each case’s own LP · original physical-link flow (LP x-axis; ADMM y-axis).</sub></td>'
             if rid=="18" else
             '<td colspan="3" align="center"><sub>'+esc(rows[0]["graphic_type"])+'</sub></td>'
             if len({r["graphic_type"] for r in rows}) == 1 else
             ''.join('<td width="266" align="center"><sub>'+esc(r["graphic_type"])+'</sub></td>' for r in rows)
         )+'</tr>',
         '<tr class="coverage-links">']
    if rid=="14":
        out.insert(5,finite_preview_row("layered","coverage-layered-preview"))
        out[6]=('<tr class="coverage-caption"><td colspan="3" align="center"><sub>'
                'First row: saved physical-to-time construction views. Second row: selected-layer network excerpts. '
                'Time expansion is a finite-model representation also used by same-graph LP and applicable decomposition checks.'
                '</sub></td></tr>')
    if rid=="16":
        out.insert(5,finite_preview_row("flow","coverage-final-flow-preview"))
        out.insert(6,finite_preview_row("path","coverage-path-preview"))
        captions={
          "Boston":"Top: Phase I/II traces; middle: 52/125 positive physical links and same-graph LP objective difference 5.7×10⁻¹⁴; bottom: saved B07 column.",
          "Sioux Falls":"Top and middle: 200-OD example and its final flow; 250-OD results remain in the case page. No independent full-DAG pricing closure is claimed. Bottom: saved XS170 route/arc record.",
          "Hong Kong":"Top: R5 Phase I/II traces; middle: 69/111 positive physical links and same-graph LP agreement with independent 10/10 pricing closure. Bottom: local HK10 display cutaway, not the exported column.",
        }
        out[7]='<tr class="coverage-caption">'+''.join('<td width="266" align="center"><sub>'+esc(captions[c])+'</sub></td>' for c in CITIES)+'</tr>'
    if rid=="17":
        captions={"Boston":"Saved Boston R2 10-OD best bounds by recorded iteration; missing primal points are not interpolated. Feasible primal, but 1.1002% misses the frozen 1% gate. The source history CSV remains private.",
                  "Sioux Falls":"Left: saved 200-OD best bounds by iteration; right: accepted 200-OD 0.0746% and 250-OD 0.3177% gaps.",
                  "Hong Kong":"Saved ten-OD best bounds by recorded iteration; missing primal points are not interpolated; accepted 0.7444% gap."}
        out[5]='<tr class="coverage-caption">'+''.join('<td width="266" align="center"><sub>'+esc(captions[c])+'</sub></td>' for c in CITIES)+'</tr>'
    for r in rows:
        source=r["data_or_figure_source"]
        if rid=="18":
            source=r["preview_path"].removesuffix(".png")+".source.json"
        reuse_record=reused.get(r["city"]) if reused else None
        links=('<a href="'+esc(row_target(r))+'">Evidence</a> · <a href="'+esc(reuse_record["original_figure"] if reuse_record else r["preview_path"])+
               '">'+('Full figure' if reuse_record else 'Full preview')+'</a>')
        if rid == "05" and r["city"] in GPS_PAIR_SECONDARY:
            figure,_,_,link_name=GPS_PAIR_SECONDARY[r["city"]]
            links += ' · <a href="'+esc(figure)+'">'+esc(link_name)+'</a>'
        if rid=="14":
            links += (' · <a href="'+esc(FINITE_FIGURES[r["city"]]["construction"][0])+'">Construction</a>'
                      ' · <a href="'+esc(FINITE_FIGURES[r["city"]]["layered"][0])+'">Layered figure</a>')
        if rid=="16":
            links += (' · <a href="'+esc(FINITE_FIGURES[r["city"]]["flow"][0])+'">Final flow</a>'
                      ' · <a href="'+esc(FINITE_FIGURES[r["city"]]["path"][0])+'">Local path</a>')
        if rid=="18" and r["city"]=="Hong Kong":
            links += (' · <a href="docs/assets/admm_r3/hong_kong/'
                      'hk_admm_r3_residual_objective_physical_flow_triptych.svg">Full three-panel figure</a>')
        if source:links+=' · <a href="'+esc(source)+'">Source record</a>'
        # GitHub strips <small> from README tables, but supports <sub>.
        # Keep the original link names and use a native footnote-size row.
        out.append('<td width="266"><sub>'+links+'</sub></td>')
    out+=['</tr></tbody></table>']
    return '\n'.join(out)

def section03(matrix):
    out=['<a id="coverage"></a>','## 03 / Case coverage and selected evidence','',
      'Most shared row previews use one evidence graphic type and one 600 × 360 source canvas across the three cities. The GPS row pairs accepted city-specific figures; the static finite-path/L3 rows pair saved-result distributions with physical-network (Sioux: schematic topology) views. The Arc-flow LP reference row reuses accepted full figures. Local scales, instance scope and missing stages remain explicit; static BPR/Beckmann and fixed-cost hard-capacity computations are separate branches. [Complete statistics](docs/capabilities.md#comparable-statistics).','']
    for group,old_anchor,ids in ROW_GROUPS:
        new_anchor='section03-'+group.split(' / ',1)[0].lower()
        out += ['<a id="'+old_anchor+'"></a><a id="'+new_anchor+'"></a>','### '+group,'']
        for rid in ids:
            out += [component_table(matrix,rid),'']
    out += ['<a id="e--reusable-outputs-and-tools"></a><a id="section03-vi"></a>','### VI / Reusable outputs and tools','',
      'Reusable queries, exports, saved examples, and checks remain linked from the [Boston](docs/cases/boston.md#reproduction), [Sioux Falls](docs/cases/sioux-falls.md#reproduction), and [Hong Kong](docs/cases/hong-kong.md#reproduction) case entries and the [getting-started guide](docs/getting-started.md).','']
    out += ['<a id="cg-experiments"></a><a id="admm-r2"></a><a id="algorithm-b"></a><a id="distributed-assignment"></a>',
      'The [cross-case CG evidence](docs/methods/space-time-cg.md#cg-experiments), [ADMM](docs/methods/admm-space-time.md), [official tap-b Algorithm B method](docs/methods/origin-based-algorithm-b.md) and [adapter distinction](docs/integrations/taplab-tapb.md), and [Lagrangian records](docs/methods/distributed-assignment.md) retain their full figure families. Boston and Hong Kong have independent 10/10 pricing closure on **different** ten-demand graphs; this is not imputed to the historical Sioux runs.','']
    return '\n'.join(out)

def card(city,stage,label,img,target,method,instance,kind="original"):
    p=ROOT/img
    if not p.is_file():raise FileNotFoundError(img)
    page=target.split('#',1)[0]
    if not (ROOT/page).is_file():raise FileNotFoundError(page)
    preview=("docs/assets/homepage_alignment_r3/atlas/"+hashlib.sha256(img.encode("utf-8")).hexdigest()[:16]+".png") if kind=="original" else img
    # The classic Sioux source is already a lightweight, legible figure. Show
    # its native aspect ratio rather than the padded 5:3 atlas derivative.
    if img=="docs/assets/homepage_evidence_r1/sioux_falls_classic_topology.png":preview=img
    # Keep the saved GPS positions and road projections legible in the atlas.
    if img==BOSTON_GPS_PROJECTION:preview=img
    if not (ROOT/preview).is_file():raise FileNotFoundError(preview)
    row={"city":city,"stage":stage,"asset_path":img,"asset_hash":hashlib.sha256(p.read_bytes()).hexdigest(),"preview_path":preview,"preview_hash":hashlib.sha256((ROOT/preview).read_bytes()).hexdigest(),"label":label,"method":method,"instance":instance,"target_link":target,"kind":kind}
    return row

def depth_badge(c):
    """Reading labels only; no card evidence, method, or result state changes."""
    label=c["label"].lower()
    if c["stage"]=="static":return "A"
    if c["stage"]=="sources":
        return "C" if c["label"] in {
            "GMNS network, zones and access", "Special zones and access",
            "Classic network topology", "Roads, zones and turns",
        } else ""
    if c["stage"]!="finite":return ""
    if "case overview" in label or "case-sequence overview" in label:return ""
    if "network construction and generated columns" in label:return "B · C"
    if "arc-flow lp reference" in label:return "D"
    if "two-phase column generation" in label:return "B"
    if "lagrangian" in label or "admm" in label:return "B · D"
    if "physical to time-expanded" in label or "physical to time-indexed" in label:return "C"
    if "generated time-indexed column" in label or "approved hk10 77-arc column" in label:return "B · C"
    if "phase i" in label or "phase ii" in label:return "B"
    if "shared-capacity" in label:return "D"
    if "final" in label and "flow" in label:return "C · D"
    if "pricing closure" in label:return "B · D"
    return ""

DEPTH_MEANING={
    "A":"Native assignment",
    "B":"Decomposition and distributed computation",
    "C":"Spatial hierarchy and representation",
    "D":"Coordination and verification",
}

# GitHub renders README tables at max-content width and strips colgroup.
# Primer's border-box cells make these groups 800px wide. Three
# integer-pixel columns total 798px; the 800px spanning header takes the rest.
NATIVE_CELL_WIDTH={1:'800',2:'400',3:'266',4:'200'}

def stage_rows(cards, stage_id):
    columns=min(4,len(cards))
    cell_width=NATIVE_CELL_WIDTH[columns]
    out=[]
    for start in range(0,len(cards),columns):
        group=cards[start:start+columns]
        for part in ("title", "preview", "meta", "links"):
            out.append('<tr class="atlas-card-'+part+'-row" data-stage="'+stage_id+'">')
            tag='th' if part=='title' else 'td'
            cell_class='atlas-card-cell' if part=='preview' else 'atlas-'+part+'-cell'
            cell='<'+tag+' width="'+cell_width+'" class="'+cell_class+'"'
            for c in group:
                if part=='title':
                    depth=depth_badge(c)
                    meaning='; '.join(letter+' — '+DEPTH_MEANING[letter] for letter in depth.split(' · ')) if depth else ''
                    badge_key=depth.replace(' · ','_') if depth else ''
                    badge_width='13' if len(depth)==1 else '30'
                    badge=(' <a class="atlas-depth-badge" href="#computational-depth-legend" title="'+esc(meaning)+
                           '" aria-label="'+esc(meaning)+'"><img src="docs/assets/atlas_depth_badges/'+badge_key+
                           '.svg" width="'+badge_width+'" height="11" alt="['+esc(depth)+']"></a>') if depth else ''
                    out.append(cell+' scope="col"><strong>'+esc(c["label"])+
                               '</strong>'+badge+'</th>')
                elif part=='preview':
                    gps_projection = c["asset_path"] == BOSTON_GPS_PROJECTION
                    out.append(cell+'><a href="'+esc(c["target_link"])+
                               '"><img'+(' class="gps-projection-preview"' if gps_projection else '')+
                               ' src="'+esc(c["preview_path"])+'" width="'+('220' if gps_projection else '165')+'" alt="'+
                               esc(c["city"]+' '+c["label"]+'; '+c["instance"])+
                               '"></a></td>')
                elif part=='meta':
                    note=c["instance"] if c["method"] in c["label"] else c["method"]+' · '+c["instance"]
                    out.append(cell+'><small class="atlas-meta">'+esc(note)+'</small></td>')
                else:
                    out.append(cell+'><small class="atlas-links"><a href="'+esc(c["target_link"])+
                               '">Evidence</a> · <a href="'+esc(c["asset_path"])+
                               '">Figure</a></small></td>')
            for _ in range(columns-len(group)):
                out.append('<'+tag+' width="'+cell_width+
                           '" class="atlas-empty" aria-hidden="true"></'+tag+'>')
            out.append('</tr>')
    return '\n'.join(out)

def city_finite_representation_table(city):
    """A city's existing three saved previews, now owned by its case atlas."""
    slug=SLUG[city]
    page={"Boston":"boston", "Sioux Falls":"sioux", "Hong Kong":"hong-kong"}[city]
    detailed='docs/cases/'+page+'-space-time.md'
    headings=("Physical network to finite graph","Selected time layers","Local path / cutaway")
    scopes={
        "Boston":("Bounded 10-OD graph cutaway.","B07 excerpt across selected time layers.",
                  "Saved B07 time-indexed column; <a href=\"docs/assets/three_city_r2/boston_generated_column_time_indexed_path.png\">another retained column view</a>."),
        "Sioux Falls":("Selected finite graph for the historical cases.","XS170 selected-layer example.",
                       "Saved XS170 route and ordered arcs; the 200/250-OD runs are distinct."),
        "Hong Kong":("Turn-aware bounded 10-OD graph cutaway.","Approved HK10 excerpt across selected layers.",
                     "Local HK10 display cutaway, not the full exported CG column; <a href=\"docs/assets/three_city_r2/hong_kong_generated_column_time_indexed_path.png\">approved 77-arc column figure</a>."),
    }[city]
    targets=(detailed+'#from-the-physical-network-to-the-finite-time-expanded-graph',
             detailed+'#from-the-physical-network-to-the-finite-time-expanded-graph',
             detailed+'#a-generated-column-as-a-time-indexed-path')
    out=['<table class="atlas-city-table atlas-finite-representation" data-city="'+slug+'" data-stage="'+slug+'-representation" width="100%"><colgroup>'+('<col width="33.333%">'*3)+'</colgroup><thead>',
         '<tr class="atlas-stage-heading" data-stage="'+slug+'-representation" data-columns="3" data-items="3"><th colspan="3" scope="colgroup" width="800"><a id="'+slug+'-representation"></a>Time-expanded network and path examples</th></tr></thead><tbody>',
         '<tr class="atlas-card-title-row" data-stage="'+slug+'-representation">'+''.join(
             '<th width="266" class="atlas-title-cell" scope="col"><strong>'+esc(h)+'</strong> '+
             '<a class="atlas-depth-badge" href="#computational-depth-legend" title="'+
             esc('B — Decomposition and distributed computation; C — Spatial hierarchy and representation'
                 if i==2 and city!="Hong Kong" else 'C — Spatial hierarchy and representation')+'" aria-label="'+
             esc('B — Decomposition and distributed computation; C — Spatial hierarchy and representation'
                 if i==2 and city!="Hong Kong" else 'C — Spatial hierarchy and representation')+'"><img src="docs/assets/atlas_depth_badges/'+
             ('B_C.svg" width="30" height="11" alt="[B · C]' if i==2 and city!="Hong Kong" else
              'C.svg" width="13" height="11" alt="[C]')+'"></a></th>'
             for i,h in enumerate(headings))+'</tr>']
    image_cells=[]
    for kind in ("construction","layered","path"):
        original,scope=FINITE_FIGURES[city][kind]
        preview='docs/assets/homepage_finite_atlas_r1/'+FINITE_SLUG[city]+'_'+kind+'.png'
        if not (ROOT/original).is_file() or not (ROOT/preview).is_file():
            raise FileNotFoundError((original,preview))
        image_cells.append('<td width="266" height="140" class="atlas-card-cell" align="center" valign="middle"><a href="'+
                           esc(original)+'"><img class="atlas-finite-preview" src="'+esc(preview)+
                           '" width="220" alt="'+esc(city+' '+scope)+'"></a></td>')
    out.append('<tr class="atlas-card-preview-row" data-stage="'+slug+'-representation">'+''.join(image_cells)+'</tr>')
    out.append('<tr class="atlas-card-meta-row" data-stage="'+slug+'-representation">'+''.join(
        '<td width="266" class="atlas-meta-cell"><small class="atlas-meta">'+scope+'</small></td>' for scope in scopes)+'</tr>')
    out.append('<tr class="atlas-card-links-row" data-stage="'+slug+'-representation">'+''.join(
        '<td width="266" class="atlas-links-cell"><small class="atlas-links"><a href="'+esc(targets[i])+
        '">Evidence</a> · <a href="'+esc(FINITE_FIGURES[city][kind][0])+'">Figure</a></small></td>'
        for i,kind in enumerate(("construction","layered","path")))+'</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)

def section04(matrix):
    out=['## 04 / Explore the three cases','',
       'Each city has a complete stage atlas. The same stage order is used throughout; different data, static and finite instance scales are never combined into a single case size.','',
       '<a id="computational-depth-legend"></a>',
       '**A — Native assignment**  ',
       '**B — Decomposition and distributed computation**  ',
       '**C — Spatial hierarchy and representation**  ',
       '**D — Coordination and verification**','',
       'A–D are reading labels for computational depth. City-data and four-stage-demand evidence remain outside A–D. The current repository demonstrates coordination and verification components.','']
    assets=[]
    row15_figures=row15_reuse([matrix[("15",city)] for city in CITIES])
    extra_by={(c,s):[] for c in CITIES for s,_ in STAGES}
    for item in EXTRAS:
        # Keep the historical source figures, but do not repeat comparisons or
        # multiple FW scales in the homepage's one-card-per-method static row.
        if item[1]=="finite" and item[2] in {
            "Physical to time-expanded graph", "Physical to time-indexed movement",
            "Generated time-indexed column", "Approved HK10 77-arc column",
        }:
            continue  # The city representation table carries these links and scopes.
        if item[1]!="static":extra_by[(item[0],item[1])].append(item)
    for city in CITIES:
        slug=SLUG[city]
        out += ['<a id="'+slug+'"></a>','<article class="case-atlas" data-city="'+slug+'">','<h3>'+city+'</h3>',
           '<p>'+esc(ROLE[city])+' <a href="'+esc(CASE_PAGE[city])+'">Open complete case →</a></p>',
           '<a href="'+esc(CASE_PAGE[city])+'"><img class="atlas-cover" src="'+esc(COVER[city])+'" width="780" alt="'+esc(city)+' canonical case cover"></a>',
           '<table class="atlas-quick-facts" width="100%"><colgroup>'+('<col width="25%">'*4)+'</colgroup><thead><tr>'+''.join('<th width="200">'+label+'</th>' for label in ("City/model foundation","Static assignment","Finite time-expanded","Observation/data scope"))+'</tr></thead>',
           '<tbody><tr>'+''.join('<td width="200">'+esc(value)+'</td>' for value in FACTS[city])+'</tr></tbody></table>',
           '<a id="'+slug+'-tools"></a>',
           '<p class="atlas-nav">'+' · '.join(
               '<a href="'+esc(CASE_PAGE[city]+'#reproduction' if sid=="tools" else '#'+slug+'-'+sid)+'">'+esc(name)+'</a>'
               for sid,name in STAGES[:7])+
               ' · <a href="#'+slug+'-representation">Time-expanded network and path examples</a> · '+
               ' · '.join('<a href="'+esc(CASE_PAGE[city]+'#reproduction' if sid=="tools" else '#'+slug+'-'+sid)+'">'+esc(name)+'</a>'
                        for sid,name in STAGES[7:])+'</p>']
        if city=="Sioux Falls":
            compact=(
              ("population","Population, households and activity","Not part of the supplied benchmark"),
              ("transit","Transit and observations","Not part of the supplied benchmark"),
              ("generation","Trip generation","Supplied OD enters downstream methods directly"),
              ("distribution","Trip distribution","Supplied OD enters downstream methods directly"),
              ("mode","Mode choice","Vehicle OD is supplied; no mode-choice run"),
            )
            out += ['<table class="atlas-city-table atlas-benchmark-table" data-city="'+slug+'" width="100%"><colgroup>'+('<col width="33.333%">'*3)+'</colgroup><thead>',
                    '<tr class="atlas-benchmark-heading"><th colspan="3" scope="colgroup" width="800">City-data and four-stage scope</th></tr>',
                    '<tr class="atlas-benchmark-header"><th width="266">Stage</th><th width="266">Scope in Sioux Falls benchmark</th><th width="266">Relevant next entry</th></tr></thead><tbody>']
            for sid,label,scope in compact:
                out.append('<tr class="atlas-benchmark-row"><td width="266"><a id="'+slug+'-'+sid+'"></a>'+esc(label)+'</td><td width="266">'+esc(scope)+
                           '</td><td width="266"><a href="#'+slug+'-static">Static assignment</a></td></tr>')
            out.append('</tbody></table>')
        for stage,name in STAGES:
            if stage=="tools":continue
            if city=="Sioux Falls" and stage in {"population","transit","generation","distribution","mode"}:continue
            if stage=="finite":
                out += ['<p class="atlas-branch-transition">Static BPR/Beckmann assignment and the fixed-cost, hard-capacity time-expanded optimization below are independent mathematical branches. The next table shows the latter\'s graph representation, which also supports its arc-flow LP and applicable decomposition methods; example paths or generated columns are recorded outputs, not universal advance inputs.</p>',
                        '<a id="finite-network-representation-and-local-path-atlas"></a>' if city=="Boston" else '',
                        city_finite_representation_table(city)]
            cards=[]
            for rid in STAGE_ROWS[stage]:
                if stage=="finite" and rid=="14":
                    continue  # The moved three-view representation table replaces this repeated card.
                # This bounded R2 intake changes only the two Section 03 cells;
                # the existing Section 04 case atlas is intentionally unchanged.
                if city=="Hong Kong" and stage=="static" and rid in {"12","13"}:
                    continue
                r=matrix[(rid,city)]
                if r["status"] in {"outside benchmark","not demonstrated"}:continue
                target=r["target_page"]+("#"+r["target_anchor"] if r["target_anchor"] else "")
                label=r["row_title"].replace('01 / ','').replace('02 / ','').replace('03 / ','').replace('04 / ','')
                if stage=="static" and city=="Sioux Falls" and rid=="10":
                    asset=card(city,stage,label,
                        "docs/assets/homepage_alignment_r3/sioux_historical_fw_summary.png",
                        "docs/datasets/sioux-static-fw.md",label,
                        "528-OD historical approximate result; saved objective and gap", "saved-result summary")
                elif stage=="static" and city=="Boston" and rid=="13":
                    asset=card(city,stage,label,
                        "docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_flow.png",
                        target,label,"ABS_PLANNED 26-OD; rank-26 diagnostic")
                elif stage=="static" and city=="Sioux Falls" and rid=="13":
                    asset=card(city,stage,label,
                        "docs/assets/homepage_alignment_r3/sioux_native_l3_rank50_link_flows.png",
                        target,label,"rank-50 diagnostic; not UE")
                elif stage=="finite" and rid=="15":
                    # The accepted Phase-II figure displays its own LP reference;
                    # keep the old row preview as a historical asset, not this card.
                    asset=card(city,stage,label,
                        row15_figures[city]["original_figure"],target,label,
                        r["result_scope"],"reused saved figure")
                else:
                    asset=card(city,stage,label,r["preview_path"],target,label,r["result_scope"],"R2 row preview")
                cards.append(asset);assets.append(asset)
            for item in extra_by[(city,stage)]:
                asset=card(*item)
                cards.append(asset);assets.append(asset)
            stage_id=slug+'-'+stage
            extra_anchor='<a id="hong-kong-cg-r5"></a>' if city=="Hong Kong" and stage=="finite" else ''
            columns=max(1,min(4,len(cards)))
            col_width={1:'100%',2:'50%',3:'33.333%',4:'25%'}[columns]
            out.append('<table class="atlas-city-table" data-city="'+slug+'" data-stage="'+stage_id+'" width="100%"><colgroup>'+(('<col width="'+col_width+'">')*columns)+'</colgroup><thead>')
            out.append('<tr class="atlas-stage-heading" data-stage="'+stage_id+'" data-columns="'+str(columns)+'" data-items="'+str(len(cards))+'"><th colspan="'+str(columns)+'" scope="colgroup" width="800"><a id="'+stage_id+'"></a>'+extra_anchor+name+'</th></tr></thead><tbody>')
            if not cards:
                out.append('<tr class="atlas-scope-row"><td colspan="'+str(columns)+'">'+("Outside the supplied Sioux Falls benchmark; no city-data stage was executed." if city=="Sioux Falls" else "No accepted result for this stage in the bounded case.")+'</td></tr>')
            else:out.append(stage_rows(cards,stage_id))
            out.append('</tbody></table>')
        out += ['</article>','']
    out += ['[All retained scientific figure families](docs/visualizations.md) · [Full technical walkthrough](docs/full-walkthrough.md).','']
    return '\n'.join(out),assets

def update_readme():
    matrix=load_matrix()
    text=README.read_text(encoding='utf-8')
    if not text.startswith("# Mobility Computation Lab\n") or text.count('<a id="what-this-project-adds"></a>')!=1:
        raise AssertionError('homepage hero boundary')
    text=HERO+text[text.index('<a id="what-this-project-adds"></a>'):]
    existing_axes=text.find('<a id="two-axes"></a>')
    if existing_axes>=0:
        text=text[:existing_axes]+text[text.index('<a id="coverage"></a>',existing_axes):]
    start=text.index('<a id="coverage"></a>')
    end=text.index('<a id="run-your-input"></a>',start)
    atlas,assets=section04(matrix)
    body=section03(matrix)+atlas
    new=text[:start]+TWO_AXES+body+'\n'+text[end:]
    if new.count('[Hao Zheng](https://scholarhaozheng.github.io/)')!=1 or 'Project author:' in new[:new.index('<a id="what-this-project-adds"></a>')]:
        raise AssertionError('author introduction')
    README.write_text(new,encoding='utf-8',newline='\n')
    return assets

if __name__=='__main__':
    assets=update_readme();print(f"Composed Section 03 and {len(assets)} city-owned atlas cards")
