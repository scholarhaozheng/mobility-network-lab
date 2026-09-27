"""Solver-free, relocation-safe audit of the Hong Kong public candidate bundle."""
import argparse
import csv
import hashlib
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def table(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def j(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(root):
    root=root.resolve()
    failures=[]
    checks={}
    def check(name,good):
        checks[name]=bool(good)
        if not good:failures.append(name)
    figures=sorted((root/"figures").glob("*.source.json"))
    check("figure_count_18",len(figures)==18)
    for meta in figures:
        x=j(meta);name=x["figure_id"]
        svg=root/x["svg"];png=root/x["png"]
        check(f"figure_files_{name}",svg.is_file() and png.is_file())
        if svg.is_file():
            try:ET.parse(svg);valid=True
            except ET.ParseError:valid=False
            check(f"svg_xml_{name}",valid)
        if png.is_file():
            b=png.read_bytes()[:24]
            check(f"png_900x500_{name}",len(b)==24 and b[:8]==b"\x89PNG\r\n\x1a\n" and struct.unpack(">II",b[16:24])==(900,500))
        for rel,expected in x["input_sha256"].items():
            p=(root/rel).resolve()
            check(f"source_hash_{name}_{rel}",p.is_file() and root in p.parents and sha(p)==expected)
    banned=[p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
            and (p.suffix.lower() in {".exe",".npz",".kmz",".gml",".pdf",".zip"}
                 or "trajectory_points" in p.name.lower()
                 or "urban_nav_viterbi_points" in p.name.lower()
                 or "building_allocation_private" in p.name.lower())]
    check("private_or_raw_files_absent",not banned)
    leaked=[]
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md",".json",".csv",".py",".geojson"}:
            content=p.read_text(encoding="utf-8-sig",errors="replace")
            if re.search(r"[A-Za-z]:\\(?:Users|mobility_computation_lab_v2)",content):
                leaked.append(p.relative_to(root).as_posix())
    check("local_absolute_paths_absent",not leaked)
    a=j(root/"phase_a/PHASE_A_CHECKPOINT.json")
    b=j(root/"phase_b/PHASE_B_CHECKPOINT.json")
    stat=j(root/"phase_b/STATIC_ASSIGNMENT_COMPARISON.json")["full"]
    check("phase_a_static_accepted",a["phase_a_status"]=="ACCEPTED")
    check("phase_b_four_stage_accepted",b["phase_b_status"]=="ACCEPTED")
    check("full_static_independent",stat["status"]=="ACCEPTED" and stat["positive_od"]==8930
          and stat["prohibited_turns_in_used_paths"]==0
          and stat["max_od_path_conservation_residual_pce"]<1e-6)
    case=root/"phase_c/case"
    arcs=table(case/"dynamic_arc.csv");demand=table(case/"dynamic_demand.csv")
    manifest=j(case/"case.json")
    signature=hashlib.sha256((case/"dynamic_arc.csv").read_bytes()+b"\0"+(case/"dynamic_demand.csv").read_bytes()).hexdigest()
    check("dynamic_input_hashes",sha(case/"dynamic_arc.csv")==manifest["arc_sha256"] and sha(case/"dynamic_demand.csv")==manifest["demand_sha256"])
    check("dynamic_model_signature",signature==manifest["model_signature"])
    byarc={r["arc_id"]:r for r in arcs}
    physical={r["link_id"] for r in table(case/"selected_physical_links.csv")}
    check("physical_link_mapping",all(r["physical_link_id"] in physical for r in arcs if r["arc_type"]=="movement"))
    check("dynamic_forward_time",all(float(r["to_time"])>=float(r["from_time"]) for r in arcs))
    flows=table(root/"phase_c/reference_positive_commodity_arc_flow.csv")
    balance=defaultdict(float);usage=defaultdict(float);obj=0.
    for f in flows:
        arc=byarc[f["arc_id"]];q=float(f["flow"])
        balance[f["demand_id"],arc["from_node_time_id"]]+=q
        balance[f["demand_id"],arc["to_node_time_id"]]-=q
        usage[f["arc_id"]]+=q;obj+=q*float(arc["cost"])
    for d in demand:
        did=d["demand_id"];q=float(d["volume"])
        balance[did,f"source_{did}_t0"]-=q
        balance[did,f"sink_{did}_t50"]+=q
    lp=j(root/"phase_c/ARC_FLOW_REFERENCE_SUMMARY.json")
    check("reference_lp_balance",max(map(abs,balance.values()),default=0)<1e-6)
    check("reference_lp_capacity",max((usage[aid]-float(a["capacity"]) for aid,a in byarc.items()),default=0)<1e-6)
    check("reference_lp_objective",abs(obj-lp["objective_value"])<1e-6)
    lag=j(root/"phase_c/lagrangian_evaluation.json")
    check("lagrangian_independent",lag["status"]=="PASS" and lag["duality_gap"]<=.01
          and abs(lag["objective_recomputed"]-obj)<1e-6
          and lag["dual_recomputed"]<=obj+1e-6)
    cg=j(root/"phase_c/cg_run/full_cg_v1_run_summary.json")
    admm=j(root/"phase_c/admm_run/result.json")
    check("cg_gated_truthful",cg["phase_i_status"]=="PHASE_I_BLOCKED"
          and cg["phase_i_artificial_flow_final"]>0 and cg["phase_ii_rounds_attempted"]==0)
    check("admm_gated_truthful",admm["status"]=="NOT_CONVERGED" and admm["completed_iterations"]==0)
    rights=table(root/"HONG_KONG_SOURCE_AND_RIGHTS_REGISTER.csv")
    check("urbannav_rights_private",any(x["source_id"]=="URBANNAV_TST_GT" and x["public_decision"]=="PRIVATE_RAW_AND_POINT_LEVEL" for x in rights))
    return {"status":"PASS" if not failures else "FAIL","checks":checks,"failures":failures,
            "figure_count":len(figures),"dynamic_arcs":len(arcs),"dynamic_od":len(demand),
            "reference_objective_recomputed":obj,"banned_files":banned,"path_leaks":leaked,
            "solver_calls":0}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--output")
    args=parser.parse_args()
    result=verify(Path(args.root))
    if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","figure_count","dynamic_arcs","dynamic_od","reference_objective_recomputed","failures","solver_calls")},indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 1)
