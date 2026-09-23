"""Frozen input reconstruction for the bounded native L3 alignment experiment."""
import ast
import hashlib
import json
import os
import pathlib
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import sparse
import pyomo.environ as pyo

ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON = pathlib.Path(os.environ.get("MCL_NATIVE_PYTHON", sys.executable))
SOLVER = pathlib.Path(os.environ.get("MCL_IPOPT", ""))
SOURCE = ROOT / "source_snapshot" / "run_diagnostic_levels.py"
CONFIGS = {
    "A_REG001": {"name":"L3_ZERO_FLOW_STRICT_REG001", "gamma":0.01},
    "B_BECKMANN": {"name":"L3_ZERO_FLOW_STRICT_BECKMANN", "gamma":0.0},
}
IPOPT_OPTIONS = dict(tol=1e-8, constr_viol_tol=1e-9, dual_inf_tol=1e-6,
                     compl_inf_tol=1e-8, acceptable_iter=0, bound_relax_factor=0,
                     honor_original_bounds="no", max_iter=500,
                     mu_strategy="adaptive", linear_solver="mumps", print_level=5)
OD_TOL = lambda q: 1e-6 + 1e-8 * np.maximum(1, np.abs(q))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=str), encoding="utf-8")

def load_case(city):
    folder = ROOT / "inputs_snapshot" / city
    src = np.load(folder / "source_arrays.npz", allow_pickle=False)
    rep = np.load(folder / "representation.npz", allow_pickle=False)
    A = sparse.load_npz(folder / "A_od_by_path.npz").tocsr()
    B = sparse.load_npz(folder / "B_path_by_link.npz").tocsr()
    paths = pd.read_csv(folder / "columns.csv")
    links = pd.read_csv(folder / "link.csv")
    ods = pd.read_csv(folder / "demand.csv")
    link_ids = sorted(int(x) for x in links.link_id)
    od_pairs = sorted((int(o), int(d)) for o, d in zip(ods.o_zone_id, ods.d_zone_id))
    errors = []
    if len(paths) != B.shape[0] or len(links) != B.shape[1] or A.shape != (len(ods), len(paths)):
        errors.append("Frozen incidence shape or CSV row mismatch")
    if not np.array_equal(np.array(link_ids), src["links"]):
        errors.append("Frozen source link order differs from copied link IDs")
    if len(set(link_ids)) != len(link_ids) or len(set(od_pairs)) != len(od_pairs):
        errors.append("Duplicate link or OD identity")
    if len(paths.path_id.unique()) != len(paths):
        errors.append("Duplicate path identity")
    od_index = {x:i for i,x in enumerate(od_pairs)}
    link_index = {x:i for i,x in enumerate(link_ids)}
    rows_b=[]; cols_b=[]; rows_a=[]; cols_a=[]
    for p,row in enumerate(paths.itertuples(index=False)):
        od=(int(row.o_zone_id),int(row.d_zone_id))
        if od not in od_index:
            errors.append(f"Path {p} has OD absent from demand")
            continue
        rows_a.append(od_index[od]); cols_a.append(p)
        seq=str(row.link_sequence); sep=";" if ";" in seq else ","
        for lid in (int(x.strip()) for x in seq.split(sep) if x.strip()):
            if lid not in link_index:
                errors.append(f"Path {p} has link absent from link table: {lid}")
                continue
            rows_b.append(p); cols_b.append(link_index[lid])
    Braw=sparse.csr_matrix((np.ones(len(rows_b)),(rows_b,cols_b)),shape=B.shape)
    Araw=sparse.csr_matrix((np.ones(len(rows_a)),(rows_a,cols_a)),shape=A.shape)
    if (Braw-B).nnz: errors.append("Frozen B differs from raw path sequences")
    if (Araw-A).nnz: errors.append("Frozen A differs from raw path OD identities")
    if not np.allclose(paths.volume.to_numpy(float), src["x_ref"],rtol=0,atol=1e-12):
        errors.append("Reference path flow differs from frozen source array")
    od_table=ods.set_index(["o_zone_id","d_zone_id"])
    demand=np.array([od_table.loc[od,"volume"] for od in od_pairs],dtype=float)
    if not np.allclose(demand,src["demand"],rtol=0,atol=1e-12):
        errors.append("Demand differs from frozen source array")
    ordered_links=links.sort_values("link_id")
    effective=dict(capacity=np.maximum(ordered_links.capacity.to_numpy(float),1.0),
                   t0=np.maximum(ordered_links.vdf_fftt.to_numpy(float),0.01),
                   alpha=ordered_links.vdf_alpha.to_numpy(float),
                   beta=ordered_links.vdf_beta.to_numpy(float))
    for key,values in effective.items():
        if not np.allclose(values,src[key],rtol=0,atol=1e-12):
            errors.append(f"Effective source {key} differs from raw CSV loader rule")
    if not np.all(src["beta"]==4.0): errors.append("Source beta differs from model power four")
    major=rep["major_idx"].astype(int); minor=rep["minor_idx"].astype(int)
    if len(major)+len(minor)!=len(paths) or not np.array_equal(np.sort(np.r_[major,minor]),np.arange(len(paths))):
        errors.append("Frozen major/minor partition is incomplete or overlapping")
    U=rep["U_r"]; D=rep["D"]; M=rep["M"]
    if U.shape!=(len(minor),50) or D.shape!=(len(links),50) or M.shape!=(len(ods),50):
        errors.append("Frozen rank-50 representation shape mismatch")
    d_err=float(np.max(np.abs(np.asarray(B[minor,:].T@U)-D)))
    m_err=float(np.max(np.abs(np.asarray(A[:,minor]@U)-M)))
    if d_err>1e-9 or m_err>1e-9: errors.append("Frozen D or M reconstruction differs")
    if not np.allclose(rep["x1_ref"],src["x_ref"][major],rtol=0,atol=1e-12):
        errors.append("Frozen major reference differs")
    zero_support=np.flatnonzero(np.asarray(B.getnnz(axis=0))==0)
    zero_ids=[link_ids[i] for i in zero_support]
    if np.any(D[zero_support,:]!=0): errors.append("Zero-support link has nonzero compressed D row")
    data={key:np.asarray(src[key]) for key in ["x_ref","demand","capacity","t0","alpha","beta"]}
    data.update(B=B,A=A,links=link_ids,n_paths=len(paths),n_links=len(links),n_od=len(ods))
    comp=dict(B1=B[major,:],A1=A[:,major].tocsr(),D=D,M=M,U_r=U,
              x1_ref=rep["x1_ref"],theta_ref=rep["theta_ref"],
              n_major=len(major),n_minor=len(minor),r=50)
    report=dict(city=city,errors=errors,source_csv_hashes={p.name:sha(p) for p in folder.glob("*.csv")},
                frozen_array_hashes={p.name:sha(p) for p in folder.glob("*.npz")},
                n_paths=len(paths),n_links=len(links),n_od=len(ods),n_major=len(major),n_minor=len(minor),rank=50,
                D_reconstruction_max_abs=d_err,M_reconstruction_max_abs=m_err,
                zero_support_link_ids=zero_ids,zero_support_D_rows_exactly_zero=bool(np.all(D[zero_support,:]==0)),
                raw_to_effective_rules={"capacity":"max(raw, 1.0)","t0":"max(raw, 0.01)",
                                        "alpha":"raw", "beta":"raw"},
                raw_capacity_below_floor=int(np.sum(ordered_links.capacity.to_numpy(float)<1)),
                raw_t0_below_floor=int(np.sum(ordered_links.vdf_fftt.to_numpy(float)<0.01)),
                reference_flow_sum=float(paths.volume.sum()), demand_sum=float(demand.sum()))
    return data,comp,report

def source_builder():
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"),filename=str(SOURCE))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_alm_model_levels")
    namespace=dict(np=np,pyo=pyo,defaultdict=defaultdict)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),"exec"),namespace)
    return namespace["build_alm_model_levels"], hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
