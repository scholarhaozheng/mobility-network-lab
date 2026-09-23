"""Independent original-space audit; does not import or invoke the optimizer."""
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import shortest_path

ROOT=pathlib.Path(__file__).resolve().parents[1]
GAMMA={"A_REG001":0.01,"B_BECKMANN":0.0}

def dump(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False,default=str),encoding="utf-8")

def objective(flow,t0,alpha,capacity):
    return float(np.sum(t0*flow+(t0*alpha/5.0)*flow*(flow/np.maximum(capacity,1e-6))**4))

def main(city,config,outer):
    folder=ROOT/"inputs_snapshot"/city
    out=ROOT/"runs"/city/config
    sol=np.load(out/f"outer_{outer:02d}_solution.npz",allow_pickle=False)
    rep=np.load(folder/"representation.npz",allow_pickle=False)
    src=np.load(folder/"source_arrays.npz",allow_pickle=False)
    paths=pd.read_csv(folder/"columns.csv")
    links=pd.read_csv(folder/"link.csv").sort_values("link_id").reset_index(drop=True)
    ods=pd.read_csv(folder/"demand.csv").sort_values(["o_zone_id","d_zone_id"]).reset_index(drop=True)
    major=rep["major_idx"].astype(int);minor=rep["minor_idx"].astype(int)
    U=rep["U_r"];x1=sol["x1"];theta=sol["theta"];v=sol["v"]
    lam=sol["lambda_used"];rho=float(sol["rho"][0]);gamma=GAMMA[config]
    f=np.empty(len(paths),dtype=float);f[major]=x1;f[minor]=U@theta
    link_index={int(lid):i for i,lid in enumerate(links.link_id)}
    od_index={(int(o),int(d)):i for i,(o,d) in enumerate(zip(ods.o_zone_id,ods.d_zone_id))}
    agg=np.zeros(len(links));od_total=np.zeros(len(ods));sequences=[]
    for row,flow in zip(paths.itertuples(index=False),f):
        od_total[od_index[(int(row.o_zone_id),int(row.d_zone_id))]]+=flow
        seq=str(row.link_sequence);sep=";" if ";" in seq else ","
        ids=[int(x.strip()) for x in seq.split(sep) if x.strip()]
        sequences.append(ids)
        for lid in ids: agg[link_index[lid]]+=flow
    q=ods.volume.to_numpy(float)
    r=od_total-q
    link_r=agg-v
    od_limit=1e-6+1e-8*np.maximum(1,np.abs(q))
    link_limit=1e-6+1e-8*np.maximum(1,np.abs(agg))
    t0=src["t0"];alpha=src["alpha"];capacity=src["capacity"]
    F_v=objective(v,t0,alpha,capacity)
    F_agg=objective(agg,t0,alpha,capacity)
    regularizer=float(gamma/2.0*(np.sum((x1-rep["x1_ref"])**2)+np.sum((theta-rep["theta_ref"])**2)))
    linear=float(lam@r);quadratic=float(0.5*rho*np.sum(r**2))
    total=F_v+regularizer+linear+quadratic
    native=json.loads((out/f"outer_{outer:02d}_native.json").read_text(encoding="utf-8"))
    native_obj=native.get("native_unscaled_objective")
    pyomo_obj=native.get("model_objective")
    obj_limit=1e-5+1e-7*max(1,abs(total))
    obj_pyomo_agree=pyomo_obj is not None and abs(total-pyomo_obj)<=obj_limit
    obj_native_agree=native_obj is not None and abs(total-native_obj)<=obj_limit
    A=sparse.load_npz(folder/"A_od_by_path.npz")
    B=sparse.load_npz(folder/"B_path_by_link.npz")
    matrix_link=np.asarray(B.T@f).ravel()
    matrix_od=np.asarray(A@f).ravel()
    source_zero=np.flatnonzero(np.asarray(B.getnnz(axis=0))==0)
    zero_ids=[int(links.link_id.iloc[i]) for i in source_zero]
    counts=dict(paths=len(paths),ods=len(ods),links=len(links),
                original_path_ids_unique=bool(paths.path_id.is_unique),
                link_ids_unique=bool(links.link_id.is_unique),
                od_pairs_unique=bool(not ods.duplicated(["o_zone_id","d_zone_id"]).any()),
                all_input_columns_present=all(x in paths for x in ["path_id","o_zone_id","d_zone_id","volume","link_sequence"])
                    and all(x in links for x in ["link_id","from_node_id","to_node_id","capacity","vdf_fftt","vdf_alpha","vdf_beta"])
                    and all(x in ods for x in ["o_zone_id","d_zone_id","volume"]))
    criteria=dict(native_optimal=(native.get("solver_status")=="ok" and native.get("termination")=="optimal" and native.get("solution_loaded") is True),
                  all_finite=bool(np.isfinite(f).all() and np.isfinite(v).all() and np.isfinite(r).all()),
                  path_sign=bool(np.min(f)>=-1e-8),major_bound=bool(np.min(x1)>=-1e-8),
                  link_bound=bool(np.min(v)>=-1e-8),
                  all_od=bool(np.all(np.abs(r)<=od_limit)),
                  all_link_equalities=bool(np.all(np.abs(link_r)<=link_limit)),
                  matrix_table_agreement=bool(np.max(np.abs(matrix_link-agg))<=1e-8 and np.max(np.abs(matrix_od-od_total))<=1e-8),
                  complete_ids=bool(counts["original_path_ids_unique"] and counts["link_ids_unique"] and counts["od_pairs_unique"] and counts["all_input_columns_present"]),
                  zero_support_domain_consistent=bool(np.all(rep["D"][source_zero,:]==0)
                         and native.get("zero_support_link_bound_permits_zero") is True),
                  objective_decomposition_agrees_with_pyomo=bool(obj_pyomo_agree),
                  objective_decomposition_agrees_with_native=bool(obj_native_agree))
    passed=bool(all(criteria.values()))
    report=dict(city=city,config=config,outer=outer,gamma=gamma,rho=rho,
       accepted=passed,criteria=criteria,counts=counts,
       native_status=native.get("solver_status"),native_termination=native.get("termination"),
       stats=dict(min_path_flow=float(np.min(f)),negative_path_count=int(np.sum(f<0)),
                  count_below_minus_1e_8=int(np.sum(f< -1e-8)),
                  negative_flow_mass=max(0.0,float(-np.minimum(f,0).sum())),
                  min_major=float(np.min(x1)),min_minor=float(np.min(f[minor])),
                  min_explicit_link=float(np.min(v)),
                  max_abs_od=float(np.max(np.abs(r))),L1_od=float(np.sum(np.abs(r))),
                  failed_od_count=int(np.sum(np.abs(r)>od_limit)),
                  max_abs_link=float(np.max(np.abs(link_r))),L1_link=float(np.sum(np.abs(link_r))),
                  failed_link_count=int(np.sum(np.abs(link_r)>link_limit)),
                  max_abs_table_matrix_link=float(np.max(np.abs(matrix_link-agg))),
                  max_abs_table_matrix_od=float(np.max(np.abs(matrix_od-od_total))),
                  zero_support_link_ids=zero_ids,
                  max_abs_zero_support_v=float(np.max(np.abs(v[source_zero]))) if len(source_zero) else 0.0,
                  F_explicit_v=F_v,F_reconstructed_link=F_agg,F_difference=F_agg-F_v,
                  regularizer=regularizer,alm_linear=linear,alm_quadratic=quadratic,
                  total_decomposed_objective=total,native_unscaled_objective=native_obj,
                  pyomo_model_objective=pyomo_obj,objective_agreement_tolerance=obj_limit))
    # Save every raw coordinate and complete original-order table for this returned iterate.
    np.save(out/f"outer_{outer:02d}_od_residual.npy",r)
    cls=np.full(len(paths),"minor",dtype=object);cls[major]="major"
    path_out=paths.copy();path_out["path_row_zero_based"]=np.arange(len(paths))
    path_out["class"]=cls;path_out["raw_reconstructed_flow"]=f
    path_out.to_csv(out/f"outer_{outer:02d}_original_path_flows.csv",index=False)
    od_out=ods.copy();od_out["reconstructed_flow"]=od_total;od_out["raw_residual"]=r
    od_out["audit_abs_tolerance"]=od_limit;od_out["audit_pass"]=np.abs(r)<=od_limit
    od_out.to_csv(out/f"outer_{outer:02d}_od_balance.csv",index=False)
    link_out=links.copy();link_out["effective_capacity"]=capacity;link_out["effective_t0"]=t0
    link_out["effective_alpha"]=alpha;link_out["explicit_v"]=v;link_out["path_aggregate"]=agg
    link_out["link_residual"]=link_r;link_out["audit_abs_tolerance"]=link_limit
    link_out.to_csv(out/f"outer_{outer:02d}_link_flows.csv",index=False)
    pd.DataFrame({"major_coordinate":np.arange(len(x1)),"path_row_zero_based":major,
                  "reference_flow":rep["x1_ref"],"raw_solution":x1}).to_csv(out/f"outer_{outer:02d}_major.csv",index=False)
    pd.DataFrame({"latent_coordinate":np.arange(len(theta)),"reference_theta":rep["theta_ref"],
                  "raw_solution":theta}).to_csv(out/f"outer_{outer:02d}_theta.csv",index=False)
    if passed:
        costs=t0*(1+alpha*(v/capacity)**4)
        path_cost=np.array([sum(costs[link_index[lid]] for lid in seq) for seq in sequences])
        pool_min=np.full(len(ods),np.inf)
        for row,cost in zip(paths.itertuples(index=False),path_cost):
            w=od_index[(int(row.o_zone_id),int(row.d_zone_id))]
            pool_min[w]=min(pool_min[w],cost)
        travel=float(f@path_cost)
        pool_lb=float(q@pool_min)
        nodes=sorted(set(int(x) for x in links.from_node_id)|set(int(x) for x in links.to_node_id))
        node_index={x:i for i,x in enumerate(nodes)}
        arc_min={}
        for row,cost in zip(links.itertuples(index=False),costs):
            key=(node_index[int(row.from_node_id)],node_index[int(row.to_node_id)])
            arc_min[key]=min(float(cost),arc_min.get(key,np.inf))
        graph=sparse.csr_matrix((list(arc_min.values()),
             ([key[0] for key in arc_min],[key[1] for key in arc_min])),shape=(len(nodes),len(nodes)))
        origins=sorted(set(int(x) for x in ods.o_zone_id))
        dist=shortest_path(graph,directed=True,indices=[node_index[x] for x in origins])
        origin_idx={x:i for i,x in enumerate(origins)}
        full_lb=float(sum(float(demand)*dist[origin_idx[int(o)],node_index[int(d)]]
                for o,d,demand in zip(ods.o_zone_id,ods.d_zone_id,q)))
        report["gap_diagnostics"]={"travel_cost":travel,"restricted_pool_lower_cost":pool_lb,
           "restricted_pool_relative_gap":(travel-pool_lb)/travel if travel else None,
           "full_network_lower_cost":full_lb,
           "full_network_relative_gap":(travel-full_lb)/travel if travel else None,
           "parallel_arcs":"minimum individual arc cost per ordered endpoint pair; arcs were not summed",
           "interpretation":"Unregularized cost-gap diagnostic on a numerically feasible compressed candidate, not a full-network UE certificate."}
    else:
        report["gap_diagnostics"]={"status":"NOT_COMPUTED_NUMERICAL_CRITERIA_NOT_ALL_MET"}
    dump(out/f"outer_{outer:02d}_check.json",report)
    print(json.dumps({"city":city,"config":config,"outer":outer,"accepted":passed,
                      "max_abs_od":report["stats"]["max_abs_od"],
                      "failed_od_count":report["stats"]["failed_od_count"],
                      "min_path":report["stats"]["min_path_flow"]}))
    return 0

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("city",choices=["SiouxFalls","Anaheim"])
    parser.add_argument("config",choices=list(GAMMA));parser.add_argument("outer",type=int)
    args=parser.parse_args();sys.exit(main(args.city,args.config,args.outer))
