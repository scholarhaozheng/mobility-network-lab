#!/usr/bin/env python3
"""Validate the 2026-10-04 presentation migration without changing HK10 disclosure history."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess

RECORD = "docs/assets/atlas/HK10_PRESENTATION_20261004.json"
HISTORICAL = "docs/assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json"
SOURCE = "docs/assets/atlas/construction/r07-hong-kong-layered-construction.source.json"
SVG = "docs/assets/atlas/construction/r07-hong-kong-layered-construction.svg"
MIGRATED_PAGES = {"README.md", "docs/index.md", "docs/index.html"}
READING_PAGES = {
    "docs/volumes/overview.html", "docs/volumes/boston.html", "docs/volumes/sioux-falls.html", "docs/volumes/hong-kong.html",
    "docs/volumes/01-overview.md", "docs/volumes/02-boston.md", "docs/volumes/03-sioux-falls.md", "docs/volumes/04-hong-kong.md",
}
BASELINE = "6ce18b8bea5bf3b9b7caa6ee4c0ff4e701a34a8b"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path) -> dict:
    if not (root / RECORD).is_file():
        return {"status": "NOT_PRESENT", "checks": 0, "errors": [], "migrated_pages": {}}
    errors: list[str] = []
    checks = 0
    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)
    try:
        record = json.loads((root / RECORD).read_text(encoding="utf-8"))
        old = json.loads((root / HISTORICAL).read_text(encoding="utf-8"))
        check(record.get("schema") == "mcl_hk10_presentation_migration_v1", "Unknown HK10 presentation migration schema")
        check(record.get("source_baseline") == BASELINE, "HK10 migration baseline differs")
        check(record.get("historical_approval") == {"path": HISTORICAL, "sha256": sha(root / HISTORICAL)}, "Historical HK10 approval was changed")
        check(record.get("approved_identity") == old["approved_identity"], "HK10 migration changes the approved column identity")
        check(record.get("scientific_solver_rerun") is False, "Presentation migration claims a solver rerun")
        check(record.get("new_scientific_payload_disclosure") is False, "Presentation migration broadens scientific disclosure")
        authorization = record.get("authorization", {})
        check(authorization.get("type") == "current_maintainer_publication_instruction" and authorization.get("date") == "2026-10-04", "Current publication instruction missing")
        check(authorization.get("historical_approval_rewritten") is False, "Migration rewrites historical authorization")
        historical_hashes = record.get("historical_page_hashes", {})
        check(set(historical_hashes) == MIGRATED_PAGES, "HK10 migrated historical page scope differs")
        for relative in MIGRATED_PAGES:
            check(historical_hashes.get(relative) == old["shared_dependency_paths_sha256"].get(relative), f"Historical page identity differs: {relative}")
            if (root / ".git").exists():
                result = subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), "show", f"{BASELINE}:{relative}"], capture_output=True, check=False)
                check(result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == historical_hashes.get(relative), f"Historical page does not match the retained Git baseline: {relative}")
        current = record.get("current_presentation_paths_sha256", {})
        check(set(current) == MIGRATED_PAGES | READING_PAGES | {SOURCE, SVG}, "Current HK10 presentation file scope differs")
        for relative, digest in current.items():
            check((root / relative).is_file() and sha(root / relative) == digest, f"Current HK10 presentation hash differs: {relative}")
        source = json.loads((root / SOURCE).read_text(encoding="utf-8"))
        check(source.get("optimizer_calls") == 0, "HK10 redraw claims optimization calls")
        check(source.get("exports", {}).get("svg") == sha(root / SVG), "HK10 redraw export differs from the reviewed SVG")
        source_paths = {
            "docs/assets/cg_layered_companions_r1/DISPLAY_INPUTS.json",
            "docs/assets/cg_layered_companions_r1/hong_kong_display_edges.csv",
            "docs/assets/cg_layered_companions_r1/hong_kong_display_states.csv",
            "docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.source.json",
        }
        check({item["repository_path"] for item in source.get("sources", [])} == source_paths, "HK10 redraw source set differs")
        for item in source.get("sources", []):
            target = root / item["repository_path"]
            check(target.is_file() and sha(target) == item["sha256"], f"HK10 redraw source changed: {item['repository_path']}")
        with (root / "docs/assets/cg_layered_companions_r1/hong_kong_display_edges.csv").open(encoding="utf-8-sig", newline="") as handle:
            edges = list(csv.DictReader(handle))
        selected = [edge for edge in edges if edge["role"] == "selected"]
        check(source.get("selected_arc_records") == selected, "HK10 redraw altered selected arc identities, endpoints or times")
        check(source.get("displayed_arc_count") == len(edges) == 7, "HK10 redraw expanded the seven-edge local excerpt")
        check(source.get("selected_arc_ids") == [edge["arc_id"] for edge in selected], "HK10 redraw selected-arc order differs")
        check(source.get("displayed_time_indices") == list(range(24, 31)), "HK10 redraw time layers differ")
        check("no waiting arc" in source.get("caption", "").lower() and "zero-time turn" in source.get("caption", "").lower(), "HK10 redraw lost turn/wait scope")
        for relative in ("docs/index.html", "docs/volumes/hong-kong.html", "docs/volumes/04-hong-kong.md"):
            text = (root / relative).read_text(encoding="utf-8")
            check("r07-hong-kong-layered-construction.svg" in text, f"Current reading page lost the HK10 construction redraw: {relative}")
        for relative, targets in (("README.md", ("docs/volumes/04-hong-kong.md", "docs/volumes/hong-kong.html")), ("docs/index.md", ("volumes/hong-kong.html",))):
            text = (root / relative).read_text(encoding="utf-8")
            check(any(target in text for target in targets), f"Current entry page lost the complete HK10 reading destination: {relative}")
        return {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
                "migrated_pages": {path: current[path] for path in MIGRATED_PAGES if path in current}}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"Invalid HK10 presentation migration: {exc}")
        return {"status": "FAIL", "checks": checks, "errors": errors, "migrated_pages": {}}


if __name__ == "__main__":
    result = validate(Path(__file__).resolve().parents[2])
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))
