"""Sparse path restricted master shared by explicit and implicit graph adapters.

The Phase I capacity slack variables are algorithmic artificials only. The
commodity equality rows always cover every original positive release event.
"""
from dataclasses import dataclass
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

def solve_master(model,columns,phase,epsilon=1e-9,time_limit=1800):
    if phase not in ("I","II"):raise ValueError("bad CG phase")
    K=model.K
    P=len(columns)
    if P<K:raise ValueError("missing initial column for an original commodity")
    commodity=np.fromiter((int(c.commodity) for c in columns),dtype=np.int32,count=P)
    if np.any(commodity<0) or np.any(commodity>=K):
        raise ValueError("column commodity out of range")
    represented=np.bincount(commodity,minlength=K)
    if np.any(represented==0):raise ValueError("hidden unserved positive commodity")
    lengths=np.fromiter((len(c.resources) for c in columns),dtype=np.int32,count=P)
    if int(lengths.sum()):
        resources=np.concatenate([c.resources for c in columns]).astype(np.int32,copy=False)
        if np.any(resources<0) or np.any(resources>=model.resource_count):
            raise ValueError("capacity resource outside original graph")
        rows=np.unique(resources)
        ridx=np.searchsorted(rows,resources).astype(np.int32)
        cidx=np.repeat(np.arange(P,dtype=np.int32),lengths)
        aub=sparse.coo_matrix((np.ones(len(resources),dtype=np.float64),(ridx,cidx)),
                              shape=(len(rows),P)).tocsr()
    else:
        rows=np.empty(0,dtype=np.int32)
        aub=sparse.csr_matrix((0,P),dtype=np.float64)
    aeq=sparse.coo_matrix((np.ones(P,dtype=np.float64),
                           (commodity,np.arange(P,dtype=np.int32))),
                          shape=(K,P)).tocsr()
    costs=np.fromiter((float(c.objective_cost) for c in columns),dtype=np.float64,count=P)
    if np.any(~np.isfinite(costs)) or np.any(costs<0):
        raise ValueError("invalid true path cost")
    cap=model.capacity_for_rows(rows)
    if phase=="I":
        objective=np.r_[epsilon*costs,np.ones(len(rows),dtype=np.float64)]
        aub=sparse.hstack((aub,-sparse.eye(len(rows),format="csr")),format="csr")
        aeq=sparse.hstack((aeq,sparse.csr_matrix((K,len(rows)))),format="csr")
    else:
        objective=costs
    result=linprog(objective,A_ub=aub,b_ub=cap,A_eq=aeq,b_eq=model.q,
                   bounds=(0,None),method="highs",
                   options={"presolve":True,"time_limit":float(time_limit),
                            "primal_feasibility_tolerance":1e-9,
                            "dual_feasibility_tolerance":1e-9})
    if not result.success:
        raise RuntimeError(f"RMP {phase} failed status={result.status}: {result.message}")
    eq=np.asarray(result.eqlin.marginals,dtype=np.float64)
    mu=np.asarray(result.ineqlin.marginals,dtype=np.float64)
    if eq.shape!=(K,) or mu.shape!=(len(rows),) or np.any(mu>1e-7):
        raise ValueError("RMP dual coverage/sign failure")
    art=float(np.sum(result.x[P:])) if phase=="I" else 0.0
    return MasterResult(phase,result,rows,costs,eq,mu,art,P,len(rows))
