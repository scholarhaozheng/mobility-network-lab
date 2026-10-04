"""Create one shortest-path seed per OD using input costs only, never LP output."""
import csv
import hashlib
import json
import sys
from pathlib import Path

R=Path(__file__).resolve().parent
C=R/"phase_c"
CASE=C/"case"
sys.path.insert(0,str(R/"algorithms/frozen_lagrangian_r3"))
from problem_contract import load,shortest_path


def rows(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


p=load(CASE/"dynamic_arc.csv",CASE/"dynamic_demand.csv")
arcs=p["arcs"]
seeds=[]
for k,d in enumerate(p["demands"]):
    value,path=shortest_path(p,k,p["cost"])
    selected=[arcs[a] for a in path]
    if not selected or selected[0]["arc_type"]!="source_connector" or selected[-1]["arc_type"]!="sink_connector":
        raise RuntimeError(f"broken input-only shortest path {d['demand_id']}")
    movement=[a["physical_link_id"] for a in selected if a["arc_type"]=="movement"]
    times=[a["from_time"] for a in selected]
    times.append(selected[-1]["to_time"])
    seeds.append({"column_id":f"hk_seed_{d['demand_id']}",
                  "demand_id":d["demand_id"],"origin_node_id":d["origin_node_id"],
                  "destination_node_id":d["destination_node_id"],
                  "departure_time":0,"arrival_time":selected[-1]["from_time"],
                  "travel_time":int(selected[-1]["from_time"]),"generalized_cost":value,
                  "node_sequence":"|".join(a["from_physical_node_id"] for a in selected)+"|"+selected[-1]["to_physical_node_id"],
                  "link_sequence":"|".join(movement),"time_sequence":"|".join(map(str,times)),
                  "arc_sequence":"|".join(a["arc_id"] for a in selected)})
with (CASE/"dynamic_columns.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(seeds[0]));w.writeheader();w.writerows(seeds)
reference=json.loads((C/"ARC_FLOW_REFERENCE_SUMMARY.json").read_text(encoding="utf-8"))
manifest={"benchmark_id":"HK_TST_JORDAN_10OD_30S_50STEPS_R2_R4",
          "scope_label":"HONG_KONG_BOUNDED_FOUR_STAGE_DRIVE_FINITE_CASE",
          "network_mode":"explicit_allowed_network",
          "model_schema_version":"gmns_dynamic_explicit_allowed_network_v2_seconds",
          "model_signature":p["model_signature"],
          "seed_pool_signature":hashlib.sha256((CASE/"dynamic_columns.csv").read_bytes()).hexdigest(),
          "dynamic_data_dir":str(CASE),"demand_file":str(CASE/"dynamic_demand.csv"),
          "dynamic_arc_file":str(CASE/"dynamic_arc.csv"),
          "current_candidate_pool_file":str(CASE/"dynamic_columns.csv"),
          "output_root":str(C/"cg_run"),
          "max_phase_i_rounds":20,"max_phase_ii_rounds":25,
          "max_candidates_per_demand_per_round":4,
          "runtime_cap_seconds":300,
          "phase_ii_pricing_mode":"k_shortest",
          "phase_ii_add_policy":"add_best_one_per_demand",
          "k_shortest_k":4,"max_phase_ii_candidates_per_demand":4,
          "max_phase_ii_candidates_per_round":40,
          "strict_phase_ii_candidate_round_cap":False,
          "no_mutate":True,"reference_comparison_policy":"objective_level_when_reference_available",
          "stop_certificate_policy":"always_write","claim_boundary_policy":"bounded_finite_fixture_only",
          "arc_lp_reference_objective":reference["objective_value"],
          "arc_lp_reference_summary_path":str(C/"ARC_FLOW_REFERENCE_SUMMARY.json"),
          "reference_and_cg_share_exact_dynamic_graph":True,
          "seed_columns_define_network":False,"no_full_assignment_claim":True,
          "no_global_convergence_claim":True,"no_exact_flow_pattern_reproduction_claim":True,
          "workflow_provenance":{"seed_mode":"input_cost_shortest_path_only","seed_k":1,
                                 "reference_paths_flows_or_duals_used":False}}
(C/"cg_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"seed_paths":len(seeds),"seed_costs":{r["demand_id"]:r["generalized_cost"] for r in seeds},
                  "graph_signature":p["model_signature"]},indent=2))
