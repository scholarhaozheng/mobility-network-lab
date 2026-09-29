#!/usr/bin/env python3
"""Validate the packaged public tables and rebuilt SQLite without private inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    manifest = ROOT / "data" / "public_table_manifest.csv"
    errors = []
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        for item in csv.DictReader(f):
            path = ROOT / item["source_file"]
            rows = sum(1 for _ in path.open("r", encoding="utf-8-sig")) - 1
            if rows != int(item["expected_rows"]):
                errors.append(f"row count: {item['table_name']}")
            if sha256(path) != item["sha256"]:
                errors.append(f"hash: {item['table_name']}")
    db = ROOT / "boston_central_public.sqlite"
    connection = sqlite3.connect(db)
    checks = {
        "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
        "trace": connection.execute("SELECT COUNT(*) FROM end_to_end_feedback_trace").fetchone()[0] == 1,
        "response": connection.execute("SELECT COUNT(*) FROM scenario_transit_response WHERE od_id='panel_od_019' AND departure_time='12:30:00' AND mu_transit_sensitivity=1.0").fetchone()[0] == 3,
        "zone_id_text": connection.execute("SELECT type FROM pragma_table_info('zonal_population_households') WHERE name='zone_id'").fetchone()[0] == "TEXT",
        "all_targeted_checks": connection.execute("SELECT COUNT(*) FROM targeted_validation_checks WHERE lower(passed) NOT IN ('true','1')").fetchone()[0] == 0,
        "available_transit_has_ride": connection.execute("SELECT COUNT(*) FROM od_multimodal_skims WHERE mode='transit_walk_access' AND availability_status='available' AND CAST(ride_segment_count AS REAL)<1").fetchone()[0] == 0,
        "restore_skim_exact": connection.execute("SELECT COUNT(*) FROM srestore_skim_comparison WHERE CAST(mismatch_count AS REAL)>0").fetchone()[0] == 0,
        "source_alias_map": connection.execute("SELECT COUNT(*) FROM source_id_alias_map").fetchone()[0] >= 9,
    }
    connection.close()
    result = {"manifest_errors": errors, "checks": checks, "passed": not errors and all(checks.values())}
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
