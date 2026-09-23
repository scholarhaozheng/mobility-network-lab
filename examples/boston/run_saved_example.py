#!/usr/bin/env python3
"""Rebuild and inspect the accepted Central Boston saved public results."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path


COMPONENT = "behavior_feedback_r1_semantic_fix_r1"
MANIFEST_SHA256 = "0759e86895b3557ada100b4c6a07529fc1713040d162d2d0abb0407bc1aebb49"
BUILDER_SHA256 = "18c0bcedeb1e3ed5a36a8814d262aed3feccf066b029d42b4f5c4c600e44850b"
QUERY_SHA256 = "92fd4446ee0d4ed8820de1d1eb19d28ed36a0ac8e2f16d038a01d7436223a606"
REQUIRED_COLUMNS = {
    "feedback_trace": {"trace_id", "od_id", "departure_time"},
    "od_multimodal_skims": {"od_id", "departure_time", "mode", "availability_status", "transfers", "path_id"},
    "od_mode_probabilities": {"od_id", "departure_time", "scenario_id", "mode", "mu_transit_sensitivity", "probability"},
    "parameter_registry": {"parameter_id", "source_id", "page_table_row", "symbol", "value", "unit", "status"},
    "trip_generation_by_purpose": {"productions_person_trips_daily", "unit"},
    "person_to_vehicle_crosswalk": {"scenario_id", "mu_transit_sensitivity", "assignment_inclusion", "vehicle_trips"},
    "feedback_scenario_registry": {"scenario_id", "execution_status", "validation_status"},
}
QUERY_NAMES = ("trace", "response", "unavailable", "parameters", "transfers")
NOTICE = (
    "This rebuilds and inspects saved results. It did NOT download sources, "
    "estimate demand, match GPS, reroute transit, estimate parameters, run "
    "FW/CG, or validate predictions."
)


class DemoError(Exception):
    """A failed input, build, or query check with an actionable message."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def validate_paths(data_dir: Path, output: Path, script_dir: Path) -> tuple[Path, Path, Path]:
    data_dir = data_dir.resolve(strict=True)
    script_dir = script_dir.resolve(strict=True)
    output = output.resolve(strict=False)
    if not data_dir.is_dir():
        raise DemoError("--data-dir must be an extracted public component directory.")
    if overlaps(output, data_dir) or overlaps(output, script_dir):
        raise DemoError("Output overlaps the data or trusted code directory; choose a separate new directory.")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise DemoError("Output directory is populated; choose a new or empty directory.")
    return data_dir, output, script_dir


def validate_code(script_dir: Path) -> tuple[Path, Path]:
    component = script_dir / COMPONENT
    builder = component / "build_public_database.py"
    query_file = component / "query_behavior_feedback.py"
    for path, expected in ((builder, BUILDER_SHA256), (query_file, QUERY_SHA256)):
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            raise DemoError(f"Trusted {path.name} is missing or differs from the accepted component; install the matching {COMPONENT} code beside this script.")
    return builder, query_file


def safe_source(root: Path, name: str) -> Path:
    relative = Path(name)
    if (not name or relative.is_absolute() or len(relative.parts) != 2
            or relative.parts[0] != "data" or relative.suffix.lower() != ".csv"
            or any(part in (".", "..") for part in relative.parts)
            or ":" in name or "\\" in name):
        raise DemoError(f"Unsafe manifest source_file {name!r}; use a data/*.csv path in the extracted component.")
    path = root / relative
    if path.is_symlink() or path.parent.is_symlink() or root not in path.resolve(strict=False).parents:
        raise DemoError(f"Manifest source_file escapes the component: {name!r}.")
    return path


def validate_manifest(data_dir: Path) -> tuple[Path, list[dict[str, str]], int]:
    manifest = data_dir / "data" / "public_table_manifest.csv"
    if manifest.is_symlink() or manifest.parent.is_symlink() or not manifest.is_file():
        raise DemoError("Missing safe data/public_table_manifest.csv; extract the accepted public component.")
    if data_dir not in manifest.resolve().parents:
        raise DemoError("Manifest escapes the extracted component directory.")
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["table_name", "source_file", "expected_rows", "sha256"]:
            raise DemoError("Manifest header differs from the accepted public table format.")
        items = list(reader)
    if not items or any(None in item or "" in item for item in items):
        raise DemoError("Manifest has a malformed row; re-extract the public component.")
    names = [item["table_name"] for item in items]
    if len(names) != len(set(names)) or not REQUIRED_COLUMNS.keys() <= set(names):
        raise DemoError("Manifest has duplicate or missing required tables; re-extract the public component.")
    # Check paths first, so a modified manifest reports unsafe paths explicitly.
    for item in items:
        safe_source(data_dir, item["source_file"])
    if sha256(manifest) != MANIFEST_SHA256:
        raise DemoError("Public table manifest differs from the accepted semantic-fix release; use the matching component.")
    total = 0
    for item in items:
        path = safe_source(data_dir, item["source_file"])
        if not path.is_file():
            raise DemoError(f"Missing mandatory CSV {item['source_file']}; re-extract the public component.")
        expected_hash = item["sha256"].lower()
        if sha256(path) != expected_hash:
            raise DemoError(f"Hash mismatch for {item['source_file']}; re-extract the public component.")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames
            if not columns or len(columns) != len(set(columns)) or any(not col for col in columns):
                raise DemoError(f"Invalid CSV header in {item['source_file']}; re-extract the public component.")
            missing = REQUIRED_COLUMNS.get(item["table_name"], set()) - set(columns)
            if missing:
                raise DemoError(f"Missing required columns in {item['source_file']}: {', '.join(sorted(missing))}.")
            rows = 0
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise DemoError(f"Malformed CSV row in {item['source_file']}; re-extract the public component.")
                rows += 1
        if rows != int(item["expected_rows"]):
            raise DemoError(f"Row count mismatch for {item['source_file']}: {rows} found, {item['expected_rows']} declared.")
        total += rows
    return manifest, items, total


