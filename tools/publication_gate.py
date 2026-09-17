#!/usr/bin/env python3
"""Run the v2 public-release safety and claim-boundary gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mobilitylab.data.evidence import load_evidence_catalog


def main() -> int:
    errors: list[str] = []
    checks = 0

    repository = subprocess.run(
        [sys.executable, "-B", str(ROOT / "tools" / "check_repository.py"), "--publication"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        repository_result = json.loads(repository.stdout)
    except json.JSONDecodeError:
        repository_result = {"status": "FAIL", "errors": [repository.stdout, repository.stderr]}
    if repository.returncode != 0:
        errors.extend(f"repository: {item}" for item in repository_result.get("errors", []))
    checks += int(repository_result.get("checks", 0))

    forbidden_parts = {
        "external_data",
        "private_data",
        "private_audit",
        "conversation_exports",
        "cache",
        "release",
        "paper",
        "manuscript",
    }
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part.lower() in forbidden_parts for part in relative.parts):
            errors.append(f"Forbidden public path: {relative.as_posix()}")
        if path.is_file() and path.suffix.lower() in {".zip", ".7z", ".pbf", ".gpkg"}:
            errors.append(f"Forbidden public payload: {relative.as_posix()}")
        checks += 1

    catalog = load_evidence_catalog()
    checks += len(catalog["layers"])
    if catalog["omdv_visuals"]["included"]:
        errors.append("OMDV visual included outside the current selected-file allowlist")

    provenance = json.loads((ROOT / "catalog" / "omdv-provenance.json").read_text())
    if provenance["code_redistribution_status"] != "selected_original_files_authorized_mit":
        errors.append("OMDV selected-copy authorization status is missing or incorrect")

    allowlist_path = ROOT / provenance.get("authorized_file_allowlist", "")
    if not allowlist_path.is_file():
        errors.append("OMDV authorized-file allowlist is missing")
        allowlist = {"authorization": {}, "files": []}
    else:
        allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
    if allowlist.get("authorization", {}).get("license_in_this_repository") != "MIT":
        errors.append("OMDV selected-copy license is not recorded as MIT")

    listed_destinations: set[str] = set()
    listed_sources: set[str] = set()
    for item in allowlist.get("files", []):
        destination = item.get("destination_path", "")
        if not destination or destination in listed_destinations:
            errors.append(f"Invalid or duplicate OMDV allowlist destination: {destination}")
            continue
        listed_destinations.add(destination)
        if item.get("source_path"):
            listed_sources.add(item["source_path"])
            for field in ("source_last_commit", "source_sha256"):
                if not item.get(field):
                    errors.append(f"Missing {field} for selected source: {destination}")
        target = ROOT / destination
        if not target.is_file():
            errors.append(f"Allowlisted OMDV target is missing: {destination}")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != item.get("destination_sha256"):
            errors.append(f"Allowlisted OMDV target hash mismatch: {destination}")
        checks += 5

    actual_omdv_tree = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src" / "mobilitylab" / "omdv").rglob("*.py")
    }
    allowed_omdv_tree = {
        path for path in listed_destinations if path.startswith("src/mobilitylab/omdv/")
    }
    if actual_omdv_tree != allowed_omdv_tree:
        errors.append(
            "OMDV package differs from explicit allowlist: "
            f"missing={sorted(allowed_omdv_tree - actual_omdv_tree)}, "
            f"extra={sorted(actual_omdv_tree - allowed_omdv_tree)}"
        )
    checks += len(actual_omdv_tree) + 1

    for item in provenance["candidate_code_files"]:
        if item["public_tree_action"] == "copied_authorized_mit" and item["path"] not in listed_sources:
            errors.append(f"Authorized OMDV source is absent from the allowlist: {item['path']}")
        if item["public_tree_action"] == "copied":
            errors.append(f"Unscoped OMDV code copy: {item['path']}")
        checks += 1
    for package in provenance["accepted_packages"].values():
        if package["copied"]:
            errors.append(f"OMDV archive copied into public tree: {package['path_in_source']}")
        checks += 1

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_readme = [
        "Open city data → model-ready interfaces → assignment / optimization → verified results",
        "city compiler and hierarchical zones",
        "GPS traces and map matching",
        "Policy Bush",
        "ADMM",
        "These evidence layers are not additive",
        "mcl_data.py catalog-city-match",
        "named-entity matching",
    ]
    for phrase in required_readme:
        if phrase not in readme:
            errors.append(f"README missing required product or roadmap language: {phrase}")
        checks += 1
    readme_images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
    expected_image = "docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png"
    if readme_images != [expected_image]:
        errors.append(
            f"README must contain exactly the approved 250OD image; found {readme_images}"
        )
    if "Repository candidate" in readme:
        errors.append("README still contains internal repository-candidate language")
    checks += 2

    homepage = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "assets" / "site.css").read_text(encoding="utf-8")
    render_contract = {
        "responsive viewport": 'name="viewport" content="width=device-width,initial-scale=1"' in homepage,
        "mobile breakpoint": "@media(max-width:800px)" in css,
        "single-column mobile grids": ".stripin,.cards,.tiles,.split{grid-template-columns:1fr}" in css,
        "responsive benchmark images": ".benchmark-feature img{display:block;width:100%;height:auto}" in css,
        "open-data desktop section": "Open mobility data" in homepage,
        "data-tools section": "Executable data tools" in homepage,
        "data-tools command": "mcl_data.py catalog-city-match" in homepage,
        "data-tools navigation": 'href="data-tools.html"' in homepage,
    }
    for label, passed in render_contract.items():
        if not passed:
            errors.append(f"Generated-site render contract failed: {label}")
        checks += 1

    datasets = json.loads((ROOT / "catalog" / "datasets.json").read_text())["datasets"]
    by_id = {item["id"]: item for item in datasets}
    for item_id, expected in (("sioux-200od", 200), ("sioux-250od", 250)):
        if by_id.get(item_id, {}).get("od_pairs") != expected:
            errors.append(f"{item_id} is not labeled as its selected-OD subset")
        checks += 1

    result = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "omdv_code_bundled": True,
        "omdv_code_allowlist_valid": not any(
            "allowlist" in error.lower() or "omdv package" in error.lower()
            for error in errors
        ),
        "omdv_visuals_bundled": False,
        "bulk_scientific_rerun_performed": False
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
