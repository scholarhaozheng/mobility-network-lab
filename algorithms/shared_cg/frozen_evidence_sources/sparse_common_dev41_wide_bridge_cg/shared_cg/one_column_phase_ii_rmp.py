"""Exact sparse one-column extension of a uniform-release restricted Phase-II RMP.

The original event base path remains algebraic. Existing variable columns
are left intact; new resource rows cover every changed row of the new path.
"""
from dataclasses import dataclass
from collections import Counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

@dataclass
class Extension:
    matrix:object
    rows:np.ndarray
    rhs:np.ndarray
    costs:np.ndarray
    upper:np.ndarray
    flow:np.ndarray
    capacity_dual:np.ndarray
    lower_dual:np.ndarray
    upper_dual:np.ndarray
    objective_increment:float
    restricted_dual:float
    iterations:int
    new_rows:int
    maximum_retained_excess:float

def extend_one_column(old_matrix, old_rows, old_rhs, old_cost, old_upper,
                      selected_paths, delays, physical_pos, physical_edge,
                      baseline, capacity, H, T, base_event_rows, new_event_rows,
                      new_event_q, new_cost_increment, time_limit):
    old_rows=np.asarray(old_rows,dtype=np.int64)
    base_count=Counter(map(int,base_event_rows))
    new_count=Counter(map(int,new_event_rows))
    touched=np.array(sorted(set(base_count)|set(new_count)),dtype=np.int64)
    extra=np.setdiff1d(touched,old_rows,assume_unique=True)
    old_matrix=old_matrix.tocsr()
    if old_matrix.shape!=(len(old_rows),len(old_cost)):
        raise ValueError("existing RMP dimensions")
    if len(old_cost)!=len(selected_paths)*T:
        raise ValueError("selected source-delay family dimensions")
    extra_rhs=np.empty(len(extra),dtype=float)
    for j,row in enumerate(extra):
        p,t=divmod(int(row),H)
        edge=int(physical_edge[p])
        extra_rhs[j]=float(capacity[edge])-baseline.load_at(edge,t)
    coo_r=[];coo_c=[];coo_v=[]
    extra_location={int(row):j for j,row in enumerate(extra)}
    for g,path in enumerate(selected_paths):
        D=int(delays[g])
        for edge,offset in path:
            p=int(physical_pos[edge])
            if p<0:raise ValueError("nonphysical selected path")
            for row,j in extra_location.items():
                rp,t=divmod(row,H)
                if rp!=p:continue
                release=t-int(offset)
                if 0<=release<T:
                    coo_r.append(j);coo_c.append(g*T+release);coo_v.append(-1.0)
                release=t-int(offset)-D
                if 0<=release<T:
                    coo_r.append(j);coo_c.append(g*T+release);coo_v.append(1.0)
    extra_matrix=sparse.coo_matrix((coo_v,(coo_r,coo_c)),
                                   shape=(len(extra),len(old_cost))).tocsr()
    extra_matrix.sum_duplicates()
    old_column=np.array([new_count.get(int(r),0)-base_count.get(int(r),0)
                         for r in old_rows],dtype=np.float64)
    extra_column=np.array([new_count.get(int(r),0)-base_count.get(int(r),0)
                           for r in extra],dtype=np.float64)
    upper_matrix=sparse.hstack((old_matrix,sparse.csr_matrix(old_column[:,None])),format='csr')
    lower_matrix=sparse.hstack((extra_matrix,sparse.csr_matrix(extra_column[:,None])),format='csr')
    A=sparse.vstack((upper_matrix,lower_matrix),format='csr')
    rhs=np.r_[old_rhs,extra_rhs]
    costs=np.r_[old_cost,float(new_cost_increment)]
    upper=np.r_[old_upper,float(new_event_q)]
    if np.any(upper<=0) or not np.all(np.isfinite(rhs)):
        raise ValueError("invalid original source bounds")
    solve=linprog(costs,A_ub=A,b_ub=rhs,bounds=np.c_[np.zeros(len(upper)),upper],
                  method='highs',options={'presolve':True,'time_limit':float(time_limit),
                  'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not solve.success:
        raise RuntimeError(f'one-column restricted LP status={solve.status}: {solve.message}')
    flow=np.asarray(solve.x,dtype=float)
    excess=float(np.max(A@flow-rhs))
    if excess>1e-6 or np.any(flow<-1e-8) or np.any(flow>upper+1e-8):
        raise ValueError("new restricted primal infeasible")
    mu=np.asarray(solve.ineqlin.marginals,dtype=float)
    lower=np.asarray(solve.lower.marginals,dtype=float)
    upper_dual=np.asarray(solve.upper.marginals,dtype=float)
    dual=float(np.dot(rhs,mu)+np.dot(upper,upper_dual))
    return Extension(A,np.r_[old_rows,extra],rhs,costs,upper,flow,mu,lower,
                     upper_dual,float(solve.fun),dual,int(solve.nit),len(extra),excess)
