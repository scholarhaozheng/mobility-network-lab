#!/usr/bin/env python3
"""Check README and generated Pages links/images as separate publication surfaces."""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _local_target(source: Path, raw: str) -> Path | None:
    value = html.unescape(raw)
    if value.startswith(("http:", "https:", "mailto:", "#", "data:")):
        return None
    filepart = unquote(value.split("#", 1)[0])
    if not filepart:
        return None
    return (source.parent / filepart).resolve()


def presentation_errors(readme: str, home: str, detail: str) -> list[str]:
    """Check explicit four-stage navigation, result figures and GPS entry points."""
    if '<a id="framework"></a>' in readme:
        errors: list[str] = []
        for label, anchor, image in (
            ('Trip generation', 'step-1-trip-generation', 'step1_generation.png'),
            ('Trip distribution', 'step-2-trip-distribution', 'step2_distribution.png'),
            ('Mode choice', 'step-3-mode-choice', 'step3_mode_response.png'),
            ('Traffic assignment', 'step-4-traffic-assignment', 'boston_panel_flow_s1.png'),
        ):
            if label.lower() not in readme.lower() or 'boston-behavior-feedback.md#' + anchor not in readme:
                errors.append(f'README must name and link the actual stage: {label}')
            if label.lower() not in home.lower() or image not in home:
                errors.append(f'Homepage is missing its actual stage/result: {label}')
            if f'id="{anchor}"' not in detail:
                errors.append(f'Boston detail anchor missing: {anchor}')
        for anchor, label in (
            ('gmns-in-action', 'GMNS in Action'),
            ('how-gps-changes-the-result', 'GPS'),
        ):
            if f'<a id="{anchor}"></a>' not in readme or f'id="{anchor}"' not in home:
                errors.append(f'{label} must be visible on both primary surfaces')
        for text, surface in ((readme, 'README'), (home, 'homepage')):
            framework = text.find('id="framework"')
            gmns = text.find('GMNS is the common object contract')
            stages = text.find('id="four-step-workflow"')
            boston = text.find('id="boston"')
            open_data = text.find('Mobility data support')
            if not (0 <= framework < gmns < stages < boston < open_data):
                errors.append(f'{surface}: framework, GMNS, stages, Boston and Open order changed')
            for stem in ('gmns_connected_layers', 'gps_to_gmns_evidence',
                         'step1_generation', 'step2_distribution', 'step3_mode_response'):
                if stem + '.png' not in text:
                    errors.append(f'{surface}: saved evidence missing: {stem}')
            for key in ('panel_od_019', '29.052', '27.486', '4.0990%', '4.2246%', 'Srestore'):
                if key not in text:
                    errors.append(f'{surface}: GPS-to-response evidence missing: {key}')
        return errors
    errors: list[str] = []
    stages = (
        ("Trip generation", "step-1-trip-generation", "stage-1"),
        ("Trip distribution", "step-2-trip-distribution", "stage-2"),
        ("Mode choice", "step-3-mode-choice", "stage-3"),
        ("Traffic assignment", "step-4-traffic-assignment", "stage-4"),
    )
    for label, anchor, home_id in stages:
        if label.lower() not in readme.lower() or ("boston-behavior-feedback.md#" + anchor) not in readme:
            errors.append(f"README must name and link the actual stage: {label}")
        if f'id="{home_id}"' not in home or label.lower() not in home.lower():
            errors.append(f"Homepage is missing its actual stage card: {label}")
        if f'id="{anchor}"' not in detail:
            errors.append(f"Boston detail anchor missing: {anchor}")
    if "## How GPS changes the result" not in readme or 'id="gps-feedback"' not in home:
        errors.append("GPS must have a primary, visible explanatory section")
    if "## GMNS in Action" not in readme or 'id="gmns-in-action"' not in home:
        errors.append("GMNS in Action must be visible on README and homepage")
    if not (0 <= readme.find("## GMNS in Action") < readme.find("## Four-step workflow")):
        errors.append("GMNS data foundation must precede the four model stages in README")
    if not (0 <= home.find('id="gmns-in-action"') < home.find('id="four-step-workflow"')):
        errors.append("GMNS data foundation must precede the four model stages on homepage")
    for stem in ("gmns_connected_layers", "gps_to_gmns_evidence"):
        if stem + ".png" not in readme or stem + ".png" not in home:
            errors.append(f"Real-data GMNS figure missing on a primary surface: {stem}")
    for key in ("panel_od_019", "29.052", "27.486", "4.0990%", "4.2246%", "Srestore"):
        if key not in readme or key not in home:
            errors.append(f"Saved GPS-to-response evidence not exposed on both primary surfaces: {key}")
    for stem in ("step1_generation", "step2_distribution", "step3_mode_response"):
        if stem + ".png" not in readme or stem + ".png" not in home:
            errors.append(f"A saved stage result figure is not visible: {stem}")
    if not (0 <= readme.find("## Four-step workflow") < readme.find("## Mobility data support")):
        errors.append("Four-stage explanation must precede the supporting Open section")
    if not (0 <= home.find('id="four-step-workflow"') < home.find("Supporting mobility data")):
        errors.append("Homepage four-stage explanation must precede supporting Open data")
    return errors


