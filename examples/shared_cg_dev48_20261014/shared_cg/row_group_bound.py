"""Low-memory exact maximum positive resource use over shared demand groups."""
import numpy as np
from scipy import sparse

try:
    from numba import njit
except ImportError:
    njit = None


def _python_bound(indptr, indices, data, group, mass):
    out = np.zeros(len(indptr) - 1, dtype=np.float64)
    for r in range(len(out)):
        maxima = {}
        for p in range(int(indptr[r]), int(indptr[r + 1])):
            value = float(data[p])
            if value > 0:
                key = int(group[int(indices[p])])
                if value > maxima.get(key, 0.0):
                    maxima[key] = value
        out[r] = sum(value * float(mass[key]) for key, value in maxima.items())
    return out


if njit is not None:
    @njit(cache=False)
    def _compiled_bound(indptr, indices, data, group, mass):
        out = np.zeros(len(indptr) - 1, dtype=np.float64)
        seen = np.full(len(mass), -1, dtype=np.int64)
        maximum = np.zeros(len(mass), dtype=np.float64)
        touched = np.empty(len(mass), dtype=np.int64)
        for r in range(len(out)):
            n = 0
            for p in range(indptr[r], indptr[r + 1]):
                value = data[p]
                if value <= 0:
                    continue
                key = group[indices[p]]
                if seen[key] != r:
                    seen[key] = r
                    maximum[key] = value
                    touched[n] = key
                    n += 1
                elif value > maximum[key]:
                    maximum[key] = value
            total = 0.0
            for t in range(n):
                key = touched[t]
                total += maximum[key] * mass[key]
            out[r] = total
        return out


def max_possible_row_load(matrix, column_group, group_mass):
    """Return sum_g mass[g] max(0,max_{j in g} A[r,j]) for every row.

    Each group may distribute at most mass[g] across all its columns. This
    bound is attainable for one row independently of other capacity rows and
    therefore safely proves a row redundant if it does not exceed its RHS.
    """
    A = sparse.csr_matrix(matrix, dtype=np.float64, copy=False)
    group = np.asarray(column_group, dtype=np.int64)
    mass = np.asarray(group_mass, dtype=np.float64)
    if (len(group) != A.shape[1] or np.any(group < 0)
            or np.any(group >= len(mass)) or np.any(mass <= 0)
            or not np.all(np.isfinite(mass)) or not np.all(np.isfinite(A.data))):
        raise ValueError('capacity/group dimensions, mass or coefficients')
    A.sum_duplicates()
    args = (A.indptr, A.indices, A.data, group, mass)
    return _compiled_bound(*args) if njit is not None else _python_bound(*args)