def load_queries(path: Path) -> dict[str, str]:
    """Read the shipped query constants without executing the query utility."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "QUERIES" for t in node.targets):
            queries = ast.literal_eval(node.value)
            if not isinstance(queries, dict) or any(name not in queries for name in QUERY_NAMES):
                break
            return queries
    raise DemoError("Trusted query definitions are unavailable; install the accepted component.")


def export_queries(database: Path, query_file: Path, query_dir: Path, od_id: str, departure_time: str) -> dict[str, int]:
    queries = load_queries(query_file)
    queries["response"] = (
        "SELECT od_id,departure_time,scenario_id,total_min,mu_transit_sensitivity,probability "
        "FROM scenario_transit_response WHERE od_id=? AND departure_time=? "
        "AND mu_transit_sensitivity=1.0 ORDER BY scenario_id"
    )
    counts: dict[str, int] = {}
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise DemoError(f"Built database failed SQLite integrity_check: {integrity}.")
        query_dir.mkdir()
        for name in QUERY_NAMES:
            parameters = (od_id, departure_time) if name == "response" else ()
            cursor = connection.execute(queries[name], parameters)
            headers = [column[0] for column in cursor.description]
            target = query_dir / f"{name}.csv"
            with target.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(headers)
                count = 0
                for row in cursor:
                    writer.writerow(row)
                    count += 1
            counts[name] = count
        return counts
    finally:
        connection.close()


def database_summary(database: Path, manifest_rows: int) -> dict:
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise DemoError(f"Built database failed SQLite integrity_check: {integrity}.")
        loaded = connection.execute("SELECT COUNT(*),SUM(row_count) FROM public_build_manifest").fetchone()
        if loaded[1] != manifest_rows:
            raise DemoError("Built database row ledger disagrees with the validated manifest.")
        generation = connection.execute(
            "SELECT unit,SUM(productions_person_trips_daily) FROM trip_generation_by_purpose GROUP BY unit"
        ).fetchall()
        assignments = connection.execute(
            "SELECT scenario_id,SUM(vehicle_trips) FROM person_to_vehicle_crosswalk "
            "WHERE mu_transit_sensitivity=1.0 AND assignment_inclusion='True' GROUP BY scenario_id ORDER BY scenario_id"
        ).fetchall()
        scenarios = connection.execute(
            "SELECT scenario_id,execution_status,validation_status FROM feedback_scenario_registry ORDER BY scenario_id"
        ).fetchall()
        if not generation or not assignments or not scenarios:
            raise DemoError("Required summary tables are empty; inspect the packaged data and builder.")
        return {
            "integrity_check": integrity,
            "data_tables": loaded[0],
            "data_rows": loaded[1],
            "generation_daily_person_trips": [{"unit": unit, "value": value} for unit, value in generation],
            "fixed_panel_assigned_vehicle_trips_mu1": [
                {"scenario_id": scenario, "vehicle_trips": value} for scenario, value in assignments
            ],
            "saved_scenarios": [
                {"scenario_id": scenario, "saved_execution_status": execution, "saved_validation_status": validation}
                for scenario, execution, validation in scenarios
            ],
        }
    finally:
        connection.close()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run(args: argparse.Namespace) -> dict:
    script_dir = Path(__file__).resolve().parent
    data_dir, output, script_dir = validate_paths(args.data_dir, args.output, script_dir)
    builder, query_file = validate_code(script_dir)
    manifest, items, declared_rows = validate_manifest(data_dir)
    if len(args.od_id) > 128 or len(args.departure_time) > 64:
        raise DemoError("Selected OD ID or departure time is too long; use a key from the saved tables.")
    created_output = not output.exists()
    output.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".saved-example-", dir=output) as staging_name:
            staging = Path(staging_name)
            database = staging / "boston_saved_example.sqlite"
            command = [sys.executable, "-B", str(builder), "--manifest", str(manifest), "--output", str(database)]
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if completed.returncode:
                raise DemoError(f"Trusted builder failed (exit {completed.returncode}); verify the accepted component and see build stderr in the diagnostic log.")
            try:
                build_report = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                raise DemoError("Trusted builder returned no valid build report; inspect the matching component.") from exc
            if not database.is_file() or build_report.get("integrity_check") != "ok":
                raise DemoError("Trusted builder did not produce an intact saved database.")
            # The shipped builder does not verify hashes itself. Catch input
            # changes that happened while it was loading the CSV files.
            validate_manifest(data_dir)
            query_counts = export_queries(database, query_file, staging / "queries", args.od_id, args.departure_time)
            data_summary = database_summary(database, declared_rows)
            summary = {
                "component": COMPONENT,
                "manifest_sha256": sha256(manifest),
                "builder_sha256": sha256(builder),
                "query_code_sha256": sha256(query_file),
                "executed_at_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version.split()[0],
                "builder_exit_code": completed.returncode,
                "builder_report": {key: build_report.get(key) for key in ("tables", "loaded_rows", "integrity_check")},
                "database": data_summary,
                "query_rows": query_counts,
                "selected_response_key": {"od_id": args.od_id, "departure_time": args.departure_time},
                "response_status": "matches" if query_counts["response"] else "no_saved_rows_for_selected_key",
                "outputs": ["boston_saved_example.sqlite", *[f"queries/{name}.csv" for name in QUERY_NAMES], "DEMO_RESULTS.md", "demo_summary.json"],
                "scope_notice": NOTICE,
            }
            generation = data_summary["generation_daily_person_trips"]
            assignments = data_summary["fixed_panel_assigned_vehicle_trips_mu1"]
            lines = [
                "# Central Boston saved-result example", "",
                f"Component: `{COMPONENT}`. Manifest SHA-256: `{summary['manifest_sha256']}`.", "",
                f"Executed with Python {summary['python']}; trusted builder exit {completed.returncode}; SQLite integrity check: {data_summary['integrity_check']}.",
                f"Loaded {data_summary['data_rows']} rows across {data_summary['data_tables']} packaged data tables.", "",
                "Database: `boston_saved_example.sqlite`.", "",
                "## Distinct quantities", "",
            ]
            lines += [f"- Transferred household-rate generation: {item['value']:.6f} {item['unit']} (modeled estimate, not observed trips)." for item in generation]
            lines += [f"- Fixed-panel assigned S1/S2 or restore vehicle trips, mu_transit=1, {item['scenario_id']}: {item['vehicle_trips']:.9f} modeled vehicle trips." for item in assignments]
            lines += ["", "## Saved queries", ""]
            lines += [f"- `queries/{name}.csv`: {query_counts[name]} row{'s' if query_counts[name] != 1 else ''}." for name in QUERY_NAMES]
            if not query_counts["response"]:
                lines += ["", "The selected OD/departure key has no saved response rows. The query succeeded; this does not indicate corrupted input."]
            lines += ["", "The scenario registry contains saved execution and validation labels; they are historical records, not procedures rerun by this command.", "", NOTICE, "", "See `demo_summary.json` for scenario statuses, checks, and output paths.", ""]
            (staging / "DEMO_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
            write_json(staging / "demo_summary.json", summary)
            moved: list[Path] = []
            try:
                for name in ("boston_saved_example.sqlite", "queries", "DEMO_RESULTS.md", "demo_summary.json"):
                    destination = output / name
                    os.replace(staging / name, destination)
                    moved.append(destination)
            except Exception:
                for path in reversed(moved):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                raise
            return summary
    except Exception:
        # The output is private to this invocation and still contains no
        # successful artifacts. Retain the detail needed to diagnose a failed
        # builder/query without printing a Python traceback in the CLI.
        diagnostic = traceback.format_exc()
        if "completed" in locals():
            diagnostic += "\nBuilder stdout:\n" + completed.stdout + "\nBuilder stderr:\n" + completed.stderr
        try:
            (output / "demo_failure.log").write_text(diagnostic, encoding="utf-8")
        except OSError:
            pass
        if created_output and output.exists() and not any(output.iterdir()):
            output.rmdir()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=NOTICE)
    parser.add_argument("--data-dir", type=Path, required=True, help="Extracted accepted public component root containing data/public_table_manifest.csv")
    parser.add_argument("--output", type=Path, required=True, help="New or empty output directory, separate from data and code")
    parser.add_argument("--od-id", default="panel_od_019", help="Saved OD identifier for the response query")
    parser.add_argument("--departure-time", default="12:30:00", help="Saved departure time for the response query")
    args = parser.parse_args()
    try:
        result = run(args)
    except (DemoError, OSError, sqlite3.Error, ValueError) as exc:
        print(f"Saved-result example failed: {exc}", file=sys.stderr)
        return 1
    print(f"Saved-result example complete: {args.output.resolve()}")
    print(f"SQLite integrity: {result['database']['integrity_check']}; query rows: {result['query_rows']}")
    print(NOTICE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
