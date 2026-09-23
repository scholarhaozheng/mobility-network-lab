"""Independent original-space audit of one solver-returned Boston L3 iterate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "inputs_snapshot"
FROZEN_HASHES = {
    "link.csv": "a5a7bbf9e18ceadacbe29335e572d2ccbfa919b46960845efc3d79d876007479",
    "demand.csv": "00d8c615a03b77f3a28be674cbbed4ef435efd301732dcfd1765f88a74399b49",
    "path_pool/path_pool.csv": "eb8d62e4d338e9bba1632f8013b8d9ee5b91eb4197ec67bdae823980ce806fad",
    "path_pool/A_link_path.npz": "bf07f042c38995a39a874624f5f9c4a1bad43ee43aae0dd07be28e0d93fb98cc",
    "path_pool/C_od_path.npz": "2d25c5b9d0b966bf6ffc470d1904ed179cbc3b8f237c9d6831df8c3e4fbaad81",
}
BASIS_U_SHA = {26: "b00aed73e98d05f2f869b1efd61dab8c3e15a4fd97008289448e528ccae80880",
               52: "2a933ccf9a670339064250b4b44c9211d53575870c0596a7d0dff368ed19959e"}
BASIS_INDEX_SHA = "6754109c4b39d4b361b3534986928aa39f5201ce46c16bb0eb0a49b294e7399b"


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write(path, records, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shortest(adj, origin, destination):
    queue = [(0.0, origin)]
    best = {origin: 0.0}
    while queue:
        cost, node = heapq.heappop(queue)
        if node == destination:
            return cost
        if cost > best[node] + 1e-12:
            continue
        for neighbor, weight in adj.get(node, ()):
            new_cost = cost + weight
            if new_cost < best.get(neighbor, math.inf) - 1e-12:
                best[neighbor] = new_cost
                heapq.heappush(queue, (new_cost, neighbor))
    raise ValueError(f"unreachable OD {origin}->{destination}")


def evaluate(rank, outer):
    out = ROOT / "runs" / f"rank{rank}"
    native = json.loads((out / f"outer_{outer:02d}_native.json").read_text(encoding="utf-8"))
    if not native.get("solution_loaded"):
        raise RuntimeError("no solver-returned iterate; source initialization cannot be checked as a result")
    with np.load(out / f"outer_{outer:02d}_solution.npz", allow_pickle=False) as sol:
        x1 = np.array(sol["x1"], dtype=float)
        theta = np.array(sol["theta"], dtype=float)
        v_solver = np.array(sol["v"], dtype=float)
        lam = np.array(sol["lambda_used"], dtype=float)
        rho = float(sol["rho"][0])
    with np.load(INPUT / "bases" / f"rank{rank}.npz", allow_pickle=False) as saved:
        U = np.array(saved["U_rank"], dtype=float)
        major = np.array(saved["major_idx"], dtype=int)
        minor = np.array(saved["minor_idx"], dtype=int)
    exact_frozen_hashes = all(sha(INPUT / name) == expected for name, expected in FROZEN_HASHES.items())
    exact_basis_payload = (hashlib.sha256(U.tobytes()).hexdigest() == BASIS_U_SHA[rank]
                           and hashlib.sha256(major.tobytes()+minor.tobytes()).hexdigest() == BASIS_INDEX_SHA)
    links = rows(INPUT / "link.csv")
    demands = rows(INPUT / "demand.csv")
    paths = rows(INPUT / "path_pool" / "path_pool.csv")
    f0_rows = rows(INPUT / "path_pool" / "f0.csv")
    link_map = rows(INPUT / "path_pool" / "link_index.csv")
    od_map = rows(INPUT / "path_pool" / "od_index.csv")
    if (len(links), len(demands), len(paths)) != (5091, 26, 130):
        raise ValueError("input dimension mismatch")
    if x1.shape != (26,) or theta.shape != (rank,) or v_solver.shape != (5091,) or lam.shape != (26,):
        raise ValueError("returned coordinate size mismatch")
    if U.shape != (104, rank) or not np.array_equal(np.sort(np.r_[major, minor]), np.arange(130)):
        raise ValueError("saved basis identity mismatch")
    link_ids = [r["link_id"] for r in links]
    path_ids = [r["path_id"] for r in paths]
    od_pairs = [(r["o_zone_id"], r["d_zone_id"]) for r in demands]
    identity_pass = (len(set(link_ids)) == 5091 and len(set(path_ids)) == 130 and len(set(od_pairs)) == 26
                     and [r["link_id"] for r in link_map] == link_ids
                     and [(r["o_node_id"],r["d_node_id"]) for r in od_map] == od_pairs
                     and [r["path_id"] for r in f0_rows] == path_ids
                     and [int(r["path_index"]) for r in paths] == list(range(130)))
    if not identity_pass:
        raise ValueError("original identity/order mismatch")
    f = np.empty(130, dtype=float)
    f[major] = x1
    f[minor] = U @ theta
    all_finite = bool(np.isfinite(f).all() and np.isfinite(v_solver).all() and np.isfinite(lam).all() and np.isfinite(rho))
    if not all_finite:
        raise ValueError("nonfinite raw returned vector")
    link_index = {lid: i for i, lid in enumerate(link_ids)}
    od_index = {pair: i for i, pair in enumerate(od_pairs)}
    link_ends = {r["link_id"]: (r["from_node_id"], r["to_node_id"]) for r in links}
    v_paths = np.zeros(5091)
    od_flow = np.zeros(26)
    sequences = []
    observed_A = sparse.lil_matrix((5091, 130), dtype=float)
    observed_C = sparse.lil_matrix((26, 130), dtype=float)
    path_rows = []
    for p, (row, volume) in enumerate(zip(paths, f)):
        pair = (row["o_node_id"], row["d_node_id"])
        if pair not in od_index or int(row["od_index"]) != od_index[pair]:
            raise ValueError("path OD mismatch")
        od_flow[od_index[pair]] += volume
        observed_C[od_index[pair], p] = 1
        seq = row["link_id_sequence"].split(";")
        sequences.append(seq)
        node = pair[0]
        visited = {node}
        for lid in seq:
            if lid not in link_index:
                raise ValueError("path contains missing link")
            u, next_node = link_ends[lid]
            if u != node or next_node in visited:
                raise ValueError("path continuity or loop failure")
            index = link_index[lid]
            observed_A[index, p] = 1
            v_paths[index] += volume
            node = next_node
            visited.add(node)
        if node != pair[1]:
            raise ValueError("path destination mismatch")
        path_rows.append({"path_index": p, "path_id": row["path_id"], "od_index": od_index[pair],
                          "o_node_id": pair[0], "d_node_id": pair[1],
                          "membership": "major" if p in set(major) else "minor", "raw_flow": float(volume),
                          "link_id_sequence": row["link_id_sequence"]})
    A = sparse.load_npz(INPUT / "path_pool" / "A_link_path.npz").tocsr()
    C = sparse.load_npz(INPUT / "path_pool" / "C_od_path.npz").tocsr()
    incidence_pass = (A.shape == (5091, 130) and C.shape == (26, 130)
                      and (observed_A.tocsr()-A).nnz == 0 and (observed_C.tocsr()-C).nnz == 0)
    if not incidence_pass:
        raise ValueError("saved matrices differ from ordered path sequences")
    matrix_link_error = float(np.max(np.abs(v_paths - A @ f)))
    matrix_od_error = float(np.max(np.abs(od_flow - C @ f)))
    q = np.array([float(r["volume"]) for r in demands])
    od_residual = od_flow - q
    link_residual = v_solver - v_paths
    od_limit = 1e-6 + 1e-8*np.maximum(1, np.abs(q))
    link_limit = 1e-6 + 1e-8*np.maximum(1, np.abs(v_paths))
    cap_raw = np.array([float(r["capacity"]) for r in links])
    cap = np.maximum(cap_raw, 1.0)
    t0 = np.array([float(r["vdf_fftt"]) for r in links])
    alpha = np.array([float(r["vdf_alpha"]) for r in links])
    beta = np.array([float(r["vdf_beta"]) for r in links])
    if np.min(cap_raw) < 1 or np.min(t0) <= 0 or np.min(alpha) < 0 or np.min(beta) <= 0:
        raise ValueError("unexpected BPR domain")
    def F(v):
        return float(np.sum(t0*v + t0*alpha/(beta+1)*v*(v/cap)**beta))
    F_solver, F_paths = F(v_solver), F(v_paths)
    linear = float(lam @ od_residual)
    quadratic = float(0.5*rho*(od_residual @ od_residual))
    decomposition = F_solver + linear + quadratic
    objective_limit = 1e-5 + 1e-7*max(1, abs(decomposition))
    pyomo_objective = native.get("model_objective")
    ipopt_objective = native.get("native_unscaled_objective")
    objective_pyomo_pass = pyomo_objective is not None and abs(decomposition-pyomo_objective) <= objective_limit
    objective_ipopt_pass = ipopt_objective is not None and abs(decomposition-ipopt_objective) <= objective_limit
    counts = native.get("model_counts", {})
    counts_pass = (counts.get("total_native_variables") == 5091+26+rank
                   and counts.get("link_equalities") == 5091
                   and counts.get("minor_nonnegative_inequalities") == 104
                   and counts.get("total_active_constraints") == 5195)
    source_pass = (native.get("source_sha256") == "0a054ab078d46a8b74fa257336a65275564c38cc3e60e5c4d8cb9c412a87a22a"
                   and sha(ROOT / "source_snapshot" / "run_diagnostic_levels.py") == native.get("source_sha256"))
    native_optimal = native.get("solver_status") == "ok" and native.get("termination") == "optimal" and native.get("solution_loaded") is True
    criteria = {
        "native_optimal_returned": bool(native_optimal),
        "all_values_finite": all_finite,
        "raw_path_nonnegative_tolerance": bool(np.min(f) >= -1e-8),
        "major_bound": bool(np.min(x1) >= -1e-8),
        "explicit_link_bound": bool(np.min(v_solver) >= -1e-8),
        "all_OD_residuals": bool(np.all(np.abs(od_residual) <= od_limit)),
        "all_link_equalities": bool(np.all(np.abs(link_residual) <= link_limit)),
        "path_sequence_and_matrix_agreement": bool(incidence_pass and matrix_link_error <= 1e-8 and matrix_od_error <= 1e-8),
        "all_IDs_and_order": bool(identity_pass),
        "exact_frozen_input_hashes": bool(exact_frozen_hashes),
        "exact_saved_basis_payload": bool(exact_basis_payload),
        "active_L3_constraint_counts": bool(counts_pass),
        "exact_source_hash": bool(source_pass),
        "gamma_zero": native.get("gamma") == 0.0,
        "native_objective_decomposition": bool(objective_ipopt_pass),
        "pyomo_objective_decomposition": bool(objective_pyomo_pass),
    }
    numerical = bool(all(criteria.values()))
    tt = t0*(1+alpha*(v_paths/cap)**beta)
    T = float(v_paths @ tt)
    cheapest = np.full(26, np.inf)
    for row, seq in zip(paths, sequences):
        k = od_index[(row["o_node_id"],row["d_node_id"])]
        cheapest[k] = min(cheapest[k], sum(tt[link_index[lid]] for lid in seq))
    pool_lower = float(q @ cheapest)
    adjacency = defaultdict(list)
    for row, travel_time in zip(links, tt):
        adjacency[row["from_node_id"]].append((row["to_node_id"], float(travel_time)))
    full_shortest_by_od = np.array([shortest(adjacency,row["o_zone_id"],row["d_zone_id"])
                                    for row in demands], dtype=float)
    full_lower = float(q @ full_shortest_by_od)
    pool_gap = T - pool_lower
    full_gap = T - full_lower
    pool_rg = pool_gap/T
    full_rg = full_gap/T
    full_reference = {r["link_id"]: float(r["volume"]) for r in rows(ROOT / "reference" / "link_flow.csv")}
    fw_reference = {r["link_id"]: float(r["volume"]) for r in rows(ROOT / "reference" / "fw_solution.csv")}
    reference_v = np.array([full_reference[lid] for lid in link_ids])
    fw_v = np.array([fw_reference[lid] for lid in link_ids])
    F_ref = F(reference_v)
    F_rel = abs(F_paths-F_ref)/max(1,abs(F_ref))
    approximation = bool(numerical and abs(full_rg) <= 1e-5 and F_rel <= 1e-6)
    if numerical and approximation:
        status = "PUBLIC_ELIGIBLE_NUMERICAL_UE_APPROXIMATION"
    elif numerical:
        status = "FEASIBLE_REDUCED_APPROXIMATION_NOT_PUBLIC_ELIGIBLE"
    else:
        status = "NUMERICAL_FEASIBILITY_FAILED_NOT_PUBLIC_ELIGIBLE"
    node_balance = defaultdict(float)
    expected_node = defaultdict(float)
    for row, flow in zip(links, v_paths):
        node_balance[row["from_node_id"]] += flow
        node_balance[row["to_node_id"]] -= flow
    for row in demands:
        expected_node[row["o_zone_id"]] += float(row["volume"])
        expected_node[row["d_zone_id"]] -= float(row["volume"])
    max_node_balance = max(abs(node_balance[node]-expected_node[node]) for node in set(node_balance)|set(expected_node))
    negative_count = int(np.sum(f < 0))
    negative_mass = max(0.0, float(-np.minimum(f,0).sum()))
    od_rows = [{"od_index": i, "o_node_id": row["o_zone_id"], "d_node_id": row["d_zone_id"],
                "demand": float(q[i]), "reconstructed_flow": float(od_flow[i]),
                "raw_residual": float(od_residual[i]), "tolerance": float(od_limit[i]),
                "passes": bool(abs(od_residual[i]) <= od_limit[i])}
               for i, row in enumerate(demands)]
    link_rows = [{"link_index": i, "link_id": row["link_id"], "from_node_id": row["from_node_id"],
                  "to_node_id": row["to_node_id"], "v_solver": float(v_solver[i]),
                  "v_from_paths": float(v_paths[i]), "raw_residual": float(link_residual[i]),
                  "tolerance": float(link_limit[i]), "current_cost_minutes": float(tt[i]),
                  "effective_capacity": float(cap[i]), "vdf_fftt": float(t0[i]),
                  "vdf_alpha": float(alpha[i]), "vdf_beta": float(beta[i])}
                 for i, row in enumerate(links)]
    result = dict(rank=rank, outer=outer, status=status, numerical_feasibility_pass=numerical,
                  public_eligibility_pass=approximation, criteria=criteria,
                  native_status=native.get("solver_status"), native_termination=native.get("termination"),
                  model_counts=counts,
                  raw_stats=dict(min_path_flow=float(np.min(f)), negative_path_count=negative_count,
                                 negative_path_mass=negative_mass, min_minor_flow=float(np.min(f[minor])),
                                 min_solver_link_flow=float(np.min(v_solver)),
                                 max_abs_OD_residual=float(np.max(np.abs(od_residual))),
                                 failed_OD_count=int(np.sum(np.abs(od_residual)>od_limit)),
                                 max_abs_link_residual=float(np.max(np.abs(link_residual))),
                                 failed_link_count=int(np.sum(np.abs(link_residual)>link_limit)),
                                 max_abs_node_balance=float(max_node_balance),
                                 matrix_link_error=matrix_link_error, matrix_OD_error=matrix_od_error),
                  objective=dict(F_solver_v=F_solver, F_reconstructed_paths=F_paths,
                                 lambda_dot_OD_residual=linear, rho_half_residual_square=quadratic,
                                 gamma_regularization=0.0, decomposed_native_objective=decomposition,
                                 model_objective=pyomo_objective, ipopt_unscaled_objective=ipopt_objective,
                                 objective_tolerance=objective_limit, reference_F=F_ref,
                                 relative_F_error_from_reference=F_rel,
                                 F_paths_minus_reference=F_paths-F_ref),
                  gaps=dict(TSTT=T, restricted_pool_shortest_total=pool_lower,
                            full_network_shortest_total=full_lower,
                            restricted_pool_signed_gap=pool_gap,
                            full_network_signed_gap=full_gap,
                            restricted_pool_relative_gap=pool_rg,
                            full_network_relative_gap=full_rg,
                            OD_residual_weighted_full_shortest_cost=float(od_residual @ full_shortest_by_od),
                            diagnostic_gap_using_reconstructed_OD_totals=float(T-od_flow @ full_shortest_by_od),
                            denominator="candidate current-cost TSTT",
                            is_exact_UE_certificate=False,
                            is_checked_numerical_UE_approximation=bool(approximation),
                            signed_gap_note="A negative signed gap here reflects small accepted OD conservation residuals; it is not floating-point roundoff or an exact-feasibility certificate.",
                            full_network_parallel_link_handling="each directed link is a separate Dijkstra edge"),
                  link_difference=dict(Linf_from_full=float(np.max(np.abs(v_paths-reference_v))),
                                       L1_from_full=float(np.sum(np.abs(v_paths-reference_v))),
                                       Linf_from_FW=float(np.max(np.abs(v_paths-fw_v))),
                                       L1_from_FW=float(np.sum(np.abs(v_paths-fw_v)))),
                  acceptance_targets=dict(OD="1e-6+1e-8*max(1,abs(q)) each",
                                          link="1e-6+1e-8*max(1,abs(v_from_paths)) each",
                                          minimum_path_flow=-1e-8,
                                          full_network_relative_gap_absolute_max=1e-5,
                                          reference_relative_F_error_max=1e-6),
                  source_and_basis=dict(source_sha256=sha(ROOT / "source_snapshot" / "run_diagnostic_levels.py"),
                                        basis_sha256=sha(INPUT / "bases" / f"rank{rank}.npz")))
    label = f"outer_{outer:02d}"
    write(out / f"{label}_original_path_flows.csv", path_rows,
          ["path_index", "path_id", "od_index", "o_node_id", "d_node_id", "membership", "raw_flow", "link_id_sequence"])
    write(out / f"{label}_od_balance.csv", od_rows,
          ["od_index", "o_node_id", "d_node_id", "demand", "reconstructed_flow", "raw_residual", "tolerance", "passes"])
    write(out / f"{label}_link_flows.csv", link_rows,
          ["link_index", "link_id", "from_node_id", "to_node_id", "v_solver", "v_from_paths", "raw_residual", "tolerance", "current_cost_minutes", "effective_capacity", "vdf_fftt", "vdf_alpha", "vdf_beta"])
    np.save(out / f"{label}_od_residual.npy", od_residual)
    dump(out / f"{label}_check.json", result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, choices=(26,52), required=True)
    ap.add_argument("--outer", type=int, required=True)
    args = ap.parse_args()
    result = evaluate(args.rank, args.outer)
    print(json.dumps({"rank": args.rank, "outer": args.outer, "status": result["status"],
                      "max_abs_OD_residual": result["raw_stats"]["max_abs_OD_residual"],
                      "full_network_relative_gap": result["gaps"]["full_network_relative_gap"]}, indent=2))
