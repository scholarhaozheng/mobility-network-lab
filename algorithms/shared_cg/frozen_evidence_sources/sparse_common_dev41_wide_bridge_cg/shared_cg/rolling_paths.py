"""Recover an exact original-time path from a rolling full-graph price oracle.

This experimental common-core module uses a bounded choice window. Each
window recomputes the exact full-horizon backward dynamic program; thus
discarded action arrays never restrict the admissible path domain. A path
that leaves a window starts another full-horizon sweep. It is intentionally
a correctness-first component, not an accepted CG endpoint.
"""
from dataclasses import dataclass
import math
import numpy as np
from numba import njit
from shared_cg.rolling_price import RollingModel


@njit(cache=True)
def _sweep_window(n, H, dt, destination, offset, head, cost, duration,
                  reverse_zero_topo, toll_ptr, toll_time_desc, toll_value,
                  start, stop, origin, action_window):
    D=int(np.max(duration))
    slots=D+1
    ring=np.full((slots,n),np.inf,dtype=np.float64)
    cursor=toll_ptr[:-1].copy()
    query_value=np.inf
    for t in range(H,-1,-1):
        slot=t%slots
        for j in range(n):
            node=reverse_zero_topo[j]
            best=0.0 if node==destination else np.inf
            chosen=-1 if node==destination else -3
            if t<H:
                w=dt/60.0+ring[(t+1)%slots,node]
                if w<best:
                    best=w;chosen=-2
            for e in range(offset[node],offset[node+1]):
                d=duration[e]
                if t+d>H:continue
                future=ring[slot,head[e]] if d==0 else ring[(t+d)%slots,head[e]]
                p=cursor[e];end=toll_ptr[e+1]
                while p<end and toll_time_desc[p]>t:p+=1
                cursor[e]=p
                toll=toll_value[p] if p<end and toll_time_desc[p]==t else 0.0
                candidate=cost[e]+toll+future
                if candidate<best:
                    best=candidate;chosen=e
            ring[slot,node]=best
            if start<=t<stop:action_window[t-start,node]=chosen
        if t==start:query_value=ring[slot,origin]
    return query_value


@dataclass
class RecoveredPath:
    original_edge_time: list
    waits: list
    original_capacity_rows: list
    action_sequence: list
    raw_cost: float
    adjusted_cost: float
    full_graph_price: float
    arrival_step: int
    sweeps: int
    action_window_steps: int


def recover_path(model:RollingModel,destination,release,origin,capacity_rows=(),
                 capacity_lambda=(),window_steps=2048,max_sweeps=32):
    """Return one exact adjusted-shortest path, with original edge/resource IDs."""
    destination=int(destination);release=int(release);origin=int(origin)
    if not (0<=destination<model.n and 0<=origin<model.n and 0<=release<=model.H):
        raise ValueError("query outside original graph")
    if window_steps<=0 or max_sweeps<=0:
        raise ValueError("invalid recovery budget")
    rows=np.asarray(capacity_rows,dtype=np.int64)
    lam=np.asarray(capacity_lambda,dtype=np.float64)
    arrays=model._arrays(rows,lam)
    edge_order=np.argsort(model.u,kind="stable")
    physical_pos=np.full(len(model.u),-1,dtype=np.int32)
    physical_pos[model.physical_edges]=np.arange(len(model.physical_edges),dtype=np.int32)
    toll_lookup={int(r):float(v) for r,v in zip(rows,lam)}
    node=origin;t=release;first_value=None;sweeps=0
    edges=[];waits=[];resources=[];sequence=[];raw=0.0;adjusted=0.0
    seen=set()
    while node!=destination:
        if sweeps>=max_sweeps:raise RuntimeError("bounded recovery sweep count reached; no path certificate")
        if t>model.H:raise ValueError("path passed original horizon")
        start=t;stop=min(model.H+1,start+window_steps)
        actions=np.empty((stop-start,model.n),dtype=np.int32)
        value=float(_sweep_window(model.n,model.H,model.dt,destination,
                                  arrays[0],arrays[1],arrays[2],arrays[3],
                                  model.reverse_zero_topo.astype(np.int32),
                                  arrays[4],arrays[5],arrays[6],
                                  start,stop,node,actions))
        if not math.isfinite(value):raise ValueError("original commodity unreachable")
        if first_value is None:first_value=value
        sweeps+=1
        while node!=destination and t<stop:
            state=(t,node)
            if state in seen:raise ValueError("zero-duration cycle in recovered path")
            seen.add(state)
            action=int(actions[t-start,node])
            if action==-2:
                if t>=model.H:raise ValueError("wait beyond original horizon")
                waits.append((t,node));sequence.append(("wait",node,t))
                raw+=model.dt/60.0;adjusted+=model.dt/60.0;t+=1
            elif action>=0:
                original_e=int(edge_order[action])
                if int(model.u[original_e])!=node:raise ValueError("broken recovered edge")
                entry=t
                d=int(model.duration[original_e])
                t+=d;node=int(model.v[original_e])
                if t>model.H:raise ValueError("travel beyond original horizon")
                edges.append((original_e,entry));sequence.append(("edge",original_e,entry))
                c=float(model.cost[original_e])
                raw+=c;adjusted+=c
                p=int(physical_pos[original_e])
                if p>=0:
                    row=p*model.H+entry
                    resources.append(row)
                    adjusted+=toll_lookup.get(row,0.0)
            else:
                raise ValueError("invalid recovered action")
        del actions
    if first_value is None:first_value=0.0
    if abs(adjusted-first_value)>1e-7:
        raise ValueError("recovered path cost differs from full graph price")
    return RecoveredPath(edges,waits,resources,sequence,raw,adjusted,
                         first_value,t,sweeps,window_steps)


