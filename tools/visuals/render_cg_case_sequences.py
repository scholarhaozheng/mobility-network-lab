#!/usr/bin/env python3
"""Render matched scientific CG evidence plates from accepted saved figures.

This module never imports or calls a solver, pricing oracle, demand model, or
map matcher. Documented display crops remove presentation headers/footnotes,
not axes, curves, legends, maps, or other scientific observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"
OUTPUT = ASSETS / "presentation_r5"
SOURCES = OUTPUT / "CG_CASE_SEQUENCE_SOURCES.json"

PANEL_TITLES = (
    "From the physical network to time-indexed columns",
    "Phase I restores feasibility",
    "A new path can help a different OD",
    "Phase II improves the real-path objective",
    "Final physical-link movement flow and validation",
    "Independent pricing closure",
)

CASES = {
    "boston": {
        "panels": (
            ("boston/space_time_cg_r4/boston_space_time_construction.png",),
            ("boston/space_time_cg_r4/boston_phase_i_artificial_flow.png",),
            ("boston/space_time_cg_r4/boston_shared_capacity_event.png",),
            ("boston/space_time_cg_r4/boston_phase_ii_objective.png",),
            ("boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png",),
            ("boston/space_time_cg_r4/boston_pricing_closure_by_demand.png",),
        ),
    },
    "sioux": {
        "panels": (
            ("presentation_r3/sioux_space_time_construction.png",),
            ("presentation_r3/sioux_phase_i_pair.png",),
            ("presentation_r5/sioux_shared_capacity_canonical.png",),
            (
                "benchmarks/sioux_200od_phase2_objective_trace.png",
                "benchmarks/sioux_250od_phase2_objective_trace.png",
            ),
            (
                "benchmarks/sioux_200od_final_physical_link_flow.png",
                "benchmarks/sioux_250od_final_physical_link_flow.png",
            ),
            (),
        ),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources(manifest: dict) -> None:
    expected = {name for case in CASES.values() for panel in case["panels"] for name in panel}
    declared = manifest["sources"]
    if set(declared) != expected:
        raise ValueError("Source manifest and rendered-panel source sets differ")
    for name, digest in declared.items():
        path = ASSETS / name
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256(path) != digest:
            raise ValueError(f"Accepted source hash mismatch: {name}")


def configure_plotting() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "svg.hashsalt": "mcl-cg-case-sequence-r2",
        "savefig.facecolor": "white",
    })


def normalize_svg(path: Path) -> None:
    """Remove Matplotlib's inconsequential trailing spaces inside SVG paths."""
    content = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n",
                    encoding="utf-8")


def draw_source(fig: plt.Figure, name: str, crop: list[float],
                x: float, y: float, w: float, h: float) -> None:
    """Crop only documented presentation margins; preserve source pixels."""
    axis = fig.add_axes((x, y, w, h))
    with Image.open(ASSETS / name) as image:
        left, top, right, bottom = crop
        box = (round(left * image.width), round(top * image.height),
               round(right * image.width), round(bottom * image.height))
        axis.imshow(image.crop(box).convert("RGB"), interpolation="antialiased")
    axis.axis("off")


def draw_case(case_id: str, crops: dict[str, list[float]]) -> None:
    case = CASES[case_id]
    fig = plt.figure(figsize=(20, 16), facecolor="white")
    left, gap_x, panel_h, gap_y, top = 0.028, 0.026, 0.300, 0.019, 0.975
    panel_w = (1.0 - 2.0 * left - gap_x) / 2.0
    for index, names in enumerate(case["panels"]):
        row, col = divmod(index, 2)
        x = left + col * (panel_w + gap_x)
        y = top - (row + 1) * panel_h - row * gap_y
        fig.text(x, y + panel_h - 0.002, chr(97 + index), color="#202b33",
                 fontsize=18, fontweight="bold", va="top")
        image_x, image_y = x + 0.023, y + 0.004
        image_w, image_h = panel_w - 0.029, panel_h - 0.020
        if len(names) == 1:
            draw_source(fig, names[0], crops[names[0]],
                        image_x, image_y, image_w, image_h)
        elif len(names) == 2:
            inset_gap = 0.006
            half_w = (image_w - inset_gap) / 2.0
            for j, name in enumerate(names):
                draw_source(fig, name, crops[name],
                            image_x + j * (half_w + inset_gap),
                            image_y, half_w, image_h)
        else:
            fig.text(x + panel_w / 2, image_y + image_h / 2,
                     "Not established", color="#4a5156", fontsize=19,
                     ha="center", va="center")
    stem = OUTPUT / f"{case_id}_cg_case_sequence"
    fig.savefig(stem.with_suffix(".png"), dpi=150, metadata={"Software": "Matplotlib"})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Date": None})
    normalize_svg(stem.with_suffix(".svg"))
    plt.close(fig)


