"""Deterministic nested coverage-first selection of saved Boston HBW midday OD."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def atomic_json(path,record):
    path=Path(path)
    temporary=path.with_name(path.name+".partial")
    temporary.write_text(json.dumps(record,indent=2),encoding="utf-8")
    temporary.replace(path)


def write(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--regional-od",required=True)
    ap.add_argument("--zone-crosswalk",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    source=read(a.regional_od)
    cross={r["original_h3_zone_id"]:r for r in read(a.zone_crosswalk)}
    records=[];intrazonal=[];keys=set()
    for r in source:
        if r["purpose"]!="HBW":continue
        q=float(r["person_trips_midday_od"])
        if q<=0:continue
        k=(r["o_zone_id"],r["d_zone_id"])
        if k in keys:raise ValueError("duplicate saved OD")
        keys.add(k)
        if k[0]==k[1]:intrazonal.append(r);continue
        if k[0] not in cross or k[1] not in cross:raise ValueError("missing network-wide crosswalk")
        d=float(r["impedance_min_drive_free_flow_proxy"])
        stratum="near" if d<5 else "middle" if d<12 else "far"
        x=dict(r)
        x.update(od_id="hbw_"+hashlib.sha1((k[0]+"|"+k[1]).encode()).hexdigest()[:16],
                 o_parent_zone_id=cross[k[0]]["parent_h3_zone_id"],
                 d_parent_zone_id=cross[k[1]]["parent_h3_zone_id"],
                 o_node_id=cross[k[0]]["source_physical_access_node_id"],
                 d_node_id=cross[k[1]]["source_physical_access_node_id"],
                 distance_stratum=stratum)
        records.append(x)
    if len(records)!=30790 or len(intrazonal)!=171:
        raise ValueError(f"source count differs from expected: {len(records)} inter, {len(intrazonal)} intra")
    # Stable coverage-first rule: greedy maximum novelty over origins, destinations,
    # parent-pair and free-flow distance stratum, then demand-ranked fill.
    remaining={r["od_id"]:r for r in records}
    chosen=[];origins=set();destinations=set();parent_pairs=set();strata=set()
    for _ in range(2000):
        best=None;score=None
        for r in remaining.values():
            pp=(r["o_parent_zone_id"],r["d_parent_zone_id"])
            s=(int(r["o_zone_id"] not in origins)+int(r["d_zone_id"] not in destinations),
               int(pp not in parent_pairs),int(r["distance_stratum"] not in strata),
               float(r["person_trips_midday_od"]),r["od_id"])
            if score is None or s>score:score=s;best=r
        chosen.append(best);del remaining[best["od_id"]]
        origins.add(best["o_zone_id"]);destinations.add(best["d_zone_id"])
        parent_pairs.add((best["o_parent_zone_id"],best["d_parent_zone_id"]))
        strata.add(best["distance_stratum"])
    order=chosen+sorted(remaining.values(),key=lambda r:(-float(r["person_trips_midday_od"]),r["od_id"]))
    out=Path(a.output).resolve()
    for raw in (a.regional_od,a.zone_crosswalk):
        source_path=Path(raw).resolve()
        if out==source_path or source_path in out.parents or out in source_path.parents:
            raise ValueError("source/output overlap")
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty output")
    out.mkdir(parents=True)
    source_lock={"regional_od_sha256":sha(a.regional_od),
        "zone_crosswalk_sha256":sha(a.zone_crosswalk),"rule_version":"coverage_first_v1"}
    fields=list(order[0])
    write(out/"selection_order.csv",[{**r,"selection_rank":i+1} for i,r in enumerate(order)],fields+["selection_rank"])
    total=sum(float(r["person_trips_midday_od"]) for r in records+intrazonal)
    for label,n in (("500",500),("2000",2000),("all",len(order))):
        sub=order[:n]
        write(out/f"selected_{label}.csv",sub,fields)
        summary={"tier":label,"selected_zone_od":len(sub),"source_interzonal_od":len(records),"source_intrazonal_od":len(intrazonal),
                 "source_hbw_person_mass":total,"selected_person_mass":sum(float(r["person_trips_midday_od"]) for r in sub),
                 "distinct_origins":len({r["o_zone_id"] for r in sub}),"distinct_destinations":len({r["d_zone_id"] for r in sub}),
                 "mapped_physical_origins":len({r["o_node_id"] for r in sub}),
                 "mapped_physical_destinations":len({r["d_node_id"] for r in sub}),
                 "distinct_parent_pairs":len({(r["o_parent_zone_id"],r["d_parent_zone_id"]) for r in sub}),
                 "distinct_endpoint_nodes":len({r[k] for r in sub for k in ("o_node_id","d_node_id")}),
                 "mapped_node_od":len({(r["o_node_id"],r["d_node_id"]) for r in sub if r["o_node_id"]!=r["d_node_id"]}),
                 "same_access_node_rows":sum(r["o_node_id"]==r["d_node_id"] for r in sub),
                 "rule":"greedy_missing_zone_endpoints_then_parent_pair_then_distance_stratum_then_demand_then_OD_id; first 2000, remainder demand-ranked",
                 "expansion_factor":1}
        summary["selected_source_mass_fraction"]=summary["selected_person_mass"]/total
        atomic_json(out/f"selection_{label}.json",summary)
        print(json.dumps(summary))
    source_lock["output_hashes"]={name:sha(out/name) for name in
        ("selection_order.csv","selected_500.csv","selected_2000.csv","selected_all.csv",
         "selection_500.json","selection_2000.json","selection_all.json")}
    atomic_json(out/"SOURCE_LOCK.json",source_lock)


if __name__=="__main__":main()
