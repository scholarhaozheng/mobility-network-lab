"""Pre-register one real turn-aware static-path cohort before dynamic solvers."""
import csv
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

R=Path(__file__).resolve().parent
C=R/"phase_c"
C.mkdir(exist_ok=True)
A=R/"phase_a"
B=R/"phase_b"


def rows(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def write(p, items):
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)


expanded={r["link_id"]:r for r in rows(A/"static_input/turn_expanded_links.csv")}
cross={r["expanded_link_id"]:r for r in rows(A/"static_input/expanded_network_crosswalk.csv")}
physical={k for k,x in cross.items() if x["link_class"]=="physical"}
road={r["link_id"]:r for r in rows(A/"instance/link.csv") if r["mcl_link_class"]=="physical"}
posted={r["link_id"]:r["posted_limit_grade"] for r in rows(A/"link_speed_evidence.csv")}
flow={r["link_id"]:float(r["volume"]) for r in rows(B/"static_runs/full_algorithm_b/link_flow.csv")}
paths=rows(B/"static_runs/full_algorithm_b/path_flow.csv")
outgoing=defaultdict(list)
for lid,r in expanded.items():
    outgoing[r["from_node_id"]].append((r["to_node_id"],lid,float(r["vdf_fftt"])))
for v in outgoing.values():v.sort(key=lambda t:t[1])


def alternative(source,dest,forbid):
    dist={source:0.}; parent={}
    heap=[(0.,source)]
    while heap:
        d,u=heapq.heappop(heap)
        if d>dist[u]+1e-12:continue
        if u==dest:
            seq=[]
            while u!=source:
                prior,lid=parent[u];seq.append(lid);u=prior
            return d,tuple(reversed(seq))
        for v,lid,w in outgoing[u]:
            if lid==forbid:continue
            nd=d+w
            if nd<dist.get(v,math.inf)-1e-12:
                dist[v]=nd;parent[v]=(u,lid);heapq.heappush(heap,(nd,v))
    return None


def represented(seq,step):
    return sum(max(1,math.ceil(float(expanded[lid]["vdf_fftt"])*60/step-1e-12))
               if lid in physical else 0 for lid in seq)


bylink=defaultdict(list)
for p in paths:
    sequence=p["link_ids"].split(";")
    for lid in sequence:
        if lid in physical:bylink[lid].append((p,sequence))
# Fixed ranking before any Hong Kong dynamic solver is run: exact posted-limit
# evidence, then descending assigned static physical flow, then ID. This is
# only a case-selection heuristic; the static solver is not a dynamic seed.
candidates=sorted((lid for lid in physical if len(bylink[lid])>=10),
                  key=lambda lid:(posted[lid]!="OFFICIAL_EXACT",-flow[lid],int(lid)))
choice=None
for bottleneck in candidates:
    eligible=[]
    for p,primary in sorted(bylink[bottleneck],key=lambda x:(-float(x[0]["volume"]),int(x[0]["origin"]),int(x[0]["destination"]))):
        alt=alternative(p["origin"],p["destination"],bottleneck)
        if alt is None:continue
        primary_time=sum(float(expanded[l]["vdf_fftt"]) for l in primary)
        if alt[0]>1.75*primary_time:continue
        # The alternate remains an alternate under both candidate time grids.
        if any(represented(alt[1],step)<represented(primary,step) for step in (15,30)):
            continue
        eligible.append((p,tuple(primary),alt[1],primary_time,alt[0]))
        if len(eligible)>=30:break
    if len(eligible)>=10:
        choice=(bottleneck,eligible);break
if choice is None:raise RuntimeError("No preregistered exact-evidence bottleneck supports 10 alternate-route ODs")
bottleneck,eligible=choice

