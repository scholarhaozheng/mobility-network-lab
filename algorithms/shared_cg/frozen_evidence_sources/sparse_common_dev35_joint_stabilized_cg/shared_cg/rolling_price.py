"""Exact rolling full-time price values for arbitrary sparse nonnegative physical entry tolls.

Experimental shared-core candidate. This is a price-value oracle, not yet a
column-generating solver: it deliberately does not claim path recovery or CG
closure. It preserves all physical/connector arcs, waits, zero-time DAG
semantics, and the original capacity resource indexing.
"""
from dataclasses import dataclass
import numpy as np
from numba import njit


@njit(cache=True)
def _backward_ring(n, H, dt, destination, offset, head, cost, duration,
                   reverse_zero_topo, toll_ptr, toll_time_desc, toll_value,
                   query_time_desc, query_origin):
    D = int(np.max(duration))
    ring = np.full((D + 1, n), np.inf, dtype=np.float64)
    cursor = toll_ptr[:-1].copy()
    answer = np.empty(len(query_time_desc), dtype=np.float64)
    q = 0
    slots = D + 1
    for t in range(H, -1, -1):
        slot = t % slots
        for j in range(n):
            node = reverse_zero_topo[j]
            best = 0.0 if node == destination else np.inf
            if t < H:
                w = dt / 60.0 + ring[(t + 1) % slots, node]
                if w < best:
                    best = w
            for e in range(offset[node], offset[node + 1]):
                d = duration[e]
                if t + d > H:
                    continue
                target = ring[slot, head[e]] if d == 0 else ring[(t + d) % slots, head[e]]
                toll = 0.0
                p = cursor[e]
                stop = toll_ptr[e + 1]
                while p < stop and toll_time_desc[p] > t:
                    p += 1
                cursor[e] = p
                if p < stop and toll_time_desc[p] == t:
                    toll = toll_value[p]
                candidate = cost[e] + toll + target
                if candidate < best:
                    best = candidate
            ring[slot, node] = best
        while q < len(query_time_desc) and query_time_desc[q] == t:
            answer[q] = ring[slot, query_origin[q]]
            q += 1
    if q != len(query_time_desc):
        raise ValueError("query outside original time domain")
    return answer


@dataclass(frozen=True)
class RollingModel:
    n: int
    H: int
    dt: float
    physical_edges: np.ndarray
    u: np.ndarray
    v: np.ndarray
    cost: np.ndarray
    duration: np.ndarray
    reverse_zero_topo: np.ndarray

    def __post_init__(self):
        m = len(self.u)
        if not (len(self.v) == len(self.cost) == len(self.duration) == m):
            raise ValueError("edge array length mismatch")
        if np.any(self.duration < 0):
            raise ValueError("negative arc duration")
        if self.H < 0 or self.dt <= 0:
            raise ValueError("invalid time domain")
        if len(self.reverse_zero_topo) != self.n or set(map(int, self.reverse_zero_topo)) != set(range(self.n)):
            raise ValueError("invalid zero-layer order")
        position = np.empty(self.n, dtype=np.int32)
        position[self.reverse_zero_topo] = np.arange(self.n, dtype=np.int32)
        for e in range(m):
            if self.duration[e] == 0 and position[self.v[e]] >= position[self.u[e]]:
                raise ValueError("zero-duration arc violates reverse topological order")
        if np.any(self.cost < 0) or not np.all(np.isfinite(self.cost)):
            raise ValueError("invalid base cost")
        if np.any(self.physical_edges < 0) or np.any(self.physical_edges >= m):
            raise ValueError("invalid physical edge index")

    @classmethod
    def from_implicit(cls, model):
        return cls(model.n, model.H, model.dt, model.physical_edges,
                   model.u, model.v, model.cost, model.duration,
                   model.reverse_topo)

    def _arrays(self, capacity_rows, capacity_lambda):
        rows = np.asarray(capacity_rows, dtype=np.int64)
        lam = np.asarray(capacity_lambda, dtype=np.float64)
        if rows.ndim != 1 or lam.ndim != 1 or len(rows) != len(lam):
            raise ValueError("capacity toll shape")
        if len(rows) and (np.any(rows < 0) or np.any(rows >= len(self.physical_edges) * self.H) or len(np.unique(rows)) != len(rows)):
            raise ValueError("capacity row out of range or duplicate")
        if np.any(lam < 0) or not np.all(np.isfinite(lam)):
            raise ValueError("capacity lambda must be finite and nonnegative")
        edge_order = np.argsort(self.u, kind="stable")
        inverse = np.empty(len(edge_order), dtype=np.int32)
        inverse[edge_order] = np.arange(len(edge_order), dtype=np.int32)
        sorted_u = self.u[edge_order]
        offset = np.empty(self.n + 1, dtype=np.int32)
        offset[0] = 0
        offset[1:] = np.cumsum(np.bincount(sorted_u, minlength=self.n), dtype=np.int32)
        toll_edge = inverse[self.physical_edges[rows // self.H]] if len(rows) else np.empty(0, np.int32)
        toll_time = (rows % self.H).astype(np.int32)
        order = np.lexsort((-toll_time, toll_edge))
        toll_edge = toll_edge[order]
        toll_time = toll_time[order]
        toll_value = lam[order]
        ptr = np.empty(len(edge_order) + 1, dtype=np.int32)
        ptr[0] = 0
        ptr[1:] = np.cumsum(np.bincount(toll_edge, minlength=len(edge_order)), dtype=np.int32)
        return (offset, self.v[edge_order].astype(np.int32),
                self.cost[edge_order].astype(np.float64),
                self.duration[edge_order].astype(np.int32),
                ptr, toll_time, toll_value)

    def price(self, destination, query_time, query_origin, capacity_rows=(), capacity_lambda=()):
        destination = int(destination)
        times = np.asarray(query_time, dtype=np.int32)
        origins = np.asarray(query_origin, dtype=np.int32)
        if destination < 0 or destination >= self.n or len(times) != len(origins) or times.ndim != 1 or origins.ndim != 1:
            raise ValueError("invalid destination or query shape")
        if np.any(times < 0) or np.any(times > self.H) or np.any(origins < 0) or np.any(origins >= self.n):
            raise ValueError("query outside original graph")
        arrays = self._arrays(capacity_rows, capacity_lambda)
        order = np.argsort(-times, kind="stable")
        descending = _backward_ring(self.n, self.H, self.dt, destination,
                                    arrays[0], arrays[1], arrays[2], arrays[3],
                                    self.reverse_zero_topo.astype(np.int32),
                                    arrays[4], arrays[5], arrays[6],
                                    times[order], origins[order])
        result = np.empty(len(times), dtype=np.float64)
        result[order] = descending
        return result
