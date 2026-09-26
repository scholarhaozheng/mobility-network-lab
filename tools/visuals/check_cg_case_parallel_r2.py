#!/usr/bin/env python3
"""No-solve checks for the Boston/Sioux CG public text and presentation merge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
TITLES = (
    "From the physical network to time-indexed columns",
    "Phase I restores feasibility",
    "A new path can help a different OD",
    "Phase II improves the real-path objective",
    "Final physical-link movement flow and validation",
    "Independent pricing closure",
    "Reproduction and limits",
)
LEGACY_ANCHORS = {
    "boston": (
        "network-and-construction-physical-geography-versus-time-states",
        "phase-i-total-feasibility-and-od-level-coupling",
        "r4-independent-pricing-closure-and-final-validation",
        "source-reproduction-and-limits",
    ),
    "sioux": (
        "construction-cutaway", "paired-phase-i-figures",
        "recorded-results-what-the-two-saved-runs-show", "od-level-clearance",
        "clearance-events-and-selected-columns",
        "xs170xs169-capacity-reallocation-audit", "final-validation",
        "limits-and-next-experiment", "shared-capacity-event",
        "od-level-supplementary-view", "reproduction-and-source-boundaries",
    ),
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Invalid PNG signature: {path}")
    return struct.unpack(">II", header[16:24])


def main() -> int:
    errors: list[str] = []
    checks = 0
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    gallery = (DOCS / "visualizations.md").read_text(encoding="utf-8")
    method = (DOCS / "methods" / "space-time-cg.md").read_text(encoding="utf-8")
    pages = {
        "boston": (DOCS / "cases" / "boston-space-time.md").read_text(encoding="utf-8"),
        "sioux": (DOCS / "cases" / "sioux-space-time.md").read_text(encoding="utf-8"),
    }

    for city, page in pages.items():
        positions = [page.find(f"## {i}. {title}") for i, title in enumerate(TITLES, 1)]
        require(all(pos >= 0 for pos in positions) and positions == sorted(positions),
                f"{city}: seven canonical headings missing or out of order", errors)
        checks += 1
        for anchor in LEGACY_ANCHORS[city]:
            require(f'<a id="{anchor}"></a>' in page,
                    f"{city}: legacy anchor missing: {anchor}", errors)
            checks += 1

    for name, page in (("README", readme), ("gallery", gallery),
                       ("method", method), *pages.items()):
        for forbidden in ("artificial mass", "final real-column pool",
                          "identical-graph", "same-subset"):
            require(forbidden not in page.lower(),
                    f"{name}: obsolete shared CG term: {forbidden}", errors)
            checks += 1

    require("10/10 demands at `1e-6`" in pages["boston"],
            "Boston independent-closure status missing", errors)
    require("not established for the retained 200-OD and 250-OD runs" in pages["sioux"],
            "Sioux independent-closure boundary missing", errors)
    require("second-machine receiver check" in pages["boston"] and "pending" in pages["boston"],
            "Boston pending receiver qualification missing", errors)
    checks += 3

    boston_sequence = "docs/assets/presentation_r5/boston_cg_case_sequence.png"
    sioux_sequence = "docs/assets/presentation_r5/sioux_cg_case_sequence.png"
    for path in (boston_sequence, sioux_sequence):
        require(re.search(rf'<img src="{re.escape(path)}" width="100%"', readme) is not None,
                f"README missing full-width case sequence: {path}", errors)
        checks += 1
    require(readme.index("### Boston / Population and Household Preparation")
            < readme.index("### Boston / Bounded finite space–time CG pilot")
            < readme.index("### Sioux Falls / Historical 200/250-OD finite space–time CG"),
            "README case sequence moved ahead of Boston foundation or outside city order", errors)
    checks += 1

    unique = (
        "boston/space_time_cg_r4/boston_pricing_closure_continuation.png",
        "boston/space_time_cg_r4/boston_pricing_closure_by_demand.png",
        "boston/space_time_cg_r4/boston_cg_validation.png",
        "sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png",
        "sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png",
        "sioux/phase_i_r1/od_level_phase_i_clearance.png",
        "presentation_r3/sioux_capacity_exchange.png",
        "benchmarks/sioux_200od_final_physical_link_flow.png",
        "benchmarks/sioux_250od_final_physical_link_flow.png",
        "presentation_r4/cg_experiments_overview.png",
    )
    public_text = readme + gallery + pages["boston"] + pages["sioux"]
    for rel in unique:
        require((ASSETS / rel).is_file(), f"Accepted unique asset missing: {rel}", errors)
        require(rel in public_text, f"Accepted unique asset de-linked: {rel}", errors)
        checks += 2

    manifest = json.loads((ASSETS / "presentation_r5" / "CG_CASE_SEQUENCE_SOURCES.json")
                          .read_text(encoding="utf-8"))
    for rel, expected in manifest["sources"].items():
        path = ASSETS / rel
        require(path.is_file(), f"Composite source missing: {rel}", errors)
        if path.is_file():
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                    f"Composite source hash mismatch: {rel}", errors)
        checks += 2
    for city in ("boston", "sioux"):
        png = ASSETS / "presentation_r5" / f"{city}_cg_case_sequence.png"
        svg = png.with_suffix(".svg")
        require(png_size(png) == (3000, 2400), f"{city}: wrong canvas", errors)
        labels = ["".join(node.itertext()) for node in ET.parse(svg).getroot().iter()
                  if node.tag.endswith("}text")]
        expected_labels = list("abcdef") + (["Not established"] if city == "sioux" else [])
        require(labels == expected_labels,
                f"{city}: unexpected slide-style title or in-figure prose: {labels}", errors)
        require(png.name in pages[city], f"{city}: sequence absent from case page", errors)
        checks += 3
    canonical = ASSETS / "presentation_r5" / "sioux_shared_capacity_canonical.png"
    canonical_meta = json.loads((ASSETS / "presentation_r5" /
                                 "SIOUX_CAPACITY_CANONICAL_SOURCES.json")
                                .read_text(encoding="utf-8"))
    for rel, expected in canonical_meta["source_hashes"].items():
        path = ASSETS / rel
        require(path.is_file(), f"Sioux canonical source missing: {rel}", errors)
        if path.is_file():
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                    f"Sioux canonical source hash mismatch: {rel}", errors)
        checks += 2
    require(png_size(canonical)[0] >= 1800, "Sioux canonical capacity figure too small", errors)
    require(any(node.tag.endswith("}text") for node in
                ET.parse(canonical.with_suffix(".svg")).getroot().iter()),
            "Sioux canonical capacity SVG text not editable", errors)
    require("sioux_shared_capacity_canonical.png" in readme and
            "sioux_shared_capacity_canonical.png" in pages["sioux"],
            "Sioux canonical capacity figure not used in README/case", errors)
    checks += 3
    overview = ASSETS / "presentation_r5" / "boston_sioux_cg_parallel_overview.png"
    require(png_size(overview) == (2700, 1500), "Overview has wrong canvas", errors)
    require(overview.name in readme and overview.name in gallery,
            "Overview missing from README/gallery", errors)
    checks += 2

    home = (DOCS / "index.html").read_text(encoding="utf-8")
    require('index.html#cg-experiments">CG experiments' in home,
            "Generated site navigation omits CG", errors)
    for stem in ("boston_cg_case_sequence.png", "sioux_cg_case_sequence.png",
                 "boston_sioux_cg_parallel_overview.png"):
        require(stem in home, f"Generated homepage missing {stem}", errors)
        checks += 1

    result = {"status": "PASS" if not errors else "FAIL", "checks": checks,
              "errors": errors, "composites": 3,
              "boston_closure": "10/10 at 1e-6",
              "sioux_closure": "not established"}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