def main() -> int:
    errors: list[str] = []
    checks = 0

    readme = ROOT / "README.md"
    readme_text = readme.read_text(encoding="utf-8")
    # GitHub READMEs support both Markdown images and limited HTML. Check both.
    readme_links = re.findall(r"\]\(([^)]+)\)", readme_text) + re.findall(
        r"(?:href|src)=[\"']([^\"']+)", readme_text
    )
    readme_images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme_text) + re.findall(
        r"<img\b[^>]*\bsrc=[\"']([^\"']+)", readme_text
    )
    expected_image = "docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png"
    # Protect the new cover, Boston overview and retained benchmark access.
    required_images = {
        "docs/assets/boston/visual_release_r1/mcl_boston_hero.png",
        "docs/assets/boston/visual_release_r1/boston_network_zones.png",
        expected_image,
        "docs/assets/boston/four_step_results_r1/step1_generation.png",
        "docs/assets/boston/four_step_results_r1/step2_distribution.png",
        "docs/assets/boston/four_step_results_r1/step3_mode_response.png",
        "docs/assets/boston/gmns_in_action_r1/gmns_connected_layers.png",
        "docs/assets/boston/gmns_in_action_r1/gps_to_gmns_evidence.png",
        "docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
        "docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png",
        "docs/assets/benchmarks/sioux_250od_phase2_objective_trace.png",
    }
    for required in sorted(required_images):
        if required not in readme_images:
            errors.append(f"README required visual missing: {required}")
        checks += 1
    if not (DOCS / "assets/hero.png").is_file():
        errors.append("Retained previous hero asset is missing")
    checks += 1
    for raw in readme_images:
        target = _local_target(readme, raw)
        if target is None or not target.is_file():
            errors.append(f"Unresolved/nonlocal README image: {raw}")
        elif target.suffix.lower() == ".png" and not target.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(f"Invalid PNG signature: {raw}")
        checks += 1
    for required in ("docs/city-workflow.md", "docs/visualizations.md", "docs/data-tools.md"):
        if required not in readme_links:
            errors.append(f"README required workflow link missing: {required}")
        checks += 1
    if not (0 <= readme_text.find("## City network workflow") < readme_text.find("## Mobility data support")):
        errors.append("README must present the city/network workflow before optional metadata support")
    checks += 1
    gallery = (DOCS / "visualizations.md").read_text(encoding="utf-8")
    for od in ("200", "250"):
        for suffix in ("final_physical_link_flow", "phase1_artificial_flow", "phase2_objective_trace"):
            asset = f"assets/benchmarks/sioux_{od}od_{suffix}.png"
            if asset not in gallery or not (DOCS / asset).is_file():
                errors.append(f"Gallery missing retained benchmark visual: {asset}")
            checks += 1
    for raw in readme_links:
        target = _local_target(readme, raw)
        if target is not None and not target.exists():
            errors.append(f"Broken README link: {raw}")
        checks += 1

    pages = sorted(DOCS.rglob("*.html"))
    page_image_refs = 0
    page_local_refs = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        refs = re.findall(r"(?:href|src)=[\"']([^\"']+)", text)
        page_image_refs += len(re.findall(r"<img\b[^>]*\bsrc=[\"'][^\"']+", text))
        for raw in refs:
            target = _local_target(page, raw)
            if target is not None:
                page_local_refs += 1
                if not target.exists():
                    errors.append(
                        f"Broken Pages link: {page.relative_to(ROOT).as_posix()} -> {raw}"
                    )
            checks += 1

    homepage = (DOCS / "index.html").read_text(encoding="utf-8")
    for label, present in {
        "Boston-backed site cover": 'src="assets/boston/visual_release_r1/mcl_boston_hero.png"' in homepage,
        "Boston network feature": 'src="assets/boston/visual_release_r1/boston_network_zones.png"' in homepage,
        "retained Boston map gallery link": 'href="datasets/boston-central.html#boston-visual-gallery"' in homepage,
        "data-tools navigation": 'href="data-tools.html"' in homepage,
        "data-tools command": "mcl_data.py catalog-city-match" in homepage,
        "approved benchmark image": expected_image.removeprefix("docs/") in homepage,
        "city workflow navigation": 'href="city-workflow.html"' in homepage,
        "visual gallery navigation": 'href="visualizations.html"' in homepage,
        "network command": "tools/mnl.py run" in homepage,
        "framework-first homepage": 0 <= homepage.find('id="framework"') < homepage.find('id="coverage"') < homepage.find('id="boston"') < homepage.find('id="sioux-falls"') < homepage.find("Mobility data support"),
        "GMNS in Action section": 'id="gmns-in-action"' in homepage,
        "GMNS relationship figure": 'src="assets/boston/gmns_in_action_r1/gmns_connected_layers.png"' in homepage,
        "GPS relationship figure": 'src="assets/boston/gmns_in_action_r1/gps_to_gmns_evidence.png"' in homepage,
    }.items():
        if not present:
            errors.append(f"Homepage contract failed: {label}")
        checks += 1

    boston_gallery = (DOCS / "datasets/boston-central.html").read_text(encoding="utf-8")
    for stem in ("boston_network_zones", "boston_activity_prior", "boston_gps_projection", "boston_panel_flow_s1", "boston_panel_flow_delta"):
        asset = f"../assets/boston/visual_release_r1/{stem}.png"
        if asset not in boston_gallery or not (DOCS / "assets/boston/visual_release_r1" / f"{stem}.png").is_file():
            errors.append(f"Boston gallery missing image: {asset}")
        checks += 1

    # Protect the supporting evidence overview as well as the city-first presentation.
    evidence = json.loads((ROOT / "catalog/open-data-evidence.json").read_text(encoding="utf-8"))
    layers = {layer["id"]: layer for layer in evidence["layers"]}
    metric_ids = {
        "global_city_frame": "ghsl_urban_centres",
        "gtfs_static": "cities_with_inside_polygon_stop_evidence",
        "gtfs_realtime": "endpoint_representatives",
        "osm_map_features": "sample_extracts",
        "gbfs_shared_mobility": "system_rows",
        "model_interoperability": "crosswalk_entries",
    }
    for layer_id, metric_id in metric_ids.items():
        metric = next(m for m in layers[layer_id]["metrics"] if m["id"] == metric_id)
        expected_value = f"{metric['value']:,}"
        for label, surface in (("README", readme_text), ("Pages homepage", homepage)):
            pattern = rf'<(?:td|article)\b[^>]*data-evidence-layer="{re.escape(layer_id)}"[^>]*>(.*?)</(?:td|article)>'
            match = re.search(pattern, surface, re.S)
            if not match or expected_value not in match.group(1):
                errors.append(f"{label}: evidence card missing/stale for {layer_id}")
            checks += 1
    if not (0 <= readme_text.find('id="framework"') < readme_text.find('id="coverage"') < readme_text.find('id="boston"') < readme_text.find('id="sioux-falls"') < readme_text.find("## Mobility data support")):
        errors.append("Data overview must follow framework and both case introductions")
    checks += 1

    detail = (DOCS / "datasets/boston-behavior-feedback.html").read_text(encoding="utf-8")
    errors.extend(presentation_errors(readme_text, homepage, detail))
    checks += 1
    gmns_detail = (DOCS / "datasets/boston-gmns-exchange.html").read_text(encoding="utf-8")
    for required in (
        'id="one-network-multiple-connected-data-layers"',
        'id="from-gps-coordinates-to-gmns-linked-evidence"',
        'id="reproduce-the-relationships"',
        "trace_gmns_figure.py",
        "Separate objects, explicit relationships",
        "Shared network reference",
    ):
        if required not in gmns_detail:
            errors.append(f"GMNS detail missing required relationship evidence: {required}")
        checks += 1

    result = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "readme_image_count": len(readme_images),
        "readme_images": readme_images,
        "pages_html_files": len(pages),
        "pages_local_refs_checked": page_local_refs,
        "pages_image_refs": page_image_refs,
        "visual_qa_performed": False,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
