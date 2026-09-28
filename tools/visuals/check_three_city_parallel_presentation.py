#!/usr/bin/env python3
"""Solver-free three-city public presentation, provenance and retention checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets/three_city_r1"
TABLES = ROOT / "docs/data/three_city_r1"
CITIES = {"boston": "Boston", "sioux": "Sioux Falls", "hong_kong": "Hong Kong"}
FAMILIES = (
    "physical_to_time_expanded_graph", "generated_column_time_indexed_path",
    "time_expanded_to_physical_link_flow", "finite_space_time_case_sequence",
)
CASE_HEADINGS = (
    "Role in the repository", "Scope and statistics", "GMNS, zones, and source evidence",
    "Demand, transit, and observations", "Static assignment", "Finite time-expanded algorithms",
    "Independent verification", "City-specific evidence and limits", "Reproduction",
)
FINITE_HEADINGS = (
    "Case role, scope, and model statistics",
    "From the physical network to the finite time-expanded graph",
    "A generated column as a time-indexed path", "Phase I restores feasibility",
    "Shared capacity couples different OD demands", "Phase II improves the real-path objective",
    "From time-expanded flows back to final physical-link movement flow",
    "Reference-objective agreement", "Independent pricing closure",
    "Reproduction, evidence boundary, and limits",
)
HOME_HEADINGS = (
    "01 / Shared computational architecture", "02 / Cross-city coverage matrix",
    "03 / Comparable statistics", "04 / Case study — Boston",
    "05 / Case study — Sioux Falls", "06 / Case study — Hong Kong",
    "07 / Methods, reproduction, evidence, and limits",
)
STATUS = {
    "Verified", "Verified bounded case", "Reference-objective agreement",
    "Independent pricing closure established", "Gated", "Not established",
    "Not demonstrated", "Not part of this benchmark", "Pending accepted result",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primary(text: str) -> str:
    return re.sub(r"<details>.*?</details>", "", text, flags=re.S)


def ordered_headings(path: Path, headings: tuple[str, ...]) -> list[str]:
    visible = primary(path.read_text(encoding="utf-8"))
    found = re.findall(r"^#{2,3}\s+(.+)$", visible, flags=re.M)
    pos = -1
    issues = []
    for heading in headings:
        try:
            next_pos = found.index(heading, pos + 1)
        except ValueError:
            issues.append(f"{path.relative_to(ROOT)}: missing or out-of-order heading {heading}")
            continue
        pos = next_pos
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, help="Read-only exact prior checkout for non-deletion checks")
    args = parser.parse_args()
    errors: list[str] = []
    checks = 0
    errors += ordered_headings(ROOT / "README.md", HOME_HEADINGS)
    checks += len(HOME_HEADINGS)
    for landing, finite in (("boston.md", "boston-space-time.md"),
                            ("sioux-falls.md", "sioux-space-time.md"),
                            ("hong-kong.md", "hong-kong-space-time.md")):
        errors += ordered_headings(ROOT / "docs/cases" / landing, CASE_HEADINGS)
        errors += ordered_headings(ROOT / "docs/cases" / finite, FINITE_HEADINGS)
        checks += len(CASE_HEADINGS) + len(FINITE_HEADINGS)
        visible = primary((ROOT / "docs/cases" / finite).read_text(encoding="utf-8"))
        if re.search(r"^##\s+.*(?:physical network to time-indexed columns|physical links to time-indexed movement)", visible, re.M | re.I):
            errors.append(f"conflated primary heading: {finite}")
        if "original" not in visible.lower() and "physical-link" not in visible.lower():
            errors.append(f"missing original-space explanation: {finite}")
    for slug, city in CITIES.items():
        case = ROOT / "docs/cases" / ("sioux-space-time.md" if slug == "sioux" else f"{slug.replace('_', '-')}-space-time.md")
        text = case.read_text(encoding="utf-8")
        for family in FAMILIES:
            stem = f"{slug}_{family}"
            for ext in ("png", "svg", "source.json", "caption.md"):
                file = ASSETS / f"{stem}.{ext}"
                if not file.is_file():
                    errors.append(f"missing {file.relative_to(ROOT)}")
                checks += 1
            if f"{stem}.png" not in text:
                errors.append(f"{city} detail lacks {stem}")
            source = ASSETS / f"{stem}.source.json"
            if not source.is_file():
                continue
            record = json.loads(source.read_text(encoding="utf-8"))
            if record.get("scientific_solver_rerun") is not False:
                errors.append(f"solver status not explicit: {stem}")
            if record.get("city") != city:
                errors.append(f"city mismatch: {stem}")
            for rel, expected in record.get("input_sha256", {}).items():
                path = ROOT / rel
                if not path.is_file() or sha(path) != expected:
                    errors.append(f"input hash mismatch: {stem} -> {rel}")
                checks += 1
            for ext in ("png", "svg"):
                if sha(ASSETS / f"{stem}.{ext}") != record.get(f"{ext}_sha256"):
                    errors.append(f"output hash mismatch: {stem}.{ext}")
                checks += 1
            renderer = ROOT / "tools/visuals/render_three_city_parallel.py"
            if sha(renderer) != record.get("renderer_sha256"):
                errors.append(f"renderer hash mismatch: {stem}")
            checks += 1
    for name in ("THREE_CITY_GMNS_STATISTICS", "THREE_CITY_STATIC_ASSIGNMENT_STATISTICS",
                 "THREE_CITY_FINITE_TIME_EXPANDED_STATISTICS", "THREE_CITY_CAPABILITY_MATRIX"):
        csvfile = TABLES / f"{name}.csv"
        with csvfile.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            errors.append(f"empty table: {name}")
        record = json.loads((TABLES / f"{name}.source.json").read_text(encoding="utf-8"))
        if sha(csvfile) != record.get("csv_sha256"):
            errors.append(f"table hash mismatch: {name}")
        for rel, expected in record.get("source_sha256", {}).items():
            path = ROOT / rel
            if not path.is_file() or sha(path) != expected:
                errors.append(f"table source hash mismatch: {name} -> {rel}")
            checks += 1
        if name == "THREE_CITY_CAPABILITY_MATRIX":
            if set(rows[0]) != {"capability", *CITIES.values()}:
                errors.append("capability matrix lacks three city columns")
            for row in rows:
                for city in CITIES.values():
                    if row[city] not in STATUS:
                        errors.append(f"invalid status: {row['capability']} / {city}: {row[city]}")
                    checks += 1
            by_cap = {row["capability"]: row for row in rows}
            if by_cap["ADMM"]["Hong Kong"] != "Gated":
                errors.append("Hong Kong ADMM gate was upgraded")
            if by_cap["independent pricing closure"]["Sioux Falls"] != "Not established":
                errors.append("Sioux historical pricing closure was upgraded")
        else:
            if "city" not in rows[0]:
                errors.append(f"missing city field: {name}")
            if not all(any(row.get("city", "").startswith(city) for row in rows) for city in CITIES.values()):
                errors.append(f"missing city row: {name}")
        checks += 2
    hk = json.loads((ASSETS / "data/hong_kong_selected_generated_column.source.json").read_text(encoding="utf-8"))
    with (ASSETS / "data/hong_kong_selected_generated_column.csv").open(newline="", encoding="utf-8") as handle:
        path_rows = list(csv.DictReader(handle))
    if hk["accepted_status"] != "ACCEPTED_BOUNDED_HONG_KONG_CG_WITH_INDEPENDENT_PRICING_CLOSURE":
        errors.append("Hong Kong R5 accepted status not retained")
    if hk["flow_pce"] <= 0 or hk["path_arc_count"] != len(path_rows):
        errors.append("Hong Kong selected column is not a positive-flow complete saved path")
    if sha(ASSETS / "data/hong_kong_selected_generated_column.csv") != hk["derived_public_table_sha256"]:
        errors.append("Hong Kong selected column hash mismatch")
    checks += 3
    public = [ROOT / "README.md", *ROOT.glob("docs/**/*.md"), *ROOT.glob("docs/**/*.html"),
              *ASSETS.glob("*.source.json"), *TABLES.glob("*.source.json")]
    private_pattern = re.compile(r"(?:[A-Za-z]:\\(?:Users|mobility_computation_lab_v2)|/mnt/" + "data/|/home" + "/|/Users" + "/)")
    for file in public:
        if private_pattern.search(file.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"private absolute path in {file.relative_to(ROOT)}")
        checks += 1
    if args.baseline:
        baseline = args.baseline.resolve()
        for file in baseline.rglob("*"):
            if not file.is_file() or any(part in {".git", ".pytest_cache", "__pycache__"} for part in file.relative_to(baseline).parts):
                continue
            rel = file.relative_to(baseline)
            dest = ROOT / rel
            if not dest.is_file():
                errors.append(f"deleted prior public file: {rel.as_posix()}")
            elif file.suffix.lower() in {".png", ".svg", ".jpg", ".jpeg", ".csv", ".json"} and sha(file) != sha(dest):
                errors.append(f"changed protected prior asset/data: {rel.as_posix()}")
            checks += 1
        for rel in ("README.md", "docs/cases/boston.md", "docs/cases/sioux-falls.md",
                    "docs/cases/hong-kong.md", "docs/cases/boston-space-time.md",
                    "docs/cases/sioux-space-time.md", "docs/cases/hong-kong-space-time.md"):
            prior = (baseline / rel).read_text(encoding="utf-8")
            current = (ROOT / rel).read_text(encoding="utf-8")
            prior_refs = set(re.findall(r"(?:src|href)=[\"']([^\"']+)|\]\(([^)]+)\)", prior))
            for ref in prior_refs:
                value = ref[0] or ref[1]
                if value.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                if value not in current:
                    errors.append(f"prior local reference not retained in {rel}: {value}")
                checks += 1
    result = {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
