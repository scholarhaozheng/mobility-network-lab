#!/usr/bin/env python3
"""Render two matched CG case-sequence collages from accepted saved figures only.

This module never imports or calls a solver, pricing oracle, demand model, or
map matcher. The scientific panels are existing public PNGs shown without crop.
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
        "title": "BOSTON  /  ONE BOUNDED CG PILOT",
        "scope": "90 physical nodes · 125 directed links · 10 ODs · 3-second steps · 100-step horizon",
        "notes": (
            "Actual B07 column; schematic time cutaway",
            "Artificial flow 20.5536 → 0 by round 90",
            "Saved B07/B09/B10 shared-capacity reallocation",
            "Reference-objective agreement by round 15",
            "52 positive-flow links; final numerical checks pass",
            "Established: 10/10 demands at 1e-6",
        ),
        "panels": (
            ("boston/space_time_cg_r4/boston_space_time_construction.png",),
            ("boston/space_time_cg_r4/boston_phase_i_artificial_flow.png",),
            ("boston/space_time_cg_r4/boston_shared_capacity_event.png",),
            ("boston/space_time_cg_r4/boston_phase_ii_objective.png",),
            (
                "boston/space_time_cg_r4/boston_cg_final_physical_link_flow.png",
                "boston/space_time_cg_r4/boston_cg_validation.png",
            ),
            ("boston/space_time_cg_r4/boston_pricing_closure_by_demand.png",),
        ),
    },
    "sioux": {
        "title": "SIOUX FALLS  /  TWO HISTORICAL CG BENCHMARKS",
        "scope": "Distinct selected-OD instances: 200 ODs and 250 ODs · not a real-city demand model",
        "notes": (
            "Actual XS170 local cutaway; schematic positions",
            "Artificial flow clears at rounds 51 / 62",
            "XS170/XS169 shared-capacity reallocation",
            "Each selected-OD graph matches its own reference",
            "Separate 200/250-OD flows; reported checks pass",
            "Not established for the retained historical runs",
        ),
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
        "savefig.facecolor": "#f3f7f9",
    })


def draw_source(fig: plt.Figure, name: str, x: float, y: float, w: float, h: float) -> None:
    """Display the entire accepted panel: no crop or local pixel adjustment."""
    axis = fig.add_axes((x, y, w, h))
    with Image.open(ASSETS / name) as image:
        axis.imshow(image.convert("RGB"), interpolation="antialiased")
    axis.axis("off")


def draw_case(case_id: str) -> None:
    case = CASES[case_id]
    fig = plt.figure(figsize=(20, 20), facecolor="#f3f7f9")
    fig.text(0.035, 0.967, case["title"], color="#173a4a", fontsize=27,
             fontweight="bold", va="top")
    fig.text(0.035, 0.928, case["scope"], color="#536b78", fontsize=15, va="top")

    left, gap_x, card_h, gap_y, top = 0.035, 0.025, 0.265, 0.022, 0.901
    card_w = (1.0 - 2.0 * left - gap_x) / 2.0
    for index, (title, names, note) in enumerate(zip(PANEL_TITLES, case["panels"], case["notes"])):
        row, col = divmod(index, 2)
        x = left + col * (card_w + gap_x)
        y = top - (row + 1) * card_h - row * gap_y
        fig.add_artist(Rectangle((x, y), card_w, card_h,
                                 transform=fig.transFigure, facecolor="white",
                                 edgecolor="#c7d7df", linewidth=1.3, zorder=0))
        fig.add_artist(Rectangle((x, y + card_h - 0.052), card_w, 0.052,
                                 transform=fig.transFigure, facecolor="#173a4a",
                                 edgecolor="none", zorder=1))
        fig.text(x + 0.012, y + card_h - 0.025,
                 f"{chr(65 + index)}  {title}", color="white", fontsize=16,
                 fontweight="bold", va="center", zorder=2)
        fig.text(x + 0.014, y + 0.023, note, color="#314e5b", fontsize=12,
                 va="center", zorder=2)

        image_y, image_h = y + 0.047, card_h - 0.108
        if len(names) == 1:
            draw_source(fig, names[0], x + 0.013, image_y, card_w - 0.026, image_h)
        elif len(names) == 2:
            inset_gap = 0.008
            image_w = (card_w - 0.026 - inset_gap) / 2.0
            for j, name in enumerate(names):
                draw_source(fig, name, x + 0.013 + j * (image_w + inset_gap),
                            image_y, image_w, image_h)
        else:
            fig.add_artist(Rectangle((x + 0.046, image_y + 0.019), card_w - 0.092,
                                     image_h - 0.038, transform=fig.transFigure,
                                     facecolor="#f6f8fa", edgecolor="#b48b55",
                                     linewidth=2, zorder=1))
            fig.text(x + card_w / 2, image_y + image_h * 0.60,
                     "NOT ESTABLISHED", color="#815a32", fontsize=24,
                     fontweight="bold", ha="center", va="center", zorder=2)
            fig.text(x + card_w / 2, image_y + image_h * 0.34,
                     "Reference-objective agreement is a separate check",
                     color="#536b78", fontsize=12, ha="center", va="center", zorder=2)

    fig.text(0.035, 0.025,
             "Saved-result presentation composite · accepted figures only · no scientific model rerun",
             color="#536b78", fontsize=12, va="center")
    stem = OUTPUT / f"{case_id}_cg_case_sequence"
    fig.savefig(stem.with_suffix(".png"), dpi=150, metadata={"Software": "Matplotlib"})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Date": None})
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
    if sizes[0] != sizes[1] or sizes[0] != (3000, 3000):
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
    args = parser.parse_args()
    manifest = json.loads(SOURCES.read_text(encoding="utf-8"))
    verify_sources(manifest)
    if not args.verify_only:
        configure_plotting()
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for case_id in CASES:
            draw_case(case_id)
        draw_overview()
    verify_outputs()
    print("CG case-sequence source hashes and matched PNG/SVG outputs: PASS")


if __name__ == "__main__":
    main()
