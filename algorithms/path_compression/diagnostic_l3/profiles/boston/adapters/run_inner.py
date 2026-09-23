"""Execute exactly one native Pyomo/IPOPT Diagnostic L3 ALM inner solve."""
from __future__ import annotations

import argparse
import contextlib
import json
import re
import time
import traceback
from pathlib import Path

import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

from common import IPOPT, IPOPT_OPTIONS, ROOT, SOURCE, build_native_l3, dump, load_case, model_counts, sha


def main(rank, outer):
    if Path.cwd().resolve() != ROOT.resolve():
        raise RuntimeError("worker cwd must be task root")
    if (ROOT / "ipopt.opt").exists():
        raise RuntimeError("task root contains inherited ipopt.opt")
    out = ROOT / "runs" / f"rank{rank}"
    out.mkdir(parents=True, exist_ok=True)
    record_path = out / f"outer_{outer:02d}_native.json"
    if record_path.exists():
        raise RuntimeError("existing native record would be overwritten")
    state_path = out / f"outer_{outer:02d}_state.npz"
    with np.load(state_path, allow_pickle=False) as state:
        lam = np.array(state["lambda_used"], dtype=float)
        rho = float(state["rho"][0])
    if lam.shape != (26,) or not np.isfinite(lam).all() or not np.isfinite(rho):
        raise ValueError("invalid ALM state")
    started = time.perf_counter()
    info = dict(rank=rank, outer=outer, rho=rho, gamma=0.0, lambda_used=lam.tolist(),
                source_sha256=sha(SOURCE), cwd=str(Path.cwd()),
                temp=str(Path(__import__("os").environ["TEMP"])),
                python=str(__import__("sys").executable), ipopt_executable=str(IPOPT),
                ipopt_options=IPOPT_OPTIONS, task_root_ipopt_opt_present=False)
    try:
        data, comp, extra = load_case(rank)
        build_start = time.perf_counter()
        model, _, adaptation = build_native_l3(data, comp, rho, lam)
        info["model_build_seconds"] = time.perf_counter() - build_start
        info["builder_adaptation"] = adaptation
        counts = model_counts(model, comp, data)
        info["model_counts"] = counts
        if counts["total_native_variables"] != 5091+26+rank or counts["total_active_constraints"] != 5195:
            raise AssertionError("native model size changed")
        if any(model.v[a].lb != 0.0 for a in model.LINKS):
            raise AssertionError("zero link bound not applied")
        if any(not model.link_con[a].active for a in model.LINKS) or any(not model.minor_con[i].active for i in model.MINOR):
            raise AssertionError("L3 constraints inactive")
        x1_init = np.array([pyo.value(model.x1[p]) for p in model.MAJOR], dtype=float)
        theta_init = np.array([pyo.value(model.theta[j]) for j in model.LATENT], dtype=float)
        v_init = np.array([pyo.value(model.v[a]) for a in model.LINKS], dtype=float)
        info["initialization"] = dict(major_min=float(np.min(x1_init)), theta_max_abs=float(np.max(np.abs(theta_init))),
                                       explicit_link_min=float(np.min(v_init)), explicit_link_max=float(np.max(v_init)),
                                       max_abs_link_equality_residual=float(np.max(np.abs(v_init-(comp["B1"].T@x1_init+comp["D"]@theta_init)))))
        if outer == 1:
            np.savez_compressed(out / "initial_values.npz", x1=x1_init, theta=theta_init, v=v_init,
                                f_major=x1_init, f_minor=comp["U_r"]@theta_init)
            dump(out / "model_counts.json", counts)
            dump(out / "initialization.json", info["initialization"])
        solver = SolverFactory("ipopt", executable=str(IPOPT))
        if not solver.available(exception_flag=False):
            raise RuntimeError("native IPOPT backend unavailable")
        solver.options.update(IPOPT_OPTIONS)
        stdout_path = out / f"outer_{outer:02d}_stdout_stderr.log"
        ipopt_log = out / f"outer_{outer:02d}_ipopt.log"
        solve_start = time.perf_counter()
        try:
            with stdout_path.open("w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                print(f"Native Boston Diagnostic L3 rank={rank} outer={outer} rho={rho} gamma=0", flush=True)
                print(json.dumps(IPOPT_OPTIONS, sort_keys=True), flush=True)
                results = solver.solve(model, tee=True, logfile=str(ipopt_log),
                                       load_solutions=False, keepfiles=False,
                                       symbolic_solver_labels=False)
            info.update(solve_wall_seconds=time.perf_counter()-solve_start,
                        solver_status=str(results.solver.status),
                        termination=str(results.solver.termination_condition),
                        solver_message=str(results.solver.message),
                        solution_records=len(results.solution))
            if len(results.solution) > 0:
                model.solutions.load_from(results)
                x1 = np.array([pyo.value(model.x1[p]) for p in model.MAJOR], dtype=float)
                theta = np.array([pyo.value(model.theta[j]) for j in model.LATENT], dtype=float)
                v = np.array([pyo.value(model.v[a]) for a in model.LINKS], dtype=float)
                if not (np.isfinite(x1).all() and np.isfinite(theta).all() and np.isfinite(v).all()):
                    raise ValueError("returned values are nonfinite")
                np.savez_compressed(out / f"outer_{outer:02d}_solution.npz", x1=x1, theta=theta, v=v,
                                    lambda_used=lam, rho=np.array([rho]))
                info.update(solution_loaded=True, model_objective=float(pyo.value(model.obj)))
            else:
                info.update(solution_loaded=False, solution_note="initialization is not a returned iterate")
        except Exception as exc:
            info.update(solve_wall_seconds=time.perf_counter()-solve_start,
                        solver_exception=repr(exc), termination="EXCEPTION", solution_loaded=False)
            (out / f"outer_{outer:02d}_exception.txt").write_text(traceback.format_exc(), encoding="utf-8")
        if ipopt_log.exists():
            contents = ipopt_log.read_text(encoding="utf-8", errors="replace")
            objectives = re.findall(r"^Objective\.+:\s*([+\-\d.eE]+)\s+([+\-\d.eE]+)", contents, re.MULTILINE)
            iterations = re.findall(r"Number of Iterations\.\.\.\.:\s*(\d+)", contents)
            seconds = re.findall(r"Total seconds in IPOPT\s*=\s*([\d\.]+)", contents)
            info.update(native_unscaled_objective=float(objectives[-1][1]) if objectives else None,
                        ipopt_iterations=int(iterations[-1]) if iterations else None,
                        ipopt_reported_seconds=float(seconds[-1]) if seconds else None,
                        mumps_confirmed="linear solver MUMPS" in contents,
                        ipopt_opt_file_used=None)
    except Exception as exc:
        info.update(worker_exception=repr(exc), termination="EXCEPTION", solution_loaded=False)
        (out / f"outer_{outer:02d}_exception.txt").write_text(traceback.format_exc(), encoding="utf-8")
    info["worker_wall_seconds"] = time.perf_counter() - started
    dump(record_path, info)
    print(json.dumps({"rank": rank, "outer": outer, "termination": info.get("termination"),
                      "solution_loaded": info.get("solution_loaded"),
                      "worker_wall_seconds": info["worker_wall_seconds"]}), flush=True)
    return 0 if "worker_exception" not in info and "solver_exception" not in info else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, choices=(26, 52), required=True)
    ap.add_argument("--outer", type=int, required=True)
    args = ap.parse_args()
    raise SystemExit(main(args.rank, args.outer))
