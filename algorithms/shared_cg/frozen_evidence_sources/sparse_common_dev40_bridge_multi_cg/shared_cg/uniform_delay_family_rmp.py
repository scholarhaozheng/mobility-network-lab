"""Exact separable Phase-I RMP for one uniform-release source-delay path family.

All T original OD release events remain individual commodities. The
source-delay alternative has the same physical edge sequence shifted by
D steps. If every delayed capacity row remains safe even at full q and
the original path uses each physical edge once, delayed rows impose no
active RMP restriction; every original base row is affected by at most
one event variable. The restricted master then separates exactly across
the T release variables, with untouched overload mass retained.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class DelayFamilyResult:
    delay_steps:int
    flow_to_delayed_path:np.ndarray
    baseline_artificial_mass:float
    optimized_artificial_mass:float
    total_diverted_pce:float
    positive_delayed_release_events:int
    independent_release_events:int
    minimum_delayed_row_margin_at_full_diversion:float
    delayed_original_capacity_rows_checked:int
    phase_I_cost_increment:float
    relative_artificial_reduction:float


def _load_at_times(base,edge,times):
    a=np.searchsorted(base.edge_index,edge,side='left')
    b=np.searchsorted(base.edge_index,edge,side='right')
    result=np.zeros(len(times),dtype=np.float64)
    if a==b:return result
    ix=np.searchsorted(base.start_step[a:b],times,side='right')-1
    valid=ix>=0
    pos=np.flatnonzero(valid)
    j=ix[valid]
    keep=times[valid]<base.stop_step[a+j]
    result[pos[keep]]=base.load_pce[a+j[keep]]
    return result


def solve_delay_family_phase_i(base,path_physical_edges,path_entry_offsets,
                               hourly_capacity_per_step,dt_seconds,
                               release_steps,horizon_steps,hourly_od_q,
                               maximum_base_arrival_offset,epsilon=1e-9):
    edges=np.asarray(path_physical_edges,dtype=np.int32)
    offsets=np.asarray(path_entry_offsets,dtype=np.int32)
    capacity=np.asarray(hourly_capacity_per_step,dtype=np.float64)
    T=int(release_steps);H=int(horizon_steps);dt=float(dt_seconds)
    q=float(hourly_od_q)/T
    if len(edges)==0 or len(edges)!=len(offsets) or len(np.unique(edges))!=len(edges):
        raise ValueError('selected base path must use each physical edge once')
    if np.any(offsets<0) or T<=0 or H<T or q<=0 or dt<=0 or epsilon<=0:
        raise ValueError('invalid original uniform-release identity')
    if np.any(edges<0) or np.any(edges>=len(capacity)) or np.any(capacity<=0):
        raise ValueError('invalid original physical capacity')
    overload=base.load_pce>capacity[base.edge_index]*(1+1e-9)
    ends_by_edge={}
    for edge,stop in zip(base.edge_index[overload],base.stop_step[overload]):
        edge=int(edge);ends_by_edge[edge]=max(ends_by_edge.get(edge,0),int(stop))
    D=max([T-1]+[ends_by_edge[int(e)]-int(a)
                 for e,a in zip(edges,offsets) if int(e) in ends_by_edge])
    if D<0 or D+T-1+int(maximum_base_arrival_offset)>H:
        raise ValueError('delayed original path exceeds original time horizon')
    releases=np.arange(T,dtype=np.int32)
    excess=np.empty((len(edges),T),dtype=np.float64)
    min_margin=np.inf
    for j,(edge,offset) in enumerate(zip(edges,offsets)):
        e=int(edge);a=int(offset)
        base_times=a+releases
        alt_times=a+D+releases
        baseline=_load_at_times(base,e,base_times)
        alt_baseline=_load_at_times(base,e,alt_times)
        excess[j]=baseline-capacity[e]
        margin=capacity[e]-alt_baseline-q
        min_margin=min(min_margin,float(np.min(margin)))
    if min_margin < -1e-9:
        raise ValueError('delayed family full-diversion capacity guard failed')
    positive=np.maximum(excess,0.0)
    slope=epsilon*D*dt/60
    if slope<1:
        y=np.minimum(q,np.max(positive,axis=0))
    else:
        y=np.empty(T,dtype=np.float64)
        for r in range(T):
            candidates=np.r_[0.,q,np.clip(excess[:,r],0,q)]
            values=np.maximum(excess[:,r,None]-candidates[None,:],0).sum(axis=0)+slope*candidates
            y[r]=candidates[int(np.argmin(values))]
    reduction=float(np.sum(positive-np.maximum(excess-y[None,:],0.0)))
    baseline_mass=float(np.sum(np.maximum(base.load_pce-capacity[base.edge_index],0)*
                               (base.stop_step-base.start_step)))
    optimized=baseline_mass-reduction
    if optimized < -1e-8 or optimized>baseline_mass+1e-8:
        raise ValueError('Phase I artificial accounting')
    return DelayFamilyResult(D,y,baseline_mass,optimized,float(np.sum(y)),
                             int(np.count_nonzero(y>1e-12)),T,min_margin,
                             len(edges)*T,slope*float(np.sum(y)),
                             reduction/max(baseline_mass,1e-12))
