"""Exact sparse RMP extension by a time-shifted legal original-path family.

The original AON base path remains algebraic for every OD/release. This
operation adds one alternative column for each selected release of ONE OD.
The caller must exclude events already carrying other alternative columns;
commodity coupling for overlapping alternatives is a separate CG feature.
"""
from collections import Counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from .two_singleton_phase_ii_rmp import Extension


def extend_shifted_family(old_matrix, old_rows, old_rhs, old_cost, old_upper,
                          selected_paths, delays, prior_base_rows, prior_new_rows,
                          physical_pos, physical_edge, baseline, capacity, H, T,
                          base_flat_offsets, new_flat_offsets, releases,
                          event_q, cost_increment, time_limit):
    old_rows=np.asarray(old_rows,dtype=np.int64)
    old_rhs=np.asarray(old_rhs,dtype=np.float64)
    old_cost=np.asarray(old_cost,dtype=np.float64)
    old_upper=np.asarray(old_upper,dtype=np.float64)
    old_matrix=old_matrix.tocsr()
    releases=np.asarray(releases,dtype=np.int32)
    family_count=len(selected_paths)*T
    prior_count=len(prior_base_rows)
    if len(prior_new_rows)!=prior_count or old_matrix.shape!=(len(old_rows),len(old_cost)):
        raise ValueError('old RMP dimensions')
    if len(old_cost)!=family_count+prior_count or len(old_rhs)!=len(old_rows) or len(old_upper)!=len(old_cost):
        raise ValueError('old RMP family dimensions')
    if len(delays)!=len(selected_paths) or len(set(map(int,old_rows)))!=len(old_rows):
        raise ValueError('selected or retained row dimensions')
    if not len(releases) or np.any(np.diff(releases)<=0) or releases[0]<0 or releases[-1]>=T:
        raise ValueError('selected original releases must be sorted unique and in range')
    if not (0<event_q<np.inf) or not (0<time_limit<np.inf):
        raise ValueError('original demand or time limit')
    before=Counter(map(int,base_flat_offsets))
    after=Counter(map(int,new_flat_offsets))
    delta={key:after.get(key,0)-before.get(key,0) for key in set(before)|set(after)}
    delta={key:value for key,value in delta.items() if value}
    if not delta:raise ValueError('path has no physical capacity difference')
    keys=np.array(sorted(delta),dtype=np.int64)
    coeff=np.array([delta[int(key)] for key in keys],dtype=np.float64)
    if np.any(keys<0) or np.any(keys//H>=len(physical_edge)):
        raise ValueError('original physical edge outside graph')
    offsets=keys%H
    if np.any(offsets[:,None]+releases[None,:]>=H):
        raise ValueError('shifted original path exceeds horizon')
    candidate_rows=(keys[:,None]+releases[None,:]).reshape(-1)
    extra=np.setdiff1d(np.unique(candidate_rows),old_rows)
    all_rows=np.r_[old_rows,extra]
    sort_order=np.argsort(all_rows,kind='stable')
    sorted_rows=all_rows[sort_order]
    positions=np.searchsorted(sorted_rows,candidate_rows)
    if np.any(positions>=len(sorted_rows)) or not np.array_equal(sorted_rows[positions],candidate_rows):
        raise ValueError('incomplete exact original row mapping')
    row_index=sort_order[positions]
    column_index=np.tile(np.arange(len(releases),dtype=np.int32),len(keys))
    data=np.repeat(coeff,len(releases))
    new_matrix=sparse.coo_matrix((data,(row_index,column_index)),
                                 shape=(len(all_rows),len(releases))).tocsr()
    new_matrix.sum_duplicates()
    extra_rhs=np.empty(len(extra),dtype=np.float64)
    extra_by_edge={}
    location={int(row):j for j,row in enumerate(extra)}
    for row,j in location.items():
        p,t=divmod(row,H)
        edge=int(physical_edge[p])
        extra_rhs[j]=float(capacity[edge])-baseline.load_at(edge,t)
        extra_by_edge.setdefault(p,[]).append((t,j))
    rr=[];cc=[];vv=[]
    for g,path in enumerate(selected_paths):
        delay=int(delays[g])
        for edge,offset in path:
            p=int(physical_pos[int(edge)])
            if p<0:raise ValueError('nonphysical selected source path')
            for t,j in extra_by_edge.get(p,()):
                release=t-int(offset)
                if 0<=release<T:
                    rr.append(j);cc.append(g*T+release);vv.append(-1.)
                release-=delay
                if 0<=release<T:
                    rr.append(j);cc.append(g*T+release);vv.append(1.)
    for k,(base_path,new_path) in enumerate(zip(prior_base_rows,prior_new_rows)):
        b=Counter(map(int,base_path));n=Counter(map(int,new_path))
        for row,j in location.items():
            value=n.get(row,0)-b.get(row,0)
            if value:
                rr.append(j);cc.append(family_count+k);vv.append(float(value))
    extra_matrix=sparse.coo_matrix((vv,(rr,cc)),shape=(len(extra),len(old_cost))).tocsr()
    extra_matrix.sum_duplicates()
    left=sparse.vstack((old_matrix,extra_matrix),format='csr')
    A=sparse.hstack((left,new_matrix),format='csr')
    rhs=np.r_[old_rhs,extra_rhs]
    costs=np.r_[old_cost,np.full(len(releases),float(cost_increment))]
    upper=np.r_[old_upper,np.full(len(releases),float(event_q))]
    if np.any(upper<=0) or not np.all(np.isfinite(rhs)):
        raise ValueError('invalid original source bounds or capacity')
    solved=linprog(costs,A_ub=A,b_ub=rhs,
                   bounds=np.c_[np.zeros(len(upper)),upper],method='highs',
                   options={'presolve':True,'time_limit':float(time_limit),
                            'primal_feasibility_tolerance':1e-9,
                            'dual_feasibility_tolerance':1e-9})
    if not solved.success:
        raise RuntimeError(f'shifted family RMP status={solved.status}: {solved.message}')
    flow=np.asarray(solved.x,dtype=np.float64)
    excess=float(np.max(A@flow-rhs)) if len(rhs) else float('-inf')
    if excess>1e-6 or np.any(flow<-1e-8) or np.any(flow>upper+1e-8):
        raise ValueError('new family restricted primal infeasible')
    mu=np.asarray(solved.ineqlin.marginals,dtype=np.float64)
    lo=np.asarray(solved.lower.marginals,dtype=np.float64)
    up=np.asarray(solved.upper.marginals,dtype=np.float64)
    dual=float(np.dot(rhs,mu)+np.dot(upper,up))
    return Extension(A,all_rows,rhs,costs,upper,flow,mu,lo,up,
                     float(solved.fun),dual,int(solved.nit),len(extra),excess)
