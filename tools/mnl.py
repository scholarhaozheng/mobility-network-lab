#!/usr/bin/env python3
"""User entry point for the selected GMNS-CG engine and result verifier.

The numerical engine is retained from 0.3.0-rc5. This entry point only selects
inputs, isolates the worker process, and presents results in English.
"""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def json_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object: {path}")
    return data


def public_report(run: Path, result: dict) -> None:
    fields = [
        ("Verification", result.get("status")),
        ("CG objective", result.get("reported_cg_objective")),
        ("Recomputed objective", result.get("recomputed_objective")),
        ("Reference objective", result.get("reference_objective")),
        ("Final columns", result.get("final_pool_count")),
        ("Zero-flow columns", result.get("zero_flow_column_count")),
        ("Stopping reason", result.get("pricing_stop_reason")),
        ("Objective certificate source", result.get("objective_optimality_certificate_source")),
        ("Independent pricing closure", result.get("pricing_closure_proven")),
    ]
    rows = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v) if v is not None else 'Not recorded')}</td></tr>" for k, v in fields)
    page = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Run results | Mobility Network Lab</title>
<style>body{font:16px/1.65 system-ui,sans-serif;background:#f5f7fa;color:#152c3a;margin:0}main{max-width:850px;margin:50px auto;padding:30px;background:white;border:1px solid #dbe4eb;border-radius:16px}h1{font-size:34px;line-height:1.2}table{border-collapse:collapse;width:100%;margin:28px 0}th,td{text-align:left;border-bottom:1px solid #e2e8ed;padding:11px}th{width:45%}a{color:#087e83}code{font-size:13px;overflow-wrap:anywhere}.label{letter-spacing:.12em;text-transform:uppercase;font-size:12px;color:#087e83}@media(max-width:600px){main{margin:10px;padding:20px}h1{font-size:28px}}</style>
<main><p class="label">Mobility Network Lab / Run results</p><h1>Network optimization,<br>with inspectable outputs.</h1>
<p>This report is generated from the saved output tables. Verification does not run an optimizer.</p><table>""" + rows + """</table>
<p><a href="offline_verification.json">Verification JSON</a> &middot;
<a href="seeds/static_seed_candidates.csv">Initial routes</a> &middot;
<a href="full_cg_v1_run/full_cg_v1_phase_ii_final_solution_by_column.csv">Final path flows</a></p>
<p>Reference agreement and independent missing-column pricing certification are distinct conclusions. Consult the recorded stopping reason and certificate source.</p></main></html>"""
    (run / "report.html").write_text(page, encoding="utf-8")


def worker(action: str, arguments: list[str]) -> int:
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(ROOT / "app/src/gmns_dynamic"), str(ROOT / "launcher")]
    if action == "run":
        from run_external_network_pipeline import main
        return main(arguments)
    if action == "validate":
        p = argparse.ArgumentParser()
        p.add_argument("--input", required=True); p.add_argument("--config", required=True)
        a = p.parse_args(arguments)
        from external_network_input import load_case_config, normalize_inputs
        spec, paths = load_case_config(Path(a.config).resolve(), Path(a.input).resolve())
        data = normalize_inputs(spec, paths)
        report = {"status": "PASS", "scope": "input schema, attributes and identifier consistency; not a feasibility or optimality certificate", "nodes": len(data["nodes"]), "links": len(data["links"]), "positive_demands": len(data["demands"]), "zone_access_records": len(data["zone_access"]), "schema_version": spec["schema_version"]}
        print(json.dumps(report, indent=2)); return 0
    if action == "verify":
        from verify_artifacts import verify_run
        run = Path(arguments[0]).resolve()
        if not (run / "external_run_manifest.json").is_file():
            raise ValueError("This verifier expects a completed external-network run and its manifest.")
        result = verify_run(run, write_outputs=False)
        (run / "offline_verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        public_report(run, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") == "PASS" else 1
    raise ValueError(f"Unknown worker action: {action}")


def invoke(action: str, arguments: list[str], timeout: int = 300) -> int:
    environment = dict(os.environ)
    for key in ("PYTHONHOME", "PYTHONPATH"):
        environment.pop(key, None)
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    try:
        result = subprocess.run([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "_worker", action, *arguments], env=environment, timeout=timeout, check=False)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"Stopped: the Python worker exceeded {timeout} seconds. Outputs, if any, are not a successful run.", file=sys.stderr)
        return 124


def main() -> int:
    if len(sys.argv) > 2 and sys.argv[1] == "_worker":
        try:
            return worker(sys.argv[2], sys.argv[3:])
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr); return 1
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalog", help="List runnable examples and recorded benchmark results")
    for name in ("run", "validate"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True, help="Directory containing the input CSV files")
        p.add_argument("--config", required=True, help="Case JSON configuration")
        if name == "run":
            p.add_argument("--seed-mode", choices=("auto", "supplied"), default="auto")
            p.add_argument("--seed-k", type=int)
            p.add_argument("--seeds")
            p.add_argument("--output", required=True, help="New output directory, separate from inputs")
            p.add_argument("--timeout", type=int, default=300, help="External worker timeout in seconds")
    p = sub.add_parser("verify", help="Recompute checks from existing result files; no optimization")
    p.add_argument("--run", required=True)
    args = parser.parse_args()
    if args.command == "catalog":
        for case in json_file(ROOT / "catalog/datasets.json")["datasets"]:
            print(f"{case['id']:<29} {case['access']:<18} {case['title']}")
        return 0
    if args.command == "verify":
        return invoke("verify", [args.run])
    common = ["--input", str(Path(args.input).resolve()), "--config", str(Path(args.config).resolve())]
    if args.command == "validate":
        return invoke("validate", common)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.seed_mode == "auto" and args.seeds:
        parser.error("--seeds is not accepted in auto mode")
    if args.seed_mode == "supplied" and (not args.seeds or args.seed_k is not None):
        parser.error("supplied mode requires --seeds and does not accept --seed-k")
    run_args = common + ["--seed-mode", args.seed_mode, "--output", str(Path(args.output).resolve())]
    if args.seed_mode == "auto":
        run_args += ["--seed-k", str(args.seed_k if args.seed_k is not None else 1)]
    else:
        run_args += ["--seeds", str(Path(args.seeds).resolve())]
    return invoke("run", run_args, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
