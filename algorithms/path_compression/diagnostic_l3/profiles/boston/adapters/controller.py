"""Monitor two bounded native Boston L3 ALM sequences, one solver at a time."""
from __future__ import annotations

import ctypes
import datetime
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import numpy as np

from common import IPOPT, IPOPT_OPTIONS, PYTHON, ROOT, SOURCE, dump, sha

MAX_INNER_SECONDS = 600
MAX_RANK_SECONDS = 1500
MAX_TOTAL_HEAVY_SECONDS = 2700
MAX_OUTER = 8
MAX_NEW_ARTIFACT_BYTES = 2*1024**3


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def available_physical_bytes():
    state = MEMORYSTATUSEX()
    state.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    return int(state.ullAvailPhys) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)) else None


def tree_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def sample_processes(worker_pid, started_iso):
    command = (f"$cut=[datetime]'{started_iso}'; "
               f"Get-Process -Name python,ipopt -ErrorAction SilentlyContinue | "
               f"Where-Object {{$_.Id -eq {worker_pid} -or ($_.ProcessName -eq 'ipopt' -and $_.StartTime -ge $cut)}} | "
               "Select-Object Id,ProcessName,WorkingSet64,PeakWorkingSet64,PrivateMemorySize64,StartTime | ConvertTo-Json -Compress")
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, timeout=10)
        return json.loads(result.stdout) if result.stdout.strip() else []
    except Exception as exc:
        return {"sample_error": repr(exc)}


def stop_own_tree(pid):
    return subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                          capture_output=True, text=True, timeout=20)


