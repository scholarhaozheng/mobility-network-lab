"""Exact interval aggregation of uniform-release base path capacity loads.

For a fixed per-OD path template and a uniform T-step release, each
physical edge entry offset a contributes q/T on [a,a+T). Superpose
signed endpoints to represent all original edge-time rows without a
dense E x H array. No OD, release event, physical resource, or capacity
constraint is removed.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class BaseLoadIntervals:
    edge_index: np.ndarray
    start_step: np.ndarray
    stop_step: np.ndarray
    load_pce: np.ndarray
    overloaded_edge_count: int
    overloaded_entry_row_count: int
    max_capacity_ratio: float
    positive_capacity_row_count: int

    def load_at(self,edge,time):
        e=int(edge);t=int(time)
        lo=np.searchsorted(self.edge_index,e,side='left')
        hi=np.searchsorted(self.edge_index,e,side='right')
        if lo==hi:return 0.0
        starts=self.start_step[lo:hi]
        j=int(np.searchsorted(starts,t,side='right'))-1
        if j<0 or t>=int(self.stop_step[lo+j]):return 0.0
        return float(self.load_pce[lo+j])


def build_base_load(od_edge_offset,edge_index,entry_offset_steps,od_hourly_pce,
                    physical_mask,hourly_capacity,dt_seconds,release_steps,horizon_steps):
    offsets=np.asarray(od_edge_offset,dtype=np.int64)
    edge=np.asarray(edge_index,dtype=np.int32)
    entry=np.asarray(entry_offset_steps,dtype=np.int32)
    volume=np.asarray(od_hourly_pce,dtype=np.float64)
    physical=np.asarray(physical_mask,dtype=bool)
    cap=np.asarray(hourly_capacity,dtype=np.float64)
    m=len(physical);T=int(release_steps);H=int(horizon_steps);dt=float(dt_seconds)
    if len(cap)!=m or len(edge)!=len(entry) or len(offsets)!=len(volume)+1:
        raise ValueError('base template array shape')
    if T<=0 or H<T or dt<=0 or abs(T*dt-3600)>1e-8:
        raise ValueError('original full-hour time model')
    if offsets[0]!=0 or offsets[-1]!=len(edge) or np.any(np.diff(offsets)<0):
        raise ValueError('base template offsets')
    if np.any(edge<0) or np.any(edge>=m) or np.any(entry<0) or np.any(entry+T>H):
        raise ValueError('base path original edge/time')
    if np.any(volume<=0) or not np.all(np.isfinite(volume)):
        raise ValueError('missing original positive OD')
    if np.any(cap<=0) or not np.all(np.isfinite(cap)):
        raise ValueError('invalid original capacity')
    od_for_arc=np.repeat(np.arange(len(volume),dtype=np.int32),np.diff(offsets))
    take=physical[edge]
    pe=edge[take]
    st=entry[take]
    delta=(volume[od_for_arc[take]]/T).astype(np.float64)
    event_edge=np.r_[pe,pe]
    event_time=np.r_[st,st+T]
    event_delta=np.r_[delta,-delta]
    order=np.lexsort((event_time,event_edge))
    event_edge=event_edge[order]
    event_time=event_time[order]
    event_delta=event_delta[order]
    unique=np.empty(len(event_edge),dtype=bool)
    unique[0]=True
    unique[1:]=(event_edge[1:]!=event_edge[:-1]) | (event_time[1:]!=event_time[:-1])
    group=np.cumsum(unique)-1
    merged_delta=np.bincount(group,weights=event_delta)
    merged_edge=event_edge[unique]
    merged_time=event_time[unique]
    out_edge=[];out_start=[];out_stop=[];out_load=[]
    overload_edges=set();over_rows=0;positive_rows=0;max_ratio=0.0
    at=0
    while at<len(merged_edge):
        e=int(merged_edge[at])
        load=0.0;last=0
        while at<len(merged_edge) and int(merged_edge[at])==e:
            now=int(merged_time[at])
            if now>last and load>1e-12:
                out_edge.append(e);out_start.append(last);out_stop.append(now);out_load.append(load)
                ratio=load/(float(cap[e])*dt/3600)
                positive_rows+=now-last
                if ratio>1+1e-9:
                    overload_edges.add(e);over_rows+=now-last
                max_ratio=max(max_ratio,ratio)
            load+=float(merged_delta[at])
            last=now
            at+=1
        if abs(load)>1e-8:raise ValueError('unbalanced original uniform-release events')
    return BaseLoadIntervals(np.asarray(out_edge,dtype=np.int32),
                             np.asarray(out_start,dtype=np.int32),
                             np.asarray(out_stop,dtype=np.int32),
                             np.asarray(out_load,dtype=np.float64),
                             len(overload_edges),over_rows,max_ratio,positive_rows)
