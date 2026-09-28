#!/usr/bin/env python3
"""Build matched public tables from accepted saved records; no model execution."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/data/three_city_r1"
OUT.mkdir(parents=True,exist_ok=True)


def path(rel: str) -> Path:
    result=ROOT/rel
    if not result.is_file(): raise FileNotFoundError(rel)
    return result


def sha(rel: str) -> str:
    return hashlib.sha256(path(rel).read_bytes()).hexdigest()


def js(rel: str) -> dict:
    return json.loads(path(rel).read_text(encoding="utf-8"))


def rows(rel: str) -> list[dict]:
    with path(rel).open(newline="",encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def emit(name: str, data: list[dict], sources: list[str], note: str) -> None:
    fields=list(data[0])
    out=OUT/(name+".csv")
    with out.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader();writer.writerows(data)
    md="| "+" | ".join(fields)+" |\n|"+"|".join(["---"]*len(fields))+"|\n"
    for row in data:
        md+="| "+" | ".join(str(row[f]).replace("|","/") for f in fields)+" |\n"
    (OUT/(name+".md")).write_text(md+"\n"+note+"\n",encoding="utf-8")
    record={"table_id":name,"status":"saved-record extraction and source-qualified interpretation",
            "source_sha256":{rel:sha(rel) for rel in sorted(set(sources))},
            "builder_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "csv_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"scope_note":note,
            "scientific_solver_rerun":False}
    (OUT/(name+".source.json")).write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    b_nodes="examples/boston/gmns_exchange_r1/data/node.csv"
    b_links="examples/boston/gmns_exchange_r1/data/link.csv"
    b_zones="examples/boston/gmns_exchange_r1/data/zone.csv"
    h_base="docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_a/instance/"
    h_nodes=h_base+"node.csv"; h_links=h_base+"link.csv"; h_zones=h_base+"zone.csv"
    h_parent=h_base+"super_zone.csv"
    h_selected="docs/assets/hong_kong/full_stack_r5/case/selected_physical_links.csv"
    bn=rows(b_nodes);bl=rows(b_links);bz=rows(b_zones)
    hn=rows(h_nodes);hl=rows(h_links);hz=rows(h_zones)
    hp=rows(h_parent)
    bphysical=sum(r["node_type"]=="physical" for r in bn)
    hphysical=sum(r["node_type"]=="physical_road" for r in hn)
    bdirected=sum(r["mcl_link_class"]=="physical" for r in bl)
    hdirected=sum(r["mcl_link_class"]=="physical" for r in hl)
    b_parent_count=len({r["super_zone"] for r in bz if r["super_zone"]})
    b_fine_count=len(bz)-b_parent_count
    if (bphysical,bdirected,b_fine_count,b_parent_count,len(bn)-bphysical,len(bl)-bdirected)!=(2852,5091,177,9,177,354):
        raise ValueError("Boston GMNS identity changed")
    h_fine_count=len(hz)-len(hp)
    if (hphysical,hdirected,h_fine_count,len(hp),len(hn)-hphysical,len(hl)-hdirected)!=(780,1239,95,10,95,190):
        raise ValueError("Hong Kong GMNS identity changed")
    s_links="examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv"
    sl=rows(s_links)
    s_nodes={r[k] for r in sl for k in ("from_node_id","to_node_id")}
    if (len(sl),len(s_nodes))!=(76,24):raise ValueError("Sioux static graph changed")
    gmns=[
        {"city":"Boston","study_role":"bounded real-city GMNS / four-stage case","physical_nodes":bphysical,
         "directed_physical_links":bdirected,"fine_zones":b_fine_count,"parent_zones":b_parent_count,
         "centroids":len(bn)-bphysical,"nonphysical_connectors":len(bl)-bdirected,
         "transit_stops_routes":"3,553 referenced stops / 112 routes (dated GTFS slice)",
         "observation_records":"581 GPS path-link associations; 56 planned-shape links",
         "data_evidence_status":"Verified bounded case; not a calibrated citywide forecast"},
        {"city":"Sioux Falls","study_role":"classic supplied vehicle-OD road benchmark","physical_nodes":len(s_nodes),
         "directed_physical_links":len(sl),"fine_zones":"Not part of this benchmark",
         "parent_zones":"Not part of this benchmark","centroids":"Not part of this benchmark",
         "nonphysical_connectors":"Not part of this benchmark","transit_stops_routes":"Not part of this benchmark",
         "observation_records":"Not part of this benchmark","data_evidence_status":"Verified static topology; historical selected-OD finite cases are separate"},
        {"city":"Hong Kong","study_role":"bounded turn-aware real-city engineering case","physical_nodes":hphysical,
         "directed_physical_links":hdirected,"fine_zones":h_fine_count,"parent_zones":len(hp),
         "centroids":len(hn)-hphysical,"nonphysical_connectors":len(hl)-hdirected,
         "transit_stops_routes":"183 stops / 294 routes (pilot service layer)",
         "observation_records":"50 detector lane snapshot records; UrbanNav point data private",
         "data_evidence_status":"Verified bounded case; activity and demand use graded assumptions"},
    ]
    b_eval="algorithms/origin_based_algorithm_b/accepted_results/boston_b1_evaluation.json"
    s_eval="algorithms/origin_based_algorithm_b/accepted_results/sioux_evaluation.json"
    h_eval="docs/assets/hong_kong/full_stack_r5/r2r4_baseline/phase_b/STATIC_ASSIGNMENT_COMPARISON.json"
    be=js(b_eval);se=js(s_eval);he=js(h_eval)["full"]
    static=[
        {"city":"Boston B1","static_od_pairs":be["positive_od"],"assigned_demand_and_unit":f"{be['total_demand']:.6f} PCE / 2 h",
         "cost_model":"static BPR / Beckmann","fw_status":"Verified bounded case",
         "algorithm_b_status":"Verified bounded case; task-local TAPLab-compatible lossless adapter",
         "objective_gap_certificate":f"Beckmann {be['objective']:.9f} PCE-min; independent relative gap {be['relative_gap']:.3g}",
         "physical_link_back_projection":f"Verified; max path/link mismatch {be['max_link_mismatch']:.3g} PCE"},
        {"city":"Sioux Falls","static_od_pairs":se["positive_od"],"assigned_demand_and_unit":f"{se['total_demand']:.0f} vehicles",
         "cost_model":"static BPR / Beckmann","fw_status":"Verified historical run; input-identity caveat",
         "algorithm_b_status":"Verified; official TAPLab registered-adapter parity",
         "objective_gap_certificate":f"Beckmann {se['objective']:.9f} vehicle-min; independent relative gap {se['relative_gap']:.3g}",
         "physical_link_back_projection":f"Verified; max path/link mismatch {se['max_link_mismatch']:.3g} vehicles"},
        {"city":"Hong Kong","static_od_pairs":he["positive_od"],"assigned_demand_and_unit":f"{he['total_drive_pce']:.6f} PCE / 1 h",
         "cost_model":"turn-aware static BPR / Beckmann","fw_status":"Verified bounded case",
         "algorithm_b_status":"Verified bounded case; task-local lossless adapter",
         "objective_gap_certificate":f"Beckmann {he['fw_beckmann_objective']:.9f} PCE-min; independent relative gap {he['frozen_evaluator_relative_gap']:.3g}",
         "physical_link_back_projection":f"Verified; max path/link mismatch {he['max_algorithm_b_physical_path_reconstruction_residual_pce']:.3g} PCE"},
    ]
    b_val="docs/assets/boston/space_time_cg_r4/data/validation_summary.json"
    h_frz="docs/assets/hong_kong/full_stack_r5/HK_CG_R5_CASE_FREEZE.json"
    h_closure="docs/assets/hong_kong/full_stack_r5/closure/INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json"
    bv=js(b_val);hf=js(h_frz);hc=js(h_closure)
    if not bv["independent_pricing_closure_pass"] or not hc["independent_pricing_closure_established"]:
        raise ValueError("Accepted closure status changed")
    s200="docs/datasets/sioux-200od.md";s250="docs/datasets/sioux-250od.md"
    def number_in_table(rel: str, label: str) -> str:
        match=re.search(r"^\|\s*"+re.escape(label)+r"\s*\|\s*([^|]+)\|",path(rel).read_text(encoding="utf-8"),re.M)
        if not match:raise ValueError(f"missing {label}: {rel}")
        return match.group(1).strip()
    finite=[
        {"city":"Boston","physical_subnetwork_nodes_links":f"{bv['physical_nodes']} / {bv['physical_directed_links']}",
         "dynamic_od_demands":bv["demands"],"time_step_horizon":f"{bv['time_step_seconds']} s / {bv['horizon_steps']} steps",
         "dynamic_nodes_arcs":"9,110 / 22,217","reference_lp_objective_vehicle_min":f"{bv['identical_graph_arc_lp_reference_objective']:.12f}",
         "cg_phase_i_zero_round":bv["phase_i_zero_round"],"final_column_pool":bv["r4_final_columns"],
         "lagrangian_status_gap":"Gated; 1.1002% exceeds frozen 1% gate",
         "admm_status_residual_gate":"Verified bounded case; R2_S own-LP gap 6.68e−6",
         "independent_pricing_closure":"Independent pricing closure established; 10/10"},
        {"city":"Sioux Falls (200 / 250 OD)","physical_subnetwork_nodes_links":f"24 / {number_in_table(s200,'Selected physical links')} or {number_in_table(s250,'Selected physical links')}",
         "dynamic_od_demands":"200 / 250","time_step_horizon":"Not stated in released summary",
         "dynamic_nodes_arcs":f"{number_in_table(s200,'Dynamic nodes')} / {number_in_table(s200,'Dynamic arcs')}; {number_in_table(s250,'Dynamic nodes')} / {number_in_table(s250,'Dynamic arcs')}",
         "reference_lp_objective_vehicle_min":f"{number_in_table(s200,'Recomputed path-flow objective')} / {number_in_table(s250,'Recomputed path-flow objective')}",
         "cg_phase_i_zero_round":"51 / 62","final_column_pool":f"{number_in_table(s200,'Final columns')} / {number_in_table(s250,'Final columns')}",
         "lagrangian_status_gap":"Verified bounded case; 0.0746% / 0.3177% duality gaps",
         "admm_status_residual_gate":"Verified bounded case; R2_S own-LP gaps 6.30e−6 / 7.16e−6",
         "independent_pricing_closure":"Not established"},
        {"city":"Hong Kong","physical_subnetwork_nodes_links":f"{len({r[k] for r in rows(h_selected) for k in ('from_node_id','to_node_id')})} / {len(rows(h_selected))}",
         "dynamic_od_demands":hf["demand_count"],"time_step_horizon":f"{hf['time_step_seconds']} s / {hf['horizon_steps']} steps",
         "dynamic_nodes_arcs":f"{hf['dynamic_nodes']:,} / {hf['dynamic_arcs']:,}",
         "reference_lp_objective_vehicle_min":f"{hf['reference_lp_objective_vehicle_minutes']:.12f}",
         "cg_phase_i_zero_round":12,"final_column_pool":25,
         "lagrangian_status_gap":"Verified bounded case; 0.7444% duality gap",
         "admm_status_residual_gate":"Gated; first local conservation residual 0.082467622 PCE",
         "independent_pricing_closure":"Independent pricing closure established; 10/10"},
    ]
    cap_rows=[
        ("GMNS physical network",["Verified","Verified","Verified bounded case"]),
        ("hierarchical zones / parent zones",["Verified bounded case","Not part of this benchmark","Verified bounded case"]),
        ("population / households / activity",["Verified bounded case","Not part of this benchmark","Verified bounded case"]),
        ("transit / pedestrian layer",["Verified bounded case","Not part of this benchmark","Verified bounded case"]),
        ("GPS / detector / trajectory evidence",["Verified bounded case","Not part of this benchmark","Verified bounded case"]),
        ("four-stage demand",["Verified bounded case","Not part of this benchmark","Verified bounded case"]),
        ("static Frank–Wolfe",["Verified bounded case","Verified","Verified bounded case"]),
        ("origin-based / Algorithm B",["Verified bounded case","Verified","Verified bounded case"]),
        ("full-path / compression evidence",["Verified bounded case","Verified bounded case","Not demonstrated"]),
        ("finite arc-flow LP",["Verified bounded case","Verified bounded case","Verified bounded case"]),
        ("column generation",["Verified bounded case","Verified bounded case","Verified bounded case"]),
        ("Lagrangian decomposition",["Gated","Verified bounded case","Verified bounded case"]),
        ("ADMM",["Verified bounded case","Verified bounded case","Gated"]),
        ("reference-objective agreement",["Reference-objective agreement","Reference-objective agreement","Reference-objective agreement"]),
        ("independent pricing closure",["Independent pricing closure established","Not established","Independent pricing closure established"]),
        ("clean-room / independent evaluator",["Verified bounded case","Verified bounded case","Verified bounded case"]),
    ]
    capabilities=[{"capability":name,"Boston":states[0],"Sioux Falls":states[1],"Hong Kong":states[2]} for name,states in cap_rows]
    current_docs=["docs/cases/boston.md","docs/cases/sioux-falls.md","docs/cases/hong-kong.md",
                  "docs/cases/boston-space-time.md","docs/cases/sioux-space-time.md","docs/cases/hong-kong-space-time.md"]
    emit("THREE_CITY_GMNS_STATISTICS",gmns,[b_nodes,b_links,b_zones,s_links,h_nodes,h_links,h_zones,h_parent,
         "docs/datasets/boston-gmns-exchange.md","docs/datasets/boston-central.md","docs/cases/hong-kong.md"],
         "Counts refer to distinct current city-data instances. Sioux Falls has supplied road/OD benchmark input, not a demographic or transit build. Observation record types differ and are not pooled.")
    emit("THREE_CITY_STATIC_ASSIGNMENT_STATISTICS",static,[b_eval,s_eval,h_eval],
         "Static BPR/Beckmann objectives are case- and unit-specific; no cross-city objective leaderboard or comparison with finite fixed-cost vehicle-minute objectives is implied.")
    emit("THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS",finite,[b_val,h_frz,h_closure,s200,s250,h_selected,
         "docs/cases/boston-space-time.md","docs/cases/sioux-space-time.md","docs/cases/hong-kong-space-time.md"],
         "Each row is a different bounded finite graph. Sioux 200/250 values are paired in consistent order; its retained historical pricing closure is not established. Dynamic objectives are vehicle-minutes on separate graphs.")
    emit("THREE_CITY_CAPABILITY_MATRIX",capabilities,current_docs,
         "Status labels describe only the executed scope linked by each city case; a gated or absent result is not upgraded for symmetry. ADMM in Hong Kong remains gated.")
    print("Built four source-qualified cross-city CSV/Markdown tables")


if __name__=="__main__":main()