pre=[]
for tier in (10,20,30):
    if len(eligible)<tier:
        pre.append({"tier_od":tier,"status":"INSUFFICIENT_QUALIFYING_OD"});continue
    selected=eligible[:tier]
    selected_links=set(l for _,a,b,_,_ in selected for l in a+b)
    selected_physical={l for l in selected_links if l in physical}
    selected_road_nodes={x for lid in selected_physical for x in (road[lid]["from_node_id"],road[lid]["to_node_id"])}
    # Add all allowed turn edges between the selected physical links to retain
    # route alternatives. Keep only zone connectors actually used by a route.
    selected_links.update(lid for lid,x in cross.items()
                          if x["link_class"]=="nonphysical_allowed_movement"
                          and x["from_physical_link_id"] in selected_physical
                          and x["to_physical_link_id"] in selected_physical)
    selected_nodes={x for lid in selected_links for x in (expanded[lid]["from_node_id"],expanded[lid]["to_node_id"])}
    # Use 30 s × 50 steps = 25 min; 15 s × 100 as resolution audit.
    horizon=50;step=30
    durations={lid:max(1,math.ceil(float(expanded[lid]["vdf_fftt"])*60/step-1e-12)) if lid in physical else 0 for lid in selected_links}
    arc_count=sum(max(0,horizon-durations[lid]+1) for lid in selected_links)+len(selected_nodes)*horizon+tier*(horizon+2)
    dyn_nodes=len(selected_nodes)*(horizon+1)+tier*2
    refvars=arc_count*tier
    estimated_memory=refvars*96+arc_count*80+dyn_nodes*64
    maxroute=max(represented(a,step) for _,a,_,_,_ in selected)
    maxalt=max(represented(b,step) for _,_,b,_,_ in selected)
    fits=(len(selected_road_nodes)<=200 and len(selected_physical)<=300 and
          dyn_nodes<=15000 and arc_count<=40000 and refvars<=250000 and
          estimated_memory<=1_000_000_000 and max(maxroute,maxalt)<=horizon-5)
    pre.append({"tier_od":tier,"status":"FITS" if fits else "RESOURCE_OR_HORIZON_GATE",
                "physical_nodes":len(selected_road_nodes),"physical_links":len(selected_physical),
                "expanded_selected_links":len(selected_links),"expanded_selected_nodes":len(selected_nodes),
                "step_seconds":step,"horizon_steps":horizon,"horizon_minutes":horizon*step/60,
                "dynamic_nodes_estimate":dyn_nodes,"dynamic_arcs_estimate":arc_count,
                "reference_variables_estimate":refvars,"reference_constraints_estimate":dyn_nodes*tier+arc_count,
                "estimated_memory_bytes":estimated_memory,
                "max_primary_travel_steps":maxroute,"max_alternate_travel_steps":maxalt})

write(C/"HK_SPACETIME_PREFLIGHT.csv",pre)
fitting=[p for p in pre if p["status"]=="FITS"]
selected_tier=max(fitting,key=lambda p:p["tier_od"])["tier_od"] if fitting else None
if selected_tier is None:
    result={"status":"PREDECLARED_RESOURCE_GATE","bottleneck_link_id":bottleneck,
            "qualifying_od":len(eligible),"preflight":pre}
else:
    selected=eligible[:selected_tier]
    selected_links=set(l for _,a,b,_,_ in selected for l in a+b)
    selected_physical={l for l in selected_links if l in physical}
    selected_links.update(lid for lid,x in cross.items()
                          if x["link_class"]=="nonphysical_allowed_movement"
                          and x["from_physical_link_id"] in selected_physical
                          and x["to_physical_link_id"] in selected_physical)
    roads=[dict(road[lid]) for lid in sorted(selected_physical,key=int)]
    arcs=[dict(expanded[lid],link_class=cross[lid]["link_class"],
               physical_link_id=cross[lid]["physical_link_id"]) for lid in sorted(selected_links,key=int)]
    od=[]
    for k,(p,a,b,pt,at) in enumerate(selected,1):
        od.append({"demand_id":f"HK{k:02d}","origin_node_id":p["origin"],
                   "destination_node_id":p["destination"],"departure_time":0,
                   "volume":p["volume"],"source_o_zone_id":int(p["origin"])-4000000000,
                   "source_d_zone_id":int(p["destination"])-4100000000,
                   "primary_static_minutes":pt,"alternate_static_minutes":at,
                   "primary_15s_steps":represented(a,15),"alternate_15s_steps":represented(b,15),
                   "primary_30s_steps":represented(a,30),"alternate_30s_steps":represented(b,30)})
    write(C/"selected_od.csv",od)
    write(C/"selected_expanded_links.csv",arcs)
    write(C/"selected_physical_links.csv",roads)
    result={"status":"PRE_REGISTERED","selection_rule":"exact posted-limit bottleneck first, then descending static flow, then link ID; ODs descending four-stage drive PCE; require alternate route excluding bottleneck <=1.75x primary and stable order at 15/30 seconds; select largest fitting tier 10/20/30",
            "bottleneck_link_id":bottleneck,"bottleneck_static_flow_pce":flow[bottleneck],
            "bottleneck_posted_limit_grade":posted[bottleneck],
            "qualifying_od":len(eligible),"selected_od":selected_tier,
            "selected_total_drive_pce":sum(float(x["volume"]) for x in od),
            "time_step_seconds":30,"horizon_steps":50,
            "preflight":pre,
            "use_of_static_solution":"selection only; no dynamic primal/dual seeding or tuning"}
(C/"HK_SPACETIME_CASE_SELECTION.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
