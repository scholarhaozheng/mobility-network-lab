"""Recover many exact original-time paths from shared full-horizon price windows.

Each needed window recomputes the full backward dynamic program; only its
bounded action array is retained. All legal travel, zero-time, wait, and
terminal actions are the same as the single-event rolling recovery.
"""
from collections import defaultdict
from dataclasses import dataclass
import numpy as np
from .rolling_paths import _sweep_window
from .rolling_price import RollingModel

@dataclass
class BatchPaths:
    original_edge_index:list
    original_entry_step:list
    raw_cost:np.ndarray
    adjusted_cost:np.ndarray
    arrival_step:np.ndarray
    wait_count:np.ndarray
    windows_per_path:np.ndarray
    full_horizon_sweeps:int


def recover_many_paths(model:RollingModel,destination,origins,releases,
                       capacity_rows=(),capacity_lambda=(),
                       window_steps=2048,max_windows_per_path=12):
    destination=int(destination)
    origins=np.asarray(origins,dtype=np.int32)
    releases=np.asarray(releases,dtype=np.int32)
    if origins.shape!=releases.shape or origins.ndim!=1 or not len(origins):
        raise ValueError('original event query dimensions')
    if (np.any(origins<0) or np.any(origins>=model.n) or np.any(releases<0)
        or np.any(releases>model.H) or not 0<=destination<model.n):
        raise ValueError('original graph query outside model')
    if window_steps<=0 or max_windows_per_path<=0:
        raise ValueError('bounded exact recovery parameters')
    rows=np.asarray(capacity_rows,dtype=np.int64)
    lam=np.asarray(capacity_lambda,dtype=np.float64)
    if len(rows)!=len(lam) or len(set(map(int,rows)))!=len(rows) or np.any(lam<0):
        raise ValueError('original capacity toll mapping')
    arrays=model._arrays(rows,lam)
    edge_order=np.argsort(model.u,kind='stable')
    physical_pos=np.full(len(model.u),-1,dtype=np.int32)
    physical_pos[model.physical_edges]=np.arange(len(model.physical_edges),dtype=np.int32)
    toll={int(row):float(value) for row,value in zip(rows,lam) if value>0}
    M=len(origins)
    node=origins.copy();time=releases.copy()
    raw=np.zeros(M,dtype=np.float64);adjusted=np.zeros(M,dtype=np.float64)
    arrival=np.full(M,-1,dtype=np.int32)
    waits=np.zeros(M,dtype=np.int32);windows=np.zeros(M,dtype=np.int32)
    edges=[[] for _ in range(M)];entries=[[] for _ in range(M)]
    pending=defaultdict(list)
    for j in range(M):pending[int(time[j]//window_steps)].append(j)
    sweeps=0
    reverse=model.reverse_zero_topo.astype(np.int32)
    while pending:
        index=min(pending)
        group=pending.pop(index)
        start=index*window_steps;stop=min(model.H+1,start+window_steps)
        if start>model.H or not group:raise ValueError('original path beyond horizon')
        actions=np.empty((stop-start,model.n),dtype=np.int32)
        _sweep_window(model.n,model.H,model.dt,destination,
                      arrays[0],arrays[1],arrays[2],arrays[3],reverse,
                      arrays[4],arrays[5],arrays[6],
                      start,stop,int(node[group[0]]),actions)
        sweeps+=1
        for j in group:
            windows[j]+=1
            if windows[j]>max_windows_per_path:
                raise RuntimeError('bounded exact path recovery window count reached')
            while int(node[j])!=destination and int(time[j])<stop:
                t=int(time[j]);u=int(node[j]);choice=int(actions[t-start,u])
                if choice==-2:
                    if t>=model.H:raise ValueError('wait beyond original horizon')
                    increment=model.dt/60.
                    raw[j]+=increment;adjusted[j]+=increment
                    waits[j]+=1;time[j]=t+1
                elif choice>=0:
                    e=int(edge_order[choice])
                    if int(model.u[e])!=u:raise ValueError('broken exact policy edge')
                    next_time=t+int(model.duration[e])
                    if next_time>model.H:raise ValueError('travel beyond original horizon')
                    edges[j].append(e);entries[j].append(t)
                    increment=float(model.cost[e])
                    raw[j]+=increment;adjusted[j]+=increment
                    p=int(physical_pos[e])
                    if p>=0:adjusted[j]+=toll.get(p*model.H+t,0.)
                    node[j]=int(model.v[e]);time[j]=next_time
                else:
                    raise ValueError('unreachable original state in exact policy')
            if int(node[j])==destination:
                arrival[j]=int(time[j])
            else:
                if time[j]<=start or time[j]>model.H:
                    raise ValueError('original path failed to advance')
                pending[int(time[j]//window_steps)].append(j)
        del actions
    if np.any(arrival<0) or not np.all(np.isfinite(adjusted)):
        raise ValueError('unrecovered original commodity')
    return BatchPaths(edges,entries,raw,adjusted,arrival,waits,windows,sweeps)
