"""Lossless capacity-load interval update for a whole uniform-release path family."""
import numpy as np
from shared_cg.uniform_base_load import BaseLoadIntervals


def apply_delay_family(base,path_physical_edges,path_entry_offsets,delay_steps,
                       diverted_flow_per_release,hourly_capacity_per_step,
                       horizon_steps):
    edges=np.asarray(path_physical_edges,dtype=np.int32)
    offsets=np.asarray(path_entry_offsets,dtype=np.int32)
    y=np.asarray(diverted_flow_per_release,dtype=np.float64)
    cap=np.asarray(hourly_capacity_per_step,dtype=np.float64)
    H=int(horizon_steps);D=int(delay_steps)
    if len(edges)!=len(offsets) or len(np.unique(edges))!=len(edges):
        raise ValueError('noninjective physical path')
    if len(y)==0 or np.any(y<0) or not np.all(np.isfinite(y)) or D<0:
        raise ValueError('invalid original release split')
    if np.any(offsets<0) or np.any(offsets+D+len(y)>H):
        raise ValueError('shifted entry beyond original horizon')
    parts_edge=[base.edge_index,base.edge_index]
    parts_time=[base.start_step,base.stop_step]
    parts_delta=[base.load_pce,-base.load_pce]
    cuts=np.r_[0,np.flatnonzero(y[1:]!=y[:-1])+1,len(y)]
    nonzero=[]
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        amount=float(y[lo])
        if amount>1e-15:nonzero.append((int(lo),int(hi),amount))
    if nonzero:
        event_e=[];event_t=[];event_d=[]
        for edge,offset in zip(edges,offsets):
            e=int(edge);a=int(offset)
            for lo,hi,amount in nonzero:
                event_e.extend((e,e,e,e))
                event_t.extend((a+lo,a+hi,a+D+lo,a+D+hi))
                event_d.extend((-amount,amount,amount,-amount))
        parts_edge.append(np.asarray(event_e,np.int32))
        parts_time.append(np.asarray(event_t,np.int32))
        parts_delta.append(np.asarray(event_d,np.float64))
    ee=np.concatenate(parts_edge);tt=np.concatenate(parts_time);dd=np.concatenate(parts_delta)
    order=np.lexsort((tt,ee));ee=ee[order];tt=tt[order];dd=dd[order]
    same=np.r_[False,(ee[1:]==ee[:-1])&(tt[1:]==tt[:-1])]
    group=np.cumsum(~same)-1
    merged_delta=np.bincount(group,weights=dd)
    merged_e=ee[~same];merged_t=tt[~same]
    out_e=[];out_s=[];out_t=[];out_l=[]
    overload_edges=set();over_rows=0;positive_rows=0;max_ratio=0.0
    k=0
    while k<len(merged_e):
        e=int(merged_e[k]);load=0.0;last=0
        while k<len(merged_e) and int(merged_e[k])==e:
            now=int(merged_t[k])
            if now>last and load>1e-12:
                out_e.append(e);out_s.append(last);out_t.append(now);out_l.append(load)
                ratio=load/float(cap[e]);positive_rows+=now-last
                if ratio>1+1e-9:
                    over_rows+=now-last;overload_edges.add(e)
                max_ratio=max(max_ratio,ratio)
            if load < -1e-8:raise ValueError('negative original capacity load')
            load+=float(merged_delta[k]);last=now;k+=1
        if abs(load)>1e-8:raise ValueError('unbalanced shifted original flow')
    result=BaseLoadIntervals(np.asarray(out_e,np.int32),np.asarray(out_s,np.int32),
                             np.asarray(out_t,np.int32),np.asarray(out_l,np.float64),
                             len(overload_edges),over_rows,max_ratio,positive_rows)
    original_entry_mass=float(np.dot(base.load_pce,(base.stop_step-base.start_step)))
    updated_entry_mass=float(np.dot(result.load_pce,(result.stop_step-result.start_step)))
    if abs(updated_entry_mass-original_entry_mass)>max(1e-6,1e-9*original_entry_mass):
        raise ValueError('original physical entry mass changed')
    return result
