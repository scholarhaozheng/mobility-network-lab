#!/usr/bin/env python3
"""Validate the dated presentation continuation, separately from HK10 approval.

Whole-page bytes can change for city navigation and current coverage. This
receipt grants no scientific approval: the old exact payload hashes and five
canonical HK scientific-content sections remain fixed to the published baseline.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from bs4 import BeautifulSoup

RECEIPT = "docs/assets/atlas/HK10_PUBLICATION_20261008.json"
BASELINE = "f2e97d0ee760a0feac65d6b5731037caea7324f7"
HISTORICAL = "docs/assets/three_city_r2/HK10_DISCLOSURE_APPROVAL_CURRENT.json"
MIGRATION = "docs/assets/atlas/HK10_PRESENTATION_20261004.json"
EDITORIAL = "docs/assets/atlas/HK10_EDITORIAL_20261005.json"
DERIVATIVE = "docs/assets/cg_layered_companions_r1/HK10_LAYERED_COMPANION_DISCLOSURE.json"
SOURCE = "docs/assets/atlas/construction/r07-hong-kong-layered-construction.source.json"
SVG = "docs/assets/atlas/construction/r07-hong-kong-layered-construction.svg"
RECORDS = (HISTORICAL, MIGRATION, EDITORIAL, DERIVATIVE)
# These scientific DOM fingerprints were extracted from BASELINE, not from
# the changed pages. Only CRLF and empty compatibility anchors are normalized.
PROTECTED_SECTIONS = {
    "docs/index.html": ("article.case-atlas[data-city=\"hong-kong\"]", "736a4364a202bda53a73916d460a972c2f1e4a704fd88dacfeb8a54e6aa22b5c"),
    "docs/volumes/hong-kong.html": ("article", "ee283456fac7a82f06b55ce8fe93adcfe9934f4f9ccef706c225950d59ddefc4"),
    "docs/cases/hong-kong.html": ("main", "43838426ff22b3fa0e39919532dae2cdd421699ed4f357f07450f44898c3e421"),
    "docs/cases/hong-kong-space-time.html": ("main", "da6306436ea64cda5562f517fb53bc99e689d3209147c2f610ceab824b9d8373"),
    "docs/full-walkthrough.html": ("main", "e5f1a09b700e73fa640a0a6ca263993fd9c23aaf137103c6e253603dda38c571"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return digest(path.read_bytes())


def protected_hash(text: str, selector: str) -> str:
    nodes = BeautifulSoup(text.replace("\r\n", "\n"), "html.parser").select(selector)
    if len(nodes) != 1:
        raise ValueError(f"Expected one protected section: {selector}")
    section = nodes[0]
    for anchor in section.select("a[id]"):
        if not anchor.get_text(strip=True) and not anchor.get("href") and not anchor.find(True):
            anchor.decompose()
    return digest(str(section).encode("utf-8"))


def expected_scope(root: Path) -> tuple[dict, dict, dict]:
    documents = {path: json.loads((root / path).read_text(encoding="utf-8")) for path in RECORDS}
    approval, editorial, derivative = documents[HISTORICAL], documents[EDITORIAL], documents[DERIVATIVE]
    pages = {path: value for path, value in editorial["current_presentation_paths_sha256"].items()
             if path.endswith((".html", ".md"))}
    pages.update({path: value for path, value in approval["shared_dependency_paths_sha256"].items()
                  if path.endswith((".html", ".md")) and path not in pages})
    pages.update(approval["current_presentation_dependencies_sha256"])
    science = dict(approval["approved_payload_paths_sha256"])
    science.update({path: value for path, value in approval["shared_dependency_paths_sha256"].items()
                    if path not in pages})
    science.update(derivative["derived_asset_paths_sha256"])
    science.update(derivative["shared_dependency_paths_sha256"])
    science.update({path: editorial["current_presentation_paths_sha256"][path] for path in (SOURCE, SVG)})
    return pages, science, documents


def validate(root: Path) -> dict:
    if not (root / RECEIPT).is_file():
        return {"status": "NOT_PRESENT", "checks": 0, "errors": [], "current_pages": {}}
    checks, errors = 0, []
    def check(ok: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(message)
    try:
        record = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
        baseline_pages, science, documents = expected_scope(root)
        check(record.get("schema") == "mcl_hk10_publication_continuation_v1", "Unknown HK10 continuation schema")
        check(record.get("source_baseline") == BASELINE, "HK10 continuation baseline changed")
        check(record.get("record_type") == "presentation-change-verification-not-scientific-approval", "HK10 continuation misrepresents its authority")
        check(record.get("publication_instruction") == {"date": "2026-10-08", "instruction_original": "推送吧", "scope": "Publish the reviewed current presentation"}, "Current presentation publication instruction differs")
        for flag in ("historical_approval_rewritten", "scientific_solver_rerun", "new_hk10_scientific_payload_disclosure", "new_artifact_level_scientific_approval"):
            check(record.get(flag) is False, "HK10 continuation overstates authority: " + flag)
        check(record.get("approved_identity") == documents[HISTORICAL]["approved_identity"], "HK10 continuation changes approved identity")
        check(record.get("historical_records_sha256") == {path: sha(root / path) for path in RECORDS}, "HK10 continuation historical record binding differs")
        check(record.get("baseline_presentation_paths_sha256") == baseline_pages, "HK10 continuation old page hashes differ from historical records")
        check(record.get("unchanged_scientific_paths_sha256") == science, "HK10 continuation scientific scope or old hashes differ")
        current = record.get("current_presentation_paths_sha256", {})
        check(set(current) == set(baseline_pages), "HK10 continuation changes the allowed presentation page set")
        check(record.get("changed_pages") == sorted(path for path in baseline_pages if current.get(path) != baseline_pages[path]), "HK10 continuation changed-page inventory differs")
        for path, expected in {**science, **current}.items():
            check((root / path).is_file() and sha(root / path) == expected, "HK10 continuation file missing or changed: " + path)
        proofs = {path: {"selector": selector, "normalization": "html.parser; CRLF-to-LF; remove empty compatibility anchors", "baseline_sha256": expected, "current_sha256": expected}
                  for path, (selector, expected) in PROTECTED_SECTIONS.items()}
        check(record.get("protected_scientific_sections") == proofs, "HK10 continuation protected-section proof differs")
        for path, (selector, expected) in PROTECTED_SECTIONS.items():
            check(protected_hash((root / path).read_text(encoding="utf-8"), selector) == expected, "HK10 scientific presentation content changed: " + path)
        if (root / ".git").exists():
            for path, expected in {**baseline_pages, **science, **{path: sha(root / path) for path in RECORDS}}.items():
                result = subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), "show", f"{BASELINE}:{path}"], capture_output=True, check=False)
                check(result.returncode == 0 and digest(result.stdout) == expected, "HK10 continuation does not match the published Git baseline: " + path)
                if path in PROTECTED_SECTIONS and result.returncode == 0:
                    selector, expected_section = PROTECTED_SECTIONS[path]
                    check(protected_hash(result.stdout.decode("utf-8"), selector) == expected_section, "HK10 baseline section proof differs: " + path)
        return {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
                "current_pages": current if not errors else {}, "scientific_hashes_retained": len(science), "protected_sections": len(PROTECTED_SECTIONS)}
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append("Invalid HK10 publication continuation: " + str(exc))
        return {"status": "FAIL", "checks": checks, "errors": errors, "current_pages": {}}


if __name__ == "__main__":
    result = validate(Path(__file__).resolve().parents[2])
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))
