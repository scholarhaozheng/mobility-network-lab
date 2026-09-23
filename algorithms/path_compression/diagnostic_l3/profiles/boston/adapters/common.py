"""Frozen Boston representation for the native Diagnostic L3 transfer."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyomo.environ as pyo
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "inputs_snapshot"
SOURCE = ROOT / "source_snapshot" / "run_diagnostic_levels.py"
PYTHON = Path(os.environ.get("MCL_NATIVE_PYTHON", sys.executable))
IPOPT = Path(os.environ.get("MCL_IPOPT", ""))
IPOPT_OPTIONS = dict(tol=1e-8, constr_viol_tol=1e-9, dual_inf_tol=1e-6,
                     compl_inf_tol=1e-8, acceptable_iter=0, bound_relax_factor=0,
                     honor_original_bounds="no", max_iter=500,
                     mu_strategy="adaptive", linear_solver="mumps", print_level=5)
SOURCE_HASH = "27644472699b1c93f9795b6a7940928c4935e43a2a062c96a6f7a682df8208b5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=str), encoding="utf-8")


def csv_rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_case(rank):
    """Read saved Boston matrices and U; never recompute paths or SVD."""
    rank = int(rank)
    if rank not in (26, 52):
        raise ValueError("only predeclared saved ranks 26 and 52 are allowed")
    links = csv_rows(INPUT / "link.csv")
    demands = csv_rows(INPUT / "demand.csv")
    paths = csv_rows(INPUT / "path_pool" / "path_pool.csv")
    link_map = csv_rows(INPUT / "path_pool" / "link_index.csv")
    od_map = csv_rows(INPUT / "path_pool" / "od_index.csv")
    f0_rows = csv_rows(INPUT / "path_pool" / "f0.csv")
    if (len(links), len(demands), len(paths)) != (5091, 26, 130):
        raise ValueError("frozen Boston dimension mismatch")
    link_ids = [r["link_id"] for r in links]
    path_ids = [r["path_id"] for r in paths]
    od = [(r["o_zone_id"], r["d_zone_id"]) for r in demands]
    if len(set(link_ids)) != 5091 or len(set(path_ids)) != 130 or len(set(od)) != 26:
        raise ValueError("duplicate original identity")
    if [r["link_id"] for r in link_map] != link_ids or [int(r["link_index"]) for r in link_map] != list(range(5091)):
        raise ValueError("link index map differs from frozen CSV order")
    if [(r["o_node_id"], r["d_node_id"]) for r in od_map] != od or [int(r["od_index"]) for r in od_map] != list(range(26)):
        raise ValueError("OD index map differs from frozen CSV order")
    if [int(r["path_index"]) for r in paths] != list(range(130)):
        raise ValueError("path order mismatch")
    if [r["path_id"] for r in f0_rows] != path_ids or [int(r["path_index"]) for r in f0_rows] != list(range(130)):
        raise ValueError("f0 path order mismatch")
    A_link_path = sparse.load_npz(INPUT / "path_pool" / "A_link_path.npz").tocsr()
    C_od_path = sparse.load_npz(INPUT / "path_pool" / "C_od_path.npz").tocsr()
    if A_link_path.shape != (5091, 130) or C_od_path.shape != (26, 130):
        raise ValueError("frozen matrix shape mismatch")
    expected_A = sparse.lil_matrix((5091, 130), dtype=float)
    expected_C = sparse.lil_matrix((26, 130), dtype=float)
    link_index = {lid: i for i, lid in enumerate(link_ids)}
    od_index = {pair: i for i, pair in enumerate(od)}
    link_end = {r["link_id"]: (r["from_node_id"], r["to_node_id"]) for r in links}
    for p, row in enumerate(paths):
        pair = (row["o_node_id"], row["d_node_id"])
        if pair not in od_index or int(row["od_index"]) != od_index[pair]:
            raise ValueError("path OD identity mismatch")
        expected_C[od_index[pair], p] = 1
        node = pair[0]
        visited = {node}
        for lid in row["link_id_sequence"].split(";"):
            if lid not in link_index:
                raise ValueError("path link absent from frozen network")
            u, v = link_end[lid]
            if u != node or v in visited:
                raise ValueError("path is discontinuous or non-loopless")
            expected_A[link_index[lid], p] = 1
            node = v
            visited.add(v)
        if node != pair[1]:
            raise ValueError("path destination mismatch")
    if (expected_A.tocsr() - A_link_path).nnz or (expected_C.tocsr() - C_od_path).nnz:
        raise ValueError("saved incidence differs from ordered path sequences")
    q = np.array([float(r["volume"]) for r in demands], dtype=float)
    if np.max(np.abs(q - np.array([float(r["volume"]) for r in od_map]))) > 1e-12:
        raise ValueError("demand/index volume mismatch")
    f0 = np.array([float(r["flow"]) for r in f0_rows], dtype=float)
    if not np.isfinite(f0).all() or np.min(f0) < 0 or np.max(np.abs(C_od_path @ f0 - q)) > 1e-12:
        raise ValueError("f0 is not a valid frozen path assignment")
    capacity_raw = np.array([float(r["capacity"]) for r in links], dtype=float)
    t0 = np.array([float(r["vdf_fftt"]) for r in links], dtype=float)
    alpha = np.array([float(r["vdf_alpha"]) for r in links], dtype=float)
    beta = np.array([float(r["vdf_beta"]) for r in links], dtype=float)
    capacity = np.maximum(capacity_raw, 1.0)
    if np.any(capacity_raw < 1) or np.any(t0 <= 0) or np.any(alpha < 0) or np.any(beta <= 0):
        raise ValueError("unexpected raw-to-effective BPR parameter condition")
    with np.load(INPUT / "bases" / f"rank{rank}.npz", allow_pickle=False) as saved:
        U = np.array(saved["U_rank"], dtype=float)
        major = np.array(saved["major_idx"], dtype=int)
        minor = np.array(saved["minor_idx"], dtype=int)
        # Deliberately ignore saved["theta"]: it belongs to old infeasible v4.
    if U.shape != (104, rank) or major.shape != (26,) or minor.shape != (104,):
        raise ValueError("saved basis/partition shape mismatch")
    if not np.array_equal(np.sort(np.r_[major, minor]), np.arange(130)) or np.max(np.abs(f0[minor])) > 1e-12:
        raise ValueError("basis partition incompatible with frozen f0")
    B = A_link_path.T.tocsr()
    D = np.asarray(A_link_path[:, minor] @ U)
    M = np.asarray(C_od_path[:, minor] @ U)
    theta_ref = U.T @ f0[minor]
    data = dict(B=B, A=C_od_path, links=link_ids, n_paths=130, n_links=5091, n_od=26,
                x_ref=f0, demand=q, capacity=capacity, t0=t0, alpha=alpha, beta=beta)
    comp = dict(B1=B[major, :], A1=C_od_path[:, major].tocsr(), D=D, M=M, U_r=U,
                x1_ref=f0[major], theta_ref=theta_ref, n_major=26, n_minor=104, r=rank)
    identity = dict(rank=rank, link_count=5091, path_count=130, od_count=26,
                    major_count=26, minor_count=104, support_link_count=int(np.count_nonzero(A_link_path.getnnz(axis=1))),
                    zero_support_link_count=int(np.count_nonzero(A_link_path.getnnz(axis=1) == 0)),
                    raw_capacity_below_one=int(np.sum(capacity_raw < 1)), raw_t0_below_point01=int(np.sum(t0 < 0.01)),
                    raw_to_effective={"capacity": "max(raw_capacity,1.0), inactive on this input", "t0": "raw vdf_fftt with no floor", "alpha": "raw vdf_alpha", "beta": "raw vdf_beta"},
                    beta_values=np.unique(beta).tolist(), demand_total=float(np.sum(q)),
                    theta_ref_max_abs=float(np.max(np.abs(theta_ref))),
                    D_max_abs_reconstruction_error=float(np.max(np.abs(D - A_link_path[:, minor] @ U))),
                    M_max_abs_reconstruction_error=float(np.max(np.abs(M - C_od_path[:, minor] @ U))))
    extra = dict(links=links, demands=demands, paths=paths, f0=f0, major=major, minor=minor,
                 A_link_path=A_link_path, C_od_path=C_od_path, link_index=link_index, od_index=od_index,
                 identity=identity)
    return data, comp, extra


def build_native_l3(data, comp, rho, lambda_od):
    """AST-isolate the authoritative L3 function and replace its BPR term only."""
    if sha(SOURCE) != SOURCE_HASH:
        raise RuntimeError("authoritative source snapshot hash mismatch")
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_alm_model_levels")
    segment = ast.get_source_segment(source, node)
    old = """routing_cost = sum(data['t0'][a] * m.v[a] + (data['t0'][a] * data['alpha'][a] / 5.0) * m.v[a] * (
                    (m.v[a] / max(data['capacity'][a], 1e-6)) ** 4) for a in m.LINKS)"""
    new = """routing_cost = sum(data['t0'][a] * m.v[a] + (data['t0'][a] * data['alpha'][a] / (data['beta'][a] + 1.0)) * m.v[a] * (
                    (m.v[a] / data['capacity'][a]) ** data['beta'][a]) for a in m.LINKS)"""
    if segment.count(old) != 1:
        raise RuntimeError("expected single L3 BPR expression not found")
    adapted = segment.replace(old, new)
    namespace = dict(np=np, pyo=pyo, defaultdict=defaultdict)
    exec(compile(adapted, str(SOURCE) + "::isolated_L3_BPR", "exec"), namespace)
    model, auxiliaries = namespace["build_alm_model_levels"](
        data, comp, level=3, rho=float(rho), lambda_od=np.asarray(lambda_od, dtype=float), gamma=0.0)
    for a in model.LINKS:
        model.v[a].setlb(0.0)
    return model, auxiliaries, dict(original_function_ast_sha256=hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
                                    adapted_function_sha256=hashlib.sha256(adapted.encode()).hexdigest(),
                                    exact_bpr_replacement_count=1, gamma=0.0,
                                    link_lower_bound=0.0)


def model_counts(model, comp, data):
    return dict(path_coordinates=comp["n_major"] + comp["r"], major_variables=comp["n_major"],
                latent_variables=comp["r"], explicit_link_variables=data["n_links"],
                total_native_variables=sum(1 for _ in model.component_data_objects(pyo.Var, active=True)),
                link_equalities=len(model.link_con), minor_nonnegative_inequalities=len(model.minor_con),
                total_active_constraints=sum(1 for _ in model.component_data_objects(pyo.Constraint, active=True)),
                od_alm_terms=data["n_od"])
