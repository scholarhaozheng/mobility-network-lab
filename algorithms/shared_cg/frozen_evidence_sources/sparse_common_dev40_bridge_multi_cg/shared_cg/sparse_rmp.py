"""Exact sparse path RMP with capacity-row and fixed-commodity elimination.

Every original commodity and capacity resource remains in the mathematical
model.  A commodity with one current path has a fixed flow q; substituting it
into the current restricted master is an exact algebraic reduction.  The
elimination and row-redundancy proof are recomputed after every column batch.
"""
from dataclasses import dataclass
from types import SimpleNamespace
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

@dataclass
class MasterResult:
    phase:str
    optimization:object
    capacity_rows:np.ndarray
    column_costs:np.ndarray
    equality_dual:np.ndarray
    capacity_dual:np.ndarray
    artificial_total:float
    path_variable_count:int
    capacity_row_count:int
    used_capacity_rows_before_exact_reduction:int
    exactly_redundant_capacity_rows:int
    fixed_commodity_count:int
    reduced_master_path_variables:int
    reduced_master_equality_rows:int

def solve_master(model,columns,phase,epsilon=1e-9,time_limit=1800):
    if phase not in ('I','II'):raise ValueError('bad CG phase')
    K=model.K;P=len(columns)
    if P<K:raise ValueError('missing initial column for an original commodity')
    commodity=np.fromiter((int(c.commodity) for c in columns),dtype=np.int32,count=P)
    if np.any(commodity<0) or np.any(commodity>=K):raise ValueError('column commodity out of range')
    counts=np.bincount(commodity,minlength=K)
    if np.any(counts==0):raise ValueError('hidden unserved positive commodity')
    fixed_col=np.flatnonzero(counts[commodity]==1)
    var_col=np.flatnonzero(counts[commodity]>1)
    multi_k=np.flatnonzero(counts>1)
    fixed_x=model.q[commodity[fixed_col]]
    lengths=np.fromiter((len(c.resources) for c in columns),dtype=np.int32,count=P)
    if int(lengths.sum()):
        resources=np.concatenate([c.resources for c in columns]).astype(np.int32,copy=False)
        if np.any(resources<0) or np.any(resources>=model.resource_count):
            raise ValueError('capacity resource outside original graph')
        rows=np.unique(resources)
        ridx=np.searchsorted(rows,resources).astype(np.int32)
        cidx=np.repeat(np.arange(P,dtype=np.int32),lengths)
        aub=sparse.coo_matrix((np.ones(len(resources),dtype=np.float64),(ridx,cidx)),
                              shape=(len(rows),P)).tocsr()
        before=len(rows)
        # All original adapters are DAGs; repeated use of a resource within a
        # path is nevertheless handled conservatively by retaining all rows.
        if len(aub.data) and np.max(aub.data)>1.0:
            keep=np.ones(len(rows),dtype=np.bool_)
        else:
            K64=np.int64(K)
            pair=np.unique(ridx.astype(np.int64)*K64+commodity[cidx].astype(np.int64))
            upper=np.bincount(pair//K64,weights=model.q[(pair%K64).astype(np.int64)],
                              minlength=len(rows))
            cap_all=model.capacity_for_rows(rows)
            margin=np.maximum(1e-9,1e-9*np.abs(cap_all))
            keep=upper>cap_all-margin
        aub=aub[keep,:]
        rows=rows[keep]
    else:
        rows=np.empty(0,dtype=np.int32)
        aub=sparse.csr_matrix((0,P),dtype=np.float64)
        before=0
    cap=model.capacity_for_rows(rows)
    nrow=len(rows)
    costs=np.fromiter((float(c.objective_cost) for c in columns),dtype=np.float64,count=P)
    if np.any(~np.isfinite(costs)) or np.any(costs<0):raise ValueError('invalid true path cost')
    scale=epsilon if phase=='I' else 1.0
    fixed_cost=float(np.dot(scale*costs[fixed_col],fixed_x))
    fixed_load=np.asarray(aub[:,fixed_col]@fixed_x,dtype=np.float64).reshape(-1)
    residual_cap=cap-fixed_load
    xfull=np.zeros(P+(nrow if phase=='I' else 0),dtype=np.float64)
    xfull[fixed_col]=fixed_x
    if len(var_col)==0:
        excess=np.maximum(fixed_load-cap,0.0)
        if phase=='II' and np.any(excess>1e-8):
            raise RuntimeError('fixed restricted pool violates original capacity')
        mu=np.where(excess>1e-10,-1.0,0.0) if phase=='I' else np.zeros(nrow)
        if phase=='I':xfull[P:]=excess
        fun=fixed_cost+(float(np.sum(excess)) if phase=='I' else 0.0)
        result=SimpleNamespace(x=xfull,fun=fun)
        eq=np.zeros(K,dtype=np.float64)
    else:
        var_commodity=commodity[var_col]
        eqrow=np.searchsorted(multi_k,var_commodity)
        aeq=sparse.coo_matrix((np.ones(len(var_col),dtype=np.float64),
                               (eqrow,np.arange(len(var_col),dtype=np.int32))),
                              shape=(len(multi_k),len(var_col))).tocsr()
        aub_var=aub[:,var_col]
        if phase=='I':
            objective=np.r_[epsilon*costs[var_col],np.ones(nrow,dtype=np.float64)]
            aub_var=sparse.hstack((aub_var,-sparse.eye(nrow,format='csr')),format='csr')
            aeq=sparse.hstack((aeq,sparse.csr_matrix((len(multi_k),nrow))),format='csr')
        else:objective=costs[var_col]
        raw=linprog(objective,A_ub=aub_var if nrow else None,
                    b_ub=residual_cap if nrow else None,
                    A_eq=aeq,b_eq=model.q[multi_k],bounds=(0,None),method='highs',
                    options={'presolve':True,'time_limit':float(time_limit),
                             'primal_feasibility_tolerance':1e-9,
                             'dual_feasibility_tolerance':1e-9})
        if not raw.success:
            raise RuntimeError(f'RMP {phase} failed status={raw.status}: {raw.message}')
        xfull[var_col]=raw.x[:len(var_col)]
        if phase=='I':xfull[P:]=raw.x[len(var_col):]
        mu=np.asarray(raw.ineqlin.marginals if nrow else [],dtype=np.float64)
        eq=np.zeros(K,dtype=np.float64)
        eq[multi_k]=np.asarray(raw.eqlin.marginals,dtype=np.float64)
        result=SimpleNamespace(x=xfull,fun=float(raw.fun)+fixed_cost)
    if mu.shape!=(nrow,) or np.any(mu>1e-7):raise ValueError('RMP capacity dual sign/coverage failure')
    # The omitted equality for a one-path commodity is reconstructed so its
    # existing path has zero reduced cost under the retained capacity dual.
    if len(fixed_col):
        fixed_adjust=np.asarray(aub[:,fixed_col].T@mu,dtype=np.float64).reshape(-1)
        eq[commodity[fixed_col]]=scale*costs[fixed_col]-fixed_adjust
    if eq.shape!=(K,) or np.any(~np.isfinite(eq)):
        raise ValueError('RMP reconstructed equality dual coverage failure')
    art=float(np.sum(xfull[P:])) if phase=='I' else 0.0
    return MasterResult(phase,result,rows,costs,eq,mu,art,P,nrow,before,before-nrow,
                        len(fixed_col),len(var_col),len(multi_k))