def monitored_worker(command, log, timeout, rank, outer, kind, env):
    started = time.perf_counter()
    started_iso = datetime.datetime.now().isoformat()
    with log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
        next_sample = 0.0
        low_memory_samples = 0
        stop_reason = None
        while process.poll() is None:
            elapsed = time.perf_counter() - started
            if elapsed >= timeout:
                stop_reason = "TIME_BUDGET_EXHAUSTED_OWN_PROCESS_TREE_STOPPED"
                stop_own_tree(process.pid)
                break
            if elapsed >= next_sample:
                available = available_physical_bytes()
                sample = dict(timestamp=datetime.datetime.now().isoformat(), kind=kind,
                              rank=rank, outer=outer, worker_pid=process.pid,
                              elapsed_seconds=elapsed, available_physical_bytes=available,
                              sampled_processes=sample_processes(process.pid, started_iso),
                              measurement_note="Sampled working set/private bytes; short peaks may be missed.")
                with (ROOT / "checks" / "RESOURCE_SAMPLES.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(sample, default=str) + "\n")
                low_memory_samples = low_memory_samples+1 if available is not None and available < 100*1024**2 else 0
                if low_memory_samples >= 2:
                    stop_reason = "AVAILABLE_MEMORY_UNDER_100_MIB_TWICE_OWN_TREE_STOPPED"
                    stop_own_tree(process.pid)
                    break
                next_sample = elapsed + 10.0
            time.sleep(0.5)
        try:
            code = process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            stop_own_tree(process.pid)
            code = None
    return dict(return_code=code, wall_seconds=time.perf_counter()-started,
                stop_reason=stop_reason, worker_pid=process.pid, timeout_seconds=timeout)


def environment():
    if Path.cwd().resolve() != ROOT.resolve() or (ROOT / "ipopt.opt").exists():
        raise RuntimeError("controller must run in new task root without ipopt.opt")
    for rank in (26, 52):
        p = ROOT / "checks" / f"preflight_rank{rank}.json"
        if not p.exists() or not json.loads(p.read_text(encoding="utf-8"))["accepted_pre_solve"]:
            raise RuntimeError(f"rank {rank} preflight not accepted")
    if sha(SOURCE) != "27644472699b1c93f9795b6a7940928c4935e43a2a062c96a6f7a682df8208b5":
        raise RuntimeError("source identity changed")
    if not PYTHON.is_file() or not IPOPT.is_file():
        raise RuntimeError("native Python or IPOPT path missing")
    opts = subprocess.run([str(IPOPT), "--print-options"], capture_output=True, text=True, timeout=30)
    option_names = [name for name in IPOPT_OPTIONS if name not in opts.stdout]
    if opts.returncode != 0 or option_names:
        raise RuntimeError(f"native IPOPT option support unresolved: {option_names}")
    env = os.environ.copy()
    env["PATH"] = str(IPOPT.parent) + os.pathsep + str(PYTHON.parent / "Scripts") + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["OMP_NUM_THREADS"] = "2"
    env["OPENBLAS_NUM_THREADS"] = "2"
    env["MKL_NUM_THREADS"] = "2"
    env["NUMEXPR_NUM_THREADS"] = "2"
    for key in ("TMP", "TEMP", "TMPDIR", "MPLCONFIGDIR"):
        env[key] = str(ROOT / "tmp")
    (ROOT / "tmp").mkdir(parents=True, exist_ok=True)
    import pyomo
    import numpy
    import scipy
    report = dict(python=str(PYTHON), python_version=sys.version, pyomo_version=pyomo.__version__,
                  numpy_version=numpy.__version__, scipy_version=scipy.__version__,
                  ipopt=str(IPOPT), ipopt_version=subprocess.run([str(IPOPT), "-v"], capture_output=True, text=True, timeout=10).stdout.strip(),
                  ipopt_options_supported=True, ipopt_options=IPOPT_OPTIONS,
                  source_sha256=sha(SOURCE), cwd=str(ROOT), temp=str(ROOT / "tmp"),
                  initial_available_physical_bytes=available_physical_bytes(),
                  max_inner_seconds=MAX_INNER_SECONDS, max_rank_seconds=MAX_RANK_SECONDS,
                  max_total_heavy_seconds=MAX_TOTAL_HEAVY_SECONDS,
                  max_new_artifact_bytes=MAX_NEW_ARTIFACT_BYTES)
    dump(ROOT / "checks" / "ENVIRONMENT.json", report)
    return env


def run_rank(rank, total_heavy, env):
    out = ROOT / "runs" / f"rank{rank}"
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise RuntimeError(f"rank {rank} already has artifacts; inspect before a new sequence")
    lam = np.zeros(26)
    rho = 10.0
    history = []
    rank_start = time.perf_counter()
    status = "STARTED"
    accepted_outer = None
    dump(out / "CONFIG.json", dict(rank=rank, gamma=0.0, level=3, initial_lambda=lam.tolist(),
                                   initial_rho=rho, max_outer=MAX_OUTER, options=IPOPT_OPTIONS,
                                   initialization="source reference rebuilt each outer",
                                   saved_basis=f"inputs_snapshot/bases/rank{rank}.npz"))
    for outer in range(1, MAX_OUTER+1):
        remaining = min(MAX_INNER_SECONDS, MAX_RANK_SECONDS-(time.perf_counter()-rank_start),
                        MAX_TOTAL_HEAVY_SECONDS-total_heavy)
        if remaining <= 0:
            status = "TIME_BUDGET_EXHAUSTED"
            break
        if tree_bytes(ROOT) > MAX_NEW_ARTIFACT_BYTES:
            status = "OUTPUT_BUDGET_EXHAUSTED"
            break
        np.savez_compressed(out / f"outer_{outer:02d}_state.npz", lambda_used=lam, rho=np.array([rho]))
        command = [str(PYTHON), "-u", "-B", str(ROOT / "adapters" / "run_inner.py"),
                   "--rank", str(rank), "--outer", str(outer)]
        print(f"START rank={rank} outer={outer} rho={rho} timeout={remaining:.1f}s", flush=True)
        monitor = monitored_worker(command, out / f"outer_{outer:02d}_controller.log",
                                   remaining, rank, outer, "native_inner", env)
        total_heavy += monitor["wall_seconds"]
        native_path = out / f"outer_{outer:02d}_native.json"
        record = dict(outer=outer, rho=rho, lambda_before=lam.tolist(), monitor=monitor,
                      native_record_present=native_path.exists())
        if native_path.exists():
            record["native"] = json.loads(native_path.read_text(encoding="utf-8"))
        if monitor["stop_reason"]:
            status = monitor["stop_reason"]
            history.append(record)
            break
        if not native_path.exists():
            status = "WORKER_NO_NATIVE_RECORD"
            history.append(record)
            break
        native = record["native"]
        if not native.get("solution_loaded"):
            status = "NATIVE_NO_RETURNED_ITERATE"
            history.append(record)
            break
        checker = [str(PYTHON), "-u", "-B", str(ROOT / "checks" / "check_returned.py"),
                   "--rank", str(rank), "--outer", str(outer)]
        try:
            check_process = subprocess.run(checker, cwd=str(ROOT), env=env,
                                           capture_output=True, text=True, timeout=120)
            (out / f"outer_{outer:02d}_checker_stdout_stderr.log").write_text(
                check_process.stdout+check_process.stderr, encoding="utf-8")
        except subprocess.TimeoutExpired as exc:
            status = "CHECKER_TIMEOUT"
            history.append(record)
            break
        check_path = out / f"outer_{outer:02d}_check.json"
        if check_process.returncode != 0 or not check_path.exists():
            status = "CHECKER_FAILED"
            record["checker_return_code"] = check_process.returncode
            history.append(record)
            break
        check = json.loads(check_path.read_text(encoding="utf-8"))
        record["check_summary"] = dict(status=check["status"], numerical_feasibility_pass=check["numerical_feasibility_pass"],
                                       public_eligibility_pass=check["public_eligibility_pass"],
                                       raw_stats=check["raw_stats"], gaps=check["gaps"])
        history.append(record)
        dump(out / "control_history.json", history)
        print(f"RESULT rank={rank} outer={outer} native={native.get('termination')} OD={check['raw_stats']['max_abs_OD_residual']:.9g} "
              f"full_RG={check['gaps']['full_network_relative_gap']:.9g} status={check['status']}", flush=True)
        if check["numerical_feasibility_pass"]:
            status = "NUMERICAL_ACCEPTED_AND_PUBLIC_ELIGIBLE" if check["public_eligibility_pass"] else "FEASIBLE_REDUCED_APPROXIMATION"
            accepted_outer = outer
            break
        if native.get("solver_status") != "ok" or native.get("termination") != "optimal":
            status = "NONOPTIMAL_INNER_TERMINATION"
            break
        if not check["criteria"]["native_objective_decomposition"] or not check["criteria"]["pyomo_objective_decomposition"]:
            status = "OBJECTIVE_AUDIT_FAILED"
            break
        residual = np.load(out / f"outer_{outer:02d}_od_residual.npy", allow_pickle=False)
        lam = lam + rho*residual
        rho *= 2.0
    else:
        status = "MAX_OUTER_NUMERICAL_CRITERIA_NOT_MET"
    final = dict(rank=rank, status=status, accepted_outer=accepted_outer,
                 attempted_outers=len(history), rank_wall_seconds=time.perf_counter()-rank_start,
                 total_heavy_seconds_after=total_heavy)
    dump(out / "status.json", final)
    dump(out / "control_history.json", history)
    print(f"END rank={rank} status={status}", flush=True)
    return final, total_heavy


def main():
    env = environment()
    statuses = {}
    total_heavy = 0.0
    for rank in (26, 52):
        status, total_heavy = run_rank(rank, total_heavy, env)
        statuses[str(rank)] = status
    dump(ROOT / "checks" / "CONTROLLER_SUMMARY.json",
         dict(statuses=statuses, total_heavy_seconds=total_heavy,
              output_bytes=tree_bytes(ROOT)))
    print(json.dumps({k:v["status"] for k,v in statuses.items()}, indent=2), flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Opt-in Boston native Diagnostic L3 controller. Requires staged fresh run root and native Pyomo/IPOPT/MUMPS environment.")
    parser.add_argument("--execute-native", action="store_true", help="explicitly authorize a NEW native solver run")
    args = parser.parse_args()
    if not args.execute_native:
        parser.error("native solve is opt-in; use tools/mcl_results.py for saved inspection")
    main()
