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
    # Protect the banner and network-result access, not an arbitrary one-image cap.
    required_images = {
        "docs/assets/hero.png",
        expected_image,
        "docs/assets/benchmarks/sioux_200od_final_physical_link_flow.png",
        "docs/assets/benchmarks/sioux_200od_phase2_objective_trace.png",
        "docs/assets/benchmarks/sioux_250od_phase2_objective_trace.png",
    }
    for required in sorted(required_images):
        if required not in readme_images:
            errors.append(f"README required visual missing: {required}")
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
        "data-tools navigation": 'href="data-tools.html"' in homepage,
        "data-tools command": "mcl_data.py catalog-city-match" in homepage,
        "approved benchmark image": expected_image.removeprefix("docs/") in homepage,
        "city workflow navigation": 'href="city-workflow.html"' in homepage,
        "visual gallery navigation": 'href="visualizations.html"' in homepage,
        "network command": "tools/mnl.py run" in homepage,
        "network-first homepage": 0 <= homepage.find("Networks and visual results") < homepage.find("Supporting mobility data"),
    }.items():
        if not present:
            errors.append(f"Homepage contract failed: {label}")
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
