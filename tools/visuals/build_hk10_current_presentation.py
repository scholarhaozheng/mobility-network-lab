#!/usr/bin/env python3
"""Record the specifically authorized 2026-10-04 reading presentation; leave historical HK10 approvals intact."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from check_hk10_presentation import BASELINE, HISTORICAL, MIGRATED_PAGES, READING_PAGES, RECORD, SOURCE, SVG

ROOT = Path(__file__).resolve().parents[2]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    old = json.loads((ROOT / HISTORICAL).read_text(encoding="utf-8"))
    record = {
        "schema": "mcl_hk10_presentation_migration_v1",
        "release_id": "20261004-r12",
        "source_baseline": BASELINE,
        "authorization": {
            "type": "current_maintainer_publication_instruction",
            "date": "2026-10-04",
            "instruction_translation": "Update the code entry and README, change the homepage font, then commit and push, including the code entry.",
            "instruction_original_language": "zh",
            "instruction_original_sha256": "d91e0afc896bee4342ef5f619fb4c53f7741ad4e7fcd2a3173ee7b94b880a868",
            "font_confirmation": "Keep DejaVu Serif for the homepage; retain monospace for code.",
            "historical_approval_rewritten": False,
        },
        "scope": "Current reading presentation and code-entry publication. The existing exact 77-arc model-generated HK10 excerpt is unchanged. The construction redraw uses the same already-published edges, states and approved column identity. This record does not authorize unrelated input tables, point trajectories, solver states or path pools.",
        "historical_approval": {"path": HISTORICAL, "sha256": sha(ROOT / HISTORICAL)},
        "approved_identity": old["approved_identity"],
        "historical_page_hashes": {path: old["shared_dependency_paths_sha256"][path] for path in sorted(MIGRATED_PAGES)},
        "current_presentation_paths_sha256": {path: sha(ROOT / path) for path in sorted(MIGRATED_PAGES | READING_PAGES | {SOURCE, SVG})},
        "scientific_solver_rerun": False,
        "new_scientific_payload_disclosure": False,
    }
    (ROOT / RECORD).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(RECORD)

if __name__ == "__main__":
    main()
