#!/usr/bin/env python3
"""No-solve check of the exact HK10 approval and current presentation wording."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from check_hk10_presentation import validate as validate_current_presentation

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "docs/assets/three_city_r2"
errors: list[str] = []
checks = 0


def check(ok: bool, message: str) -> None:
    global checks
    checks += 1
    if not ok:
        errors.append(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


historical_path = ASSET / "DISCLOSURE_STATUS_R2.json"
historical = json.loads(historical_path.read_text(encoding="utf-8"))
approved = json.loads((ASSET / "HK10_DISCLOSURE_APPROVAL_CURRENT.json").read_text(encoding="utf-8"))
check(historical["owner_artifact_level_publication_approval"] == "PENDING",
      "historical R2 pending-decision record was rewritten")
check(approved["status"] == "APPROVED_EXACT_HK10_EXCERPT", "current exact HK10 approval absent")
check(approved["historical_decision_record"]["sha256"] == sha(historical_path),
      "historical decision record hash mismatch")
presentation_migration = validate_current_presentation(ROOT)
errors.extend(presentation_migration["errors"])
checks += presentation_migration["checks"]
migrated_pages = presentation_migration["migrated_pages"]
continued_pages = presentation_migration.get("continued_pages", {})

identity = approved["approved_identity"]
check(identity == {"demand_id": "HK10", "column_id": "ORACLE_R1_HK10_K1",
                   "ordered_arc_count": 77, "final_positive_flow_pce": 0.8352150831808043,
                   "excerpt_csv_sha256": sha(ROOT / "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv")},
      "exact approved HK10 path identity differs")
with (ROOT / "docs/assets/three_city_r1/data/hong_kong_selected_generated_column.csv").open(
    encoding="utf-8-sig", newline=""
) as handle:
    rows = list(csv.DictReader(handle))
check(len(rows) == 77, "approved excerpt arc count differs")

payload = approved["approved_payload_paths_sha256"]
shared = approved["shared_dependency_paths_sha256"]
recorded = set(historical["pending_paths"])
check(set(payload).isdisjoint(shared), "payload and shared dependencies overlap")
check(set(payload) | set(shared) == recorded, "approved exact group differs from recorded dependencies")
check(len(payload) == 22 and len(shared) == 9, "approved dependency partition changed")
for rel, digest in {**payload, **shared}.items():
    target = ROOT / rel
    current_digest = continued_pages.get(rel, migrated_pages.get(rel, digest))
    check(target.is_file() and sha(target) == current_digest, f"approved dependency missing or hash changed: {rel}")
    check(not any(token in rel.lower() for token in ("full_pool", "dual_array", "raw_gps", "urbannav", "trajectory")),
          f"unapproved private scope entered exact allowlist: {rel}")
check("not blanket authorization" in approved["shared_dependency_rule"].lower(),
      "shared dependency rule over-authorizes unrelated data")
check(approved["scientific_solver_rerun"] is False, "approval record claims a model rerun")
presentation = approved.get("current_presentation_dependencies_sha256", {})
expected_presentation = {"docs/full-walkthrough.md", "docs/full-walkthrough.html"}
check(set(presentation) == expected_presentation,
      "layered presentation dependency set differs from the exact added walkthrough pages")
for rel, digest in presentation.items():
    check((ROOT / rel).is_file() and sha(ROOT / rel) == continued_pages.get(rel, digest),
          f"new exact-HK10 presentation page missing or hash changed: {rel}")
    check(not any(token in rel.lower() for token in ("full_pool", "dual_array", "raw_gps", "urbannav", "trajectory")),
          f"private scope entered presentation dependency: {rel}")

extension_path = ROOT / "docs/assets/cg_layered_companions_r1/HK10_LAYERED_COMPANION_DISCLOSURE.json"
extension = json.loads(extension_path.read_text(encoding="utf-8"))
check(extension["status"] == "APPROVED_SAME_EXACT_HK10_EXCERPT", "HK10 derivative status differs")
check(extension["parent_approval"] == {
    "path": "docs/assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json",
    "sha256": sha(ASSET / "HK10_DISCLOSURE_APPROVAL_CURRENT.json")},
    "HK10 derivative parent approval hash differs")
check(extension["approved_identity"] == {
    "demand_id": "HK10", "column_id": "ORACLE_R1_HK10_K1", "ordered_arc_count": 77,
    "excerpt_csv_sha256": identity["excerpt_csv_sha256"]},
    "HK10 derivative identity differs")
prefix = "docs/assets/cg_layered_companions_r1/"
expected_derivatives = {
    prefix + "hong_kong_display_edges.csv", prefix + "hong_kong_display_states.csv",
    *(prefix + "hong_kong_layered_space_time_construction." + suffix for suffix in
      ("caption.html", "caption.md", "png", "source.json", "svg"))}
expected_shared = {prefix + "DISPLAY_INPUTS.json", "tools/visuals/render_cg_layered_companions.py"}
derived = extension["derived_asset_paths_sha256"]
dependencies = extension["shared_dependency_paths_sha256"]
check(set(derived) == expected_derivatives, "HK10 derivative exact asset set differs")
check(set(dependencies) == expected_shared, "HK10 derivative shared dependency set differs")
for rel, digest in {**derived, **dependencies}.items():
    target = ROOT / rel
    check(target.is_file() and sha(target) == digest, f"HK10 derivative missing or hash changed: {rel}")
    check(not any(token in rel.lower() for token in ("full_pool", "dual_array", "raw_gps", "urbannav", "trajectory")),
          f"private scope entered HK10 derivative extension: {rel}")
expected_pages = {"README.md", "docs/index.md", "docs/index.html",
                  "docs/cases/hong-kong-space-time.md", "docs/cases/hong-kong-space-time.html",
                  *expected_presentation}
check(set(extension["page_dependencies_recorded_in_parent_approval"]) == expected_pages,
      "HK10 derivative page dependency set differs")
check(expected_pages <= set(shared) | set(presentation),
      "HK10 derivative pages are not recorded in the exact approval/presentation dependencies")
for rel in expected_pages:
    content = (ROOT / rel).read_text(encoding="utf-8")
    if rel not in migrated_pages:
        check("hong_kong_layered_space_time_construction.png" in content,
              f"HK10 derived figure not embedded in approved page: {rel}")
check("not authorize unrelated data" in extension["shared_dependency_rule"].lower(),
      "HK10 derivative shared dependency rule over-authorizes data")
check(extension["scientific_solver_rerun"] is False, "HK10 derivative record claims model rerun")

current = ["README.md", "docs/index.md", "docs/index.html", *sorted(expected_presentation), "docs/cases/hong-kong.md",
           "docs/cases/hong-kong.html", "docs/cases/hong-kong-space-time.md",
           "docs/cases/hong-kong-space-time.html"]
for family in ("generated_column_time_indexed_path", "finite_space_time_case_sequence"):
    current.extend(f"docs/assets/three_city_r2/hong_kong_{family}.{ext}"
                   for ext in ("svg", "caption.md", "caption.html", "source.json"))
for rel in current:
    content = (ROOT / rel).read_text(encoding="utf-8")
    check(not re.search(r"approval pending|pending owner approval|disclosure pending|awaits owner approval|review-only pending|pending-disclosure",
                        content, re.I), f"obsolete HK10 approval-pending wording: {rel}")
    if rel.endswith(("README.md", "hong-kong.md", "hong-kong-space-time.md")):
        check("model-generated" in content.lower(), f"model-generated scope absent: {rel}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
walkthrough = (ROOT / "docs/full-walkthrough.md").read_text(encoding="utf-8")
cg_method = (ROOT / "docs/methods/space-time-cg.md").read_text(encoding="utf-8")
check('<a id="cg-experiments"></a>' in readme and
      any(link in readme for link in ("docs/methods/space-time-cg.md#cg-experiments",
                                     "https://scholarhaozheng.github.io/mobility-network-lab/volumes/overview.html#src-docs-methods-space-time-cg-document")),
      "shortened homepage lost the cross-case CG compatibility pointer")
check(cg_method.count("### Executed finite space–time CG experiments") == 1 and
      walkthrough.count("### Executed finite space–time CG experiments") == 1,
      "executed CG block is not preserved in the canonical method and complete walkthrough")
for needle in ("boston_sioux_cg_parallel_overview.png", "| Executed evidence | Boston | Sioux Falls | Hong Kong |",
               "| **Phase I** |", "| **Phase II** |", "| **Pricing certificate** |"):
    check(needle in cg_method and needle in walkthrough,
          f"moved CG block lost accepted canonical/walkthrough content: {needle}")
check('id="cg-experiments"' in (ROOT / "docs/index.html").read_text(encoding="utf-8"),
      "generated homepage lost cg-experiments fragment")

result = {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
          "exact_hk10_public_disclosure": "APPROVED", "historical_r2_decision": "PENDING_AT_THAT_TIME",
          "scientific_solver_rerun": False,
          "current_presentation_migration": presentation_migration["status"]}
print(json.dumps(result, indent=2, ensure_ascii=False))
raise SystemExit(bool(errors))
