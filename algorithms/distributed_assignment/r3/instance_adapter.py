"""Portable case manifests for Sioux, Boston, and synthetic dynamic CSV inputs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from problem_contract import load


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_local(manifest_path, relative_name):
    relative = Path(relative_name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("case paths must be local relative paths")
    parent = Path(manifest_path).resolve().parent
    path = (parent / relative).resolve()
    if path != parent and parent not in path.parents:
        raise ValueError("case path escapes its directory")
    return path


def load_case(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "cross_city_lagrangian_case_v1":
        raise ValueError("unsupported case manifest schema")
    if manifest.get("adapter") != "finite_dynamic_csv_v1":
        raise ValueError("unsupported dynamic input adapter")
    if manifest.get("objective_unit") != "vehicle_minutes":
        raise ValueError("objective unit mismatch")
    arc = resolve_local(manifest_path, manifest["arc_file"])
    demand = resolve_local(manifest_path, manifest["demand_file"])
    if sha(arc) != manifest["arc_sha256"] or sha(demand) != manifest["demand_sha256"]:
        raise ValueError("input hash mismatch")
    problem = load(arc, demand)
    if "physical_link_file" in manifest:
        physical = resolve_local(manifest_path, manifest["physical_link_file"])
        if sha(physical) != manifest["physical_link_sha256"]:
            raise ValueError("physical link file hash mismatch")
        with physical.open(newline="", encoding="utf-8-sig") as handle:
            allowed_ids = {row[manifest["physical_link_id_column"]] for row in csv.DictReader(handle)}
        movement_ids = {row["physical_link_id"] for row in problem["arcs"] if row["arc_type"] == "movement"}
        if not movement_ids <= allowed_ids:
            raise ValueError("dynamic movement links do not map to accepted physical IDs")
    metadata = {"case_id": manifest["case_id"], "city": manifest["city"],
                "model_signature": problem["model_signature"],
                "arc_sha256": manifest["arc_sha256"], "demand_sha256": manifest["demand_sha256"],
                "case_manifest_sha256": sha(manifest_path),
                "dynamic_arcs": len(problem["ids"]), "dynamic_nodes": len(problem["nodes"]),
                "commodities": len(problem["commodities"]),
                "movement_link_ids": len({row["physical_link_id"] for row in problem["arcs"]
                                          if row["arc_type"] == "movement"}),
                "objective_unit": manifest["objective_unit"],
                "capacity_unit": manifest["capacity_unit"],
                "time_step_seconds": manifest.get("time_step_seconds")}
    return problem, manifest, metadata
