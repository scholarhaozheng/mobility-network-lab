"""Compile the pre-registered Hong Kong link-state corridor into one finite DAG."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

R=Path(__file__).resolve().parent
C=R/"phase_c"
CASE=C/"case"
CASE.mkdir(exist_ok=True)


def rows(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def write(p, items):
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)


selection=json.loads((C/"HK_SPACETIME_CASE_SELECTION.json").read_text(encoding="utf-8"))
if selection["status"]!="PRE_REGISTERED":raise RuntimeError("selection gate")
static=rows(C/"selected_expanded_links.csv")
od=rows(C/"selected_od.csv")
physical=rows(C/"selected_physical_links.csv")
step=selection["time_step_seconds"]
horizon=selection["horizon_steps"]
total=sum(float(r["volume"]) for r in od)
large_capacity=total+1.0
arcs=[]
rounding=[]
for r in static:
    lid=r["link_id"]
    isphys=r["link_class"]=="physical"
    t0=float(r["vdf_fftt"])
    duration=max(1,math.ceil(t0*60/step-1e-12)) if isphys else 0
    cap=float(r["capacity"])*step/3600 if isphys else large_capacity
    if isphys:
        rounding.append({"physical_link_id":lid,"source_ff_minutes":t0,
                         "represented_15s_minutes":max(1,math.ceil(t0*60/15-1e-12))*15/60,
                         "represented_30s_minutes":duration*step/60,
                         "rounding_15s_seconds":max(1,math.ceil(t0*60/15-1e-12))*15-t0*60,
                         "rounding_30s_seconds":duration*step-t0*60,
                         "hourly_capacity_pce":r["capacity"],
                         "capacity_pce_per_30s_departure":cap,
                         "capacity_conversion":"hourly_pce * 30/3600"})
    kind="movement" if isphys else ("turn_connector" if r["link_class"]=="nonphysical_allowed_movement" else "zone_connector")
    for t in range(horizon-duration+1):
        arcs.append({"arc_id":f"arc_{lid}_t{t}",
                     "from_node_time_id":f"n{r['from_node_id']}_t{t}",
                     "to_node_time_id":f"n{r['to_node_id']}_t{t+duration}",
                     "from_physical_node_id":r["from_node_id"],
                     "to_physical_node_id":r["to_node_id"],
                     "from_time":t,"to_time":t+duration,
                     "arc_type":kind,"physical_link_id":lid if isphys else "",
                     "cost":t0,"capacity":cap})
nodes=sorted({r["from_node_id"] for r in static}|{r["to_node_id"] for r in static},key=int)
for node in nodes:
    for t in range(horizon):
        arcs.append({"arc_id":f"wait_{node}_t{t}",
                     "from_node_time_id":f"n{node}_t{t}",
                     "to_node_time_id":f"n{node}_t{t+1}",
                     "from_physical_node_id":node,"to_physical_node_id":node,
                     "from_time":t,"to_time":t+1,"arc_type":"waiting",
                     "physical_link_id":"","cost":step/60,"capacity":large_capacity})
for r in od:
    did=r["demand_id"]
    origin=r["origin_node_id"]
    dest=r["destination_node_id"]
    q=float(r["volume"])
    arcs.append({"arc_id":f"source_{did}",
                 "from_node_time_id":f"source_{did}_t0","to_node_time_id":f"n{origin}_t0",
                 "from_physical_node_id":f"source_{did}","to_physical_node_id":origin,
                 "from_time":0,"to_time":0,"arc_type":"source_connector",
                 "physical_link_id":"","cost":0.,"capacity":q})
    for t in range(horizon+1):
        arcs.append({"arc_id":f"sink_{did}_{dest}_t{t}",
                     "from_node_time_id":f"n{dest}_t{t}","to_node_time_id":f"sink_{did}_t{horizon}",
                     "from_physical_node_id":dest,"to_physical_node_id":f"sink_{did}",
                     "from_time":t,"to_time":horizon,"arc_type":"sink_connector",
                     "physical_link_id":"","cost":0.,"capacity":large_capacity})
demands=[{k:r[k] for k in ("demand_id","origin_node_id","destination_node_id","departure_time","volume")} for r in od]
write(CASE/"dynamic_arc.csv",arcs)
write(CASE/"dynamic_demand.csv",demands)
write(CASE/"selected_physical_links.csv",physical)
write(C/"TIME_DISCRETIZATION_AND_CAPACITY_AUDIT.csv",rounding)
signature=hashlib.sha256((CASE/"dynamic_arc.csv").read_bytes()+b"\0"+(CASE/"dynamic_demand.csv").read_bytes()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={"schema_version":"cross_city_lagrangian_case_v1","adapter":"finite_dynamic_csv_v1",
          "case_id":"HK_TST_JORDAN_10OD_30S_50STEPS_R2_R4","city":"Hong Kong",
          "arc_file":"dynamic_arc.csv","demand_file":"dynamic_demand.csv",
          "arc_sha256":sha(CASE/"dynamic_arc.csv"),"demand_sha256":sha(CASE/"dynamic_demand.csv"),
          "physical_link_file":"selected_physical_links.csv",
          "physical_link_sha256":sha(CASE/"selected_physical_links.csv"),
          "physical_link_id_column":"link_id","model_signature":signature,
          "objective_unit":"vehicle_minutes","capacity_unit":"PCE_per_30s_movement_departure",
          "time_step_seconds":step,"horizon_steps":horizon,
          "model_note":"turns and zone access are zero-time nonphysical DAG arcs; physical movement traversals use positive integer steps; waiting incurs elapsed time"}
(CASE/"case.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
quality={"status":"COMPILED","dynamic_arcs":len(arcs),
         "dynamic_nodes":len({a["from_node_time_id"] for a in arcs}|{a["to_node_time_id"] for a in arcs}),
         "arc_types":dict(Counter(a["arc_type"] for a in arcs)),
         "selected_od":len(od),"selected_total_pce":total,
         "physical_links":len(physical),"step_seconds":step,"horizon_steps":horizon,
         "max_15s_rounding_seconds":max(r["rounding_15s_seconds"] for r in rounding),
         "max_30s_rounding_seconds":max(r["rounding_30s_seconds"] for r in rounding),
         "path_order_stability":all(int(r["alternate_15s_steps"])>=int(r["primary_15s_steps"])
                                    and int(r["alternate_30s_steps"])>=int(r["primary_30s_steps"]) for r in od),
         "model_signature":signature,
         "static_vs_dynamic_objective":"not comparable; static Beckmann BPR vs fixed-cost finite capacity flow"}
(C/"DYNAMIC_GRAPH_BUILD_REPORT.json").write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
print(json.dumps(quality,indent=2))
