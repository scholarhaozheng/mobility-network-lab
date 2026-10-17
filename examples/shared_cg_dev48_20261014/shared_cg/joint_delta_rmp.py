"""Joint sparse path master over a full valid algebraic base assignment.

Each candidate moves mass from one base path to one legal path. Candidates
for the same commodity share its demand. Restricted master only.
"""
from dataclasses import dataclass
from collections import Counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from .row_group_bound import max_possible_row_load


@dataclass
class JointResult:
    y: np.ndarray
    objective_delta: float
    phase_i_artificial: float
    capacity_mu: np.ndarray
    group_mu: np.ndarray
    reduced_cost: np.ndarray
    retained_capacity_rows: int
    redundant_capacity_rows: int
    iterations: int
    max_capacity_excess: float
    max_group_excess: float


def solve_joint_delta(matrix, resource_rows, residual_capacity, delta_cost,
                      column_group, group_mass, *, phase="II", epsilon=1e-9,
                      time_limit=1800.0, numerical_margin=1e-10):
    """Optimize all candidate columns together under original shared capacities.

    matrix[r,j] = a(new path)-a(base path), with repeated uses counted.
    residual_capacity[r] = original capacity[r]-full base load[r].
    Caller includes all candidate-touched and base-overloaded original rows.
    """
    A=sparse.csr_matrix(matrix,dtype=np.float64)
    A.sum_duplicates()
    rows=np.asarray(resource_rows,dtype=np.int64)
    rhs=np.asarray(residual_capacity,dtype=np.float64)
    c=np.asarray(delta_cost,dtype=np.float64)
    group=np.asarray(column_group,dtype=np.int64)
    mass=np.asarray(group_mass,dtype=np.float64)
    if phase not in ("I","II") or A.shape!=(len(rows),len(c)) or len(rhs)!=len(rows) or len(group)!=len(c):
        raise ValueError("joint RMP dimensions or phase")
    if len(rows)!=len(np.unique(rows)) or np.any(rows<0) or np.any(group<0) or np.any(group>=len(mass)):
        raise ValueError("duplicate/out-of-range resource or group")
    if np.any(mass<=0) or not np.all(np.isfinite(mass)) or not np.all(np.isfinite(rhs)) or not np.all(np.isfinite(c)):
        raise ValueError("nonfinite demand, capacity or cost")
    if not 0<time_limit<np.inf or epsilon<0 or numerical_margin<0:
        raise ValueError("numerical policy")
    # Each group can choose at most one path mixture up to its total mass.
    # Recompute this exact current-pool row upper bound after adding columns.
    bound=max_possible_row_load(A,group,mass)
    keep=bound>rhs-numerical_margin
    B=A[keep];b=rhs[keep]
    G=sparse.coo_matrix((np.ones(len(c)),(group,np.arange(len(c)))),shape=(len(mass),len(c))).tocsr()
    if phase=="I":
        n=len(b)
        Aub=sparse.vstack((sparse.hstack((B,-sparse.eye(n,format="csr")),format="csr"),
                           sparse.hstack((G,sparse.csr_matrix((len(mass),n))),format="csr")),format="csr")
        objective=np.r_[epsilon*c,np.ones(n)]
    else:
        Aub=sparse.vstack((B,G),format="csr")
        objective=c
    sol=linprog(objective,A_ub=Aub,b_ub=np.r_[b,mass],bounds=(0,None),method="highs",
                options={"presolve":True,"time_limit":time_limit,
                         "primal_feasibility_tolerance":1e-9,"dual_feasibility_tolerance":1e-9})
    if not sol.success:raise RuntimeError(f"joint RMP {phase} status={sol.status}: {sol.message}")
    y=np.asarray(sol.x[:len(c)],dtype=np.float64)
    artificial=float(np.sum(sol.x[len(c):])) if phase=="I" else 0.0
    capacity_mu=np.zeros(len(rows),dtype=np.float64)
    capacity_mu[keep]=np.asarray(sol.ineqlin.marginals[:len(b)],dtype=np.float64)
    group_mu=np.asarray(sol.ineqlin.marginals[len(b):],dtype=np.float64)
    if np.max(capacity_mu,initial=0)>1e-7 or np.max(group_mu,initial=0)>1e-7:
        raise ValueError("joint master inequality dual sign")
    rc=(epsilon if phase=="I" else 1.0)*c-A.T@capacity_mu-group_mu[group]
    cap_excess=float(np.max(A@y-rhs,initial=0))
    group_excess=float(np.max(G@y-mass,initial=0))
    if group_excess>1e-7 or (phase=="II" and cap_excess>1e-7) or np.min(y,initial=0)<-1e-8:
        raise ValueError("joint master primal infeasible")
    return JointResult(y,float(c@y),artificial,capacity_mu,group_mu,
                       np.asarray(rc).reshape(-1),int(np.count_nonzero(keep)),
                       int(len(rows)-np.count_nonzero(keep)),int(sol.nit),cap_excess,group_excess)


def original_path_reduced_cost(raw_path_cost,base_cost,raw_path_rows,
                               base_rows,price_by_resource,group_mu):
    """Evaluate c_new + lambda*a_new - sigma.

    sigma=c_base+lambda*a_base+group_mu in this base-path elimination.
    """
    new=Counter(map(int,raw_path_rows));base=Counter(map(int,base_rows))
    diff=sum(float(price_by_resource.get(r,0.0))*(new[r]-base[r]) for r in new.keys()|base.keys())
    return float(raw_path_cost-base_cost+diff-group_mu)


