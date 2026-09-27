"""Solver-free R5 receiver/public bundle audit; standard library only."""
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def verify():
    failures = []
    def check(name, ok):
        if not ok: failures.append(name)
    hashes = load(ROOT / "HASH_MANIFEST.json")
    actual_files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p != ROOT / "HASH_MANIFEST.json"}
    check("package_file_inventory", actual_files == set(hashes))
    for rel, expected in hashes.items():
        p = ROOT / rel
        check("hash:" + rel, p.is_file() and sha(p) == expected)
    path_leaks = []
    for p in ROOT.rglob("*"):
        if not p.is_file(): continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.lower().endswith((".json", ".csv", ".md", ".txt", ".py", ".svg", ".log")):
            content = p.read_text(encoding="utf-8", errors="replace")
            if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", content): path_leaks.append(rel)
    check("no_private_absolute_paths", not path_leaks)
    check("no_raw_archives", not any(p.suffix.lower() in (".zip", ".7z", ".rar") for p in ROOT.rglob("*") if p.is_file()))
    check("no_private_trajectory_points", not any("trajectory_points" in p.name.lower() or "raw_gnss" in p.name.lower() for p in ROOT.rglob("*") if p.is_file()))
    freeze = load(ROOT / "HK_CG_R5_CASE_FREEZE.json")
    identity = load(ROOT / "HK_CG_R5_SOURCE_IDENTITY.json")
    summary = load(ROOT / "cg_run" / "full_cg_v1_run_summary.json")
    cert = load(ROOT / "closure" / "INDEPENDENT_PRICING_CLOSURE_CERTIFICATE.json")
    reference = load(ROOT / "case" / "ARC_FLOW_REFERENCE_SUMMARY.json")
    base_case = ROOT / "r2r4_baseline" / "phase_c" / "case"
    arc_file = base_case / "dynamic_arc.csv"
    demand_file = base_case / "dynamic_demand.csv"
    model = hashlib.sha256(arc_file.read_bytes() + b"\0" + demand_file.read_bytes()).hexdigest()
    check("frozen_model_signature", model == freeze["model_signature"] == reference["model_signature"])
    check("case_counts", freeze["dynamic_arcs"] == len(rows(arc_file)) == 24910 and freeze["demand_count"] == len(rows(demand_file)) == 10)
    check("current_source_identity", identity["status"] == "PASS" and
          identity["required_current_source_hashes"]["phase_i_general_pricing_oracle.py"] == "0554ae3c19248fc62a22a2d02d359df371887f62a0400f1ca55dcb8b60b1dc71")
    if (ROOT / "source" / "independent_pricing_closure.py").exists():
        check("independent_evaluator_hash", sha(ROOT / "source" / "independent_pricing_closure.py") == identity["required_current_source_hashes"]["independent_pricing_closure.py"])
    phase_i = rows(ROOT / "cg_run" / "full_cg_v1_phase_i_artificial_flow_trace.csv")
    phase_ii = rows(ROOT / "cg_run" / "full_cg_v1_phase_ii_objective_trace.csv")
    check("phase_i_zero", abs(float(phase_i[-1]["total_artificial_flow"])) <= 1e-6 and summary["phase_i_status"] == "PASS")
    check("phase_ii_completed", summary["run_status"] == "PASS" and summary["phase_ii_loop_status"] == "PASS")
    check("phase_ii_objective", abs(float(phase_ii[-1]["objective_value"]) - summary["phase_ii_final_objective"]) <= 1e-6)
    check("reference_objective_agreement", abs(float(phase_ii[-1]["objective_value"]) - reference["objective_value"]) <= 1e-5)
    check("closure_declared", cert["independent_pricing_closure_established"] is True and cert["demand_count"] == 10 and cert["continuation_rounds"] <= 25 and cert["added_columns"] <= 100)
    check("closure_by_demand", len(cert["by_demand"]) == 10 and all(r["closure_pass"] and (r["min_ungenerated_reduced_cost"] is None or r["min_ungenerated_reduced_cost"] >= -1e-6) for r in cert["by_demand"]))
    check("closure_objective", abs(cert["objective_recomputed"] - reference["objective_value"]) <= 1e-5)
    figs = rows(ROOT / "HONG_KONG_CG_R5_FIGURE_MANIFEST.csv")
    check("figure_inventory", len(figs) == 26 and len({r["figure_id"] for r in figs}) == 26)
    figure_failures = []
    for row in figs:
        svg, png = ROOT / row["svg"], ROOT / row["png"]
        sidecar = svg.with_suffix(".source.json")
        if not svg.is_file() or not png.is_file() or not sidecar.is_file():
            figure_failures.append(row["figure_id"] + ":file"); continue
        info = load(sidecar)
        base = ROOT / "r2r4_baseline" if row["svg"].startswith("r2r4_baseline/") else ROOT
        if not info.get("caption"):
            figure_failures.append(row["figure_id"] + ":caption")
        for rel, expected in info.get("input_sha256", {}).items():
            p = base / rel
            if not p.is_file() or sha(p) != expected:
                figure_failures.append(row["figure_id"] + ":source:" + rel)
    check("figure_links_sidecars_sources", not figure_failures)
    receiver = (ROOT / "case" / "dynamic_columns.csv").exists()
    deep = None
    if receiver:
        case = ROOT / "case"
        check("original_seed_signature", sha(case / "dynamic_columns.csv") == freeze["seed_pool_signature"])
        check("exact_public_graph_copy", sha(case / "dynamic_arc.csv") == sha(arc_file) and sha(case / "dynamic_demand.csv") == sha(demand_file))
        for name, expected in freeze["dynamic_input_hashes"].items():
            check("frozen_input:" + name, sha(case / name) == expected)
        sys.path.insert(0, str(ROOT / "source"))
        from independent_pricing_closure import evaluate_files
        result = evaluate_files(case, ROOT / "closure" / "CLOSURE_FINAL_POOL.csv",
                                ROOT / "closure" / "CLOSURE_FINAL_DUAL_SOLUTION.json",
                                ROOT / "closure" / "CLOSURE_FINAL_SOLUTION_BY_COLUMN.csv")
        deep = result
        check("independent_repricing_closure", result["closure_pass"] is True and result["demand_count"] == 10)
        check("independent_objective", abs(result["objective_recomputed"] - cert["objective_recomputed"]) <= 1e-6)
        check("independent_feasibility", result["max_demand_residual"] <= 1e-6 and result["max_capacity_violation"] <= 1e-6 and result["stationarity_max_abs"] <= 1e-6)
        check("independent_graph_pool_dual_signatures", all(result[k] == cert[k] for k in ("graph_signature", "demand_signature", "pool_signature", "dual_signature")))
        check("independent_by_demand", all(a["demand_id"] == b["demand_id"] and a["min_ungenerated_path_arc_sequence"] == b["min_ungenerated_path_arc_sequence"] and
              (a["min_ungenerated_reduced_cost"] is None and b["min_ungenerated_reduced_cost"] is None or
               a["min_ungenerated_reduced_cost"] is not None and b["min_ungenerated_reduced_cost"] is not None and abs(a["min_ungenerated_reduced_cost"] - b["min_ungenerated_reduced_cost"]) <= 1e-9)
              for a, b in zip(result["by_demand"], cert["by_demand"])))
        orig = {r["column_id"]: r for r in rows(case / "dynamic_columns.csv")}
        pool = {r["column_id"]: r for r in rows(ROOT / "closure" / "CLOSURE_FINAL_POOL.csv")}
        check("original_seed_pool_unchanged", all(cid in pool and pool[cid]["arc_sequence"] == r["arc_sequence"] for cid, r in orig.items()))
        check("column_generation_provenance", all(cid in orig or cid.startswith(("PHASEI_R", "ORACLE_R", "R5_CLOSURE_R")) for cid in pool))
        check("no_reference_primal_dual_seeding", load(ROOT / "PUBLIC_RUN_MANIFEST.json")["workflow_provenance"]["reference_paths_flows_or_duals_used"] is False)
        arc = {r["arc_id"]: r for r in rows(case / "dynamic_arc.csv")}
        flow_by_id = {r["column_id"]: float(r["flow"]) for r in rows(ROOT / "closure" / "CLOSURE_FINAL_SOLUTION_BY_COLUMN.csv")}
        physical = defaultdict(float)
        for cid, row in pool.items():
            flow = flow_by_id[cid]
            for aid in row["arc_sequence"].split("|"):
                if arc[aid]["arc_type"] == "movement": physical[arc[aid]["physical_link_id"]] += flow
        saved_physical = {r["physical_link_id"]: float(r["flow_from_final_columns"]) for r in rows(ROOT / "cg_run" / "solver_free_physical_link_flows.csv")}
        selected = {r["link_id"] for r in rows(case / "selected_physical_links.csv")}
        check("physical_link_back_projection", selected == set(saved_physical) and all(abs(physical[k] - saved_physical[k]) <= 1e-6 for k in selected))
    else:
        check("public_seed_pool_absent", not (ROOT / "case" / "dynamic_columns.csv").exists())
        check("public_final_pool_dual_absent", not (ROOT / "closure" / "CLOSURE_FINAL_POOL.csv").exists() and not (ROOT / "closure" / "CLOSURE_FINAL_DUAL_SOLUTION.json").exists())
        check("public_path_sequences_redacted", all(not r.get("min_ungenerated_path_arc_sequence") for r in cert["by_demand"]))
    return {"status": "PASS" if not failures else "FAIL", "mode": "receiver_deep" if receiver else "public_projection",
            "failures": failures[:100], "failure_count": len(failures), "figure_failures": figure_failures[:30],
            "figure_count": len(figs), "model_signature": model, "objective_recomputed": deep["objective_recomputed"] if deep else cert["objective_recomputed"],
            "closure_demands": cert["demand_count"], "private_absolute_path_hits": path_leaks[:20],
            "optimization_invocations": 0}

if __name__ == "__main__":
    try: result = verify()
    except Exception as exc: result = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}", "optimization_invocations": 0}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    raise SystemExit(0 if result["status"] == "PASS" else 1)
