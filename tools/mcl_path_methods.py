"""Finite path and native Diagnostic L3 for newly prepared GMNS instances."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import heapq
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

from mcl_assignment import load_instance, write_rows, atomic_json, objective, costs, sha, aon, graph, GATES


def k_paths(links, adj, origin, dest, k):
    """Accepted Boston edge-identity Yen scheme, with stable tie breaking."""
    edge_cost=[float(r["vdf_fftt"]) for r in links]
    def dijkstra(start,banned_nodes=frozenset(),banned_edges=frozenset()):
        heap=[(0.0,(),start,(start,))]
        best={start:0.0}
        while heap:
            c,edges,u,nodes=heapq.heappop(heap)
            if c>best.get(u,math.inf)+1e-12:continue
            if u==dest:return c,edges,nodes
            for v,i in adj.get(u,()):
                if v in banned_nodes or i in banned_edges or v in nodes:continue
                nc=c+edge_cost[i]
                if nc<best.get(v,math.inf)-1e-12:
                    best[v]=nc;heapq.heappush(heap,(nc,edges+(i,),v,nodes+(v,)))
        return None
    first=dijkstra(origin)
    if first is None:return []
    accepted=[first];seen={first[1]};candidate=[];queued=set()
    while len(accepted)<k:
        old=accepted[-1]
        for i in range(len(old[1])):
            root_edges=old[1][:i];root_nodes=old[2][:i+1]
            banned={p[1][i] for p in accepted if len(p[1])>i and p[1][:i]==root_edges}
            spur=dijkstra(root_nodes[-1],frozenset(root_nodes[:-1]),frozenset(banned))
            if spur is None:continue
            seq=root_edges+spur[1]
            if seq in seen or seq in queued:continue
            nodes=root_nodes[:-1]+spur[2]
            candidate.append((sum(edge_cost[j] for j in seq),seq,nodes));queued.add(seq)
        if not candidate:break
        heapq.heapify(candidate);nxt=heapq.heappop(candidate)
        queued.remove(nxt[1]);seen.add(nxt[1]);accepted.append(nxt)
    return accepted


def build_pool(instance, output, k=5):
    from scipy import sparse
    import numpy as np
    started=time.perf_counter()
    if not 1<=k<=5:raise ValueError("K must be 1..5")
    m,links,od=load_instance(instance)
    out=Path(output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty path output")
    out.mkdir(parents=True)
    adj=defaultdict(list)
    for j,r in enumerate(links):adj[r["from_node_id"]].append((r["to_node_id"],j))
    for values in adj.values():values.sort(key=lambda x:(float(links[x[1]]["vdf_fftt"]),links[x[1]]["link_id"]))
    paths=[];ar=[];ac=[];cr=[];cc=[];f0=[]
    for i,r in enumerate(od):
        alternatives=k_paths(links,adj,r["o_node_id"],r["d_node_id"],k)
        if not alternatives:raise ValueError(f"no path OD {i}")
        for rank,(cost,seq,nodes) in enumerate(alternatives):
            if nodes[0]!=r["o_node_id"] or nodes[-1]!=r["d_node_id"] or len(nodes)!=len(set(nodes)):
                raise ValueError("path endpoints/loop")
            for u,v,j in zip(nodes[:-1],nodes[1:],seq):
                if (links[j]["from_node_id"],links[j]["to_node_id"])!=(u,v):raise ValueError("path continuity")
            p=len(paths)
            paths.append({"path_index":p,"od_index":i,"rank_in_od":rank,"o_node_id":nodes[0],"d_node_id":nodes[-1],
                          "link_id_sequence":";".join(links[j]["link_id"] for j in seq),"free_flow_cost_min":cost})
            f0.append(float(r["volume"]) if rank==0 else 0.0)
            cr.append(i);cc.append(p)
            for j in seq:ar.append(j);ac.append(p)
    A=sparse.coo_matrix((np.ones(len(ar)),(ar,ac)),shape=(len(links),len(paths))).tocsr()
    C=sparse.coo_matrix((np.ones(len(cr)),(cr,cc)),shape=(len(od),len(paths))).tocsr()
    q=np.array([float(x["volume"]) for x in od])
    if np.max(np.abs(C@np.array(f0)-q))>1e-10:raise ValueError("seed demand residual")
    write_rows(out/"paths.csv",paths,["path_index","od_index","rank_in_od","o_node_id","d_node_id","link_id_sequence","free_flow_cost_min"])
    write_rows(out/"f0.csv",[{"path_index":i,"flow":f} for i,f in enumerate(f0)],["path_index","flow"])
    sparse.save_npz(out/"A_link_path.npz",A);sparse.save_npz(out/"C_od_path.npz",C)
    info={"instance_signature":m["instance_signature"],"k":k,"paths":len(paths),"od":len(od),
          "links":len(links),"minor_paths":len(paths)-len(od),"A_nnz":A.nnz,"C_nnz":C.nnz,
          "seed_policy":"all demand on minimum-free-flow path; no FW output read",
          "path_generation_seconds":time.perf_counter()-started,
          "paths_sha256":sha(out/"paths.csv")}
    atomic_json(out/"pool.json",info)
    return info


def load_pool(instance,pool):
    import numpy as np
    from scipy import sparse
    m,links,od=load_instance(instance)
    pool=Path(pool)
    info=json.loads((pool/"pool.json").read_text(encoding="utf-8"))
    if info["instance_signature"]!=m["instance_signature"] or sha(pool/"paths.csv")!=info["paths_sha256"]:
        raise ValueError("pool signature/integrity mismatch")
    with (pool/"paths.csv").open(newline="",encoding="utf-8") as f:paths=list(csv.DictReader(f))
    with (pool/"f0.csv").open(newline="",encoding="utf-8") as f:f0=np.array([float(r["flow"]) for r in csv.DictReader(f)])
    A=sparse.load_npz(pool/"A_link_path.npz").tocsr();C=sparse.load_npz(pool/"C_od_path.npz").tocsr()
    if A.shape!=(len(links),len(paths)) or C.shape!=(len(od),len(paths)) or f0.shape!=(len(paths),):raise ValueError("pool dimension mismatch")
    edge={r["link_id"]:i for i,r in enumerate(links)}
    expA=sparse.lil_matrix(A.shape);expC=sparse.lil_matrix(C.shape)
    for p,r in enumerate(paths):
        i=int(r["od_index"]);at=od[i]["o_node_id"];visited={at}
        if int(r["path_index"])!=p:raise ValueError("path order")
        for lid in r["link_id_sequence"].split(";"):
            j=edge[lid];e=links[j]
            if e["from_node_id"]!=at or e["to_node_id"] in visited:raise ValueError("path invalid")
            expA[j,p]=1;at=e["to_node_id"];visited.add(at)
        if at!=od[i]["d_node_id"]:raise ValueError("path destination")
        expC[i,p]=1
    if (expA.tocsr()-A).nnz or (expC.tocsr()-C).nnz:raise ValueError("path incidence integrity")
    q=np.array([float(x["volume"]) for x in od])
    if np.max(np.abs(C@f0-q))>1e-10 or np.min(f0)<0:raise ValueError("invalid feasible seed")
    return m,links,od,paths,A,C,f0,q


def full_path(instance,pool,output,maxiter=300,memory_ceiling=2*1024**3):
    import numpy as np
    from scipy.optimize import Bounds,LinearConstraint,minimize
    t=time.perf_counter()
    m,links,od,paths,A,C,f0,q=load_pool(instance,pool)
    out=Path(output)
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty output")
    n=len(paths)
    # SLSQP uses dense workspace and dense equality Jacobian; refuse unsafe size.
    conservative=8*(n+len(od)+1)**2*12
    if conservative>memory_ceiling:raise MemoryError(f"SLSQP workspace estimate {conservative} exceeds measured method ceiling {memory_ceiling}")
    def value(f):return objective(np.asarray(A@f).ravel(),links)
    def grad(f):return np.asarray(A.T@np.asarray(costs(np.asarray(A@f).ravel(),links))).ravel()
    solve_start=time.perf_counter()
    result=minimize(value,f0.copy(),jac=grad,method="SLSQP",bounds=Bounds(0,np.inf),
                    constraints=[LinearConstraint(C,q,q)],options={"maxiter":maxiter,"ftol":1e-10,"disp":False})
    f=np.asarray(result.x);v=np.asarray(A@f).ravel()
    out.mkdir(parents=True)
    write_rows(out/"path_flow.csv",[{"path_index":i,"od_index":paths[i]["od_index"],"flow":float(f[i])} for i in range(n)],["path_index","od_index","flow"])
    write_rows(out/"link_flow.csv",[{"link_id":r["link_id"],"flow_pce_per_period":float(v[i])} for i,r in enumerate(links)],["link_id","flow_pce_per_period"])
    record={"method":"finite_full_path_SLSQP","instance_signature":m["instance_signature"],"pool_sha256":sha(Path(pool)/"paths.csv"),
            "solver_success":bool(result.success),"message":str(result.message),"iterations":int(result.nit),
            "objective":float(result.fun),"solver_seconds":time.perf_counter()-solve_start,
            "total_seconds":time.perf_counter()-t,"path_count":n,"od_count":len(od),"link_count":len(links),
            "max_abs_od_error":float(np.max(np.abs(C@f-q))),"min_path_flow_raw":float(np.min(f)),
            "workspace_estimate_bytes":conservative}
    atomic_json(out/"run.json",record)
    return record


def check_path_solution(instance,pool,path_flow,link_flow,fw_run=None):
    """Re-read ordered paths and raw returned flows in original coordinates."""
    import numpy as np
    m,links,od,paths,A,C,f0,q=load_pool(instance,pool)
    with Path(path_flow).open(newline="",encoding="utf-8") as f:pr=list(csv.DictReader(f))
    with Path(link_flow).open(newline="",encoding="utf-8") as f:lr=list(csv.DictReader(f))
    if len(pr)!=len(paths) or len(lr)!=len(links):raise ValueError("returned dimension mismatch")
    if [r["link_id"] for r in lr]!=[r["link_id"] for r in links]:raise ValueError("returned link identity mismatch")
    if [int(r["path_index"]) for r in pr]!=list(range(len(paths))):raise ValueError("returned path identity mismatch")
    x=np.array([float(r["flow"]) for r in pr]);v=np.array([float(r["flow_pce_per_period"]) for r in lr])
    if not np.isfinite(x).all() or not np.isfinite(v).all():raise ValueError("nonfinite returned flows")
    reconstructed=np.asarray(A@x).ravel()
    residual=np.asarray(C@x).ravel()-q
    c=np.asarray(costs(v,links))
    adj,_=graph(links)
    _,_,short_sum=aon(links,adj,od,c)
    total=float(v@c)
    pool_short=0.0
    for i in range(len(od)):
        pool_short+=q[i]*min(float(np.asarray(A[:,j].T@c).item()) for j in C.getrow(i).indices)
    out={"instance_signature":m["instance_signature"],"method":"finite_full_path",
         "min_path_flow_raw":float(np.min(x)),"negative_path_count_raw":int(np.sum(x<0)),
         "negative_path_mass_raw":float(np.sum(np.maximum(-x,0))),
         "min_link_flow_raw":float(np.min(v)),"negative_link_count_raw":int(np.sum(v<0)),
         "max_od_residual":float(np.max(np.abs(residual))),"od_residual_sum":float(np.sum(residual)),
         "od_residual_l1":float(np.sum(np.abs(residual))),
         "max_link_reconstruction_error":float(np.max(np.abs(v-reconstructed))),
         "objective_checked":objective(v,links),"signed_full_gap":float(total-short_sum),
         "full_relative_gap":float((total-short_sum)/max(total,1e-12)),
         "signed_pool_gap":float(total-pool_short),"pool_relative_gap":float((total-pool_short)/max(total,1e-12)),
         "demand_total":float(np.sum(q)),"path_count":len(paths),"node_od":len(od),"physical_links":len(links),"gates":GATES}
    if fw_run:
        fw=json.loads((Path(fw_run)/"run.json").read_text(encoding="utf-8"))
        if fw["instance_signature"]!=m["instance_signature"]:raise ValueError("FW signature mismatch")
        out["objective_minus_fw"]=out["objective_checked"]-fw["objective"]
    valid=(np.min(x)>=-GATES["negative_flow_abs"] and np.min(v)>=-GATES["negative_flow_abs"]
           and out["max_link_reconstruction_error"]<=GATES["link_reconstruction_abs"]
           and all(abs(residual[i])<=GATES["max_od_error_abs"]+GATES["max_od_error_rel"]*max(1,q[i]) for i in range(len(q)))
           and out["od_residual_l1"]/max(out["demand_total"],1e-12)<=GATES["total_od_l1_rel"])
    out["status"]=("SOLVED_WITHIN_DECLARED_TOLERANCE" if valid and abs(out["full_relative_gap"])<=GATES["full_relative_gap_abs"]
                   else "RESTRICTED_POOL_ONLY" if valid and abs(out["pool_relative_gap"])<=GATES["full_relative_gap_abs"]
                   else "SOLVER_TERMINATED_BUT_NOT_ACCEPTED")
    return out


def basis(instance,pool,output,fraction,memory_ceiling=2*1024**3):
    import numpy as np
    from scipy import sparse
    t=time.perf_counter()
    m,links,od,paths,A,C,f0,q=load_pool(instance,pool)
    major=np.flatnonzero(f0>0);minor=np.flatnonzero(f0==0)
    n=len(minor)
    requested_rank=min(max(1,round(fraction*n)),n-1,len(links)-1) if n>1 else 0
    rank=requested_rank
    if rank<=0:raise ValueError("no legitimate compression rank")
    B2=A[:,minor].T.tocsr()
    dense_bytes=B2.shape[0]*B2.shape[1]*8
    conservative=12*dense_bytes+8*n*n
    if conservative>memory_ceiling:raise MemoryError(f"basis workspace estimate {conservative} exceeds measured method ceiling {memory_ceiling}")
    weighted=sparse.diags(np.sqrt(np.abs(f0[minor])+1.0))@B2
    if n*len(links)<20_000_000:
        U,s,_=np.linalg.svd(weighted.toarray(),full_matrices=False)
        U=U[:,:rank];singular=s[:rank]
        engine="exact_dense_svd"
    else:
        from scipy.sparse.linalg import svds
        rng=np.random.default_rng(42)
        u,s,_=svds(weighted,k=rank,which="LM",v0=rng.random(min(weighted.shape)))
        order=np.argsort(s)[::-1];U=u[:,order];singular=s[order]
        engine="scipy_sparse_svds_seed42"
    rank_threshold=max(B2.shape)*np.finfo(float).eps*max(float(singular[0]),1.0)
    retained=int(np.count_nonzero(singular>rank_threshold))
    if retained<=0:raise ValueError("deficient path-link operator has no informative compression direction")
    if retained<rank:
        U=U[:,:retained]
        singular=singular[:retained]
        rank=retained
    theta=U.T@f0[minor]
    if np.max(np.abs(U@theta-f0[minor]))>1e-10:raise ValueError("projected seed infeasible")
    D=np.asarray(A[:,minor]@U);M=np.asarray(C[:,minor]@U)
    out=Path(output)
    if out.exists() and any(out.iterdir()):raise ValueError("nonempty basis output")
    out.mkdir(parents=True)
    np.savez_compressed(out/"basis.npz",U=U,major=major,minor=minor,theta_ref=theta,D=D,M=M,singular=singular)
    info={"instance_signature":m["instance_signature"],"pool_sha256":sha(Path(pool)/"paths.csv"),
          "rank_fraction":fraction,"requested_rank":requested_rank,"rank":rank,
          "numeric_rank_threshold":rank_threshold,"retained_positive_singular_values":retained,
          "major_paths":len(major),"minor_paths":n,
          "path_count":len(paths),"link_count":len(links),"od_count":len(od),"engine":engine,
          "operator":"sqrt(abs(f0_minor)+1) * B2, B2=minor path by physical link incidence",
          "reconstruction":"f_minor=U theta; D=A_minor U; M=C_minor U",
          "basis_seconds":time.perf_counter()-t,"dense_raw_bytes":dense_bytes,
          "conservative_workspace_bytes":conservative,"singular_values":singular.tolist()}
    atomic_json(out/"basis.json",info)
    return info


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="action",required=True)
    p=sub.add_parser("paths");p.add_argument("--instance",required=True);p.add_argument("--output",required=True);p.add_argument("--k",type=int,default=5)
    p=sub.add_parser("full-path");p.add_argument("--instance",required=True);p.add_argument("--pool",required=True);p.add_argument("--output",required=True);p.add_argument("--maxiter",type=int,default=300)
    p=sub.add_parser("basis");p.add_argument("--instance",required=True);p.add_argument("--pool",required=True);p.add_argument("--output",required=True);p.add_argument("--fraction",type=float,required=True)
    a=ap.parse_args()
    try:
        if a.action=="paths":result=build_pool(a.instance,a.output,a.k)
        elif a.action=="full-path":result=full_path(a.instance,a.pool,a.output,a.maxiter)
        else:result=basis(a.instance,a.pool,a.output,a.fraction)
        print(json.dumps(result,indent=2,allow_nan=False));return 0
    except Exception as exc:
        print(json.dumps({"status":"ERROR","action":a.action,"reason":str(exc)}),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(main())
