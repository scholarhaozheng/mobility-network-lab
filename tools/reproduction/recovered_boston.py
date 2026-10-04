"""Portable Boston recovery entry points; inspect never calls an optimizer.

run executes a declared computation. inspect verifies retained numerical evidence.
verify checks a prior output. Full source acquisition and prepared replay have
separate boundaries; see docs/reproduction/recovered-boston.md.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, importlib.util, json, math, os, shutil, subprocess, sys
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))
def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")
def table(path, records):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer=csv.DictWriter(stream, fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj
def invoke(root, out, label, argv, env=None):
    result=subprocess.run([sys.executable,"-B",*map(str,argv)],cwd=root,text=True,capture_output=True,env=env)
    (out/(label+".log")).write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
    if result.returncode: raise RuntimeError(label+" failed; inspect its log")
def close(a,b,tol=1e-7): return math.isfinite(float(a)) and abs(float(a)-float(b))<=tol

# A missing fresh product is a failed reproduction, never permission to inspect
# a historical result. These contracts are independent of output-file presence.
FRESH_CONTRACTS = {
    "boston-gmns-exchange-r1": ("fresh_structural_validation", ("exchange_validation.json",)),
    "boston-acs-population-allocation-r1": ("fresh_prepared_crosswalk_arithmetic", ("population_or_household_by_zone.csv", "trip_generation_by_purpose.csv")),
    "boston-regional-trip-generation-r1": ("fresh_prepared_crosswalk_arithmetic", ("population_or_household_by_zone.csv", "trip_generation_by_purpose.csv")),
    "boston-semantic-fix-srestore": ("fresh_prepared_feedback_choice_only", ("prepared/run/derived/srestore_model_comparison.csv", "prepared/run/derived/srestore_od_mode_probabilities.csv", "prepared/run/derived/srestore_person_demand_by_mode.csv")),
    "boston-finite-construction": ("fresh_finite_graph_construction", tuple("computed/"+name for name in ("dynamic_node.csv", "dynamic_arc.csv", "dynamic_demand.csv", "dynamic_columns.csv"))),
    "boston-finite-arc-flow-lp": ("fresh_finite_arc_lp", ("arc_lp_reference_summary.json",)),
    "boston-finite-cg-pilot-r2-r3": ("fresh_finite_cg", tuple("computed/full_cg_v1_phase_ii_final_"+name for name in ("pool.csv", "dual_solution.json", "solution_by_column.csv"))),
    "boston-finite-cg-r4-pricing-closure": ("fresh_finite_cg", tuple("continuation/results/FINAL_CLOSURE_"+name for name in ("POOL.csv", "DUAL_SOLUTION.json", "SOLUTION_BY_COLUMN.csv"))),
    "boston-admm-r2-s": ("fresh_finite_admm", ("computed/state.npz", "computed/result.json", "computed/history.csv")),
}

def verification_source(report, record):
    if report.get("record") != record or report.get("success") is not True:
        raise ValueError("Verification requires a successful receipt for the requested record")
    basis=report.get("evidenceBasis")
    if basis == "saved_run_inspected":
        source_action="inspect"
    elif record in FRESH_CONTRACTS and basis == FRESH_CONTRACTS[record][0]:
        source_action="run"
    else:
        raise ValueError("Unknown or mismatched original evidence basis; cannot choose verification inputs")
    if report.get("sourceAction",source_action) != source_action:
        raise ValueError("Original action disagrees with its evidence basis")
    return source_action

def require_fresh_outputs(out, record):
    if record not in FRESH_CONTRACTS:
        raise ValueError("No prepared run contract for this record; use its documented external source pipeline")
    required=FRESH_CONTRACTS[record][1]
    missing=[name for name in required if not (out/name).is_file()]
    if missing:
        raise ValueError("Missing required fresh output(s): "+", ".join(missing))
    return list(required)

def graph_check(data):
    arcs=rows(data/"dynamic_arc.csv"); demands=rows(data/"dynamic_demand.csv"); nodes=rows(data/"dynamic_node.csv")
    ids={r["node_time_id"] for r in nodes}
    checks={"node_count":len(nodes)==9110,"arc_count":len(arcs)==22217,"demand_count":len(demands)==10,
      "unique_arcs":len({a["arc_id"] for a in arcs})==len(arcs),
      "endpoints":all(a["from_node_time_id"] in ids and a["to_node_time_id"] in ids for a in arcs),
      "forward_time":all(float(a["to_time"])>float(a["from_time"]) or a["arc_type"] in ("source_connector","sink_connector") for a in arcs)}
    return checks,{"nodes":len(nodes),"arcs":len(arcs),"commodities":len(demands)}

def lp_feasibility(dynamic, flows):
    arcs={r["arc_id"]:r for r in rows(dynamic/"dynamic_arc.csv")};demands={r["demand_id"]:r for r in rows(dynamic/"dynamic_demand.csv")}
    balances=collections.defaultdict(float);loads=collections.defaultdict(float);own=True;nonnegative=True
    for row in flows:
        arc=arcs[row["arc_id"]];did=row["demand_id"];value=float(row["flow"])
        if did not in demands:raise ValueError("Unknown LP commodity")
        nonnegative=nonnegative and value>=-1e-10
        if arc["arc_type"] in ("source_connector","sink_connector"):own=own and arc["arc_id"].split("_")[1]==did
        balances[did,arc["from_node_time_id"]]+=value;balances[did,arc["to_node_time_id"]]-=value;loads[arc["arc_id"]]+=value
    for did,demand in demands.items():
        balances[did,"source_"+did+"_t"+demand["departure_time"]]-=float(demand["volume"])
        sink=next(a["to_node_time_id"] for a in arcs.values() if a["arc_type"]=="sink_connector" and a["arc_id"].split("_")[1]==did)
        balances[did,sink]+=float(demand["volume"])
    excess=max((loads[aid]-float(a["capacity"]) for aid,a in arcs.items() if a["capacity"] and math.isfinite(float(a["capacity"]))),default=0)
    return {"recomputed_commodity_balance":max(map(abs,balances.values()),default=0)<=1e-6,"recomputed_capacity":excess<=1e-6,"own_connectors_only":own,"nonnegative_positive_flows":nonnegative}

def execute(root, out, record, action, source_root=None, verification_origin=None):
    data=root/"examples/boston/recovered-r14"; finite=data/"finite"; source=root/"algorithms/recovered_boston/finite"
    sys.path.insert(0,str(source)); checks={};metrics={}; basis="saved_run_inspected";opt=0
    verify_fresh=action=="verify" and verification_origin=="run"
    if record=="boston-gmns-exchange-r1":
        gmns=module("recovered_exchange",root/"tools/gmns/boston_exchange.py")
        result=gmns.validate(root/"examples/boston/gmns_exchange_r1/data",root/"examples/boston/gmns_exchange_r1/schema")
        if action!="verify":write(out/"exchange_validation.json",result)
        checks={k:v for k,v in result.items() if isinstance(v,bool)}
        if verify_fresh:checks["stored_validation_matches"]=read(out/"exchange_validation.json")==result
        metrics={k:v for k,v in result.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
        if action=="run": basis="fresh_structural_validation"
    elif record in ("boston-acs-population-allocation-r1","boston-regional-trip-generation-r1"):
        pop=root/"examples/boston/population_r1/data"; model=root/"examples/boston/behavior_feedback_r1_semantic_fix_r1/data"
        verifier=module("recovered_allocation",root/"tools/population/verify_saved_allocation.py")
        result=verifier.verify(pop,model/"trip_generation_by_purpose.csv",model/"external_flow_ledger.csv")
        totals=collections.defaultdict(lambda:[0.0,0.0]);stats={r["source_geoid"]:r for r in rows(pop/"acs_block_group_stats.csv")}
        for r in rows(pop/"acs_block_group_h3_crosswalk.csv"):
            share=float(r["overlap_area_m2"])/float(stats[r["source_geoid"]]["source_area_m2"])
            for i,k in enumerate(("population_estimate","households_estimate")): totals[r["zone_id"]][i]+=float(stats[r["source_geoid"]][k])*share
        allocation=[dict(zone_id=z,population_estimate_area_weighted=v[0],households_estimate_area_weighted=v[1]) for z,v in sorted(totals.items())]
        if action!="verify":table(out/"population_or_household_by_zone.csv",allocation)
        generated=[dict(zone_id=z,purpose=k,productions_person_trips_daily=v[1]*rate) for z,v in sorted(totals.items()) for k,rate in verifier.RATES.items()]
        if action!="verify":table(out/"trip_generation_by_purpose.csv",generated)
        checks={"saved_allocation_independent_check":True,"zones_177":len(totals)==177,"generation_1062":len(generated)==1062,
           "households":close(sum(v[1] for v in totals.values()),79537.49255074753),"population":close(sum(v[0] for v in totals.values()),171049.52015979076)}
        metrics={k:v for k,v in result.items() if isinstance(v,(int,float))}
        if action=="verify":
            got={r["zone_id"]:r for r in rows(out/"population_or_household_by_zone.csv")}
            checks["output_zone_identity"]=got.keys()==totals.keys()
            checks["output_population_values"]=all(close(got[z]["population_estimate_area_weighted"],v[0]) and close(got[z]["households_estimate_area_weighted"],v[1]) for z,v in totals.items())
            expected={(r["zone_id"],r["purpose"]):r for r in generated};actual={(r["zone_id"],r["purpose"]):r for r in rows(out/"trip_generation_by_purpose.csv")}
            checks["output_generation_identity"]=actual.keys()==expected.keys()
            checks["output_generation_values"]=all(close(actual[k]["productions_person_trips_daily"],v["productions_person_trips_daily"]) for k,v in expected.items())
        if action=="run":basis="fresh_prepared_crosswalk_arithmetic"
    elif record=="boston-massgis-activity-prior-r1":
        fine=rows(data/"activity/zone_activity_r9.csv"); coarse=rows(data/"activity/zone_activity_r7_from_r9.csv");pa=rows(data/"activity/productions_attractions.csv")
        checks={"fine_zones_177":len(fine)==177,"parent_zones_9":len(coarse)==9}
        for key in ("official_res_area_sqft_weighted","official_nonres_bld_area_sqft_weighted"):
            a=sum(float(r[key]) for r in fine if r[key].strip());b=sum(float(r[key]) for r in coarse if r[key].strip());metrics[key+"_unknown_fine_zones"]=sum(not r[key].strip() for r in fine);checks[key]=abs(a-b)<=1e-7*max(1,abs(a));metrics[key]=a
        checks["production_50000"]=close(sum(float(r["productions_person_trips_daily"]) for r in pa),50000)
        checks["attraction_50000"]=close(sum(float(r["attractions_person_trips_daily"]) for r in pa),50000)
        checks["historical_assignment_not_run"]=read(data/"activity/demand_prior_summary.json")["assignment_run"] is False
        if action=="run":
            if source_root is None: raise ValueError("MassGIS raw-source build requires --source-root; see the documented layout and official acquisition command")
            env=dict(os.environ,MCL_BOSTON_SOURCE_ROOT=str(source_root.resolve()))
            invoke(root,out,"activity-build",[root/"algorithms/recovered_boston/preparation/build_activity_demand_prior.py"],env);basis="source_build_executed_external_inputs"
    elif record=="boston-transit-walk-semantic-preparation":
        saved=read(data/"preparation/multimodal_panel_summary.json")
        checks={"panel_36":saved["panel_od_count"]==36,"skim_rows_1296":saved["skim_rows"]==1296,"no_transit_without_ride":saved["available_transit_rows_without_ride"]==0,"restore_mismatches_zero":saved["srestore_skim_mismatch_rows"]==0}
        metrics={k:saved[k] for k in ("panel_od_count","skim_rows","active_service_ids","active_trips","s1_connections")}
        if action=="run":
            if source_root is None:raise ValueError("Transit rebuild requires --source-root with dated GTFS, OSM and prepared panel inputs; see data acquisition instructions")
            invoke(root,out,"transit-build",[root/"algorithms/recovered_boston/preparation/build_multimodal_panel.py","--root",source_root,"--run-dir",out/"computed"]);basis="source_build_executed_external_inputs"
    elif record=="boston-gps-network-association":
        saved=read(data/"gps/gps_quality_summary.json"); exchange=root/"examples/boston/gmns_exchange_r1/data"
        linkids={r["source_link_id"] for r in rows(exchange/"link.csv") if r["mcl_link_class"]=="physical"};matched=rows(exchange/"gps_path_links.csv")
        checks={"retained_association_nonempty":bool(matched),"association_physical_link_ids":all(r["link_id"] in linkids for r in matched)}
        metrics={"retained_path_rows":len(matched),"physical_links":len(linkids)}
        write(out/"saved_quality_summary.json",saved)
        if action=="run":raise ValueError("Raw GPS positions are not bundled. Use the documented official acquisition/matching pipeline with your supplied observation snapshots; inspect verifies the released association.")
    elif record=="boston-semantic-fix-srestore":
        comparison=rows(data/"preparation/srestore_model_comparison.csv");skim=rows(data/"preparation/srestore_skim_comparison.csv")
        p=max(float(r["probability_abs_error"]) for r in comparison);q=max(float(r["person_demand_abs_error"]) for r in comparison)
        checks={"probability_restore":p<=1e-12,"person_demand_restore":q<=1e-12,"skim_restore":all(float(r["mismatch_count"])==0 for r in skim),"negative_control":read(data/"preparation/srestore_negative_control.json")["detected"]}
        metrics={"max_probability_error":p,"max_person_demand_error":q,"comparison_rows":len(comparison)}
        if verify_fresh:
            fresh=rows(out/"prepared/run/derived/srestore_model_comparison.csv")
            checks["fresh_restore_probability"]=max(float(r["probability_abs_error"]) for r in fresh)<=1e-12
            checks["fresh_row_count"]=len(fresh)==len(comparison)
            expected={(r["od_id"],r["departure_time"],r["mu_transit_sensitivity"],r["mode"]):r for r in comparison}
            checks["fresh_matches_saved"]=all(close(r["probability_restore"],expected[(r["od_id"],r["departure_time"],r["mu_transit_sensitivity"],r["mode"])]["probability_restore"],1e-12) for r in fresh)
        if action=="run":
            task=out/"prepared";derived=task/"run/derived";derived.mkdir(parents=True)
            for f in ("ctps_tdm23_base_mode_share.csv","mode_specific_od_costs.csv","validation_panel.csv"):shutil.copyfile(data/"preparation"/f,derived/f)
            (task/"database/zones").mkdir(parents=True);shutil.copyfile(data/"preparation/zone_access.csv",task/"database/zones/zone_access.csv")
            (task/"staging/assignment/boston_quality_r1_20260922").mkdir(parents=True);shutil.copyfile(root/"examples/boston/assignment_methods_r1/inputs_snapshot/link.csv",task/"staging/assignment/boston_quality_r1_20260922/link.csv")
            (task/"run/reports").mkdir(parents=True);shutil.copyfile(data/"preparation/srestore_negative_control.json",task/"run/reports/srestore_negative_control.json")
            invoke(root,out,"restore-choice",[root/"algorithms/recovered_boston/preparation/run_mode_choice_feedback.py","--root",task,"--run-dir",task/"run"])
            fresh=rows(derived/"srestore_model_comparison.csv");checks["fresh_restore_probability"]=max(float(r["probability_abs_error"]) for r in fresh)<=1e-12;checks["fresh_row_count"]=len(fresh)==len(comparison);basis="fresh_prepared_feedback_choice_only"
    elif record=="boston-finite-construction":
        target=out/"computed" if verify_fresh else finite/"dynamic"
        if action=="run":
            from external_sioux_static_to_dynamic import build_explicit_allowed_network,ExplicitAllowedNetworkConfig
            case=read(finite/"case/case.json");cfg=ExplicitAllowedNetworkConfig(**case["model"],model_schema_version="gmns_dynamic_explicit_allowed_network_v2_seconds",scope_label=case["scope_label"])
            demands=[dict(r,origin_node_id=r["origin"],destination_node_id=r["destination"]) for r in rows(finite/"case/demand.csv")]
            built=build_explicit_allowed_network(rows(finite/"case/node.csv"),rows(finite/"case/link.csv"),demands,rows(finite/"case/static_seed_candidates.csv"),cfg)
            target=out/"computed";target.mkdir()
            for k,name in (("dynamic_nodes","dynamic_node.csv"),("dynamic_arcs","dynamic_arc.csv"),("dynamic_demands","dynamic_demand.csv"),("dynamic_columns","dynamic_columns.csv")):table(target/name,built[k])
            basis="fresh_finite_graph_construction"
        checks,metrics=graph_check(target)
        if action in ("run","verify"):
            for name,key in (("dynamic_node.csv","node_time_id"),("dynamic_arc.csv","arc_id"),("dynamic_demand.csv","demand_id")):
                old={r[key]:r for r in rows(finite/"dynamic"/name)};new={r[key]:r for r in rows(target/name)}
                checks[name+"_identities"]=old.keys()==new.keys()
                fields=("from_node_time_id","to_node_time_id","arc_type","physical_link_id") if "arc" in name else ()
                checks[name+"_structure"]=all(all(new[k].get(f)==v.get(f) for f in fields) for k,v in old.items())
                numeric=("cost","capacity","from_time","to_time") if "arc" in name else (("volume","departure_time") if "demand" in name else ())
                checks[name+"_numbers"]=all(all((new[k].get(f)==v.get(f)) or close(new[k].get(f),v.get(f),1e-10) for f in numeric) for k,v in old.items())
    elif record=="boston-finite-arc-flow-lp":
        result=read(out/"arc_lp_reference_summary.json" if verify_fresh else finite/"reference/arc_lp_reference_summary.json")
        if action=="run":
            from external_sioux_static_to_dynamic import solve_small_subset_arc_lp
            result=solve_small_subset_arc_lp(rows(finite/"dynamic/dynamic_arc.csv"),rows(finite/"dynamic/dynamic_demand.csv"));write(out/"arc_lp_reference_summary.json",result);basis="fresh_finite_arc_lp";opt=1
        flows=result["positive_flows"];arc_cost={r["arc_id"]:float(r["cost"]) for r in rows(finite/"dynamic/dynamic_arc.csv")}
        objective=sum(float(r["flow"])*arc_cost[r["arc_id"]] for r in flows)
        costs_match=all(close(r["unit_cost"],arc_cost[r["arc_id"]],1e-12) for r in flows)
        checks={"solver_optimal":result["solver_status"]=="optimal","objective":close(objective,64.3968615115296,1e-6),"balance":result["max_flow_balance_residual"]<=1e-7,"capacity":result["capacity_violation_count"]==0};metrics={"objective":objective,"variables":result["variable_count"]}
        checks["reported_unit_costs_match_fixed_graph"]=costs_match
        checks.update(lp_feasibility(finite/"dynamic",flows))
    elif record in ("boston-finite-cg-pilot-r2-r3","boston-finite-cg-r4-pricing-closure"):
        from independent_pricing_closure import evaluate_files
        is_r4="r4-pricing" in record;target=finite/("r4" if is_r4 else "r3")
        if verify_fresh:
            target=out/"continuation/results" if is_r4 else out/"computed"
        if action=="run":
            if is_r4:
                staging=out/"continuation";accepted=staging/"accepted_r3_copy";shutil.copytree(finite/"dynamic",accepted/"dynamic_inputs");shutil.copytree(finite/"r3",accepted/"boston_exact_final")
                env=dict(os.environ,MCL_BOSTON_R3_ROOT=str(finite/"r3"),MCL_BOSTON_R4_OUTPUT=str(staging));invoke(root,out,"cg-r4",[source/"run_pricing_closure_continuation.py"],env);target=staging/"results"
            else:
                manifest=read(finite/"r3/predeclared_manifest.json")
                for k,v in {"dynamic_data_dir":finite/"dynamic","dynamic_arc_file":finite/"dynamic/dynamic_arc.csv","demand_file":finite/"dynamic/dynamic_demand.csv","current_candidate_pool_file":finite/"dynamic/dynamic_columns.csv","output_root":out/"computed"}.items():manifest[k]=str(v)
                write(out/"manifest.json",manifest);target=out/"computed"
                invoke(root,out,"cg-r3",[source/"run_full_cg_v1.py","--input-manifest",out/"manifest.json","--output-dir",target,"--benchmark-id","BOSTON_BOUNDED_12_30_BOS10_S3_R1","--max-phase-i-rounds","120","--max-phase-ii-rounds","25","--max-candidates-per-demand","4","--phase-ii-pricing-mode","k_shortest","--phase-ii-add-policy","add_best_one_per_demand","--k-shortest-k","4","--max-phase-ii-candidates-per-demand","4","--max-phase-ii-candidates-per-round","40","--runtime-cap-seconds","7200","--no-mutate-accepted-outputs","--reference-objective","64.3968615115296","--reference-summary",finite/"reference/arc_lp_reference_summary.json"])
            basis="fresh_finite_cg";opt=None
        prefix="FINAL_CLOSURE_" if is_r4 else "full_cg_v1_phase_ii_final_"
        files=(target/(prefix+"POOL.csv"),target/(prefix+"DUAL_SOLUTION.json"),target/(prefix+"SOLUTION_BY_COLUMN.csv")) if is_r4 else (target/(prefix+"pool.csv"),target/(prefix+"dual_solution.json"),target/(prefix+"solution_by_column.csv"))
        cert=evaluate_files(finite/"dynamic",*files,out=out/"independent")
        checks={"objective":close(cert["objective_recomputed"],64.3968615115296,1e-6),"feasible":cert.get("status")=="PASS"}
        if is_r4:checks["full_dag_pricing_closure"]=cert["closure_pass"]
        metrics={"objective":cert["objective_recomputed"],"closure_pass":cert["closure_pass"],"demands":len(cert["by_demand"])}
    elif record=="boston-admm-r2-s":
        sys.path.insert(0,str(root/"algorithms/admm_r2"))
        from independent_admm_evaluator import evaluate_files
        target=out/"computed" if verify_fresh else data/"admm"
        if action=="run":
            target=out/"computed";invoke(root,out,"admm",[root/"algorithms/admm_r2/admm_solver.py","--arc",finite/"dynamic/dynamic_arc.csv","--demand",finite/"dynamic/dynamic_demand.csv","--output",target,"--policy",data/"admm/policy.json","--variant","R2_S","--case","Boston_10OD"]);basis="fresh_finite_admm";opt=read(target/"result.json")["optimizer_calls"]
        result=evaluate_files(finite/"dynamic/dynamic_arc.csv",finite/"dynamic/dynamic_demand.csv",target,read(data/"admm/policy.json"));write(out/"independent_admm.json",result)
        checks={k:bool(v) for k,v in result["gates"].items()};checks["reference_gap"]=abs(result["objective"]-64.3968615115296)/64.3968615115296<=.001;metrics={k:result[k] for k in ("objective","max_balance","max_capacity_excess","primal_residual","dual_residual")}
    else:raise ValueError("Unknown record: "+record)
    checks={k:bool(v) for k,v in checks.items()}
    return {"success":bool(checks) and all(checks.values()),"record":record,"evidenceBasis":basis,"optimizer_calls":opt,"checks":checks,"metrics":metrics,"scope":"Only the declared Boston workflow; no claim of raw-source pipeline reconstruction from inspect or prepared-input replay."}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("action",choices=("run","inspect","verify"));parser.add_argument("--record",required=True);parser.add_argument("--repo-root",type=Path,required=True);parser.add_argument("--output",type=Path);parser.add_argument("--run",type=Path);parser.add_argument("--source-root","--input-root",dest="source_root",type=Path);args=parser.parse_args()
    out=(args.run if args.action=="verify" else args.output)
    if out is None:parser.error("Supply --output or --run")
    out=out.resolve();root=args.repo_root.resolve()
    if args.action=="verify":
        report=read(out/"verification.json");origin=verification_source(report,args.record)
        if origin=="run":require_fresh_outputs(out,args.record)
        actual=execute(root,out,args.record,"verify",verification_origin=origin)
        actual["sourceAction"]=origin;actual["sourceEvidenceBasis"]=report["evidenceBasis"]
        actual["evidenceBasis"]="fresh_result_verified" if origin=="run" else "saved_run_reinspected"
        actual["checks"]["record_identity"]=True;actual["checks"]["original_action_passed"]=True
        actual["success"]=all(actual["checks"].values());write(out/"reverification.json",actual);print(json.dumps(actual));return 0 if actual["success"] else 2
    if out.exists() and any(out.iterdir()):raise ValueError("Output must be new or empty")
    if args.action=="run" and args.record not in FRESH_CONTRACTS:raise ValueError("No prepared run contract for this record; use its documented external source pipeline")
    out.mkdir(parents=True,exist_ok=True);report=execute(root,out,args.record,args.action,args.source_root)
    report["sourceAction"]=args.action
    if args.action=="run":report["requiredOutputs"]=require_fresh_outputs(out,args.record)
    write(out/"verification.json",report);print(json.dumps(report));return 0 if report["success"] else 2
if __name__=="__main__":raise SystemExit(main())