def draw_overview() -> None:
    """Compact, case-neutral status map; never substitutes for the source panels."""
    fig = plt.figure(figsize=(18, 10), facecolor="#f3f7f9")
    fig.text(0.04, 0.957, "EXECUTED FINITE SPACE–TIME CG EVIDENCE",
             color="#173a4a", fontsize=26, fontweight="bold", va="top")
    fig.text(0.04, 0.897,
             "One method family · one bounded Boston pilot · two historical Sioux Falls selected-OD instances",
             color="#536b78", fontsize=15, va="top")

    columns = (
        (0.04, 0.29, "SHARED EVIDENCE STAGE"),
        (0.35, 0.30, "BOSTON  /  10 ODs"),
        (0.67, 0.29, "SIOUX FALLS  /  200 + 250 ODs"),
    )
    for x, width, heading in columns:
        fig.add_artist(Rectangle((x, 0.804), width, 0.054,
                                 transform=fig.transFigure, facecolor="#173a4a",
                                 edgecolor="none"))
        fig.text(x + 0.011, 0.831, heading, color="white", fontsize=13,
                 fontweight="bold", va="center")

    boston = (
        "Actual B07 time-indexed column",
        "Artificial flow clears at round 90",
        "B07/B09/B10 capacity reallocation",
        "Reference-objective agreement",
        "125-link movement-flow view; checks pass",
        "Established: 10/10 at 1e-6",
    )
    sioux = (
        "Actual XS170 local cutaway",
        "200/250 OD: clears at rounds 51/62",
        "XS170/XS169 capacity reallocation",
        "Each graph matches its own reference",
        "Two distinct movement-flow views; checks pass",
        "Not established for retained runs",
    )
    for i, title in enumerate(PANEL_TITLES):
        y = 0.684 - i * 0.108
        for j, (x, width, _) in enumerate(columns):
            face = "#e9f7f3" if i == 5 and j == 1 else (
                "#fbf1e4" if i == 5 and j == 2 else "white")
            fig.add_artist(Rectangle((x, y), width, 0.097,
                                     transform=fig.transFigure, facecolor=face,
                                     edgecolor="#c7d7df", linewidth=1))
        fig.text(0.05, y + 0.049, f"{chr(65 + i)}  {title}", color="#173a4a",
                 fontsize=13, fontweight="bold", va="center")
        fig.text(0.36, y + 0.049, boston[i], color="#314e5b",
                 fontsize=12, va="center")
        fig.text(0.68, y + 0.049, sioux[i], color="#314e5b",
                 fontsize=12, va="center")
    fig.text(0.04, 0.026,
             "Saved-result presentation composite · reference-objective agreement is distinct from independent pricing closure · no scientific model rerun",
             color="#536b78", fontsize=11, va="center")
    stem = OUTPUT / "boston_sioux_cg_parallel_overview"
    fig.savefig(stem.with_suffix(".png"), dpi=150, metadata={"Software": "Matplotlib"})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Date": None})
    normalize_svg(stem.with_suffix(".svg"))
    plt.close(fig)


def verify_outputs() -> None:
    sizes = []
    for case_id in CASES:
        png = OUTPUT / f"{case_id}_cg_case_sequence.png"
        svg = OUTPUT / f"{case_id}_cg_case_sequence.svg"
        if not png.is_file() or not svg.is_file():
            raise FileNotFoundError(f"Missing presentation outputs for {case_id}")
        with Image.open(png) as image:
            image.verify()
        with Image.open(png) as image:
            sizes.append(image.size)
        root = ET.parse(svg).getroot()
        if not any(element.tag.endswith("}text") for element in root.iter()):
            raise ValueError(f"SVG text is not editable: {svg}")
    if sizes[0] != sizes[1] or sizes[0] != (3000, 2400):
        raise ValueError(f"Case canvases differ or have wrong dimensions: {sizes}")
    overview_png = OUTPUT / "boston_sioux_cg_parallel_overview.png"
    overview_svg = OUTPUT / "boston_sioux_cg_parallel_overview.svg"
    with Image.open(overview_png) as image:
        image.verify()
    with Image.open(overview_png) as image:
        if image.size != (2700, 1500):
            raise ValueError("Overview canvas has wrong dimensions")
    if not any(element.tag.endswith("}text") for element in ET.parse(overview_svg).getroot().iter()):
        raise ValueError("Overview SVG text is not editable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="Check accepted source hashes and both already-rendered outputs")
    parser.add_argument("--case-only", action="store_true",
                        help="Regenerate the two case figures without changing the overview")
    args = parser.parse_args()
    manifest = json.loads(SOURCES.read_text(encoding="utf-8"))
    verify_sources(manifest)
    crops = manifest["display_crops"]
    if set(crops) != set(manifest["sources"]):
        raise ValueError("Every displayed source must have one documented crop")
    for name, crop in crops.items():
        if len(crop) != 4 or not (0 <= crop[0] < crop[2] <= 1 and
                                 0 <= crop[1] < crop[3] <= 1):
            raise ValueError(f"Invalid display crop: {name}")
    if not args.verify_only:
        configure_plotting()
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for case_id in CASES:
            draw_case(case_id, crops)
        if not args.case_only:
            draw_overview()
    verify_outputs()
    print("CG case-sequence source hashes and matched PNG/SVG outputs: PASS")


if __name__ == "__main__":
    main()
