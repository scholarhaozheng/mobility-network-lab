"""One bounded native IPOPT inner call on the frozen Diagnostic L3 basis."""
import argparse
import contextlib
import json
import os
import pathlib
import re
import sys
import time
import traceback

import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

from common import ROOT, SOLVER, SOURCE, CONFIGS, IPOPT_OPTIONS, dump, load_case, sha, source_builder

def model_counts(model, comp, data):
    return dict(n_paths=data["n_paths"],n_major=comp["n_major"],n_minor=comp["n_minor"],rank=comp["r"],
        path_coordinates=comp["n_major"]+comp["r"],link_variables=data["n_links"],
        total_native_variables=sum(1 for _ in model.component_data_objects(pyo.Var,active=True)),
        link_equalities=len(model.link_con),minor_inequalities=len(model.minor_con),
        total_active_constraints=sum(1 for _ in model.component_data_objects(pyo.Constraint,active=True)))

def main(city, config, outer):
    assert pathlib.Path.cwd().resolve()==ROOT.resolve(), f"Worker cwd must equal fresh run root: {pathlib.Path.cwd()}"
    assert not (ROOT/"ipopt.opt").exists(), "No inherited or task-root ipopt.opt permitted"
    out=ROOT/"runs"/city/config
    out.mkdir(parents=True,exist_ok=True)
    state=np.load(out/f"outer_{outer:02d}_state.npz",allow_pickle=False)
    lam=np.asarray(state["lambda_used"],dtype=float); rho=float(state["rho"][0])
    started=time.time()
    info=dict(city=city,config=config,outer=outer,rho=rho,gamma=CONFIGS[config]["gamma"],
              cwd=str(pathlib.Path.cwd()),source_sha256=sha(SOURCE),solver_executable=str(SOLVER),
              solver_options=IPOPT_OPTIONS,ipopt_opt_file_used=None)
    try:
        data,comp,preflight=load_case(city)
        if preflight["errors"]: raise ValueError(f"Frozen preflight errors: {preflight['errors']}")
        if len(lam)!=data["n_od"] or not np.all(np.isfinite(lam)): raise ValueError("Invalid lambda vector")
        builder,ast_hash=source_builder()
        info["builder_ast_sha256"]=ast_hash
        build_t0=time.time()
        model,_=builder(data,comp,level=3,rho=rho,lambda_od=lam,gamma=CONFIGS[config]["gamma"])
        for a in model.LINKS:
            model.v[a].setlb(0.0)
        counts=model_counts(model,comp,data)
        if counts["minor_inequalities"]!=comp["n_minor"] or counts["link_equalities"]!=data["n_links"]:
            raise AssertionError("L3 constraint components not complete")
        if counts["total_native_variables"]!=comp["n_major"]+comp["r"]+data["n_links"]:
            raise AssertionError("Native variable count mismatch")
        if any(model.v[a].lb!=0.0 for a in model.LINKS): raise AssertionError("Zero link bound not applied")
        if any(not model.minor_con[i].active for i in model.MINOR): raise AssertionError("Inactive minor inequality")
        if any(not model.link_con[a].active for a in model.LINKS): raise AssertionError("Inactive link equality")
        zero_ids=preflight["zero_support_link_ids"]
        index={int(x):i for i,x in enumerate(data["links"])}
        if any(np.any(comp["D"][index[lid],:]!=0) or comp["B1"][:,index[lid]].nnz!=0 for lid in zero_ids):
            raise AssertionError("Zero-support row is not algebraically zero")
        # At source initialization, each minor constraint evaluates to its exact U @ theta expression.
        theta_init=np.array([pyo.value(model.theta[j]) for j in model.LATENT])
        minor_eval=np.array([pyo.value(model.minor_con[i].body) for i in model.MINOR])
        if np.max(np.abs(minor_eval-comp["U_r"]@theta_init))>1e-9:
            raise AssertionError("Minor constraints differ from frozen basis")
        info.update(model_counts=counts,zero_support_link_ids=zero_ids,
                    zero_support_link_bound_permits_zero=True,
                    bound_adaptation="Runner sets every model.v lower bound from 1e-8 to 0.0 after unchanged source builder",
                    model_build_seconds=time.time()-build_t0)
        if outer==1: dump(out/"model_counts.json",counts)
        solver=SolverFactory("ipopt",executable=str(SOLVER))
        if not solver.available(exception_flag=False): raise RuntimeError("Native IPOPT unavailable")
        solver.options.update(IPOPT_OPTIONS)
        stdout_path=out/f"outer_{outer:02d}_stdout_stderr.log"
        ipopt_log=out/f"outer_{outer:02d}_ipopt.log"
        solve_t0=time.time()
        try:
            with stdout_path.open("w",encoding="utf-8") as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                print(f"Native Diagnostic L3 {city} {config} outer={outer} rho={rho} gamma={CONFIGS[config]['gamma']}",flush=True)
                print(f"Options: {json.dumps(IPOPT_OPTIONS,sort_keys=True)}",flush=True)
                results=solver.solve(model,tee=True,logfile=str(ipopt_log),load_solutions=False,
                                     keepfiles=False,symbolic_solver_labels=False)
            info.update(solve_wall_seconds=time.time()-solve_t0,
                        solver_status=str(results.solver.status),
                        termination=str(results.solver.termination_condition),
                        solver_message=str(results.solver.message),
                        solution_records=len(results.solution))
            if len(results.solution)>0:
                model.solutions.load_from(results)
                x1=np.array([pyo.value(model.x1[p]) for p in model.MAJOR],dtype=float)
                theta=np.array([pyo.value(model.theta[j]) for j in model.LATENT],dtype=float)
                v=np.array([pyo.value(model.v[a]) for a in model.LINKS],dtype=float)
                if not (np.isfinite(x1).all() and np.isfinite(theta).all() and np.isfinite(v).all()):
                    raise ValueError("Returned solution contains nonfinite values")
                np.savez_compressed(out/f"outer_{outer:02d}_solution.npz",x1=x1,theta=theta,v=v,
                                    lambda_used=lam,rho=np.array([rho]))
                info.update(solution_loaded=True,model_objective=float(pyo.value(model.obj)))
            else:
                info.update(solution_loaded=False,solution_note="Model initialization is not a returned iterate")
            if ipopt_log.exists():
                text=ipopt_log.read_text(encoding="utf-8",errors="replace")
                found=re.findall(r"^Objective\.+:\s*([+\-\d.eE]+)\s+([+\-\d.eE]+)",text,re.MULTILINE)
                info["native_unscaled_objective"]=float(found[-1][1]) if found else None
                iters=re.findall(r"Number of Iterations\.\.\.\.:\s*(\d+)",text)
                info["ipopt_iterations"]=int(iters[-1]) if iters else None
                info["mumps_confirmed"]="linear solver MUMPS" in text
        except Exception as exc:
            info.update(solve_wall_seconds=time.time()-solve_t0,solver_exception=repr(exc),
                        solution_loaded=False,termination="EXCEPTION")
            (out/f"outer_{outer:02d}_exception.txt").write_text(traceback.format_exc(),encoding="utf-8")
    except Exception as exc:
        info.update(worker_exception=repr(exc),termination="EXCEPTION",solution_loaded=False)
        (out/f"outer_{outer:02d}_exception.txt").write_text(traceback.format_exc(),encoding="utf-8")
    info["worker_wall_seconds"]=time.time()-started
    dump(out/f"outer_{outer:02d}_native.json",info)
    print(json.dumps({"city":city,"config":config,"outer":outer,"termination":info.get("termination"),
                      "solution_loaded":info.get("solution_loaded"),"wall_seconds":info["worker_wall_seconds"]}))
    return 0 if "worker_exception" not in info and "solver_exception" not in info else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("city",choices=["SiouxFalls","Anaheim"])
    parser.add_argument("config",choices=list(CONFIGS));parser.add_argument("outer",type=int)
    args=parser.parse_args();sys.exit(main(args.city,args.config,args.outer))
