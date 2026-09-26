"""Independent restricted-path LP. Its result is an upper bound only."""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def recover(problem, pool):
    paths = [(k, path) for k, group in enumerate(pool.paths) for path in group]
    if any(not group for group in pool.paths):
        return {"feasible": False, "message": "empty commodity pool", "path_count": len(paths)}
    row, col, value = [], [], []
    for j, (_, path) in enumerate(paths):
        for a in path:
            row.append(a)
            col.append(j)
            value.append(1.0)
    aub = coo_matrix((value, (row, col)), shape=(len(problem["ids"]), len(paths))).tocsr()
    aeq = coo_matrix((np.ones(len(paths)), ([k for k, _ in paths], range(len(paths)))),
                     shape=(len(pool.paths), len(paths))).tocsr()
    costs = np.asarray([sum(problem["cost"][list(path)]) for _, path in paths])
    result = linprog(costs, A_ub=aub, b_ub=problem["cap"], A_eq=aeq,
                     b_eq=[c["volume"] for c in problem["commodities"]],
                     bounds=(0, None), method="highs")
    if not result.success:
        return {"feasible": False, "message": result.message, "path_count": len(paths)}
    positive = [(k, path, float(flow)) for (k, path), flow in zip(paths, result.x) if flow > 1e-9]
    return {"feasible": True, "objective": float(result.fun), "path_count": len(paths),
            "positive_paths": positive, "message": result.message}
