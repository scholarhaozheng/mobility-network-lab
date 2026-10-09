#!/usr/bin/env python3
"""Freeze the current whole-page hashes without altering historical HK approval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from check_hk10_publication import (BASELINE, HISTORICAL, PROTECTED_SECTIONS,
                                   RECEIPT, RECORDS, expected_scope,
                                   protected_hash, sha, validate)


def build_record(root: Path) -> dict:
    baseline, science, documents = expected_scope(root)
    for path, expected in science.items():
        if sha(root / path) != expected:
            raise ValueError("Cannot freeze changed HK scientific asset: " + path)
    for path, (selector, expected) in PROTECTED_SECTIONS.items():
        if protected_hash((root / path).read_text(encoding="utf-8"), selector) != expected:
            raise ValueError("Cannot freeze changed HK scientific content: " + path)
    current = {path: sha(root / path) for path in sorted(baseline)}
    return {
        "schema": "mcl_hk10_publication_continuation_v1",
        "record_type": "presentation-change-verification-not-scientific-approval",
        "source_baseline": BASELINE,
        "publication_instruction": {"date": "2026-10-08", "instruction_original": "推送吧", "scope": "Publish the reviewed current presentation"},
        "change_scope": "Current homepage, README, nine-case navigation and coverage presentation. Canonical HK scientific text, figures, data and approved model-generated 77-arc identity retain the published baseline. This verification record is separate from historical artifact-level approval and does not grant approval to new HK data.",
        "historical_approval_rewritten": False,
        "scientific_solver_rerun": False,
        "new_hk10_scientific_payload_disclosure": False,
        "new_artifact_level_scientific_approval": False,
        "historical_records_sha256": {path: sha(root / path) for path in RECORDS},
        "approved_identity": documents[HISTORICAL]["approved_identity"],
        "baseline_presentation_paths_sha256": baseline,
        "current_presentation_paths_sha256": current,
        "changed_pages": sorted(path for path in baseline if baseline[path] != current[path]),
        "unchanged_scientific_paths_sha256": science,
        "protected_scientific_sections": {
            path: {"selector": selector, "normalization": "html.parser; CRLF-to-LF; remove empty compatibility anchors; restore original image markup from performance previews", "baseline_sha256": expected, "current_sha256": expected}
            for path, (selector, expected) in PROTECTED_SECTIONS.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    record = build_record(root)
    (root / RECEIPT).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = validate(root)
    print(json.dumps(result, indent=2))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
