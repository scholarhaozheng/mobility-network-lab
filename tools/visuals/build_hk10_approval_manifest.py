#!/usr/bin/env python3
"""Hash-bound artifact-level HK10 approval; historical R2 pending record is retained."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs/assets/three_city_r2"
HISTORICAL = ASSET / "DISCLOSURE_STATUS_R2.json"
OUT = ASSET / "HK10_DISCLOSURE_APPROVAL_CURRENT.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
if historical["owner_artifact_level_publication_approval"] != "PENDING":
    raise ValueError("historical R2 pending decision was altered")
if historical["identity_and_final_flow_local_verification"]["arc_count"] != 77:
    raise ValueError("historical HK10 identity changed")
paths = historical["pending_paths"]
if len(paths) != len(set(paths)):
    raise ValueError("duplicate recorded dependency")
payload = []
shared = []
for rel in paths:
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    if rel.startswith("docs/assets/three_city_r1/data/hong_kong_selected_generated_column.") or any(
        rel.startswith(f"docs/assets/three_city_{release}/hong_kong_{family}.")
        for release in ("r1", "r2")
        for family in ("generated_column_time_indexed_path", "finite_space_time_case_sequence")
    ):
        payload.append(rel)
    else:
        shared.append(rel)
if len(payload) != 22 or len(shared) != 9:
    raise ValueError(f"unexpected HK10 dependency partition: {len(payload)} payload, {len(shared)} shared")
excerpt = ROOT / "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv"
with excerpt.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
if len(rows) != 77:
    raise ValueError("approved exact HK10 excerpt is not 77 arcs")
source = json.loads((ROOT / "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.source.json")
                    .read_text(encoding="utf-8"))
if source["column_id"] != "ORACLE_R1_HK10_K1" or source["demand_id"] != "HK10" or source["flow_pce"] != 0.8352150831808043:
    raise ValueError("approved excerpt identity or positive flow changed")
record = {
    "record_type": "exact-artifact-level-disclosure-allowlist",
    "status": "APPROVED_EXACT_HK10_EXCERPT",
    "approval_source": "Explicit user message in this A integration conversation, 2026-09-28: exact HK10 / ORACLE_R1_HK10_K1 model-generated 77-arc excerpt, CSV, corresponding figures, captions and necessary provenance records.",
    "approved_identity": {"demand_id": "HK10", "column_id": "ORACLE_R1_HK10_K1",
                          "ordered_arc_count": 77, "final_positive_flow_pce": 0.8352150831808043,
                          "excerpt_csv_sha256": sha(excerpt)},
    "approved_payload_paths_sha256": {rel: sha(ROOT / rel) for rel in payload},
    "shared_dependency_paths_sha256": {rel: sha(ROOT / rel) for rel in shared},
    "shared_dependency_rule": "The exact HK10 disclosure embedded in these pages/scripts is approved. Inclusion of a shared file is not blanket authorization for unrelated data, other generated columns, or future additions.",
    "expressly_not_approved": ["full generated path pools", "dual or solver-state arrays",
                                "raw GPS/UrbanNav observations", "additional provider files"],
    "historical_decision_record": {"path": "docs/assets/three_city_r2/DISCLOSURE_STATUS_R2.json",
                                   "sha256": sha(HISTORICAL), "status_at_that_time": "PENDING"},
    "scientific_solver_rerun": False,
    "git_publication_performed": False,
}
OUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": record["status"], "payload_files": len(payload),
                  "shared_dependency_files": len(shared), "manifest_sha256": sha(OUT)}, indent=2))
