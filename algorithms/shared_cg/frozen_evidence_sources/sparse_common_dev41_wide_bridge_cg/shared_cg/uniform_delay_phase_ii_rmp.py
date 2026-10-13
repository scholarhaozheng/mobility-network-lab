"""Exact sparse Phase-II RMP over source-delay families on uniform full demand.

Original baseline includes every commodity. Each selected OD release has
base flow q-y and delayed flow y. A physical entry row is omitted only if
its all-variable load upper bound is below capacity; this check uses the
original baseline plus all delayed columns at full q and ignores base
removals conservatively. Unaffected rows remain at the independently
verified baseline. This is a restricted path master, not a full CG proof.
"""
from dataclasses import dataclass
import numpy as np
from scipy import sparse
from scipy.optimize import linprog


@dataclass
class PhaseIIResult:
    flow:np.ndarray
    original_resource_rows:np.ndarray
    residual_capacity:np.ndarray
    path_objective_increment:np.ndarray
    matrix:object
    base_objective:float
    total_objective:float
    retained_rows:int
    nonzeros:int
    solver_iterations:int
    maximum_original_capacity_excess_on_retained:float
    restricted_dual_objective:float
    restricted_dual_gap:float
    capacity_dual:np.ndarray
    lower_bound_dual:np.ndarray
    upper_bound_dual:np.ndarray


def solve_delay_phase_ii(base,paths,delays,hourly_q,physical_pos,capacity,
                         dt,T,H,base_objective,max_rows,max_nonzeros,
                         time_limit_seconds):
    groups=len(paths)
    if groups==0 or len(delays)!=groups or len(hourly_q)!=groups:
        raise ValueError('delay family shape')
    cap=np.asarray(capacity,dtype=np.float64)
    q=np.asarray(hourly_q,dtype=np.float64)/T
    delays=np.asarray(delays,dtype=np.int32)
    if np.any(q<=0) or np.any(delays<0) or np.any(cap<=0):
        raise ValueError('invalid original Q model')
    edge_groups={}
    for g,path in enumerate(paths):
        edges=[int(e) for e,a in path]
        if len(set(edges))!=len(edges):
            raise ValueError('repeated physical edge in a path')
        for e,offset in path:
            edge_groups.setdefault(int(e),[]).append((g,int(offset)))
    selected_edges=sorted(edge_groups)
    rows=[];rhs=[]
    releases=np.arange(T,dtype=np.int32)
    for e in selected_edges:
        a=np.searchsorted(base.edge_index,e,'left')
        b=np.searchsorted(base.edge_index,e,'right')
        baseline=np.zeros(H,dtype=np.float64)
        for j in range(a,b):
            baseline[int(base.start_step[j]):int(base.stop_step[j])]=float(base.load_pce[j])
        upper=baseline.copy()
        for g,offset in edge_groups[e]:
            t=offset+int(delays[g])+releases
            if np.min(t)<0 or np.max(t)>=H:raise ValueError('delayed original row outside horizon')
            np.add.at(upper,t,q[g])
        retain=np.flatnonzero(upper>cap[e]-1e-9)
        p=int(physical_pos[e])
        if p<0:raise ValueError('nonphysical capacity row')
        rows.append(p*H+retain.astype(np.int64))
        rhs.append(cap[e]-baseline[retain])
    original_rows=np.sort(np.concatenate(rows))
    if len(original_rows)>max_rows:
        raise MemoryError('pre-registered retained row gate')
    # The original resource index has a unique edge and time, so no duplicate.
    if len(np.unique(original_rows))!=len(original_rows):
        raise ValueError('duplicate original capacity row')
    # rhs was appended in edge-ID order; realign to original physical-row order.
    unsorted_rows=np.concatenate(rows)
    unsorted_rhs=np.concatenate(rhs)
    ordering=np.argsort(unsorted_rows)
    b_ub=unsorted_rhs[ordering]
    coo_r=[];coo_c=[];coo_v=[]
    for g,path in enumerate(paths):
        cols=g*T+releases
        for e,offset in path:
            p=int(physical_pos[int(e)])
            for entry,coef in ((int(offset)+releases,-1.0),
                               (int(offset)+int(delays[g])+releases,1.0)):
                resource=p*H+entry.astype(np.int64)
                loc=np.searchsorted(original_rows,resource)
                valid=loc<len(original_rows)
                match=np.zeros(T,dtype=bool)
                match[valid]=original_rows[loc[valid]]==resource[valid]
                if np.any(match):
                    coo_r.append(loc[match].astype(np.int32))
                    coo_c.append(cols[match].astype(np.int32))
                    coo_v.append(np.full(int(np.count_nonzero(match)),coef))
    rr=np.concatenate(coo_r) if coo_r else np.empty(0,np.int32)
    cc=np.concatenate(coo_c) if coo_c else np.empty(0,np.int32)
    vv=np.concatenate(coo_v) if coo_v else np.empty(0,np.float64)
    if len(vv)>max_nonzeros:raise MemoryError('pre-registered nonzero gate')
    matrix=sparse.coo_matrix((vv,(rr,cc)),shape=(len(original_rows),groups*T)).tocsr()
    matrix.sum_duplicates()
    objective=np.repeat(delays.astype(np.float64)*dt/60,T)
    upper_bounds=np.repeat(q,T)
    bounds=np.c_[np.zeros(groups*T),upper_bounds]
    raw=linprog(objective,A_ub=matrix,b_ub=b_ub,bounds=bounds,method='highs',
                options={'presolve':True,'time_limit':float(time_limit_seconds),
                         'primal_feasibility_tolerance':1e-9,
                         'dual_feasibility_tolerance':1e-9})
    if not raw.success:
        raise RuntimeError(f'restricted Phase II LP status={raw.status}: {raw.message}')
    flow=np.asarray(raw.x,dtype=np.float64).reshape(groups,T)
    maximum=float(np.max(np.asarray(matrix@raw.x-b_ub))) if len(b_ub) else 0.0
    if maximum>1e-6 or np.any(flow<-1e-8) or np.any(flow>q[:,None]+1e-8):
        raise ValueError('restricted original primal infeasible')
    mu=np.asarray(raw.ineqlin.marginals,dtype=np.float64)
    lower=np.asarray(raw.lower.marginals,dtype=np.float64)
    upper=np.asarray(raw.upper.marginals,dtype=np.float64)
    restricted_dual=float(np.dot(b_ub,mu)+np.dot(upper_bounds,upper))
    total=float(base_objective+raw.fun)
    return PhaseIIResult(flow,original_rows,b_ub,objective,matrix,
                         float(base_objective),total,len(original_rows),matrix.nnz,
                         int(raw.nit),maximum,restricted_dual,
                         float(raw.fun-restricted_dual),mu,lower,upper)
