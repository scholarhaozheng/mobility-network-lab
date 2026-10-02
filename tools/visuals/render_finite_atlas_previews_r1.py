#!/usr/bin/env python3
"""Make source-faithful homepage crops of already accepted finite-network figures.

These are navigation thumbnails only.  Scientific figures and source records are
left byte-for-byte unchanged; each thumbnail links back to its complete source.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/homepage_finite_atlas_r1"
SIZE = (480, 300)

# Crop boxes target the network/path area, never a numerical axis or a
# qualifying legend. The complete unmodified figure is one click away.
SOURCES = {
    "boston": {
        "construction": ("three_city_r2/boston_physical_to_time_expanded_graph.png", (45, 515, 1675, 1380), "Saved finite-graph construction cutaway"),
        "layered": ("cg_layered_companions_r1/boston_layered_space_time_construction.png", (70, 295, 1580, 1600), "B07 excerpt in selected time layers"),
        "path": ("boston/space_time_cg_r4/boston_space_time_construction.png", (965, 155, 2005, 1045), "Recorded B07 time-indexed column"),
    },
    "sioux_falls": {
        "construction": ("three_city_r2/sioux_physical_to_time_expanded_graph.png", (45, 515, 1675, 1380), "Saved finite-graph construction cutaway"),
        "layered": ("presentation_r3/sioux_space_time_construction.png", (70, 295, 1580, 1600), "XS170 example in selected time layers"),
        "path": ("three_city_r2/sioux_generated_column_time_indexed_path.png", (20, 70, 925, 710), "Saved XS170 physical route; ordered arcs remain in full figure"),
    },
    "hong_kong": {
        "construction": ("three_city_r2/hong_kong_physical_to_time_expanded_graph.png", (45, 515, 1675, 1380), "Saved turn-aware finite-graph cutaway"),
        "layered": ("cg_layered_companions_r1/hong_kong_layered_space_time_construction.png", (70, 295, 1580, 1600), "Approved HK10 excerpt in selected time layers"),
        "path": ("hong_kong/presentation_r6/hk_physical_to_time_cutaway.png", (845, 65, 1995, 850), "Display-only permitted local chain; not an exported CG column"),
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for city, roles in SOURCES.items():
        for role, (relative, crop_box, scope) in roles.items():
            source = ROOT / "docs/assets" / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            with Image.open(source) as original:
                if not (0 <= crop_box[0] < crop_box[2] <= original.width and
                        0 <= crop_box[1] < crop_box[3] <= original.height):
                    raise ValueError((source, crop_box, original.size))
                crop = original.convert("RGB").crop(crop_box)
                fitted = ImageOps.contain(crop, SIZE, method=Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", SIZE, "white")
                canvas.paste(fitted, ((SIZE[0] - fitted.width) // 2,
                                      (SIZE[1] - fitted.height) // 2))
            preview = OUT / f"{city}_{role}.png"
            canvas.save(preview, optimize=True)
            sidecar = {
                "source_figure": source.relative_to(ROOT).as_posix(),
                "source_sha256": sha(source),
                "preview": preview.relative_to(ROOT).as_posix(),
                "preview_sha256": sha(preview),
                "crop_source_box_xyxy": list(crop_box),
                "display_size_px": list(SIZE),
                "transform": "source-faithful crop and aspect-preserving containment; no scientific values redrawn",
                "scope": scope,
                "scientific_solver_rerun": False,
            }
            if city == "hong_kong":
                sidecar["disclosure_boundary"] = (
                    "Only the existing approved HK10 excerpt or source-qualified local display; "
                    "no full path pool, state arrays or raw observations"
                )
            preview.with_suffix(".source.json").write_text(
                json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
            )
    print("Rendered 9 source-faithful finite-network navigation thumbnails")


if __name__ == "__main__":
    render()
