"""Solver-independent verification and simple offline HTML/SVG rendering."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

from verify_external_run import verify_external_run


TOL = 1e-6
EXPECTED = {"R0": 5000.0, "R1": 20.0, "R2": 20.0, "R3": 27.0}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def locate_run(run_root: Path) -> tuple[str, Path, dict[str, Any]]:
    external = run_root / "external_run_result.json"
    external_manifest = run_root / "external_run_manifest.json"
    if external.is_file() and external_manifest.is_file():
        return "EXTERNAL", run_root / "full_cg_v1_run", read_json(external)
    external_summary = run_root / "final_summary.json"
    if external_summary.is_file():
        case_dir = run_root / "cases" / "external_sioux_3od"
        return "R0", case_dir / "full_cg_v1_run", read_json(case_dir / "case_status.json")
    explicit = run_root / "regression_result.json"
    if explicit.is_file():
        result = read_json(explicit)
        return str(result.get("case_id", "")).upper(), run_root / "full_cg_v1_run", result
    raise ValueError("run directory is neither an external Sioux 3OD run nor an explicit R1/R2/R3 run")


def verify_full_cg(run_dir: Path, expected_objective: float | None) -> dict[str, Any]:
    required = {
        "summary": run_dir / "full_cg_v1_run_summary.json",
        "metadata": run_dir / "full_cg_v1_phase_ii_final_solution_metadata.json",
        "solution": run_dir / "full_cg_v1_phase_ii_final_solution_by_column.csv",
        "pool": run_dir / "full_cg_v1_phase_ii_final_pool.csv",
        "dual": run_dir / "full_cg_v1_phase_ii_final_dual_solution.json",
        "stationarity": run_dir / "full_cg_v1_phase_ii_final_stationarity.csv",
        "stop": run_dir / "full_cg_v1_phase_ii_stop_certificate.json",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        return {"status": "FAIL", "blockers": ["missing required artifact: " + item for item in missing]}
    summary = read_json(required["summary"])
    metadata = read_json(required["metadata"])
    dual = read_json(required["dual"])
    stop = read_json(required["stop"])
    solution = read_csv(required["solution"])
    pool = read_csv(required["pool"])
    stationarity = read_csv(required["stationarity"])
    blockers: list[str] = []
    objective = finite_float(summary.get("phase_ii_final_objective"))
    if objective is None or (expected_objective is not None and not math.isclose(objective, expected_objective, abs_tol=TOL)):
        blockers.append(f"objective mismatch: {objective} != {expected_objective}")
    if summary.get("run_status") != "PASS" or summary.get("execution_mode") != "bounded_full_cg_v1_pass":
        blockers.append("CG run did not report bounded pass")
    if summary.get("final_solution_export_status") != "PASS" or not summary.get("full_solution_and_duals_present"):
        blockers.append("final full-pool solution/dual export did not pass")
    if metadata.get("export_status") != "PASS" or not metadata.get("solution_is_exact_last_successful_rmp"):
        blockers.append("final export metadata is not tied to the last successful solve")
    if metadata.get("unsolved_candidate_rows_defaulted_to_zero") is not False:
        blockers.append("metadata permits fabricated zero rows for unsolved candidates")
    solution_ids = [row.get("column_id", "") for row in solution]
    pool_ids = [row.get("column_id", "") for row in pool]
    if not solution_ids or solution_ids != pool_ids or len(solution_ids) != len(set(solution_ids)):
        blockers.append("final solution IDs do not exactly match unique final solved-pool IDs in order")
    if len(solution) != int(metadata.get("exported_solution_row_count", -1)):
        blockers.append("final solution row count differs from metadata")
    model_signatures = {row.get("model_signature", "") for row in solution}
    pool_signatures = {row.get("pool_signature", "") for row in solution}
    if model_signatures != {metadata.get("model_signature")} or pool_signatures != {metadata.get("pool_signature")}:
        blockers.append("per-row model/pool signatures are missing or inconsistent")
    lower = dual.get("lower_bound_marginals", {})
    upper = dual.get("upper_bound_marginals", {})
    demands = dual.get("demand_equality_duals", {})
    capacities = dual.get("capacity_inequality_duals", {})
    if set(lower) != set(solution_ids) or set(upper) != set(solution_ids):
        blockers.append("bound marginal keys do not exactly match solution columns")
    if not demands or not capacities or not dual.get("dual_fields_present") or not dual.get("dual_fields_finite"):
        blockers.append("matching demand/capacity row duals are absent or nonfinite")
    if not stationarity or any(row.get("kkt_status") != "PASS" for row in stationarity):
        blockers.append("stationarity/KKT rows are absent or did not all pass")
    residuals = [finite_float(row.get("computed_reduced_cost_or_stationarity_residual")) for row in stationarity]
    if any(value is None or abs(value) > TOL for value in residuals):
        blockers.append("stationarity residual exceeds tolerance")
    if summary.get("capacity_violation_count_final") != 0 or abs(float(summary.get("demand_residual_max_final", math.inf))) > TOL:
        blockers.append("final primal feasibility audit failed")
    if stop.get("stop_reason") != summary.get("stop_reason"):
        blockers.append("stop certificate reason differs from run summary")
    return {
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "objective": objective,
        "expected_objective": expected_objective,
        "final_solution_row_count": len(solution),
        "positive_flow_row_count": sum((finite_float(row.get("flow")) or 0.0) > TOL for row in solution),
        "zero_flow_row_count": sum(abs(finite_float(row.get("flow")) or 0.0) <= TOL for row in solution),
        "demand_dual_count": len(demands),
        "capacity_dual_count": len(capacities),
        "lower_bound_marginal_count": len(lower),
        "upper_bound_marginal_count": len(upper),
        "model_signature": metadata.get("model_signature"),
        "pool_signature": metadata.get("pool_signature"),
        "solve_iteration": metadata.get("solve_iteration"),
        "phase_ii_round": metadata.get("phase_ii_round"),
        "stop_reason": summary.get("stop_reason"),
        "phase_i_needed": summary.get("phase_i_needed"),
        "phase_i_loop_ran": summary.get("phase_i_loop_ran"),
    }


def render_visualization(output_root: Path, label: str, verification: dict[str, Any]) -> dict[str, str]:
    visual_dir = output_root / "visualization"
    visual_dir.mkdir(parents=True, exist_ok=True)
    objective = finite_float(verification.get("objective")) or 0.0
    expected = finite_float(verification.get("expected_objective")) or 0.0
    scale = max(objective, expected, 1.0)
    actual_width = 520.0 * objective / scale
    expected_width = 520.0 * expected / scale
    status = str(verification.get("status", "UNKNOWN"))
    color = "#147d64" if status == "PASS" else "#b42318"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300">
<rect width="760" height="300" fill="#f7f4ed"/><text x="40" y="48" font-family="Segoe UI,Arial" font-size="26" fill="#17212b">{html.escape(label)} offline verification</text>
<text x="40" y="82" font-family="Segoe UI,Arial" font-size="18" fill="{color}">Status: {html.escape(status)}</text>
<text x="40" y="128" font-family="Segoe UI,Arial" font-size="15" fill="#334155">Actual: {objective:g}</text><rect x="190" y="110" width="{actual_width:.2f}" height="24" rx="4" fill="#2563eb"/>
<text x="40" y="174" font-family="Segoe UI,Arial" font-size="15" fill="#334155">Expected: {expected:g}</text><rect x="190" y="156" width="{expected_width:.2f}" height="24" rx="4" fill="#94a3b8"/>
<text x="40" y="224" font-family="Segoe UI,Arial" font-size="14" fill="#475569">Final columns: {verification.get('final_solution_row_count', '')}; positive flow: {verification.get('positive_flow_row_count', '')}; zero flow: {verification.get('zero_flow_row_count', '')}</text>
<text x="40" y="252" font-family="Segoe UI,Arial" font-size="14" fill="#475569">Stop reason: {html.escape(str(verification.get('stop_reason', '')))}</text>
<text x="40" y="278" font-family="Segoe UI,Arial" font-size="12" fill="#64748b">Offline SVG; no fonts, scripts, or network resources are loaded.</text></svg>'''
    svg_path = visual_dir / "summary.svg"
    svg_path.write_text(svg, encoding="utf-8")
    html_path = visual_dir / "index.html"
    html_path.write_text(
        "<!doctype html><meta charset='utf-8'><title>GMNS CG offline verification</title>"
        "<style>body{font-family:Segoe UI,Arial;margin:2rem;background:#f7f4ed;color:#17212b}pre{background:white;padding:1rem;overflow:auto}</style>"
        f"<h1>{html.escape(label)} verification result</h1><img src='summary.svg' alt='Verification summary'>"
        f"<pre>{html.escape(json.dumps(verification, ensure_ascii=False, indent=2))}</pre>",
        encoding="utf-8",
    )
    return {"html": str(html_path), "svg": str(svg_path)}


def verify_run(run_root: Path, write_outputs: bool = True) -> dict[str, Any]:
    run_root = run_root.resolve()
    try:
        case_id, cg_dir, case_result = locate_run(run_root)
        if case_id == "EXTERNAL":
            core = verify_full_cg(cg_dir, None)
            external = verify_external_run(run_root, core)
            blockers = list(external.get("blockers", []))
            result = {"case_id": case_id, **core, **external, "blockers": blockers}
            result["expected_objective"] = external.get("reference_objective")
        elif case_id not in EXPECTED:
            raise ValueError(f"unexpected case id: {case_id}")
        else:
            core = verify_full_cg(cg_dir, EXPECTED[case_id])
            blockers = list(core.get("blockers", []))
            if case_id == "R0":
                if case_result.get("status") != "RAW_REGENERATED_REFERENCE_MATCH":
                    blockers.append("R0 source-to-result status is not RAW_REGENERATED_REFERENCE_MATCH")
                if core.get("final_solution_row_count") != 6:
                    blockers.append("R0 final solved pool does not contain exactly 6 columns")
                if core.get("phase_i_needed") is not False or core.get("phase_i_loop_ran") is not False:
                    blockers.append("R0 Phase I was not skipped")
            else:
                if case_result.get("status") != "PASS":
                    blockers.append(f"{case_id} regression_result did not pass")
                if case_result.get("network_mode") != "explicit_allowed_network":
                    blockers.append(f"{case_id} did not use explicit allowed network mode")
                if not case_result.get("reference_and_cg_share_exact_dynamic_graph"):
                    blockers.append(f"{case_id} reference/CG graph identity not certified")
                if case_id == "R1" and int(case_result.get("phase_ii_candidates_added", 0)) < 1:
                    blockers.append("R1 did not discover a non-seed path")
                if case_id == "R3" and float(case_result.get("seed_flow_final", 0.0)) <= TOL:
                    blockers.append("R3 slow seed column is not positive in a multiple-column optimum")
            result = {"case_id": case_id, **core, "blockers": blockers}
        result["status"] = "PASS" if not blockers else "FAIL"
    except Exception as exc:
        result = {"case_id": "UNKNOWN", "status": "FAIL", "blockers": [f"{type(exc).__name__}: {exc}"]}
    if write_outputs:
        (run_root / "offline_verification.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        result["visualization"] = render_visualization(run_root, result.get("case_id", "UNKNOWN"), result)
    return result


def verify_selftest(output_root: Path) -> dict[str, Any]:
    cases = {case_id: verify_run(output_root / case_id, write_outputs=True) for case_id in EXPECTED}
    blockers = [f"{case_id}: {item}" for case_id, result in cases.items() for item in result.get("blockers", [])]
    negative_path = output_root / "negative_checks" / "focused_negative_checks.json"
    negative = read_json(negative_path) if negative_path.is_file() else {
        "status": "FAIL", "blockers": ["focused negative-check result missing"]
    }
    if negative.get("status") != "PASS" or negative.get("solver_invocations") != 0:
        blockers.append("focused no-solve negative checks did not pass")
    rc4_path = output_root / "rc4_focused_checks" / "rc4_focused_checks.json"
    rc4 = read_json(rc4_path) if rc4_path.is_file() else {
        "status": "FAIL", "blockers": ["RC4/RC5 focused-check result missing"]
    }
    if rc4.get("status") != "PASS" or rc4.get("solver_invocations") != 0:
        blockers.append("RC4/RC5 no-solve focused checks did not pass")
    if cases["R1"].get("model_signature") != cases["R2"].get("model_signature"):
        blockers.append("R1/R2 model signatures differ despite identical allowed network/demand")
    if cases["R1"].get("pool_signature") == cases["R2"].get("pool_signature"):
        blockers.append("R1/R2 pool signatures unexpectedly match despite different seeds")
    result = {
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "cases": cases,
        "focused_negative_checks": negative,
        "rc4_focused_checks": rc4,
        "r1_r2_same_model_signature": cases["R1"].get("model_signature") == cases["R2"].get("model_signature"),
        "r1_r2_distinct_pool_signature": cases["R1"].get("pool_signature") != cases["R2"].get("pool_signature"),
    }
    (output_root / "selftest_verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    overview = {
        "status": result["status"],
        "objective": sum(float(item.get("objective") or 0.0) for item in cases.values()),
        "expected_objective": sum(EXPECTED.values()),
        "final_solution_row_count": sum(int(item.get("final_solution_row_count") or 0) for item in cases.values()),
        "positive_flow_row_count": sum(int(item.get("positive_flow_row_count") or 0) for item in cases.values()),
        "zero_flow_row_count": sum(int(item.get("zero_flow_row_count") or 0) for item in cases.values()),
        "stop_reason": "R0-R3 independent checks",
    }
    result["visualization"] = render_visualization(output_root, "R0–R3", overview)
    return result


def verify_release_manifest(release_root: Path) -> dict[str, Any]:
    manifest = release_root / "docs" / "RELEASE_FILE_MANIFEST.csv"
    if not manifest.is_file():
        return {"status": "NOT_AVAILABLE", "checked": 0, "blockers": ["release file manifest missing"]}
    rows = read_csv(manifest)
    blockers = []
    checked = 0
    listed: set[str] = set()
    for row in rows:
        relative_text = row.get("path", "")
        relative = Path(relative_text)
        if (
            not relative_text
            or relative.is_absolute()
            or relative.drive
            or ".." in relative.parts
            or "\\" in relative_text
            or relative_text.startswith("/")
        ):
            blockers.append(f"unsafe manifest path: {relative_text!r}")
            continue
        canonical = relative.as_posix()
        if canonical in listed:
            blockers.append(f"duplicate manifest path: {canonical}")
            continue
        listed.add(canonical)
        path = release_root / relative
        if not path.is_file():
            blockers.append(f"missing: {canonical}")
            continue
        if path.stat().st_size != int(row["size_bytes"]) or sha256(path).lower() != row["sha256"].lower():
            blockers.append(f"hash/size mismatch: {canonical}")
        checked += 1
    actual = {
        path.relative_to(release_root).as_posix()
        for path in release_root.rglob("*")
        if path.is_file()
        and path != manifest
        and path.name != "receiver_acceptance.zip"
        and "receiver_runs" not in path.relative_to(release_root).parts
    }
    missing_from_manifest = sorted(actual - listed)
    unexpected_in_manifest = sorted(listed - actual)
    if missing_from_manifest:
        blockers.append(f"unmanifested payload files: {missing_from_manifest[:20]}")
    if unexpected_in_manifest:
        blockers.append(f"manifest rows outside payload policy: {unexpected_in_manifest[:20]}")
    return {
        "status": "PASS" if not blockers else "FAIL",
        "checked": checked,
        "listed": len(listed),
        "actual_payload_files": len(actual),
        "exact_coverage": listed == actual,
        "blockers": blockers,
    }
