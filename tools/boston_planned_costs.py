"""New Boston planned-service skims from frozen road, walk and GTFS inputs.

Uses the corrected semantic_transit adapter and graph builders retained from
the accepted public pipeline. There is no GPS overlay and no saved-skim read.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/"scalable"))
import networkx as nx
import pandas as pd
import zipfile
from legacy_multimodal_core import (BOUND, WALK_MPS, MAX_WALK_SECONDS, SEARCH_END,
    active_services, build_osm_graphs, clock, make_snapper, seconds)
from semantic_transit import (FarePolicy, TransferPolicy, build_connections,
    transit_route)
from semantic_transit_batch import transit_route_many

FIELDS=["od_id","o_zone_id","d_zone_id","departure_time","service_date","scenario_id",
        "mode","availability_status","in_vehicle_min","walk_min","wait_min","distance_m",
        "fare_usd","fare_price_year","boardings","ride_segment_count","transfers","path_id",
        "cost_status","overlay_applied","source_hash"]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()


def read(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def write(path,records):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore");w.writeheader();w.writerows(records)


def atomic_json(path,record):
    path=Path(path)
    temporary=path.with_name(path.name+".partial")
    temporary.write_text(json.dumps(record,indent=2,default=str),encoding="utf-8")
    temporary.replace(path)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",required=True,type=Path)
    ap.add_argument("--source-root",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--service-date",default="2026-09-21")
    ap.add_argument("--departures",default="12:30:00,12:40:00,12:50:00")
    ap.add_argument("--reuse-skims",type=Path)
    ap.add_argument("--reuse-panel",type=Path)
    ap.add_argument("--max-wall-seconds",type=float,default=7200)
    ap.add_argument("--single-egress-reference",action="store_true",
                    help="Recompute each OD with the original unsplit semantic route for a small equivalence check")
    a=ap.parse_args();t=time.perf_counter()
    root=a.source_root.resolve();out=a.output.resolve()
    for source_path in (root,a.panel.resolve(),
                        a.reuse_skims.resolve() if a.reuse_skims else None,
                        a.reuse_panel.resolve() if a.reuse_panel else None):
        if source_path is not None and (source_path==out or source_path in out.parents or out in source_path.parents):
            raise ValueError("source/output overlap")
    out.mkdir(parents=True,exist_ok=True)
    panel=read(a.panel)
    if len({r["od_id"] for r in panel})!=len(panel):raise ValueError("duplicate selected od_id")
    departures=tuple(seconds(x) for x in a.departures.split(","))
    if not departures or min(departures)<0 or max(departures)>=SEARCH_END:raise ValueError("invalid departures")
    osm=root/"raw/osm/behavior_feedback_r1/central_boston_highways.osm"
    gtfs=root/"raw/gtfs/mdb-437_20260918.zip"
    transit=root/"database/transit"
    files=[osm,gtfs,*[transit/x for x in ("stops.txt","trips.txt","routes.txt","calendar.txt","calendar_dates.txt","stop_times.txt","transfers.txt")],root/"database/zones/zone.csv",root/"database/zones/zone_access.csv",root/"database/network/gmns/link.csv",a.panel]
    missing=[str(p) for p in files if not p.is_file()]
    if missing:raise FileNotFoundError("missing explicit routing inputs: "+repr(missing))
    identity=hashlib.sha256(json.dumps({str(p):sha(p) for p in files},sort_keys=True).encode()+a.service_date.encode()+a.departures.encode()).hexdigest()
    reused_by_od={}
    if bool(a.reuse_skims)!=bool(a.reuse_panel):raise ValueError("reuse-skims and reuse-panel must be paired")
    if a.reuse_skims:
        old_summary=json.loads((a.reuse_skims.parent/"summary.json").read_text(encoding="utf-8"))
        prior_files=files[:-1]+[a.reuse_panel]
        prior_identity=hashlib.sha256(json.dumps({str(p):sha(p) for p in prior_files},sort_keys=True).encode()+a.service_date.encode()+a.departures.encode()).hexdigest()
        if old_summary["input_signature"]!=prior_identity or old_summary["output_sha256"]!=sha(a.reuse_skims):
            raise ValueError("reuse source/skim integrity mismatch")
        prior_od={r["od_id"]:r for r in read(a.reuse_panel)}
        current_od={r["od_id"]:r for r in panel}
        for old_id,r in prior_od.items():
            if old_id not in current_od or (r["o_zone_id"],r["d_zone_id"],r["person_trips_midday_od"])!=(current_od[old_id]["o_zone_id"],current_od[old_id]["d_zone_id"],current_od[old_id]["person_trips_midday_od"]):
                raise ValueError("reused OD absent/changed")
        for r in read(a.reuse_skims):
            if r["od_id"] not in prior_od or r["departure_time"] not in a.departures.split(",") or r["mode"] not in ("drive","transit_walk_access"):
                raise ValueError("invalid reused skim key")
            reused_by_od.setdefault(r["od_id"],[]).append(r)
        if any(len(v)!=2*len(departures) for v in reused_by_od.values()) or len(reused_by_od)!=len(prior_od):
            raise ValueError("incomplete reused OD skims")
    print(json.dumps({"phase":"build_graphs","panel":len(panel),"input_signature":identity}),flush=True)
    osm_nodes,walk_graph,_,osm_stats=build_osm_graphs(osm)
    walk_snap=make_snapper(osm_nodes,walk_graph)
    zones=pd.read_csv(root/"database/zones/zone.csv",dtype={"zone_id":str})
    zones=zones[zones["zone_level"].eq("fine")].set_index("zone_id")
    access=pd.read_csv(root/"database/zones/zone_access.csv",dtype={"zone_id":str,"access_node_id":str}).set_index("zone_id")
    stops=pd.read_csv(transit/"stops.txt",dtype=str)
    for col in ("stop_lat","stop_lon"):stops[col]=pd.to_numeric(stops[col],errors="coerce")
    trips=pd.read_csv(transit/"trips.txt",dtype=str)
    routes=pd.read_csv(transit/"routes.txt",dtype=str)
    calendar=pd.read_csv(transit/"calendar.txt",dtype=str)
    exceptions=pd.read_csv(transit/"calendar_dates.txt",dtype=str)
    stop_times=pd.read_csv(transit/"stop_times.txt",dtype=str)
    transfers=pd.read_csv(transit/"transfers.txt",dtype=str)
    active=active_services(calendar,exceptions,a.service_date)
    trip_meta=trips[trips["service_id"].isin(active)][["trip_id","route_id","direction_id","service_id","block_id"]].merge(routes[["route_id","route_type","network_id"]],on="route_id",how="left",validate="many_to_one")
    active_st=stop_times[stop_times["trip_id"].isin(set(trip_meta["trip_id"]))].copy()
    connections=build_connections(active_st,trip_meta,None,search_end=SEARCH_END,earliest_departure=min(departures),max_access_seconds=MAX_WALK_SECONDS)
    with zipfile.ZipFile(gtfs) as zf:
        pathways=pd.read_csv(zf.open("pathways.txt"),dtype=str) if "pathways.txt" in zf.namelist() else None
    transfer_policy=TransferPolicy.build(stops,transfers,pathways)
    fare_policy=FarePolicy.from_gtfs_zip(gtfs)
    stop_snap={}
    for row in stops.itertuples(index=False):
        if pd.isna(row.stop_lon) or pd.isna(row.stop_lat):continue
        if not(BOUND[0]<=float(row.stop_lon)<=BOUND[2] and BOUND[1]<=float(row.stop_lat)<=BOUND[3]):continue
        node,dist=walk_snap(float(row.stop_lon),float(row.stop_lat))
        if dist<=250:stop_snap[str(row.stop_id)]=(node,dist)
    links=pd.read_csv(root/"database/network/gmns/link.csv",dtype={"link_id":str,"from_node_id":str,"to_node_id":str})
    drive=nx.DiGraph()
    for row in links[links["is_physical"].astype(str).str.lower().eq("true")].itertuples(index=False):
        sec=float(row.vdf_fftt)*60
        old=drive.get_edge_data(row.from_node_id,row.to_node_id)
        if old is None or sec<old["seconds"]:
            drive.add_edge(row.from_node_id,row.to_node_id,seconds=sec,distance_m=float(row.vdf_length_mi)*1609.344,link_id=row.link_id)
    setup_seconds=time.perf_counter()-t
    zone_walk={};zone_stops={}
    def stop_times_for_zone(z):
        if z in zone_stops:return zone_stops[z]
        zone=zones.loc[z]
        node,snap_m=walk_snap(float(zone.centroid_lon),float(zone.centroid_lat))
        zone_walk[z]=(node,snap_m)
        lengths=nx.single_source_dijkstra_path_length(walk_graph,node,cutoff=MAX_WALK_SECONDS,weight="seconds")
        times={stop:snap_m/WALK_MPS+lengths[n]+snap/WALK_MPS for stop,(n,snap) in stop_snap.items() if n in lengths}
        zone_stops[z]=times
        return times
    by_origin=defaultdict(list)
    for r in panel:by_origin[r["o_zone_id"]].append(r)
    chunk_dir=out/"chunks";chunk_dir.mkdir(exist_ok=True)
    completed=0;rows_total=0
    for oz in sorted(by_origin):
        if time.perf_counter()-t >= a.max_wall_seconds:
            partial={"status":"RESOURCE_LIMIT","reason":"skim wall budget reached at completed origin boundary",
                     "input_signature":identity,"completed_origins":completed,"total_origins":len(by_origin),
                     "completed_rows":rows_total,"reused_od":len(reused_by_od),"elapsed_seconds":time.perf_counter()-t}
            atomic_json(out/"partial_status.json",partial)
            print(json.dumps(partial),flush=True)
            return 3
        chunk=chunk_dir/(hashlib.sha1(oz.encode()).hexdigest()[:16]+".csv")
        marker=chunk.with_suffix(".json")
        if chunk.is_file() and marker.is_file():
            info=json.loads(marker.read_text(encoding="utf-8"))
            if info.get("input_signature")==identity and info.get("sha256")==sha(chunk):
                completed+=1;rows_total+=info["rows"];continue
        records=[]
        for od in by_origin[oz]:
            for reused in reused_by_od.get(od["od_id"],[]):
                records.append({**reused,"source_hash":identity})
        new_od=[od for od in by_origin[oz] if od["od_id"] not in reused_by_od]
        if new_od:
            origin_access=stop_times_for_zone(oz)
            o_node=str(access.loc[oz,"access_node_id"])
            d_lengths,d_paths=nx.single_source_dijkstra(drive,o_node,weight="seconds")
            egress_by_zone={dz:stop_times_for_zone(dz) for dz in sorted({od["d_zone_id"] for od in new_od})}
            transit_by_depart=({} if a.single_egress_reference else
                {depart:transit_route_many(depart,connections,origin_access,
                    egress_by_zone,transfer_policy,fare_policy,search_end=SEARCH_END) for depart in departures})
        for od in sorted(new_od,key=lambda r:r["od_id"]):
            dz=od["d_zone_id"]
            d_node=str(access.loc[dz,"access_node_id"])
            if d_node in d_lengths and o_node!=d_node:
                dpath=d_paths[d_node]
                ddist=sum(float(drive[u][v]["distance_m"]) for u,v in zip(dpath[:-1],dpath[1:]))
                dmin=float(d_lengths[d_node])/60
                drive_status="available"
                drive_pid=hashlib.sha1(repr(dpath).encode()).hexdigest()[:16]
            else:
                dmin=math.nan;ddist=math.nan;drive_status="unknown_buffer_or_network_disconnected";drive_pid=""
            for depart in departures:
                common={"od_id":od["od_id"],"o_zone_id":oz,"d_zone_id":dz,"departure_time":clock(depart),
                        "service_date":a.service_date,"scenario_id":"S1_planned_service","source_hash":identity,"overlay_applied":False}
                records.append({**common,"mode":"drive","availability_status":drive_status,"in_vehicle_min":dmin,
                                "walk_min":0,"wait_min":0,"distance_m":ddist,"fare_usd":"","fare_price_year":"",
                                "boardings":"","ride_segment_count":"","transfers":0,"path_id":drive_pid,
                                "cost_status":"REAL_NETWORK_SHORTEST_PATH_FREE_FLOW_NO_PARKING_COST"})
                tr=(transit_route(depart,connections,origin_access,egress_by_zone[dz],
                    transfer_policy,fare_policy,search_end=SEARCH_END) if a.single_egress_reference
                    else transit_by_depart[depart][dz])
                signature=[(x["kind"],x.get("stop"),getattr(x.get("connection"),"trip_id",None),getattr(x.get("connection"),"from_seq",None),getattr(x.get("connection"),"dep",None),getattr(x.get("connection"),"arr",None)) for x in tr.get("chain",[])]
                pid=hashlib.sha1((od["od_id"]+clock(depart)+repr(signature)).encode()).hexdigest()[:16]
                records.append({**common,"mode":"transit_walk_access","availability_status":tr["status"],
                                "in_vehicle_min":tr.get("in_vehicle_seconds",math.nan)/60,"walk_min":tr.get("walk_seconds",math.nan)/60,
                                "wait_min":tr.get("wait_seconds",math.nan)/60,"distance_m":"","fare_usd":tr.get("fare_usd",math.nan),
                                "fare_price_year":2026,"boardings":tr.get("boardings",math.nan),"ride_segment_count":tr.get("ride_segment_count",0),
                                "transfers":tr.get("transfers",math.nan),"path_id":pid,"cost_status":tr.get("fare_rule","schedule_search_no_path")})
        partial=chunk.with_suffix(".partial")
        write(partial,records);partial.replace(chunk)
        atomic_json(marker,{"input_signature":identity,"sha256":sha(chunk),"rows":len(records),"origin":oz})
        completed+=1;rows_total+=len(records)
        print(json.dumps({"phase":"origin_complete","origins":completed,"of":len(by_origin),"rows":rows_total,"wall_seconds":time.perf_counter()-t}),flush=True)
    final=out/"mode_specific_od_costs.csv"
    with final.with_suffix(".partial").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for chunk in sorted(chunk_dir.glob("*.csv")):
            writer.writerows(read(chunk))
    final.with_suffix(".partial").replace(final)
    summary={"status":"COMPLETE","input_signature":identity,"panel_od":len(panel),"skim_rows":rows_total,
             "reused_od_from_verified_prior_stage":len(reused_by_od),
             "origins":len(by_origin),"service_date":a.service_date,"departures":[clock(x) for x in departures],
             "scenario":"PLANNED_OVERLAY_OFF","setup_seconds":setup_seconds,"total_seconds":time.perf_counter()-t,
             "osm_stats":osm_stats,"active_trips":len(trip_meta),"connections":len(connections),"snapped_stops":len(stop_snap),
             "transfer_policy":transfer_policy.stats,"fare_policy":fare_policy.stats,"output_sha256":sha(final)}
    atomic_json(out/"summary.json",summary)
    print(json.dumps(summary,default=str))


if __name__=="__main__":raise SystemExit(main())
