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
    readme_links = re.findall(r"\]\(([^)]+)\)", readme_text)
    readme_images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme_text)
    expected_image = "docs/assets/benchmarks/sioux_250od_final_physical_link_flow.png"
    if readme_images != [expected_image]:
        errors.append(f"README image contract failed: {readme_images}")
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
