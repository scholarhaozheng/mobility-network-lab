"""Exact sparse RMP extension for any number of retained singleton paths."""
from collections import Counter
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from .two_singleton_phase_ii_rmp import Extension


def extend_one_column_multi(old_matrix, old_rows, old_rhs, old_cost, old_upper,
                            selected_paths, delays, prior_base_rows,
                            prior_new_rows, physical_pos, physical_edge,
                            baseline, capacity, H, T, base_event_rows,
                            new_event_rows, new_event_q, new_cost_increment,
                            time_limit):
    old_rows = np.asarray(old_rows, dtype=np.int64)
    old_rhs = np.asarray(old_rhs, dtype=float)
    old_cost = np.asarray(old_cost, dtype=float)
    old_upper = np.asarray(old_upper, dtype=float)
    old_matrix = old_matrix.tocsr()
    n_family = len(selected_paths) * T
    if len(prior_base_rows) != len(prior_new_rows):
        raise ValueError('prior singleton dimensions')
    if old_matrix.shape != (len(old_rows), len(old_cost)) or len(old_cost) != n_family + len(prior_base_rows):
        raise ValueError('existing RMP dimensions')
    if len(old_rows) != len(old_rhs) or len(old_cost) != len(old_upper):
        raise ValueError('existing row or bound dimensions')
    if len(set(map(int, old_rows))) != len(old_rows) or len(delays) != len(selected_paths):
        raise ValueError('retained row or selected path dimensions')
    if not (0 < new_event_q < np.inf) or not (0 < time_limit < np.inf):
        raise ValueError('invalid demand or time limit')
    before, after = Counter(map(int, base_event_rows)), Counter(map(int, new_event_rows))
    touched = np.array(sorted(set(before) | set(after)), dtype=np.int64)
    extra = np.setdiff1d(touched, old_rows)
    extra_rhs = np.empty(len(extra), dtype=float)
    extra_by_edge = {}
    location = {int(row): j for j, row in enumerate(extra)}
    for row, j in location.items():
        p, t = divmod(row, H)
        if p < 0 or p >= len(physical_edge):
            raise ValueError('capacity row outside graph')
        edge = int(physical_edge[p])
        extra_rhs[j] = float(capacity[edge]) - baseline.load_at(edge, t)
        extra_by_edge.setdefault(p, []).append((t, j))
    rr, cc, vv = [], [], []
    for g, path in enumerate(selected_paths):
        delay = int(delays[g])
        for edge, offset in path:
            p = int(physical_pos[int(edge)])
            if p < 0:
                raise ValueError('nonphysical selected path')
            for t, j in extra_by_edge.get(p, ()):
                release = t - int(offset)
                if 0 <= release < T:
                    rr.append(j); cc.append(g*T+release); vv.append(-1.0)
                release -= delay
                if 0 <= release < T:
                    rr.append(j); cc.append(g*T+release); vv.append(1.0)
    for k, (base_path, new_path) in enumerate(zip(prior_base_rows, prior_new_rows)):
        base_count, new_count = Counter(map(int, base_path)), Counter(map(int, new_path))
        for row, j in location.items():
            coefficient = new_count.get(row, 0) - base_count.get(row, 0)
            if coefficient:
                rr.append(j); cc.append(n_family+k); vv.append(float(coefficient))
    extra_matrix = sparse.coo_matrix((vv, (rr, cc)), shape=(len(extra), len(old_cost))).tocsr()
    extra_matrix.sum_duplicates()
    old_column = np.array([after.get(int(r), 0)-before.get(int(r), 0) for r in old_rows], dtype=float)
    extra_column = np.array([after.get(int(r), 0)-before.get(int(r), 0) for r in extra], dtype=float)
    A = sparse.vstack((
        sparse.hstack((old_matrix, sparse.csr_matrix(old_column[:, None])), format='csr'),
        sparse.hstack((extra_matrix, sparse.csr_matrix(extra_column[:, None])), format='csr')
    ), format='csr')
    rhs = np.r_[old_rhs, extra_rhs]
    costs = np.r_[old_cost, float(new_cost_increment)]
    upper = np.r_[old_upper, float(new_event_q)]
    if np.any(upper <= 0) or not np.all(np.isfinite(rhs)):
        raise ValueError('invalid source bounds or residual capacity')
    solve = linprog(costs, A_ub=A, b_ub=rhs,
                    bounds=np.c_[np.zeros(len(upper)), upper], method='highs',
                    options={'presolve': True, 'time_limit': float(time_limit),
                             'primal_feasibility_tolerance': 1e-9,
                             'dual_feasibility_tolerance': 1e-9})
    if not solve.success:
        raise RuntimeError(f'multi-column restricted LP status={solve.status}: {solve.message}')
    flow = np.asarray(solve.x, dtype=float)
    excess = float(np.max(A@flow-rhs)) if len(rhs) else float('-inf')
    if excess > 1e-6 or np.any(flow < -1e-8) or np.any(flow > upper+1e-8):
        raise ValueError('new restricted primal infeasible')
    mu = np.asarray(solve.ineqlin.marginals, dtype=float)
    lower = np.asarray(solve.lower.marginals, dtype=float)
    upper_dual = np.asarray(solve.upper.marginals, dtype=float)
    dual = float(np.dot(rhs, mu)+np.dot(upper, upper_dual))
    return Extension(A, np.r_[old_rows, extra], rhs, costs, upper, flow,
                     mu, lower, upper_dual, float(solve.fun), dual,
                     int(solve.nit), len(extra), excess)
