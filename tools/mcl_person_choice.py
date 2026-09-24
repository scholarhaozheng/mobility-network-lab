"""Evaluate supplied person OD with absolute mode attributes and fixed choice spec.

This is conditional four-known-alternative sensitivity, not population
calibration. A missing transit fare or path leaves the full case unknown.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/"scalable"))
from fixed_choice_source import MODES, nested_probabilities, utility_components


def rows(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def write(path,records,fields):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(records)


class SpoolRows:
    """Bound in-memory output rows while preserving their append/iteration order."""
    def __init__(self):
        self.file=tempfile.SpooledTemporaryFile(max_size=4*1024*1024,mode="w+t",encoding="utf-8",newline="")
    def append(self,row):
        self.file.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n")
    def __iter__(self):
        self.file.flush();self.file.seek(0)
        for line in self.file:yield json.loads(line)
    def close(self):self.file.close()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--person-od",required=True,type=Path)
    ap.add_argument("--skims",required=True,type=Path)
    ap.add_argument("--spec",required=True,type=Path)
    ap.add_argument("--config",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args();out=a.output.resolve()
    for p in (a.person_od,a.skims,a.spec,a.config):
        p=p.resolve()
        if p==out or p in out.parents or out in p.parents:raise ValueError("source/output overlap")
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty output")
    spec=json.loads(a.spec.read_text(encoding="utf-8"))
    cfg=json.loads(a.config.read_text(encoding="utf-8"))
    if set(cfg)!={"departure_weights","occupancy","scenario_id","skim_scenario_id","scale_id","person_mass_field"}:raise ValueError("choice config keys differ from contract")
    weights=cfg["departure_weights"]
    if abs(sum(float(v) for v in weights.values())-1)>1e-12 or any(float(v)<=0 for v in weights.values()):raise ValueError("invalid departure weights")
    occ={k:float(v) for k,v in cfg["occupancy"].items()}
    if set(occ)!={"DA","S2","S3"} or any(not math.isfinite(v) or v<=0 for v in occ.values()):raise ValueError("invalid occupancy")
    if cfg["scale_id"] not in spec["scale_vectors"]:raise ValueError("unknown scale id")
    person=rows(a.person_od)
    index={}
    with a.skims.open(newline="",encoding="utf-8-sig") as skim_file:
        for r in csv.DictReader(skim_file):
            if r["scenario_id"]!=cfg["skim_scenario_id"]:continue
            k=(r["od_id"],r["departure_time"],r["mode"])
            if k in index:raise ValueError("duplicate skim key")
            index[k]=r
    if not index:raise ValueError("no skims for selected source scenario")
    if len({r["od_id"] for r in person})!=len(person):raise ValueError("duplicate person OD")
    ledger=SpoolRows();prob=SpoolRows();vehicles=SpoolRows();aggregated=defaultdict(float);attributes=SpoolRows()
    for od in person:
        q=float(od[cfg["person_mass_field"]])
        if not math.isfinite(q) or q<0:raise ValueError("invalid person mass")
        for depart,weight in weights.items():
            mass=q*float(weight)
            utilities={};fail=[];unavailable=False;unknown=False
            for mode in MODES:
                source=index.get((od["od_id"],depart,"transit_walk_access" if mode=="TW" else "drive"))
                if source is None:
                    fail.append(mode+":missing_skim");unknown=True;continue
                if source["availability_status"]=="confirmed_unavailable_within_declared_search_limits":
                    unavailable=True
                try:
                    terms,attrs=utility_components(mode,source,spec)
                    utilities[mode]=sum(terms.values())
                    attributes.append({"od_id":od["od_id"],"departure_time":depart,"mode":mode,"status":"evaluated",
                                       "utility":utilities[mode],"ivtt_min":attrs["ivtt_min"],"ovtt_min":attrs["ovtt_min"],
                                       "cost_2010_usd":attrs["cost_2010_usd"],"path_id":source["path_id"]})
                except ValueError as exc:
                    fail.append(mode+":"+str(exc))
                    if str(exc)=="no_permitted_ride":unavailable=True
                    elif source["availability_status"]!="confirmed_unavailable_within_declared_search_limits":unknown=True
                    attributes.append({"od_id":od["od_id"],"departure_time":depart,"mode":mode,"status":str(exc),
                                       "utility":"","ivtt_min":"","ovtt_min":"","cost_2010_usd":"","path_id":source["path_id"]})
            complete=len(utilities)==len(MODES)
            scope_status=("EVALUATED_CONDITIONAL" if complete else
                          "MIXED_UNKNOWN_AND_UNAVAILABLE_SCOPE" if unknown and unavailable else
                          "DECLARED_SEARCH_UNAVAILABLE_FOUR_MODE_SCOPE" if unavailable else
                          "UNKNOWN_CONDITIONAL_SCOPE")
            road_status=("unresolved_access" if not od.get("o_node_id") or not od.get("d_node_id")
                         else "same_access_node" if od["o_node_id"]==od["d_node_id"] else "eligible")
            ledger.append({"od_id":od["od_id"],"o_zone_id":od["o_zone_id"],"d_zone_id":od["d_zone_id"],
                           "o_node_id":od["o_node_id"],"d_node_id":od["d_node_id"],"departure_time":depart,
                           "person_mass":mass,"status":scope_status,
                           "road_status":road_status,"reason":";".join(fail)})
            if not complete:continue
            p,_,_=nested_probabilities(utilities,spec["scale_vectors"][cfg["scale_id"]])
            if abs(sum(p.values())-1)>1e-12:raise ValueError("probability sum")
            for mode in MODES:
                prob.append({"od_id":od["od_id"],"departure_time":depart,"mode":mode,
                             "probability":p[mode],"person_mass":mass,"conditional_person_trips":mass*p[mode]})
                if mode in occ:
                    v=mass*p[mode]/occ[mode]
                    vehicles.append({"od_id":od["od_id"],"departure_time":depart,"mode":mode,
                                     "o_node_id":od["o_node_id"],"d_node_id":od["d_node_id"],
                                     "person_trips":mass*p[mode],"occupancy":occ[mode],"vehicle_trips":v,
                                     "road_status":road_status})
                    if road_status=="eligible":aggregated[(od["o_node_id"],od["d_node_id"])]+=v
    out.mkdir(parents=True)
    write(out/"choice_ledger.csv",ledger,["od_id","o_zone_id","d_zone_id","o_node_id","d_node_id","departure_time","person_mass","status","road_status","reason"])
    write(out/"choice_attributes.csv",attributes,["od_id","departure_time","mode","status","utility","ivtt_min","ovtt_min","cost_2010_usd","path_id"])
    write(out/"probabilities.csv",prob,["od_id","departure_time","mode","probability","person_mass","conditional_person_trips"])
    write(out/"person_to_vehicle.csv",vehicles,["od_id","departure_time","mode","o_node_id","d_node_id","person_trips","occupancy","vehicle_trips","road_status"])
    write(out/"vehicle_demand.csv",[{"o_node_id":o,"d_node_id":d,"volume":v} for (o,d),v in sorted(aggregated.items())],["o_node_id","d_node_id","volume"])
    summary={"model_id":spec["model_id"],"scenario":cfg["scenario_id"],"scale_id":cfg["scale_id"],
             "selected_zone_od":len(person),"selected_person_mass":sum(float(x[cfg["person_mass_field"]]) for x in person),
             "evaluated_person_mass":sum(float(x["person_mass"]) for x in ledger if x["status"]=="EVALUATED_CONDITIONAL"),
             "unknown_person_mass":sum(float(x["person_mass"]) for x in ledger if x["status"] in ("UNKNOWN_CONDITIONAL_SCOPE","MIXED_UNKNOWN_AND_UNAVAILABLE_SCOPE")),
             "declared_search_unavailable_person_mass":sum(float(x["person_mass"]) for x in ledger if x["status"]=="DECLARED_SEARCH_UNAVAILABLE_FOUR_MODE_SCOPE"),
             "non_evaluated_person_mass":sum(float(x["person_mass"]) for x in ledger if x["status"]!="EVALUATED_CONDITIONAL"),
             "evaluated_objects":sum(x["status"]=="EVALUATED_CONDITIONAL" for x in ledger),
             "unknown_objects":sum(x["status"] in ("UNKNOWN_CONDITIONAL_SCOPE","MIXED_UNKNOWN_AND_UNAVAILABLE_SCOPE") for x in ledger),
             "declared_search_unavailable_objects":sum(x["status"]=="DECLARED_SEARCH_UNAVAILABLE_FOUR_MODE_SCOPE" for x in ledger),
             "vehicle_trips_before_access_exclusion":sum(x["vehicle_trips"] for x in vehicles),
             "loaded_vehicle_trips":sum(aggregated.values()),"node_od":len(aggregated),
             "distinct_endpoint_nodes":len({n for o,d in aggregated for n in (o,d)}),
             "input_hashes":{str(p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.person_od,a.skims,a.spec,a.config)},
             "conditioning":"sufficient_vehicle_household_and_four_known_alternatives_DA_S2_S3_TW",
             "engineering_cohort_assumption":True,"empirical_validation":"NOT_PERFORMED"}
    temporary=out/"summary.json.partial"
    temporary.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    temporary.replace(out/"summary.json")
    for spool in (ledger,prob,vehicles,attributes):spool.close()
    print(json.dumps(summary))


if __name__=="__main__":main()
