"""Finite time-expanded network loader, independent of optimization methods."""
from __future__ import annotations

import csv
from collections import deque
from pathlib import Path

import numpy as np


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))


def load(arc_file, demand_file):
    arcs, demands = read_csv(arc_file), read_csv(demand_file)
    ids = [r["arc_id"] for r in arcs]
    if len(set(ids)) != len(ids): raise ValueError("duplicate arc ID")
    nodes = sorted(set(r["from_node_time_id"] for r in arcs) | set(r["to_node_time_id"] for r in arcs))
    lookup = {n:i for i,n in enumerate(nodes)}
    u = np.array([lookup[r["from_node_time_id"]] for r in arcs],dtype=np.int32)
    v = np.array([lookup[r["to_node_time_id"]] for r in arcs],dtype=np.int32)
    cost = np.array([float(r["cost"]) for r in arcs]); cap = np.array([float(r["capacity"]) for r in arcs])
    if np.any(cost < 0) or np.any(cap < 0): raise ValueError("negative cost or capacity")
    indeg=np.bincount(v,minlength=len(nodes)); adj=[[] for _ in nodes]
    for a,node in enumerate(u): adj[node].append(a)
    for lst in adj: lst.sort(key=lambda a: ids[a])
    ready=deque(i for i,d in enumerate(indeg) if d==0); order=[]
    while ready:
        node=ready.popleft(); order.append(node)
        for a in adj[node]:
            end=v[a]; indeg[end]-=1
            if indeg[end]==0: ready.append(end)
    if len(order)!=len(nodes): raise ValueError("dynamic graph is cyclic")
    max_time=max(int(float(r["to_time"])) for r in arcs)
    commodity=[]; allowed=[]
    types=np.array([r["arc_type"] for r in arcs]); base=(types!="source_connector")&(types!="sink_connector")
    for d in demands:
        ident=d["demand_id"]; src=f"source_{ident}_t{int(float(d['departure_time']))}"; sink=f"sink_{ident}_t{max_time}"
        if src not in lookup or sink not in lookup: raise ValueError(f"missing connector node for {ident}")
        volume=float(d["volume"])
        if volume<=0: raise ValueError("nonpositive demand")
        commodity.append({"id":ident,"source":lookup[src],"sink":lookup[sink],"volume":volume})
        allow=base.copy()
        allow|=(types=="source_connector")&(u==lookup[src])
        allow|=(types=="sink_connector")&(v==lookup[sink])
        allowed.append(allow)
    return {"arcs":arcs,"demands":demands,"ids":ids,"nodes":nodes,"u":u,"v":v,"cost":cost,"cap":cap,
            "order":order,"adj":adj,"commodities":commodity,"allowed":np.asarray(allowed),"types":types}


def shortest_path(p, k, weights):
    src=p["commodities"][k]["source"]; sink=p["commodities"][k]["sink"]
    dist=np.full(len(p["nodes"]),np.inf); pred=np.full(len(dist),-1,dtype=np.int32); dist[src]=0
    allowed=p["allowed"][k]
    for node in p["order"]:
        if not np.isfinite(dist[node]): continue
        for a in p["adj"][node]:
            if not allowed[a]: continue
            end=p["v"][a]; value=dist[node]+weights[a]
            if value<dist[end]-1e-10: dist[end]=value; pred[end]=a
    if not np.isfinite(dist[sink]): raise ValueError(f"unreachable demand {p['commodities'][k]['id']}")
    path=[]; node=sink
    while node!=src:
        a=int(pred[node]);
        if a<0: raise ValueError("broken predecessor")
        path.append(a); node=int(p["u"][a])
    return float(dist[sink]),tuple(path[::-1])
