#!/usr/bin/env python3
"""Check the layered README, complete walkthrough and generated Pages links.

The root is a research entry. Scientific figures and numerical details are
required on canonical case/method pages and in the complete walkthrough; they
are not required to crowd the landing page.
"""

from __future__ import annotations

import csv
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
    icon_path = DOCS / "assets/mcl-globe.svg"
    icon = icon_path.read_text(encoding="utf-8") if icon_path.is_file() else ""
    check('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"' in icon and
          '<title id="title">Mobility Computation Lab globe</title>' in icon and
          '<script' not in icon and 'http://' not in icon.replace('http://www.w3.org/2000/svg', ''),
          "The selected self-contained globe favicon is missing or malformed")
    for page in DOCS.rglob("*.html"):
        if page.is_relative_to(DOCS / "assets"):
            continue  # Immutable scientific caption pages are not site navigation.
        prefix = "../" * (len(page.relative_to(DOCS).parts) - 1)
        expected = f'<link rel="icon" type="image/svg+xml" href="{prefix}assets/mcl-globe.svg">'
        check(expected in page.read_text(encoding="utf-8"),
              f"Missing or broken globe favicon on website page: {page.relative_to(DOCS)}")
    walk_path = DOCS / "full-walkthrough.md"
    walk = walk_path.read_text(encoding="utf-8")
    architecture = (DOCS / "architecture.md").read_text(encoding="utf-8")
    contribution = (DOCS / "contributions.md").read_text(encoding="utf-8")
    contribution_html = (DOCS / "contributions.html").read_text(encoding="utf-8")
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
    removed_claim = ("It does not claim sole authorship of every component, new general convergence theorems, "
                     "empirical citywide calibration, or uniform method success in all three cities.")
    check(removed_claim not in contribution and removed_claim not in contribution_html and
          "Cite the repository and original sources" in contribution,
          "Contributions page restored removed sentence or lost its citation link")
    hero = readme[:readme.find('<a id="what-this-project-adds"></a>')]
    for needle in (
        "**Mobility Computation Lab connects city networks, travel demand, and reproducible network computation.**",
        "[Hao Zheng](https://scholarhaozheng.github.io/)",
        "a recent M.S. graduate from Tsinghua University, under the guidance of **[Professor Xuesong Zhou](https://search.asu.edu/profile/2182101)**",
        "Project-specific work includes assembling and adapting the Boston, Sioux Falls, and Hong Kong cases",
        "[General Modeling Network Specification (GMNS)](https://github.com/zephyr-data-specs/GMNS)",
        "[TAPLab: An Open Laboratory for Reproducible Traffic Assignment Experiments](https://github.com/asu-trans-ai-lab/TAPLab)",
        "official [tap-b Algorithm B](https://github.com/spartalab/tap-b)",
        "Selected static traffic-assignment experiments build on",
    ):
        check(needle in hero, f"Approved author/upstream introduction missing: {needle}")
    check('<strong><a href="https://search.asu.edu/profile/2182101">Professor Xuesong Zhou</a></strong>' in home,
          'Website hero must link and bold Professor Xuesong Zhou')
    check("Project author: Hao Zheng. This open-source research environment connects" not in hero and
          "I am Hao Zheng" not in hero and "I am [Hao Zheng]" not in hero and
          "My work in this repository" not in hero,
          "Superseded author-first hero returned")
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
        path, fragment = target(svg_root / 'project_structure.svg', href)
        check(path is not None and path.is_file() and fragment_exists(path, fragment),
              f"Broken clickable project-map target or fragment: {href}")
    for letter, label in (
        ('A', 'Native assignment'), ('B', 'Decomposition / distributed'),
        ('C', 'Spatial hierarchy / representation'), ('D', 'Coordination / verification'),
    ):
        check(f'>{letter}</text>' in structure_svg and f'>{label}</text>' in structure_svg and
              structure_svg.count('xlink:href="../../index.html#two-axes"') >= 8,
              f'Missing linked A–D reading lens: {letter}')
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
    axes = readme[readme.find("### Two axes of Mobility Computation Lab"):readme.find('<a id="coverage"></a>')]
    check(readme.count('### Two axes of Mobility Computation Lab') == 1 and
          readme.count('<a id="two-axes"></a>') == 1 and
          readme.count('<a id="02a-two-axes-of-mobility-computation-lab"></a>') == 1 and
          home.count('<h3 id="two-axes-of-mobility-computation-lab">Two axes of Mobility Computation Lab</h3>') == 1 and
          '<a id="two-axes"></a><a id="02a-two-axes-of-mobility-computation-lab"></a>' in home and
          len(axes) > 200 and 'A–D are not four mandatory execution steps' in axes,
          "The two-axis explanation must appear exactly once before Section 03")
    coverage = readme[readme.find("## 03 / Case coverage"):readme.find("## 04 / Explore")]
    finite_gallery_sources = {
        "boston": (
            "three_city_r2/boston_physical_to_time_expanded_graph.png",
            "cg_layered_companions_r1/boston_layered_space_time_construction.png",
            "boston/space_time_cg_r4/boston_space_time_construction.png"),
        "sioux_falls": (
            "three_city_r2/sioux_physical_to_time_expanded_graph.png",
            "presentation_r3/sioux_space_time_construction.png",
            "three_city_r2/sioux_generated_column_time_indexed_path.png"),
        "hong_kong": (
            "three_city_r2/hong_kong_physical_to_time_expanded_graph.png",
            "cg_layered_companions_r1/hong_kong_layered_space_time_construction.png",
            "hong_kong/presentation_r6/hk_physical_to_time_cutaway.png"),
    }
    for page_text, prefix in ((readme, "docs/"),
                              ((DOCS / "index.md").read_text(encoding="utf-8"), ""),
                              (home, "")):
        gallery = page_text.split('<table class="finite-network-gallery"', 1)[1].split('</table>', 1)[0]
        check(gallery.count('<tr data-city=') == 3 and gallery.count('<img ') == 9,
              "Finite-network gallery must have exactly three city rows and nine previews")
        for city, originals in finite_gallery_sources.items():
            for kind, source in zip(("construction", "layered", "path"), originals):
                original = prefix + "assets/" + source
                preview = prefix + f"assets/homepage_finite_atlas_r1/{city}_{kind}.png"
                check(re.search(r'<a href="' + re.escape(original) +
                                r'"><img\b[^>]*src="' + re.escape(preview) + r'"', gallery) is not None,
                      f"Finite-network thumbnail must click its own full source: {city}/{kind}")
    for city, originals in finite_gallery_sources.items():
        for kind, source in zip(("construction", "layered", "path"), originals):
            preview = ROOT / f"docs/assets/homepage_finite_atlas_r1/{city}_{kind}.png"
            sidecar = json.loads(preview.with_suffix(".source.json").read_text(encoding="utf-8"))
            original = ROOT / "docs/assets" / source
            check(sidecar["source_figure"] == original.relative_to(ROOT).as_posix() and
                  sidecar["source_sha256"] == hashlib.sha256(original.read_bytes()).hexdigest() and
                  sidecar["preview_sha256"] == hashlib.sha256(preview.read_bytes()).hexdigest() and
                  sidecar["scientific_solver_rerun"] is False,
                  f"Finite-network preview source/byte contract differs: {city}/{kind}")
    row14 = coverage.split('data-component="14"', 1)[1].split('</table>', 1)[0]
    row16 = coverage.split('data-component="16"', 1)[1].split('</table>', 1)[0]
    check(row14.count('class="coverage-preview"') == 1 and
          row14.count('class="coverage-layered-preview"') == 1 and
          all(f'row_14_{city}.png' in row14 for city in finite_gallery_sources),
          "Network-construction row lost its legacy first row or new layered second row")
    check(row16.count('class="coverage-preview"') == 1 and
          row16.count('class="coverage-final-flow-preview"') == 1 and
          row16.count('class="coverage-path-preview"') == 1 and
          all(f'row_16_{city}_r3.png' in row16 for city in finite_gallery_sources) and
          'No independent full-DAG pricing closure is claimed' in row16,
          "CG row lost a trace, final-flow, local-path or Sioux scope statement")
    gps_row = coverage.split('data-component="05"', 1)[1].split('</table>', 1)[0]
    gps_row_site = home.split('data-component="05"', 1)[1].split('</table>', 1)[0]
    projection = 'docs/assets/boston/visual_release_r1/boston_gps_projection.png'
    projection_target = 'docs/datasets/boston-central.md#one-saved-transit-position-projection'
    hk_summary = 'docs/assets/hong_kong/full_stack_r5/r2r4_baseline/figures/hk_detector_and_trajectory_evidence.png'
    hk_projection = 'docs/assets/hong_kong/visual_release_r1/hong_kong_reference_projection.png'
    preview_row = gps_row.split('<tr class="coverage-preview">', 1)[1].split('</tr>', 1)[0]
    preview_cells = re.findall(r'<td\b[^>]*>.*?</td>', preview_row, flags=re.DOTALL)
    check(gps_row.count('src="docs/assets/homepage_evidence_r2/row_05_boston.png"') == 1 and
          gps_row.count('src="'+projection+'"') == 1 and
          projection_target in gps_row and
          'src="assets/boston/visual_release_r1/boston_gps_projection.png"' in gps_row_site,
          'Boston GPS evidence cell must show the existing preview and saved point projection')
    check(len(preview_cells) == 3 and
          [cell.count('<img') for cell in preview_cells] == [2, 1, 2] and
          all('class="gps-evidence-pair"' in preview_cells[index] and
              preview_cells[index].count('class="gps-paired-preview"') == 2 and
              preview_cells[index].count('width="118"') == 2 and
              '<br' not in preview_cells[index] for index in (0, 2)) and
          hk_projection in preview_cells[2] and
          'src="assets/hong_kong/visual_release_r1/hong_kong_reference_projection.png"' in gps_row_site and
          'table.home-coverage[data-component="05"] .coverage-preview td.gps-evidence-pair img.gps-paired-preview' in
          (DOCS / 'assets/presentation-r3.css').read_text(encoding='utf-8'),
          'Boston/Hong Kong observation cells must show two aspect-ratio-safe figures side by side')
    boston_transit = readme.split('data-stage="boston-transit" width="100%"', 1)[1].split('</table>', 1)[0]
    check('GPS point-to-road projection' in boston_transit and projection in boston_transit and
          projection_target in boston_transit and 'width="220"' in boston_transit,
          'Boston point projection must remain a distinct, legible Transit and observations card')
    check((ROOT / projection).is_file() and
          hashlib.sha256((ROOT / projection).read_bytes()).hexdigest() ==
          '58921c4b7f0accf505f8c096095e1976213461851906ed83509dbee86f1b8804',
          'Saved Boston GPS projection original bytes changed')
    check((ROOT / hk_summary).is_file() and
          hashlib.sha256((ROOT / hk_summary).read_bytes()).hexdigest() ==
          '840906416d1c508f69802e80648a40ba3e0411f669ec4ebff87e01fc464f93c5',
          'Saved Hong Kong observation summary original bytes changed')
    check((ROOT / hk_projection).is_file() and
          hashlib.sha256((ROOT / hk_projection).read_bytes()).hexdigest() ==
          '7760d61ecc3a26f17305db633f6b6ad2e8edb71550eb1faa766badf59b54de08' and
          (ROOT / 'docs/assets/hong_kong/visual_release_r1/hong_kong_reference_projection.source.json').is_file(),
          'Hong Kong reference projection or its provenance changed')
    row15_readme = coverage.split('data-component="15"', 1)[1].split('</table>', 1)[0]
    row15_home = home.split('data-component="15"', 1)[1].split('</table>', 1)[0]
    with (DOCS / 'assets/homepage_evidence_r2/ROW15_REUSE_SOURCE_MAPPING.csv').open(
        newline='', encoding='utf-8'
    ) as stream:
        row15_sources = list(csv.DictReader(stream))
    with (DOCS / 'assets/homepage_evidence_r2/ROW_TEMPLATE_MATRIX.csv').open(
        newline='', encoding='utf-8'
    ) as stream:
        row15_matrix = {r['city']: r for r in csv.DictReader(stream) if r['row_id'] == '15'}
    check(len(row15_sources) == 3 and set(row15_matrix) == {'Boston', 'Sioux Falls', 'Hong Kong'},
          'Arc-flow LP reference must have three source-qualified city cells')
    check(row15_readme.count('height="160"') == 3 and row15_readme.count('width="220"') == 3 and
          'data-component="15"' in home and
          'table.home-coverage[data-component="15"] .coverage-preview img' in
          (DOCS / 'assets/presentation-r3.css').read_text(encoding='utf-8'),
          'Arc-flow LP reference image-area geometry must be equal and contained')
    for record in row15_sources:
        city = record['city']
        row = row15_matrix.get(city, {})
        figure = record['original_figure']
        source = record['source_record']
        figure_path, source_path = ROOT / figure, ROOT / source
        source_bytes = source_path.read_bytes() if source_path.is_file() else b''
        if record['source_hash_convention'] == 'LF-normalized':
            source_bytes = source_bytes.replace(b'\r\n', b'\n')
        check(figure_path.is_file() and
              hashlib.sha256(figure_path.read_bytes()).hexdigest() == record['original_sha256'] and
              source_path.is_file() and
              record['source_hash_convention'] in {'LF-normalized', 'exact-bytes'} and
              hashlib.sha256(source_bytes).hexdigest() == record['source_sha256'],
              f'Arc-flow LP original figure or source hash mismatch: {city}')
        check(row.get('original_figure') == figure and
              row.get('data_or_figure_source') == source and
              row.get('target_page') == record['target_page'] and
              row.get('target_anchor') == record['target_anchor'] and
              'reused_existing_figure=true' in row.get('notes', '') and
              'newly_generated_scientific_figure=false' in row.get('notes', '') and
              record['reused_existing_figure'] == 'true' and
              record['newly_generated_scientific_figure'] == 'false',
              f'Arc-flow LP matrix/reuse contract mismatch: {city}')
        check(figure in row15_readme and figure.removeprefix('docs/') in row15_home and
              record['caption'] in row15_readme and record['caption'] in row15_home and
              record['target_page'] + '#' + record['target_anchor'] in row15_readme and
              fragment_exists(ROOT / record['target_page'], record['target_anchor']),
              f'Arc-flow LP figure, caption, or detailed anchor missing: {city}')
    for record in row15_sources:
        city_slug = {'Boston': 'boston', 'Sioux Falls': 'sioux-falls',
                     'Hong Kong': 'hong-kong'}[record['city']]
        stage = atlas.split(f'data-stage="{city_slug}-finite"', 1)[1].split('</table>', 1)[0]
        figure = record['original_figure']
        old_slug = city_slug.replace('-', '_')
        check(figure in stage and f'row_15_{old_slug}.png' not in stage and
              figure.removeprefix('docs/') in home and
              (ROOT / f'docs/assets/homepage_evidence_r2/row_15_{old_slug}.png').is_file(),
              f'Section 04 must show the accepted LP reference figure while retaining the old preview: {record["city"]}')
    hk_static_source = json.loads((DOCS / 'assets/hong_kong/static_path_l3_r2/RESULT_SOURCE.json').read_text(encoding='utf-8'))
    with (DOCS / 'assets/homepage_evidence_r2/ROW12_13_HK_REUSE_SOURCE_MAPPING.csv').open(
        newline='', encoding='utf-8'
    ) as stream:
        hk_static_rows = list(csv.DictReader(stream))
    with (DOCS / 'assets/homepage_evidence_r2/ROW_TEMPLATE_MATRIX.csv').open(
        newline='', encoding='utf-8'
    ) as stream:
        hk_matrix = {r['row_id']: r for r in csv.DictReader(stream)
                     if r['city'] == 'Hong Kong' and r['row_id'] in {'12', '13'}}
    check(len(hk_static_rows) == 2 and set(hk_matrix) == {'12', '13'} and
          hk_static_source['source_package'] == 'corrected_R2' and
          hk_static_source['public_interpretation_label'] ==
          'ACCEPTED_BOUNDED_LOW_CONGESTION_TRANSFER' and
          hk_static_source['singleton_od']['origin_zone'] == 11 and
          hk_static_source['singleton_od']['destination_zone'] == 12 and
          hk_static_source['zone_80_to_38_legal_path_count'] == 5 and
          hk_static_source['solver_link_count'] == 3446,
          'Corrected R2 provenance, singleton OD, or basis operator is missing')
    for record in hk_static_rows:
        rid = record['row_id']
        row = hk_matrix.get(rid, {})
        figure = record['original_figure']
        source = record['source_record']
        figure_path, source_path = ROOT / figure, ROOT / source
        source_bytes = source_path.read_bytes() if source_path.is_file() else b''
        if record['source_hash_convention'] == 'LF-normalized':
            source_bytes = source_bytes.replace(b'\r\n', b'\n')
        check(figure_path.is_file() and source_path.is_file() and
              hashlib.sha256(figure_path.read_bytes()).hexdigest() == record['original_sha256'] and
              hashlib.sha256(source_bytes).hexdigest() == record['source_sha256'] and
              row.get('original_figure') == figure and
              row.get('data_or_figure_source') == source and
              row.get('target_anchor') == record['target_anchor'] and
              'source_package=corrected_R2' in row.get('notes', '') and
              record['reused_existing_figure'] == 'true' and
              record['newly_generated_scientific_figure'] == 'false',
              f'Corrected R2 Hong Kong row {rid} source contract mismatch')
        readme_row = coverage.split(f'data-component="{rid}"', 1)[1].split('</table>', 1)[0]
        html_row = home.split(f'data-component="{rid}"', 1)[1].split('</table>', 1)[0]
        check('ACCEPTED_BOUNDED_LOW_CONGESTION_TRANSFER' in readme_row and
              'ACCEPTED_BOUNDED_LOW_CONGESTION_TRANSFER' in html_row and
              record['target_page'] + '#' + record['target_anchor'] in readme_row and
              fragment_exists(ROOT / record['target_page'], record['target_anchor']),
              f'Corrected R2 Hong Kong row {rid} scope or case anchor missing')
    parity_path = DOCS / 'assets/static_path_parity_r1/FIGURE_PARITY_MAP.csv'
    with parity_path.open(newline='', encoding='utf-8') as stream:
        parity = list(csv.DictReader(stream))
    check(len(parity) == 12 and
          {(r['row_id'], r['city'], r['view']) for r in parity} ==
          {(rid, city, view) for rid in ('12', '13')
           for city in ('Boston', 'Sioux Falls', 'Hong Kong')
           for view in ('distribution', 'network')},
          'Static path/L3 parity must contain both figure types for every city and row')
    for record in parity:
        figure = ROOT / record['figure']
        source = ROOT / record['source_record']
        rid = record['row_id']
        readme_row = coverage.split(f'data-component="{rid}"', 1)[1].split('</table>', 1)[0]
        html_row = home.split(f'data-component="{rid}"', 1)[1].split('</table>', 1)[0]
        check(figure.is_file() and source.is_file() and
              hashlib.sha256(figure.read_bytes()).hexdigest() == record['sha256'] and
              record['figure'] in readme_row and
              record['figure'].removeprefix('docs/') in html_row and
              record['original_preserved'] == 'yes',
              f'Static path/L3 {rid} {record["city"]} {record["view"]} source or image mismatch')
        if record['figure'].startswith('docs/assets/static_path_parity_r1/'):
            sidecar = json.loads(source.read_text(encoding='utf-8'))
            check(sidecar['output_sha256']['png'] == record['sha256'] and
                  sidecar['renderer'] == 'tools/visuals/render_static_path_parity_r1.py',
                  f'Static path/L3 derivative sidecar mismatch: {record["figure"]}')
    check(not any(p.suffix.lower() in {'.npz', '.npy'} for p in parity_path.parent.iterdir()),
          'Private Hong Kong pool or state array entered public figure directory')
    for name, expected_hash in hk_static_source['figure_sha256'].items():
        figure_path = DOCS / 'assets/hong_kong/static_path_l3_r2' / name
        check(figure_path.is_file() and
              hashlib.sha256(figure_path.read_bytes()).hexdigest() == expected_hash,
              f'Corrected R2 original figure bytes changed: {name}')
    hk_static_page = (DOCS / 'cases/hong-kong-static-assignment.md').read_text(encoding='utf-8')
    hk_static_atlas = atlas.split('data-stage="hong-kong-static"', 1)[1].split('</table>', 1)[0]
    check(all(name in hk_static_page for name in (
              'hong_kong_finite_flow_support.png',
              'hong_kong_l3_rank26_reconstruction_difference.png',
              'hong_kong_l3_rank52_reconstruction_difference.png',
              'hong_kong_h1_objective_comparison.png')) and
          'zone 11 → 12' in hk_static_page and '80 → 38 has five legal paths' in hk_static_page and
          '3,446-link turn-expanded solver-link graph' in hk_static_page and
          'low-congestion' in hk_static_page and
          'Full Hong Kong | 8,930 positive ODs | Finite-path / L3 not demonstrated' in hk_static_page and
          'Finite-path reference' not in hk_static_atlas and
          'Native Diagnostic L3 / compression' not in hk_static_atlas,
          'Corrected R2 Hong Kong case text or fixed Section 04 scope changed')
    for removed in (
        "not an automatic observed-OD or calibrated-demand pipeline",
        "schematic topology, no city zone hierarchy",
        "not local calibration",
        "not a modeled distribution stage",
        "not measured traffic",
        "not an empirical speedup",
        "Covers are navigation assets, not scientific validation",
        "not a mandatory solver sequence",
        "Agentic execution remains a learning and research direction",
    ):
        check(removed not in readme and removed not in home,
              f"Removed homepage wording returned: {removed}")
    roman_groups = (
        ("I / City data and model foundations", "a--city-data-and-model-foundations"),
        ("II / Transit and observation evidence", "b--transit-and-observation-evidence"),
        ("III / Four-stage travel-demand workflow", "c--four-stage-travel-demand-workflow"),
        ("IV / Static assignment · BPR/Beckmann", "d1--static-assignment--bprbeckmann"),
        ("V / Finite time-expanded · fixed cost, hard capacity", "d2--finite-time-expanded--fixed-cost-hard-capacity"),
        ("VI / Reusable outputs and tools", "e--reusable-outputs-and-tools"),
    )
    check(all(coverage.count('### '+heading) == 1 and
              coverage.count('<a id="'+anchor+'"></a>') == 1 and
              coverage.count('<a id="section03-'+heading.split(' / ',1)[0].lower()+'"></a>') == 1
              for heading, anchor in roman_groups) and
          not re.search(r'^### (?:A|B|C|D1|D2|E) /', coverage, re.M),
          "Section 03 must have I–VI headings and exact old-fragment compatibility anchors")
    check(atlas.count('id="computational-depth-legend"') == 1 and
          atlas.count('A–D are reading labels for computational depth.') == 1 and
          'Agentic execution remains a learning and research direction' not in atlas and
          all(atlas.count('**'+letter+' — '+title+'**') == 1 for letter, title in (
              ('A','Native assignment'), ('B','Decomposition and distributed computation'),
              ('C','Spatial hierarchy and representation'), ('D','Coordination and verification'))),
          "The single A–D legend or its approved explanatory copy is missing")
    check(atlas.count('class="atlas-depth-badge"') >= 50 and
          'class="atlas-depth-stage"' not in atlas and
          all('['+mark+']' in atlas for mark in ('A','B','C','D','B · D','B · C','C · D')),
          "City atlas A–D badges are incomplete")
    title_cells = re.findall(r'<th [^>]*class="atlas-title-cell"[^>]*>(.*?)</th>', atlas, re.S)
    check(len(title_cells) == 86 and
          all(re.search(r'</strong> <a class="atlas-depth-badge" href="#computational-depth-legend" title="[^"]+" aria-label="[^"]+"><img src="docs/assets/atlas_depth_badges/[ABCD](?:_[CD])?\.svg" width="(?:13|30)" height="11" alt="\[[ABCD](?: · [CD])?\]"></a>$', cell)
              for cell in title_cells if 'class="atlas-depth-badge"' in cell),
          "A–D labels must be small linked gray assets inline after their existing card titles")
    check("atlas-gallery" not in atlas and atlas.count('class="atlas-card-cell"') == 86,
          "Atlas must retain 86 city-owned cards in native table cells")
    check(atlas.count('width="165" alt=') == 85 and
          atlas.count('width="220" alt="Boston GPS point-to-road projection') == 1 and
          not re.search(r'<img[^>]+width="(?:165|220)"[^>]+height="\d+"', atlas),
          "Atlas must retain aspect-ratio-safe previews, with only the GPS projection enlarged")
    check('class="atlas-scope-row"' not in atlas and 'Full figure</a>' not in atlas,
          "Atlas caption/link rows did not collapse to compact notes and short links")
    home_tables = re.findall(r'<table\b[^>]*>', coverage + atlas)
    check(len(home_tables) == 18 + 3 + 19 + 1 + 1 and
          all('width="100%"' in opening for opening in home_tables),
          "Every Section 03/04 table must have the same full-width outer boundary")
    home_css = (ROOT / "docs/assets/presentation-r3.css").read_text(encoding="utf-8")
    check('.mcl-page th{background:var(--navy);color:#fff;' in home_css and
          '.mcl-page table.atlas-city-table .atlas-stage-heading th{' not in home_css and
          '.mcl-page table.atlas-city-table .atlas-benchmark-heading th{' not in home_css,
          "Site Section 04 group headings must inherit the same th styling as Section 03")
    check('.mcl-page table.atlas-city-table .atlas-depth-badge{display:inline;color:#6a737b;' in home_css and
          '.mcl-page table.atlas-city-table .atlas-depth-badge img{display:inline-block;width:auto;height:11px;' in home_css and
          'assets/atlas-depth-tooltips.js' in home and
          (ROOT / 'docs/assets/atlas-depth-tooltips.js').is_file(),
          "A–D labels need muted small text and the website-only click explanation")
    badge_dir = ROOT / 'docs/assets/atlas_depth_badges'
    check(all((badge_dir / (name+'.svg')).is_file() and
              'fill="#626b73"' in (badge_dir / (name+'.svg')).read_text(encoding='utf-8')
              for name in ('A','B','C','D','B_C','B_D','C_D')),
          "GitHub-native muted A–D label assets are missing or inconsistent")
    check('padding:24px;margin:36px -24px 52px' in home_css and
          'padding:15px;margin:25px -15px' in home_css and
          '.mcl-page table.atlas-city-table{min-width:680px}' in home_css,
          "Site case-atlas padding must not inset Section 04 table edges from Section 03")
    check(coverage.count('class="home-coverage"') == 18 and
          coverage.count('width="100%"><colgroup>'+('<col width="33%">'*3)+'</colgroup>') == 18 and
          '### VI / Reusable outputs and tools' in coverage and
          not re.search(r'row_19_(?:boston|sioux_falls|hong_kong)\.png', coverage),
          "Coverage tables must be full width; tools remain navigation only")
    check(not re.search(r'<img[^>]+height="\d+"', coverage),
          "Coverage previews must not force an image height")
    check(coverage.count('<td width="266"><sub><a href=') == 54,
          "Three-city coverage links must use the compact GitHub-native text size")
    check(coverage.count('<th scope="col" width="266">') == 54 and
          coverage.count('<th colspan="3" scope="colgroup" width="800">') == 18 and
          coverage.count('<td width="266" valign="top">') == 54 and
          coverage.count('<td width="266" align="center">') == 64 and
          coverage.count('<td width="266" class="gps-evidence-pair" align="center">') == 2 and
          coverage.count('class="coverage-preview static-path-distribution"') == 2 and
          coverage.count('class="coverage-preview static-path-network"') == 2 and
          coverage.count('<td width="266" height="160" valign="middle" align="center">') >= 6 and
          coverage.count('<td width="266" height="130" valign="middle" align="center">') == 6 and
          800 - 3 * 266 == 2,
          "Section 03 must reserve the same GitHub-native 800px outer width as Section 04")
    captions = re.findall(r'<tr class="coverage-caption">(.*?)</tr>', coverage, re.S)
    check('<tr class="coverage-scope"><td valign="top"><sub>' not in coverage and
          len(captions) == 18 and
          all(re.fullmatch(r'<td colspan="3" align="center"><sub>[^<]+</sub></td>', caption)
              for index, caption in enumerate(captions) if index not in (4, 14, 15, 16)) and
          all(captions[index].count('<td width="266" align="center"><sub>') == 3
              for index in (4, 14, 15, 16)) and
          captions[11] == '<td colspan="3" align="center"><sub>finite-path reconstruction panel</sub></td>' and
          captions[12] == '<td colspan="3" align="center"><sub>L3 reconstruction/difference panel</sub></td>' and
          '.mcl-page table.home-coverage .coverage-caption sub{font-size:10.5px;' in home_css,
          "Rows 12/13 need one shared caption; only GPS and LP rows retain city-specific captions")
    for city, slug in (("Boston", "boston"), ("Sioux Falls", "sioux-falls"),
                       ("Hong Kong", "hong-kong")):
        case = f"docs/cases/{slug}.md#reproduction"
        check(f'<a id="{slug}-tools"></a>' in atlas and
              f'<a href="{case}">Tools and reproducibility</a>' in atlas and
              f'<section class="atlas-stage" id="{slug}-tools">' not in atlas,
              f"{city} tools navigation or historical anchor is missing")
    check('<strong>' in atlas and atlas.count('<small class="atlas-meta">') == 86 and
          atlas.count('<small class="atlas-links">') == 86 and
          '<td width="25%"><sub>' not in atlas and
          '<td width="33%"><sub>' not in atlas,
          "Atlas title, image, scope and link rows are incomplete")
    check('<img src="docs/assets/homepage_evidence_r1/sioux_falls_classic_topology.png" width="165"' in atlas,
          "Sioux classic topology must use the original aspect-ratio-preserving image")
    for city in ("boston", "sioux_falls", "hong_kong"):
        check((ROOT / f"docs/assets/homepage_evidence_r2/row_19_{city}.png").is_file(),
              f"Original {city} tools preview was deleted rather than removed from home")
    city_tables = re.findall(
        r'<table class="atlas-city-table" data-city="([^"]+)" data-stage="([^"]+)" width="100%"><colgroup>(.*?)</colgroup><thead>(.*?)</thead><tbody>(.*?)</tbody></table>',
        atlas, re.S)
    check(len(city_tables) == 19 and {city for city, _, _, _, _ in city_tables} ==
          {"boston", "sioux-falls", "hong-kong"},
          "Each of the nineteen city-stage groups needs its own full-width table")
    for city, stage_id, cols, head, body in city_tables:
        heading = re.search(r'<tr class="atlas-stage-heading" data-stage="([^"]+)" data-columns="(\d)" data-items="(\d+)">', head)
        if not heading:
            check(False, "Missing stage heading: " + stage_id)
            continue
        slots, items = int(heading.group(2)), int(heading.group(3))
        cell_width = {1: "800", 2: "400", 3: "266", 4: "200"}.get(slots)
        col_width = {1: "100%", 2: "50%", 3: "33.333%", 4: "25%"}.get(slots)
        expected_counts = [min(slots, items - start) for start in range(0, items, slots)] if slots else []
        rows = re.findall(r'<tr class="atlas-card-(title|preview|meta|links)-row" data-stage="([^"]+)">(.*?)</tr>', body, re.S)
        check(stage_id.startswith(city+'-') and heading.group(1) == stage_id and
              slots == min(4, items) and cell_width is not None and
              0 <= 800 - slots * int(cell_width) <= 2 and
              cols == ('<col width="'+col_width+'">') * slots and
              '<th colspan="'+str(slots)+'" scope="colgroup" width="800">' in head and
              '<a id="'+stage_id+'"></a>' in head and '<h4>' not in head and
              [(kind, row_stage) for kind, row_stage, _ in rows] ==
              [(kind, stage_id) for _ in expected_counts for kind in ("title", "preview", "meta", "links")] and
              all(row.count('class="atlas-'+("card-cell" if kind == "preview" else kind+"-cell")+'"') == expected and
                  row.count('class="atlas-empty"') == slots-expected and
                  re.findall(r'<(?:th|td) width="([^"]+)" class="atlas-[^"]+"', row) ==
                  [cell_width] * slots
                  for (kind, _, row), expected in zip(rows, [n for n in expected_counts for _ in range(4)])),
              "City stage rows need the common GitHub-native right edge and padded empty slots: " + stage_id)
    quick_facts = re.findall(r'<table class="atlas-quick-facts".*?</table>', atlas, re.S)
    check(len(quick_facts) == 3 and all(re.findall(r'<td width="([^"]+)"', table) == ["200"] * 4
                                        for table in quick_facts),
          "Three-city quick-facts columns are not uniformly quarter-width")
    benchmark = re.search(r'<table class="atlas-city-table atlas-benchmark-table" data-city="sioux-falls" width="100%"><colgroup>.*?</colgroup><thead>(.*?)</thead><tbody>(.*?)</tbody></table>', atlas, re.S)
    sioux_head, sioux_body = (benchmark.group(1), benchmark.group(2)) if benchmark else ("", "")
    check(bool(benchmark) and sioux_body.count('class="atlas-benchmark-row"') == 5 and
          sioux_body.count('<td width="266">') == 15 and
          '<th colspan="3" scope="colgroup" width="800">City-data and four-stage scope</th>' in sioux_head and
          '<colgroup>'+('<col width="33.333%">'*3)+'</colgroup>' in benchmark.group(0),
          "Sioux benchmark-scope columns are not equal-width")
    for text, surface in ((readme, "README"), (home, "Pages homepage")):
        groups = re.findall(r"<colgroup>(.*?)</colgroup>", text, re.S)
        check(bool(groups) and all(re.fullmatch(r'(?:<col width="(?:8\.333|25|33(?:\.333)?|50|100)%"\s*/?>){1,12}',
                                                  group) for group in groups),
              f"Malformed atlas colgroup or visible percent residue in {surface}")
        for city, count in (("boston", 4), ("sioux-falls", 4), ("hong-kong", 2)):
            match = re.search(r'<tr class="atlas-stage-heading"[^>]*data-stage="'+city+r'-static".*?(?=<tr class="atlas-stage-heading"|</tbody></table>)', text, re.S)
            check(match is not None and len(re.findall(r'<img\b[^>]*\bwidth="165"', match.group(0))) == count,
                  f"{surface} {city} static section must show one preview per executed method")
            if match:
                check(not any(old in match.group(0) for old in
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
