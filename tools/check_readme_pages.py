#!/usr/bin/env python3
"""Check the layered README, complete walkthrough and generated Pages links.

The root is a research entry. Scientific figures and numerical details are
required on canonical case/method pages and in the complete walkthrough; they
are not required to crowd the landing page.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def refs(text: str) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", text) + re.findall(r"(?:href|src)=[\"']([^\"']+)", text)


def images(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text) + re.findall(
        r"<img\b[^>]*\bsrc=[\"']([^\"']+)", text
    )


def target(source: Path, raw: str) -> tuple[Path | None, str]:
    value = html.unescape(raw)
    if value.startswith(("http:", "https:", "mailto:", "data:")):
        return None, ""
    filepart, _, fragment = value.partition("#")
    if not filepart:
        return source, unquote(fragment)
    return (source.parent / unquote(filepart)).resolve(), unquote(fragment)


def fragment_exists(path: Path, fragment: str) -> bool:
    if not fragment:
        return True
    if path.suffix.lower() == ".md" and path.is_relative_to(DOCS):
        path = path.with_suffix(".html")
    if not path.is_file() or path.suffix.lower() not in {".html", ".md"}:
        return False
    return fragment in set(re.findall(r'\bid=["\']([^"\']+)', path.read_text(encoding="utf-8")))


def main() -> int:
    errors: list[str] = []
    checks = 0

    def check(ok: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(message)

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    home_path = DOCS / "index.html"
    home = home_path.read_text(encoding="utf-8")
    walk_path = DOCS / "full-walkthrough.md"
    walk = walk_path.read_text(encoding="utf-8")
    architecture = (DOCS / "architecture.md").read_text(encoding="utf-8")
    contribution = (DOCS / "contributions.md").read_text(encoding="utf-8")
    capabilities = (DOCS / "capabilities.md").read_text(encoding="utf-8")
    cg = (DOCS / "methods/space-time-cg.md").read_text(encoding="utf-8")

    headings = [
        "## 01 / What this project adds",
        "## 02 / Complete project structure",
        "## 03 / Case coverage and selected evidence",
        "## 04 / Explore the three cases",
        "## 05 / Run and inspect",
        "## 06 / Attribution, scope and further reading",
    ]
    places = [readme.find(heading) for heading in headings]
    check(all(p >= 0 for p in places) and places == sorted(places), "README six-block research-entry order changed")
    for phrase in (
        "City-to-model representations",
        "Computational implementations and diagnostics",
        "Reusable cross-city computational tools",
    ):
        check(phrase in readme and phrase in contribution, f"Approved contribution missing: {phrase}")
        check(phrase in home, f"Homepage contribution missing: {phrase}")
    check("Controlled cross-instance evidence" not in readme + contribution,
          "Rejected failure/gate contribution has returned")
    check("TAPLite" not in readme + contribution, "Algorithm B is misnamed TAPLite")
    check(readme.find("Reusable cross-city computational tools") < readme.find("project_structure.svg"),
          "Contributions are not visible before the first large figure")

    for rel in (
        "docs/contributions.md", "docs/architecture.md", "docs/full-walkthrough.md",
        "docs/capabilities.md", "docs/getting-started.md", "docs/cases/boston.md",
        "docs/cases/sioux-falls.md", "docs/cases/hong-kong.md",
        "docs/methods/space-time-cg.md", "docs/methods/admm-space-time.md",
        "docs/methods/origin-based-algorithm-b.md", "docs/methods/distributed-assignment.md",
    ):
        check(rel in readme, f"Direct primary navigation missing: {rel}")
    for stem in ("boston", "sioux-falls", "hong-kong", "cg-experiments", "framework", "coverage"):
        check(f'id="{stem}"' in readme and f'id="{stem}"' in home,
              f"Legacy primary fragment missing: {stem}")
    check("project_structure.svg" in readme and "project_structure.svg" in home and
          "project_structure_model.json" in architecture,
          "Complete structure map or model source is not visible")
    for phrase in (
        "GMNS", "Population", "household", "01 trip generation", "02 trip distribution",
        "03 mode choice", "04 traffic assignment", "GPS traces and map matching",
        "Static", "finite", "Already-declared OD",
    ):
        check(phrase.lower() in (readme + architecture).lower(), f"Project workflow layer missing: {phrase}")

    for rel in (
        "docs/assets/project_structure_r2/project_structure.svg",
        "docs/assets/boston/visual_release_r1/boston_network_zones.png",
        "docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
        "docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png",
    ):
        check(rel in readme, f"Landing project map/city full-figure link missing: {rel}")
    atlas = readme[readme.find("## 04 / Explore"):readme.find("## 05 / Run")]
    check("atlas-gallery" not in atlas and atlas.count('class="atlas-image-row"') >= 30,
          "R3 atlas must use GitHub-native horizontal image rows")
    check(atlas.count('width="210" height="126"') == 89,
          "Atlas must use uniform 5:3 compact previews with source-preserving contain")
    for text, surface in ((readme, "README"), (home, "Pages homepage")):
        groups = re.findall(r"<colgroup>(.*?)</colgroup>", text, re.S)
        check(bool(groups) and all(re.fullmatch(r'(?:<col width="(?:25|33|50|100)%"\s*/?>){1,4}',
                                                  group) for group in groups),
              f"Malformed atlas colgroup or visible percent residue in {surface}")
        for city, count in (("boston", 4), ("sioux-falls", 4), ("hong-kong", 2)):
            match = re.search(r'<section class="atlas-stage" id="'+city+r'-static">(.*?)</section>', text, re.S)
            check(match is not None and match.group(1).count('<img ') == count,
                  f"{surface} {city} static section must show one preview per executed method")
            if match:
                check(not any(old in match.group(1) for old in
                              ("sioux_fw_flow_compact", "hk_algorithm_b_vs_fw", "minus_fw")),
                      f"Comparison-only figure returned to {surface} {city} static atlas")
    check("model-generated" in readme.lower(), "Approved HK10 path must be labeled model-generated")
    check("77-arc" in walk and "model-generated" in walk.lower(),
          "Full walkthrough lost the bounded HK10 disclosure")

    for table in ("### A. City-data and GMNS statistics", "### B. Static-assignment statistics",
                  "### C. Finite time-expanded statistics"):
        check(table in capabilities and table in walk, f"Original statistics table not retained: {table}")
    for needle in ("| **Phase I** |", "| **Phase II** |", "| **Pricing certificate** |",
                   "boston_sioux_cg_parallel_overview.png"):
        check(needle in cg and needle in walk, f"Cross-case CG detail or walkthrough lost: {needle}")
    check("<a id=\"cg-experiments\"></a>" in cg,
          "Cross-case CG canonical section lost its compatibility anchor")

    for rel, expected in (
        ("docs/cases/boston-admm.md", "convergence_Boston_10OD.png"),
        ("docs/cases/sioux-admm.md", "convergence_Sioux_200OD.png"),
        ("docs/cases/sioux-admm.md", "convergence_Sioux_250OD.png"),
        ("docs/cases/boston-algorithm-b.md", "boston_b1_fw_flow_compact.svg"),
        ("docs/cases/sioux-algorithm-b.md", "sioux_fw_flow_compact.svg"),
        ("docs/cases/boston.md", "endpoint_all_coverage.png"),
        ("docs/architecture.md", "framework_overview.png"),
        ("docs/visualizations.md", "mcl_boston_hero.png"),
    ):
        check(expected in (ROOT / rel).read_text(encoding="utf-8"),
              f"Homepage-only original figure not restored to detail: {rel} -> {expected}")

    walkthrough_images = images(walk)
    check(len(walkthrough_images) >= 74,
          f"Full technical walkthrough lost old inline images: {len(walkthrough_images)} < 74")
    detail_targets: set[Path] = set()
    for page in DOCS.rglob("*.md"):
        if page in {DOCS / "index.md", walk_path} or page.is_relative_to(DOCS / "assets"):
            continue
        for raw in images(page.read_text(encoding="utf-8")):
            path, _ = target(page, raw)
            if path:
                detail_targets.add(path)
    for raw in walkthrough_images:
        path, _ = target(walk_path, raw)
        check(path is not None and path.is_file(), f"Walkthrough image target missing: {raw}")
        if path:
            check(path in detail_targets, f"Old inline figure lacks canonical detailed display: {raw}")

    # Check root and all generated HTML file targets. New/changed surfaces also
    # check fragment IDs, including backward-compatible external bookmarks.
    changed_html = {
        "index.html", "full-walkthrough.html", "architecture.html", "contributions.html",
        "capabilities.html", "visualizations.html", "methods/space-time-cg.html",
        "cases/boston.html", "cases/boston-admm.html", "cases/sioux-admm.html",
        "cases/boston-algorithm-b.html", "cases/sioux-algorithm-b.html",
    }
    for raw in refs(readme):
        path, fragment = target(readme_path, raw)
        if path == readme_path and fragment:
            check(fragment_exists(home_path, fragment), f"Broken README fragment: {raw}")
        elif path is not None:
            check(path.exists(), f"Broken README link: {raw}")
            if fragment:
                check(fragment_exists(path, fragment), f"Broken README target fragment: {raw}")
    for page in sorted(DOCS.rglob("*.html")):
        rel = page.relative_to(DOCS).as_posix()
        text = page.read_text(encoding="utf-8")
        for raw in re.findall(r"(?:href|src)=[\"']([^\"']+)", text):
            path, fragment = target(page, raw)
            if path is None:
                continue
            check(path.exists(), f"Broken Pages link: {rel} -> {raw}")
            if fragment and rel in changed_html:
                check(fragment_exists(path, fragment), f"Broken Pages fragment: {rel} -> {raw}")
    for raw in images(readme):
        path, _ = target(readme_path, raw)
        check(path is not None and path.is_file(), f"Broken landing image: {raw}")
        if path and path.suffix.lower() == ".png" and path.is_file():
            check(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"Invalid PNG: {raw}")

    for metric in ("11,422", "2,959", "2,465", "1,516", "13 standards"):
        check(metric in walk, f"Complete old open-data evidence lost: {metric}")
    check("These evidence layers are not additive" in readme and
          "open-data-explorer.md" in readme and "data-tools.md" in readme,
          "Open-data support is no longer visible from the entry")
    check("0.3.0-rc5" in readme and "separately versioned" in readme and
          "0.3.0-rc5" in (DOCS / "getting-started.md").read_text(encoding="utf-8"),
          "F04 generic-versus-later-case version scope was lost")

    output = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "readme_image_count": len(images(readme)),
        "walkthrough_image_count": len(walkthrough_images),
        "pages_html_files": len(list(DOCS.rglob("*.html"))),
        "hierarchy_aware": True,
        "visual_qa_performed": False,
    }
    print(json.dumps(output, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
