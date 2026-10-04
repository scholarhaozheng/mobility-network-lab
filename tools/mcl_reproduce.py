"""Pinned experiment entry points. Calls existing solvers; does not implement a solver."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
ADDITIONS = HERE.parent.parent
CATALOG = ADDITIONS / "experiments" / "catalog.json"
SCHEMA = "mcl_reproduce_run_v1"
VERIFIER_VERSION = "mcl_reproduce_verifier_v1.3"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rooted(root, rel):
    """Catalog references must stay inside the selected repository, including symlinks."""
    if Path(rel).is_absolute():
        raise ValueError("Catalog path must be repository-relative: " + rel)
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise ValueError("Catalog path escapes repository: " + rel)
    return p


def environment(required):
    result = {"python": platform.python_version(), "executable": sys.executable,
              "platform": platform.platform(), "packages": {}, "missing": []}
    if sys.version_info < (3, 10):
        result["missing"].append("Python >=3.10")
    for name in required:
        try:
            result["packages"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["missing"].append(name)
    return result


def preflight(root, entry):
    env = environment(entry["environment"]["packages"])
    checked, problems = [], []
    for item in entry["files"]:
        p = rooted(root, item["path"])
        actual = sha(p) if p.is_file() else None
        checked.append({"path": item["path"], "role": item["role"],
                        "expected_sha256": item["sha256"], "actual_sha256": actual})
        if actual != item["sha256"]:
            problems.append("Missing or changed pinned " + item["role"] + ": " + item["path"])
    problems.extend("Missing dependency: " + x for x in env["missing"])
    return {"status": "PASS" if not problems else "BLOCKED", "environment": env,
            "files": checked, "problems": problems}


def child_env():
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
                "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    return env


def execute(argv, cwd, output, name, kind, timeout):
    """Argument arrays only: no shell, no command interpolation."""
    log = output / (name + ".log")
    started = time.perf_counter()
    timed_out = False
    with log.open("w", encoding="utf-8") as f:
        try:
            p = subprocess.run([str(x) for x in argv], cwd=str(cwd), env=child_env(),
                               stdout=f, stderr=subprocess.STDOUT, text=True, shell=False,
                               timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            exit_code = p.returncode
        except subprocess.TimeoutExpired:
            exit_code, timed_out = 124, True
    return {"command": [str(x) for x in argv], "cwd": str(cwd), "kind": kind,
            "exit_code": exit_code, "seconds": time.perf_counter() - started,
            "timeout_seconds": timeout, "timed_out": timed_out, "log": log.name,
            "environment_overrides": {k: child_env()[k] for k in ["PYTHONDONTWRITEBYTECODE", "PYTHONUTF8", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]}}


def python_command(*args):
    return [sys.executable, "-B", "-X", "utf8", *args]


def invoke_solver(root, entry, out):
    p = entry["parameters"]
    timeout = entry["execution"]["timeout_seconds"]
    if entry["adapter"] == "registered_python_package":
        return [execute(python_command(rooted(root, p["script"]), "run", "--repo-root", root,
                        "--output", out / "solution", *p.get("arguments", [])),
                        root, out, "solve", "fresh_computation", timeout)]
    if entry["adapter"] == "boston_frozen_slsqp":
        return [execute(python_command(rooted(root, p["script"]), "--inputs", rooted(root, p["inputs"]),
                    "--pool", rooted(root, p["pool"]), "--config", rooted(root, p["config"]), "--out", out / "solution"),
                    root, out, "solve", "fresh_solve", timeout)]
    if entry["adapter"] == "sioux_public_fw":
        write_json(out / "config.json", p["config"])
        prepare = execute(python_command(rooted(root, p["script"]), "prepare", "--input", rooted(root, p["inputs"]),
                    "--demand", rooted(root, p["demand"]), "--config", out / "config.json", "--output", out / "prepared"),
                    root, out, "prepare", "input_preparation", 30)
        if prepare["exit_code"]:
            return [prepare]
        solve = execute(python_command(rooted(root, p["script"]), "solve", "--instance", out / "prepared", "--method", "fw",
                    "--config", out / "config.json", "--output", out / "solution"), root, out, "solve", "fresh_solve", timeout)
        return [prepare, solve]
    if entry["adapter"] == "hk10_public_arc_lp":
        return [execute(python_command(HERE, "_worker", entry["id"], "--repo-root", root, "--output", out),
                        root, out, "solve", "fresh_solve", timeout)]
    if entry["adapter"] == "boston_public_fw":
        return invoke_boston_fw(root, entry, out)
    if entry["adapter"] == "admm_public_control":
        return [execute(python_command(rooted(root, p["script"]), "--arc", rooted(root, p["arcs"]),
                        "--demand", rooted(root, p["demands"]), "--policy", rooted(root, p["policy"]),
                        "--variant", p["variant"], "--case", p["case"], "--output", out / "solution"),
                        root, out, "solve", "fresh_solve", timeout)]

    raise ValueError("Unknown adapter")


def hk_worker(root, entry, out):
    """The only glue needed by the existing function-only public LP entry point."""
    p = entry["parameters"]
    sys.path.insert(0, str(rooted(root, p["module_directory"])))
    module = importlib.import_module("external_sioux_static_to_dynamic")
    result = module.solve_small_subset_arc_lp(rows(rooted(root, p["arcs"])), rows(rooted(root, p["demands"])))
    target = out / "solution"
    target.mkdir()
    write_json(target / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ["positive_flows", "capacity_violations"]}, indent=2))
    return 0 if result.get("reference_status") == "REFERENCE_GENERATED" else 2


def numeric(values):
    result = [float(x) for x in values]
    if not all(math.isfinite(x) for x in result):
        raise ValueError("Nonfinite numerical output")
    return result


def verify_boston(root, entry, out):
    """No optimizer call: reconstruct primal feasibility, integral and pool Wardrop gap."""
    import numpy as np
    from scipy import sparse
    p, gates = entry["parameters"], entry["verification"]
    pool = rooted(root, p["pool"])
    links = rows(rooted(root, p["inputs"]) / "link.csv")
    demand = rows(rooted(root, p["inputs"]) / "demand.csv")
    paths = rows(pool / "path_pool.csv")
    flows = rows(out / "solution/full_path_flow.csv")
    volumes = rows(out / "solution/link_flow.csv")
    result = read_json(out / "solution/solver_result.json")
    if [r["path_id"] for r in flows] != [r["path_id"] for r in paths]:
        raise ValueError("Path IDs/order do not match frozen pool")
    if [r["link_id"] for r in volumes] != [r["link_id"] for r in links]:
        raise ValueError("Link IDs/order do not match frozen inputs")
    if any(int(r["path_index"]) != i or r["od_index"] != paths[i]["od_index"] for i, r in enumerate(flows)):
        raise ValueError("Path/OD index mismatch")
    if any(int(r["link_index"]) != i for i, r in enumerate(volumes)):
        raise ValueError("Link index mismatch")
    f = np.array(numeric(r["flow"] for r in flows))
    v = np.array(numeric(r["volume"] for r in volumes))
    q = np.array(numeric(r["volume"] for r in demand))
    A = sparse.load_npz(pool / "A_link_path.npz").tocsr()
    C = sparse.load_npz(pool / "C_od_path.npz").tocsr()
    if A.shape != (len(links), len(paths)) or C.shape != (len(demand), len(paths)):
        raise ValueError("Frozen matrix dimensions mismatch")
    reconstructed = np.asarray(A @ f).ravel()
    cap = np.maximum(np.array(numeric(r["capacity"] for r in links)), 1.0)
    t0 = np.array(numeric(r["vdf_fftt"] for r in links))
    alpha = np.array(numeric(r["vdf_alpha"] for r in links))
    beta = np.array(numeric(r["vdf_beta"] for r in links))
    safe_v = np.maximum(v, 0.0)
    objective = float(np.sum(t0 * safe_v + t0 * alpha / (beta + 1) * safe_v * (safe_v / cap) ** beta))
    cost = t0 * (1 + alpha * (safe_v / cap) ** beta)
    path_cost = np.asarray(A.T @ cost).ravel()
    shortest = sum(float(q[i]) * float(np.min(path_cost[C.getrow(i).indices])) for i in range(len(q)))
    denominator = max(float(v @ cost), 1e-12)
    gap = (denominator - shortest) / denominator
    reference = read_json(rooted(root, p["reference"]))["reported_objective"]
    metrics = {"objective_recomputed": objective, "objective_reported": float(result["reported_objective"]),
               "objective_reference": reference, "objective_reference_absolute_error": abs(objective - reference),
               "max_od_residual": float(np.max(np.abs(C @ f - q))),
               "max_link_reconstruction_error": float(np.max(np.abs(v - reconstructed))),
               "min_path_flow": float(f.min()), "min_link_flow": float(v.min()),
               "signed_pool_relative_gap": gap, "paths": len(f), "links": len(v), "od_pairs": len(q),
               "solver_status": result.get("status"), "solver_iterations": result.get("iterations")}
    checks = {"solver_success": result.get("status") == "success",
              "nonnegative": min(f.min(), v.min()) >= -gates["negative_flow_abs"],
              "od_balance": metrics["max_od_residual"] <= gates["od_balance_abs"],
              "link_reconstruction": metrics["max_link_reconstruction_error"] <= gates["link_reconstruction_abs"],
              "objective_recompute": abs(objective - float(result["reported_objective"])) <= gates["objective_abs"],
              "objective_reference": abs(objective - reference) <= gates["reference_objective_abs"],
              "pool_gap": abs(gap) <= gates["pool_relative_gap_abs"]}
    return metrics, {k: bool(v) for k, v in checks.items()}


def verify_sioux(root, entry, out):
    """Use the public path/OD/full-network verifier; validate local prepared files first."""
    p = entry["parameters"]
    manifest = read_json(out / "prepared/manifest.json")
    expected = {Path(x["path"]).name: x["sha256"] for x in entry["files"] if x["role"] == "solver_input"}
    if manifest["source_hashes"]["link"] != expected["link.csv"] or manifest["source_hashes"]["demand"] != expected["demand.csv"]:
        raise ValueError("Prepared input source hashes mismatch")
    record = read_json(out / "solution/run.json")
    if Path(record["instance_path"]).resolve() != (out / "prepared").resolve():
        raise ValueError("Public FW output refers to another prepared instance; keep the run at its recorded location")
    sys.path.insert(0, str(root / "tools"))
    module = importlib.import_module("mcl_assignment")
    result = module.verify(out / "solution")
    # This is a new run. The historical 100-iteration FW table is never read.
    minimum_path = numeric([result["min_path_flow_raw"]])[0]
    return result, {
        "public_independent_verifier": result.get("status") == "SOLVED_WITHIN_DECLARED_TOLERANCE",
        "path_flow_nonnegative": minimum_path >= -entry["verification"]["negative_flow_abs"],
    }


def verify_hk(root, entry, out):
    """No optimizer: independently accumulate exported commodity flows and capacities."""
    p, gates = entry["parameters"], entry["verification"]
    arcs = rows(rooted(root, p["arcs"]))
    demands = rows(rooted(root, p["demands"]))
    arc = {r["arc_id"]: r for r in arcs}
    demand = {r["demand_id"]: r for r in demands}
    if len(arc) != len(arcs) or len(demand) != len(demands):
        raise ValueError("Duplicate input identity")
    result = read_json(out / "solution/result.json")
    flow_rows = result.get("positive_flows", [])
    balance, loads, seen = defaultdict(float), defaultdict(float), set()
    objective, minimum = 0.0, 0.0
    for r in flow_rows:
        key = (r["demand_id"], r["arc_id"])
        if key in seen or key[0] not in demand or key[1] not in arc:
            raise ValueError("Duplicate or unknown commodity/arc output")
        seen.add(key)
        a = arc[key[1]]
        if a["arc_type"] == "source_connector" and key[1] != "source_" + key[0]:
            raise ValueError("Flow on another commodity's source connector")
        if a["arc_type"] == "sink_connector" and key[1].split("_")[1] != key[0]:
            raise ValueError("Flow on another commodity's sink connector")
        f = numeric([r["flow"]])[0]
        minimum = min(minimum, f)
        balance[(key[0], a["from_node_time_id"])] += f
        balance[(key[0], a["to_node_time_id"])] -= f
        loads[key[1]] += f
        objective += f * float(a.get("cost") or 0)
    for k, d in demand.items():
        sinks = {a["to_node_time_id"] for a in arcs if a["arc_type"] == "sink_connector" and a["arc_id"].split("_")[1] == k}
        if len(sinks) != 1:
            raise ValueError("Missing/ambiguous commodity sink")
        balance[(k, "source_" + k + "_t" + str(d.get("departure_time", 0)))] -= float(d["volume"])
        balance[(k, next(iter(sinks)))] += float(d["volume"])
    excess = max([0.0] + [loads[k] - float(a.get("capacity") or "inf") for k, a in arc.items()])
    residual = max([0.0] + [abs(x) for x in balance.values()])
    reference = read_json(rooted(root, p["reference"]))
    ref = float(reference["objective_value"])
    reported = float(result.get("objective_value", math.inf))
    metrics = {"objective_recomputed": objective, "objective_reported": reported,
               "reference_objective": ref, "objective_reference_absolute_error": abs(objective - ref),
               "max_commodity_balance_residual": residual, "max_capacity_excess": excess,
               "minimum_exported_flow": minimum, "positive_flow_rows": len(flow_rows),
               "dynamic_arcs": len(arcs), "commodities": len(demands),
               "export_contract": "The unchanged public solver exports flow >1e-8; omitted entries are treated as zero. Checks apply to this exported feasible point, not an unavailable raw vector or new dual certificate."}
    checks = {"solver_success": result.get("reference_status") == "REFERENCE_GENERATED" and result.get("linprog_status") == 0,
              "nonnegative_export": minimum >= -gates["negative_flow_abs"],
              "commodity_balance": residual <= gates["balance_abs"], "capacity": excess <= gates["capacity_abs"],
              "objective_recompute": abs(objective - reported) <= gates["objective_abs"],
              "reference_objective": abs(objective - ref) <= gates["reference_objective_abs"]}
    return metrics, checks


def invoke_boston_fw(root, entry, out):
    """Call the published preparation/FW implementation without changing its numerical code."""
    p = entry["parameters"]
    config = read_json(rooted(root, p["config_path"]))
    # Only scenario prose is corrected; every numerical field remains byte-source derived.
    config["scenario"] = p["scenario_label"]
    write_json(out / "config.json", config)
    prep = execute(python_command(rooted(root, p["script"]), "prepare", "--input", rooted(root, p["inputs"]),
                   "--demand", rooted(root, p["demand"]), "--config", out / "config.json", "--output", out / "prepared"),
                   root, out, "prepare", "input_preparation", 30)
    if prep["exit_code"]:
        return [prep]
    solve = execute(python_command(rooted(root, p["script"]), "solve", "--instance", out / "prepared", "--method", "fw",
                    "--config", out / "config.json", "--output", out / "solution"),
                    root, out, "solve", "fresh_solve", entry["execution"]["timeout_seconds"])
    return [prep, solve]


def verify_boston_fw(root, entry, out):
    """Recompute primal/gap checks and compare each original saved physical-link flow."""
    p, gates = entry["parameters"], entry["verification"]
    config = read_json(rooted(root, p["config_path"]))
    config["scenario"] = p["scenario_label"]
    if read_json(out / "config.json") != config:
        raise ValueError("Effective configuration differs from pinned numerical configuration")
    manifest = read_json(out / "prepared/manifest.json")
    pinned = {x["path"]: x["sha256"] for x in entry["files"]}
    if (manifest["source_hashes"]["link"] != pinned[p["inputs"] + "/link.csv"] or
            manifest["source_hashes"]["demand"] != pinned[p["demand"]] or
            manifest["source_hashes"]["config"] != sha(out / "config.json")):
        raise ValueError("Prepared source/configuration hashes mismatch")
    if (manifest["scenario"] != p["scenario_label"] or manifest["period_hours"] != 2 or
            manifest["capacity_basis"] != "effective_period_pce" or manifest["pce_factor"] != 1 or
            manifest["demand_unit_input"] != "vehicle_trips_per_period" or
            manifest["assignment_unit"] != "pce_per_declared_period"):
        raise ValueError("Boston scenario or two-hour effective-capacity contract mismatch")
    record = read_json(out / "solution/run.json")
    if record["method"] != "fw" or Path(record["instance_path"]).resolve() != (out / "prepared").resolve():
        raise ValueError("FW output refers to a different method or prepared instance")
    sys.path.insert(0, str(root / "tools"))
    module = importlib.import_module("mcl_assignment")
    result = module.verify(out / "solution")
    current_rows = rows(out / "solution/link_flow.csv")
    source_rows = rows(rooted(root, p["inputs"]) / "link.csv")
    reference_rows = rows(rooted(root, p["reference"]))
    current = {row["link_id"]: numeric([row["flow_pce_per_period"]])[0] for row in current_rows}
    reference = {row["link_id"]: numeric([row["volume"]])[0] for row in reference_rows}
    source = {row["link_id"]: row for row in source_rows}
    if (len(current) != len(current_rows) or len(reference) != len(reference_rows) or
            len(source) != len(source_rows) or set(current) != set(reference) or set(current) != set(source)):
        raise ValueError("Original reference, input and output physical-link identities differ")
    def integral(flow):
        terms = []
        for key, v in flow.items():
            row = source[key]
            t0, alpha, beta, cap = numeric(row[k] for k in ["vdf_fftt", "vdf_alpha", "vdf_beta", "capacity"])
            if v < -gates["negative_flow_abs"] or cap <= 0:
                raise ValueError("Negative reference/output flow or nonpositive effective capacity")
            v = max(v, 0.0)
            terms.append(t0 * v + t0 * alpha / (beta + 1) * v * (v / cap) ** beta)
        return math.fsum(terms)
    ref_obj, new_obj = integral(reference), integral(current)
    delta = [abs(current[key] - reference[key]) for key in current]
    result.update({"scenario": p["scenario_id"], "period_hours": 2,
                   "capacity_basis": "effective_period_pce", "pce_factor": 1,
                   "flow_unit": "PCE per declared two-hour period",
                   "objective_independent_integral": new_obj, "objective_original_reference": ref_obj,
                   "reference_objective_absolute_error": abs(new_obj - ref_obj),
                   "reference_max_link_flow_error": max(delta), "reference_link_flow_l1_error": math.fsum(delta),
                   "solver_iterations": record["iterations"], "reference_links": len(reference)})
    checked = numeric(result[k] for k in ["min_path_flow_raw", "min_link_flow_raw", "max_od_residual",
                      "od_residual_l1", "demand_pce", "max_link_reconstruction_error", "full_network_relative_gap",
                      "objective_checked", "objective_reported"])
    minimum_path, minimum_link, max_od, od_l1, demand, reconstruction, gap, objective, reported = checked
    checks = {"public_independent_verifier": result.get("status") == "SOLVED_WITHIN_DECLARED_TOLERANCE",
              "path_flow_nonnegative": minimum_path >= -gates["negative_flow_abs"],
              "link_flow_nonnegative": minimum_link >= -gates["negative_flow_abs"],
              "od_balance_absolute": max_od <= gates["max_od_error_abs"],
              "od_balance_relative_l1": od_l1 / max(demand, 1e-12) <= gates["total_od_l1_rel"],
              "link_reconstruction": reconstruction <= gates["link_reconstruction_abs"],
              "full_network_gap": abs(gap) <= gates["full_relative_gap_abs"],
              "objective_integral": abs(new_obj - objective) <= gates["objective_abs"],
              "reported_objective": abs(new_obj - reported) <= gates["objective_abs"],
              "original_reference_objective": abs(new_obj - ref_obj) <= gates["reference_objective_abs"],
              "original_reference_link_flows": max(delta) <= gates["reference_link_flow_abs"],
              "case_dimensions": result["od_pairs"] == 26 and result["physical_links"] == 5091,
              "case_demand": abs(demand - p["expected_demand_pce"]) <= gates["max_od_error_abs"]}
    return result, checks



def verify_admm_control(root, entry, out):
    """Evaluate the public authored control without optimization or city-result claims."""
    import numpy as np
    p, gates = entry["parameters"], entry["verification"]
    sys.path.insert(0, str(rooted(root, p["module_directory"])))
    evaluator = importlib.import_module("independent_admm_evaluator")
    policy = read_json(rooted(root, p["policy"]))
    result = read_json(out / "solution/result.json")
    with np.load(out / "solution/state.npz", allow_pickle=False) as state:
        if not all(np.all(np.isfinite(state[k])) for k in ("x", "z", "w", "z_previous", "local_q", "potential")):
            raise ValueError("Nonfinite ADMM state or potential")
    metrics = evaluator.evaluate_files(rooted(root, p["arcs"]), rooted(root, p["demands"]), out / "solution", policy)
    value = numeric([metrics.get("objective", math.inf)])[0]
    metrics["exact_control_objective"] = gates["expected_objective"]
    metrics["exact_control_objective_absolute_error"] = abs(value - gates["expected_objective"])
    checks = {"solver_success": result.get("status") == "SOLVER_CONVERGED",
              "control_identity": result.get("method") == "full_arc_consensus_admm_r2" and result.get("variant") == p["variant"] and result.get("case") == p["case"] and result.get("arc_count") == gates["expected_arc_count"] and result.get("commodity_count") == gates["expected_commodity_count"],
              "independent_public_evaluator": metrics.get("status") == "PASS" and bool(metrics.get("gates")) and all(metrics["gates"].values()),
              "evaluator_solver_free": metrics.get("optimizer_calls") == 0,
              "exact_control_objective": metrics["exact_control_objective_absolute_error"] <= gates["expected_objective_abs"]}
    return metrics, checks




def verify_registered_package(root, entry, out):
    """Run the pinned package verifier afresh; never accept its saved PASS marker."""
    p = entry["parameters"]
    report = rooted(out / "solution", p.get("verification_report", "verification.json"))
    if report.exists():
        report.unlink()
    command = python_command(rooted(root, p["script"]), "verify", "--repo-root", root,
                             "--run", out / "solution", *p.get("arguments", []))
    completed = subprocess.run([str(x) for x in command], cwd=str(root), env=child_env(),
                               capture_output=True, text=True, shell=False,
                               timeout=entry["execution"].get("verification_timeout_seconds", 120),
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if completed.returncode or not report.is_file():
        raise ValueError("Package independent verification failed: " +
                         (completed.stderr or completed.stdout)[-3000:])
    result = read_json(report)
    raw_checks = result.get("checks")
    if isinstance(raw_checks, list):
        if not raw_checks or any(not isinstance(c, dict) or not isinstance(c.get("pass"), bool)
                                 or not isinstance(c.get("name"), str) for c in raw_checks):
            raise ValueError("Malformed package numerical checks")
        names = [c["name"] for c in raw_checks]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate package check identities")
        checks = {"package_" + c["name"]: c["pass"] for c in raw_checks}
    elif isinstance(raw_checks, dict) and raw_checks and all(isinstance(v, bool) for v in raw_checks.values()):
        checks = {"package_" + k: v for k, v in raw_checks.items()}
    else:
        raise ValueError("Missing package numerical checks")
    checks["package_success"] = result.get("success") is True
    checks["package_solver_free"] = result.get("optimizer_calls") == 0
    metrics = result.get("metrics", {})
    if not isinstance(metrics, dict):
        raise ValueError("Package metrics must be an object")
    metrics["independent_package_checks"] = len(raw_checks)
    return metrics, checks


def artifacts(out):
    # Run/verification metadata and the public FW verifier's own derivative are excluded.
    return {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob("*"))
            if p.is_file() and p != out / "run.json" and p.name != "verification.json" and not p.name.endswith(".partial")}


def verify(root, entry, out):
    started = time.perf_counter()
    checks, metrics, errors, record = {}, {}, [], {}
    try:
        record = read_json(out / "run.json")
        checks["run_identity"] = record.get("experiment_id") == entry["id"] and record.get("catalog_entry_sha256") == signature(entry)
        if not checks["run_identity"]:
            raise ValueError("Run ID/catalog definition mismatch")
        pf = preflight(root, entry)
        checks["pinned_source_and_inputs"] = pf["status"] == "PASS"
        if not checks["pinned_source_and_inputs"]:
            raise ValueError("; ".join(pf["problems"]))
        recorded = record.get("artifacts", {})
        checks["output_integrity"] = bool(recorded) and all(rooted(out, p).is_file() and sha(rooted(out, p)) == h for p, h in recorded.items())
        if not checks["output_integrity"]:
            raise ValueError("Recorded output artifact missing or changed")
        checks["solver_command_exit"] = bool(record.get("executed_runs")) and all(r["exit_code"] == 0 for r in record["executed_runs"])
        fn = {"boston_frozen_slsqp": verify_boston, "sioux_public_fw": verify_sioux, "hk10_public_arc_lp": verify_hk, "boston_public_fw": verify_boston_fw, "admm_public_control": verify_admm_control, "registered_python_package": verify_registered_package}[entry["adapter"]]
        metrics, numerical = fn(root, entry, out)
        checks.update(numerical)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    result = {"schema": "mcl_reproduce_verification_v1", "experiment_id": entry["id"],
              "status": "PASS" if checks and all(checks.values()) and not errors else "FAIL",
              "optimizer_calls": 0, "checks": checks, "metrics": metrics, "errors": errors,
              "tolerances": entry["verification"], "claim_boundary": entry["claim_boundary"],
              "verifier_version": VERIFIER_VERSION, "verifier_cli_sha256": sha(HERE),
              "run_cli_sha256": record.get("cli_sha256"),
              "verifier_command": [sys.executable, *sys.argv], "verification_seconds": time.perf_counter() - started}
    write_json(out / "verification.json", result)
    return result


def run(root, entry, out):
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Output must be a new or empty directory; existing content will not be overwritten")
    # Never allow the output to replace an input or source subtree.
    for item in entry["files"]:
        p = rooted(root, item["path"])
        if p == out or p.is_relative_to(out):
            raise ValueError("Output contains a pinned source/input path")
    out.mkdir(parents=True, exist_ok=True)
    pf = preflight(root, entry)
    write_json(out / "preflight.json", pf)
    record = {"schema": SCHEMA, "experiment_id": entry["id"], "status": "RUNNING",
              "started_at": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
              "repository_root": str(root), "baseline_commit": entry["baseline_commit"],
              "catalog_entry_sha256": signature(entry), "cli_sha256": sha(HERE),
              "environment": pf["environment"], "input_and_source_hashes": pf["files"],
              "configuration": entry["parameters"], "claim_boundary": entry["claim_boundary"], "executed_runs": []}
    write_json(out / "run.json", record)
    if pf["status"] != "PASS":
        record["status"] = "BLOCKED"
        record["errors"] = pf["problems"]
        write_json(out / "run.json", record)
        write_json(out / "verification.json", {"status": "NOT_RUN", "optimizer_calls": 0, "errors": pf["problems"]})
        return 2
    started = time.perf_counter()
    try:
        record["executed_runs"] = invoke_solver(root, entry, out)
    except Exception as exc:
        record["execution_error"] = f"{type(exc).__name__}: {exc}"
    record["seconds"] = time.perf_counter() - started
    record["artifacts"] = artifacts(out)
    record["status"] = "EXECUTED_AWAITING_VERIFICATION"
    write_json(out / "run.json", record)
    result = verify(root, entry, out)
    record["status"] = "FRESH_REPRODUCED" if result["status"] == "PASS" else "NOT_ACCEPTED"
    record["verification_status"] = result["status"]
    record["metrics"] = result["metrics"]
    write_json(out / "run.json", record)
    print(json.dumps({"id": entry["id"], "status": record["status"], "output": str(out), "metrics": result["metrics"], "errors": result["errors"]}, indent=2))
    return 0 if result["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="List available pinned computational instances")
    for action in ["describe", "run", "verify", "_worker"]:
        p = sub.add_parser(action, help=argparse.SUPPRESS if action == "_worker" else None)
        p.add_argument("id")
        p.add_argument("--repo-root", type=Path, default=ADDITIONS, help="Repository containing the unchanged public source/data")
        if action in ["run", "_worker"]:
            p.add_argument("--output", type=Path, required=True)
        if action == "verify":
            p.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    catalog = read_json(CATALOG)
    entries = {e["id"]: e for e in catalog["experiments"]}
    if args.action == "list":
        print(json.dumps([{"id": e["id"], "title": e["title"], "contract": e["contract"]} for e in entries.values()], indent=2, ensure_ascii=False))
        return 0
    if args.id not in entries:
        parser.error("Unknown experiment ID; use list")
    entry = entries[args.id]
    root = args.repo_root.resolve()
    if args.action == "describe":
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0
    if args.action == "_worker":
        if entry["adapter"] != "hk10_public_arc_lp":
            raise ValueError("Internal worker is for the HK function adapter only")
        pf = preflight(root, entry)
        if pf["status"] != "PASS":
            raise ValueError("Worker preflight failed")
        return hk_worker(root, entry, args.output.resolve())
    if args.action == "run":
        return run(root, entry, args.output.resolve())
    out = args.run.resolve()
    if not (out / "run.json").is_file():
        raise ValueError("Missing run.json")
    result = verify(root, entry, out)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
