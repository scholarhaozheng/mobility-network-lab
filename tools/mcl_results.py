#!/usr/bin/env python3
"""List, show and independently inspect registered SAVED case results; never solve."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog/case-runs.json"
BOSTON = "examples/boston/assignment_methods_r1"
SIOUX = "examples/sioux-falls/native_l3_r1"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def safe(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"catalog path escapes data root: {relative}")
    return path


def check_finite(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite saved value")
    return number


def bpr(links: list[dict], flows: dict[str, float], sioux: bool = False) -> float:
    total = 0.0
    for link in links:
        lid = link["link_id"]
        v = flows[lid]
        cap = max(check_finite(link["capacity"]), 1.0)
        t0 = check_finite(link["vdf_fftt"])
        if sioux:
            t0 = max(t0, 0.01)
        alpha = check_finite(link["vdf_alpha"])
        beta = check_finite(link["vdf_beta"])
        total += t0*v + t0*alpha/(beta+1.0)*v*(v/cap)**beta
    return total


def check_native(run: dict, root: Path) -> dict:
    sioux = run["case_id"] == "sioux-falls"
    base = safe(root, SIOUX if sioux else BOSTON)
    if sioux:
        links = rows(base / "inputs_snapshot/SiouxFalls/link.csv")
        path_rows = rows(safe(root, run["artifact"]))
        stem = f"runs/SiouxFalls/{run['scenario_id']}/outer_04"
        link_rows = rows(base / f"{stem}_link_flows.csv")
        od_rows = rows(base / f"{stem}_od_balance.csv")
        flow_field, link_field = "raw_reconstructed_flow", "path_aggregate"
        od_keys, od_tolerance = ("o_zone_id", "d_zone_id"), "audit_abs_tolerance"
    else:
        links = rows(base / "inputs_snapshot/link.csv")
        path_rows = rows(safe(root, run["artifact"]))
        stem = f"runs/rank{run['retained_rank']}/outer_02"
        link_rows = rows(base / f"{stem}_link_flows.csv")
        od_rows = rows(base / f"{stem}_od_balance.csv")
        flow_field, link_field = "raw_flow", "v_from_paths"
        od_keys, od_tolerance = ("o_node_id", "d_node_id"), "tolerance"
    check = json.loads(safe(root, run["check"]).read_text(encoding="utf-8"))
    if not check.get("accepted", check.get("public_eligibility_pass", False)):
        raise ValueError("selected saved native check is not accepted")
    link_ids = [row["link_id"] for row in links]
    link_id_set = set(link_ids)
    if len(set(link_ids)) != len(links) or {r["link_id"] for r in link_rows} != set(link_ids):
        raise ValueError("link identity coverage mismatch")
    reconstructed: dict[str, float] = defaultdict(float)
    od_sum: dict[tuple[str, str], float] = defaultdict(float)
    minimum_path = math.inf
    for path in path_rows:
        f = check_finite(path[flow_field])
        minimum_path = min(minimum_path, f)
        od_sum[(path[od_keys[0]], path[od_keys[1]])] += f
        sequence = path["link_sequence"] if sioux else path["link_id_sequence"]
        delimiter = ";" if ";" in sequence else ","
        for lid in sequence.split(delimiter):
            lid = lid.strip()
            if lid not in link_id_set:
                raise ValueError(f"path references absent link {lid}")
            reconstructed[lid] += f
    if minimum_path < -1e-8 or len(path_rows) != run["path_count"]:
        raise ValueError("path sign or count check failed")
    if len(od_rows) != (528 if sioux else 26) or len({(r[od_keys[0]], r[od_keys[1]]) for r in od_rows}) != len(od_rows):
        raise ValueError("OD identity coverage mismatch")
    max_od = 0.0
    for od in od_rows:
        key = od[od_keys[0]], od[od_keys[1]]
        error = abs(od_sum[key] - check_finite(od["volume"] if sioux else od["demand"]))
        if error > check_finite(od[od_tolerance]):
            raise ValueError(f"OD residual beyond saved tolerance: {key}")
        max_od = max(max_od, error)
    max_link = 0.0
    flows = {}
    for row in link_rows:
        lid = row["link_id"]
        reported = check_finite(row[link_field])
        error = abs(reconstructed[lid] - reported)
        tolerance = check_finite(row["audit_abs_tolerance"] if sioux else row["tolerance"])
        if error > tolerance:
            raise ValueError(f"link reconstruction beyond saved tolerance: {lid}")
        max_link = max(max_link, error)
        flows[lid] = reconstructed[lid]
    objective = bpr(links, flows, sioux)
    if abs(objective-run["objective"]) > max(1e-7, abs(run["objective"])*1e-8):
        raise ValueError("independently recomputed Beckmann component differs")
    return {"status": "saved-point-check-passed", "links": len(links), "od": len(od_rows),
            "paths": len(path_rows), "max_abs_od_residual": max_od,
            "max_abs_link_reconstruction_error": max_link,
            "recomputed_original_beckmann": objective,
            "recorded_full_network_relative_gap": run["full_network_relative_gap"],
            "equilibrium_certificate": False,
            "note": "The existing full-network shortest-path diagnostic is quoted, not recomputed by this no-solve inspector."}


def check_boston_reference(run: dict, root: Path) -> dict:
    base = safe(root, BOSTON)
    links = rows(base / "inputs_snapshot/link.csv")
    if run["method_id"] == "finite-path-slsqp":
        paths = rows(base / "inputs_snapshot/path_pool/path_pool.csv")
        flows = rows(base / "reference/full_path_flow.csv")
        if len(paths) != 130 or len(flows) != 130 or [p["path_id"] for p in paths] != [f["path_id"] for f in flows]:
            raise ValueError("frozen full-path identity mismatch")
        loaded: dict[str, float] = defaultdict(float)
        od: dict[str, float] = defaultdict(float)
        for p, f in zip(paths, flows):
            flow = check_finite(f["flow"])
            if flow < -1e-10:
                raise ValueError("negative full-path flow")
            od[p["od_index"]] += flow
            for lid in p["link_id_sequence"].split(";"):
                loaded[lid] += flow
        demands = rows(base / "inputs_snapshot/demand.csv")
        od_index = rows(base / "inputs_snapshot/path_pool/od_index.csv")
        if len(od_index) != len(demands):
            raise ValueError("OD index mismatch")
        max_od = max(abs(od[str(index)]-check_finite(row["volume"])) for index, row in enumerate(demands))
        if max_od > 1e-8:
            raise ValueError("full-path OD equality failed")
        reference = {r["link_id"]: check_finite(r["volume"]) for r in rows(base / "reference/link_flow.csv")}
        max_link = max(abs(loaded[lid]-reference[lid]) for lid in reference)
        if max_link > 1e-8:
            raise ValueError("full-path link reconstruction failed")
        volume = loaded
    else:
        solution = rows(safe(root, run["artifact"]))
        if len(solution) != 5091 or len({r["link_id"] for r in solution}) != 5091:
            raise ValueError("FW link coverage mismatch")
        volume = {r["link_id"]: check_finite(r["volume"]) for r in solution}
        max_od = None
        max_link = None
    if set(volume) != {r["link_id"] for r in links}:
        raise ValueError("network/link result mismatch")
    objective = bpr(links, volume)
    if abs(objective-run["objective"]) > 1e-7:
        raise ValueError("saved original objective mismatch")
    return {"status": "saved-point-check-passed", "links": 5091,
            "recomputed_original_beckmann": objective,
            "max_abs_od_residual": max_od, "max_abs_link_reconstruction_error": max_link,
            "note": ("Full-path OD and link flows reconstructed from saved path variables."
                     if run["method_id"] == "finite-path-slsqp" else
                     "FW result has no independent OD path decomposition in this public record.")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="list registered saved runs")
    listing.add_argument("--case", choices=("boston", "sioux-falls"))
    showing = sub.add_parser("show", help="show one registered record")
    showing.add_argument("--run", required=True)
    verify = sub.add_parser("verify-saved", help="read-only saved-point checks; no optimization")
    verify.add_argument("--run", required=True)
    verify.add_argument("--data-root", type=Path, default=ROOT, help="repository root containing public files")
    verify.add_argument("--output", type=Path, help="optional new JSON report path")
    args = parser.parse_args()
    runs = json.loads(CATALOG.read_text(encoding="utf-8"))["runs"]
    index = {run["run_id"]: run for run in runs}
    if len(index) != len(runs):
        parser.error("duplicate catalog run ID")
    if args.command == "list":
        result = [{"run_id": r["run_id"], "case_id": r["case_id"],
                   "method_id": r["method_id"], "status": r["status"]}
                  for r in runs if args.case is None or r["case_id"] == args.case]
    else:
        if args.run not in index:
            parser.error(f"unknown registered run: {args.run}")
        run = index[args.run]
        if args.command == "show":
            result = run
        else:
            root = args.data_root.resolve()
            for field in ("artifact", "code", "input", "check"):
                if field in run and not safe(root, run[field]).is_file():
                    raise FileNotFoundError(f"missing {field}: {run[field]}")
            if run["method_id"] == "native-diagnostic-l3":
                check = check_native(run, root)
            elif run["case_id"] == "boston" and run["scenario_id"].startswith("ABS_"):
                check = check_boston_reference(run, root)
            else:
                check = {"status": "record-and-artifact-present", "note": "Full numerical reconstruction is unavailable for this historical/semantic public record."}
            result = {"run_id": run["run_id"], **check}
            if args.output:
                output = args.output.resolve()
                if output.exists():
                    parser.error("output report already exists; choose a new path")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
