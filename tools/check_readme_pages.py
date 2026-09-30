#!/usr/bin/env python3
"""Check the layered README, complete walkthrough and generated Pages links.

The root is a research entry. Scientific figures and numerical details are
required on canonical case/method pages and in the complete walkthrough; they
are not required to crowd the landing page.
"""

from __future__ import annotations

import html
import hashlib
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
    hero = readme[:readme.find('<a id="what-this-project-adds"></a>')]
    for needle in (
        "**An open research and learning environment for city networks, travel demand, and reproducible network computation.**",
        "[Hao Zheng](https://scholarhaozheng.github.io/)",
        "[General Modeling Network Specification (GMNS)](https://github.com/zephyr-data-specs/GMNS)",
        "[TAPLab: An Open Laboratory for Reproducible Traffic Assignment Experiments](https://github.com/asu-trans-ai-lab/TAPLab)",
        "official [tap-b Algorithm B](https://github.com/spartalab/tap-b)",
        "Selected static traffic-assignment experiments build on",
    ):
        check(needle in hero, f"Approved author/upstream introduction missing: {needle}")
    check("Project author: Hao Zheng. This open-source research environment connects" not in hero,
          "Superseded institutional hero returned")
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
    check("project_structure_r3/project_structure.svg" in readme and
          "project_structure_r3/project_structure.svg" in home and
          "project_structure_r3/project_structure_model.json" in architecture,
          "Current clickable structure map or model source is not visible")
    structure_svg = (DOCS / "assets/project_structure_r3/project_structure.svg").read_text(encoding="utf-8")
    check(structure_svg.count("xlink:href=") >= 18 and
          "../../cases/boston.html" in structure_svg and
          "../../cases/sioux-falls.html" in structure_svg and
          "../../cases/hong-kong.html" in structure_svg and
          "Generic RC5 engine" in structure_svg,
          "R3 project-map cards are not linked to the three case routes")
    svg_root = DOCS / "assets/project_structure_r3"
    for href in set(re.findall(r'<a xlink:href="([^"]+)"', structure_svg)):
        check((svg_root / href).resolve().is_file(), f"Broken clickable project-map target: {href}")
    structure_record = json.loads(
        (DOCS / "assets/project_structure_r3/project_structure.source.json").read_text(encoding="utf-8")
    )
    for rel, expected in {
        "docs/assets/project_structure_r3/project_structure_model.json": structure_record["model_sha256"],
        "docs/assets/project_structure_r2/project_structure_model.json": structure_record["source_ledger_sha256"],
        "tools/visuals/render_project_structure_r3.py": structure_record["renderer_sha256"],
        **structure_record["outputs_sha256"],
    }.items():
        path = ROOT / rel
        check(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
              f"Project-map source/output hash mismatch: {rel}")
    for phrase in (
        "GMNS", "Population", "household", "01 trip generation", "02 trip distribution",
        "03 mode choice", "04 traffic assignment", "GPS traces and map matching",
        "Static", "finite", "Already-declared OD",
    ):
        check(phrase.lower() in (readme + architecture).lower(), f"Project workflow layer missing: {phrase}")

    for rel in (
        "docs/assets/project_structure_r3/project_structure.svg",
        "docs/assets/boston/visual_release_r1/boston_network_zones.png",
        "docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
        "docs/assets/cg_layered_companions_r1/hong_kong_layered_space_time_construction.png",
    ):
        check(rel in readme, f"Landing project map/city full-figure link missing: {rel}")
    atlas = readme[readme.find("## 04 / Explore"):readme.find("## 05 / Run")]
    check("atlas-gallery" not in atlas and atlas.count('class="atlas-image-row"') >= 28,
          "R3 atlas must use GitHub-native horizontal image rows")
    check(atlas.count('width="165" alt=') == 86 and not re.search(r'<img[^>]+height="\d+"', atlas),
          "Atlas must use width-limited previews without forced image heights")
    check('class="atlas-scope-row"' not in atlas and 'Full figure</a>' not in atlas,
          "Atlas caption/link rows did not collapse to compact notes and short links")
    coverage = readme[readme.find("## 03 / Case coverage"):readme.find("## 04 / Explore")]
    home_tables = re.findall(r'<table\b[^>]*>', coverage + atlas)
    check(len(home_tables) == 18 + atlas.count('class="atlas-stage-table"') + 4 and
          all('width="100%"' in opening for opening in home_tables),
          "Every Section 03/04 table must have the same full-width outer boundary")
    home_css = (ROOT / "docs/assets/presentation-r3.css").read_text(encoding="utf-8")
    check('padding:24px;margin:36px -24px 52px' in home_css and
          'padding:15px;margin:25px -15px' in home_css and
          '.mcl-page table.atlas-stage-table{min-width:680px}' in home_css,
          "Site case-atlas padding must not inset Section 04 table edges from Section 03")
    check(coverage.count('class="home-coverage"') == 18 and
          coverage.count('width="100%"><colgroup>'+('<col width="33%">'*3)+'</colgroup>') == 18 and
          'E / Reusable outputs and tools' not in coverage and
          not re.search(r'row_19_(?:boston|sioux_falls|hong_kong)\.png', coverage),
          "Coverage tables must be full width; tools remain navigation only")
    check(not re.search(r'<img[^>]+height="\d+"', coverage),
          "Coverage previews must not force an image height")
    check(coverage.count('<td width="33%"><sub><a href=') == 54,
          "Three-city coverage links must use the compact GitHub-native text size")
    for city, slug in (("Boston", "boston"), ("Sioux Falls", "sioux-falls"),
                       ("Hong Kong", "hong-kong")):
        case = f"docs/cases/{slug}.md#reproduction"
        check(f'<a id="{slug}-tools"></a>' in atlas and
              f'<a href="{case}">Tools and reproducibility</a>' in atlas and
              f'<section class="atlas-stage" id="{slug}-tools">' not in atlas,
              f"{city} tools navigation or historical anchor is missing")
    check('<strong>' in atlas and '</strong><br><sub>' in atlas,
          "Atlas caption title/scope font hierarchy is missing")
    check('<img src="docs/assets/homepage_evidence_r1/sioux_falls_classic_topology.png" width="165"' in atlas,
          "Sioux classic topology must use the original aspect-ratio-preserving image")
    for city in ("boston", "sioux_falls", "hong_kong"):
        check((ROOT / f"docs/assets/homepage_evidence_r2/row_19_{city}.png").is_file(),
              f"Original {city} tools preview was deleted rather than removed from home")
    stage_tables = re.findall(
        r'<table class="atlas-stage-table" data-columns="(\d)" data-filled="(\d)" width="(\d+)%"><colgroup>(.*?)</colgroup><tbody>(.*?)</tbody></table>',
        atlas, re.S)
    check(len(stage_tables) == atlas.count('class="atlas-stage-table"'),
          "Atlas stage table markup or column count attribute malformed")
    for slots_text, filled_text, width_text, cols, body in stage_tables:
        slots, filled = int(slots_text), int(filled_text)
        col_widths = re.findall(r'<col width="(\d+)%">', cols)
        rows = re.findall(r'<tr class="([^"]+)">(.*?)</tr>', body, re.S)
        check(slots == 4 and 1 <= filled <= 4 and int(width_text) == 100 and
              col_widths == ["25"] * 4 and len(rows) == 3 and
              [name for name, _ in rows] == ["atlas-image-row", "atlas-caption-row", "atlas-links-row"] and
              all(row.count('<td') == 4 and
                  re.findall(r'<td width="([^"]+)"', row) == ["25%"] * 4 and
                  row.count('class="atlas-empty"') == 4-filled
                  for _, row in rows) and
              rows[0][1].count('<img ') == filled,
              "Atlas table must use a full-width four-column grid with quarter-width filled and empty slots")
    quick_facts = re.findall(r'<table class="atlas-quick-facts".*?</table>', atlas, re.S)
    benchmark_scope = re.findall(r'<table class="atlas-benchmark-scope".*?</table>', atlas, re.S)
    check(len(quick_facts) == 3 and all(re.findall(r'<td width="([^"]+)"', table) == ["25%"] * 4
                                        for table in quick_facts),
          "Three-city quick-facts columns are not uniformly quarter-width")
    check(len(benchmark_scope) == 1 and
          set(re.findall(r'<td width="([^"]+)"', benchmark_scope[0])) == {"33%"},
          "Sioux benchmark-scope columns are not equal-width")
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
