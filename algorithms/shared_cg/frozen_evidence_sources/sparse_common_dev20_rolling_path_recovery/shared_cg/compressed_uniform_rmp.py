"""Exact Phase-I RMP with implicit uniform-release base columns and active events.

Every OD-release event starts on a source-derived base path. Only events
with new path columns become LP variables; all other original events are
algebraically fixed. Baseline load is represented by exact intervals.
Rows untouched by active events remain fixed and contribute their exact
constant artificial excess. Every touched original resource row enters
the LP explicitly. This is a component, not a full CG loop.
"""
from collections import Counter
from dataclasses import dataclass
import numpy as np
from scipy import sparse
from scipy.optimize import linprog


@dataclass
class PhaseIResult:
    status: str
    baseline_artificial_mass: float
    optimized_artificial_mass: float
    base_flow: float
    alternative_flow: float
    touched_original_capacity_rows: int
    constant_untouched_excess: float
    local_RMP_objective: float
    highS_status: int
    highS_iterations: int


def solve_one_active_phase_i(base,physical_capacity_per_step,H,q,
                             base_resources,alternative_resources,
                             base_cost,alternative_cost,epsilon=1e-9):
    cap=np.asarray(physical_capacity_per_step,dtype=np.float64)
    H=int(H);q=float(q)
    if q<=0 or H<=0 or epsilon<=0 or np.any(cap<=0):
        raise ValueError('invalid original Phase I model')
    base_c=Counter(map(int,base_resources))
    alt_c=Counter(map(int,alternative_resources))
    if any(r<0 or r>=len(cap)*H for r in set(base_c)|set(alt_c)):
        raise ValueError('original physical capacity row out of range')
    intervals=np.asarray(base.edge_index,dtype=np.int64)
    interval_capacity=cap[intervals]
    baseline_artificial=float(np.sum(np.maximum(base.load_pce-interval_capacity,0.0)*
                                     (base.stop_step-base.start_step)))
    rows=np.array(sorted(set(base_c)|set(alt_c)),dtype=np.int64)
    loads=np.array([base.load_at(r//H,r%H) for r in rows],dtype=np.float64)
    row_cap=cap[rows//H]
    old_local=float(np.sum(np.maximum(loads-row_cap,0.0)))
    constant=baseline_artificial-old_local
    if constant < -1e-6:
        raise ValueError('baseline excess accounting error')
    constant=max(constant,0.0)
    fixed=loads-q*np.array([base_c[int(r)] for r in rows],dtype=np.float64)
    bcoef=np.array([base_c[int(r)] for r in rows],dtype=np.float64)
    acoef=np.array([alt_c[int(r)] for r in rows],dtype=np.float64)
    n=len(rows)
    matrix=sparse.hstack((sparse.csr_matrix(np.c_[bcoef,acoef]),
                          -sparse.eye(n,format='csr')),format='csr')
    equality=sparse.csr_matrix(([1.,1.],([0,0],[0,1])),shape=(1,n+2))
    objective=np.r_[epsilon*np.array([base_cost,alternative_cost],dtype=np.float64),
                    np.ones(n,dtype=np.float64)]
    raw=linprog(objective,A_ub=matrix,b_ub=row_cap-fixed,
                A_eq=equality,b_eq=np.array([q]),bounds=(0,None),
                method='highs',options={'presolve':True,
                                        'primal_feasibility_tolerance':1e-9,
                                        'dual_feasibility_tolerance':1e-9})
    if not raw.success:
        raise RuntimeError(f'Phase I RMP status={raw.status}: {raw.message}')
    x=np.asarray(raw.x)
    excess=constant+float(np.sum(x[2:]))
    baseline_local=baseline_artificial+epsilon*q*float(base_cost)
    improved=excess+epsilon*(x[0]*base_cost+x[1]*alternative_cost)
    if improved>baseline_local+1e-6:
        raise ValueError('restricted master worsened incumbent Phase I objective')
    return PhaseIResult('PHASE_I_SOLVED_OPEN_GLOBAL_FEASIBILITY',
                        baseline_artificial,excess,float(x[0]),float(x[1]),
                        n,constant,improved,int(raw.status),int(raw.nit))
