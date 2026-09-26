#!/usr/bin/env python3
"""Redraw the saved Sioux shared-capacity diagram with canonical public terms.

Only the four published before/after plot-input rows are read. No optimizer,
pricing oracle, shortest-path routine, or model reconstruction is called.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
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
OUT = ASSETS / "presentation_r5"
META = OUT / "SIOUX_CAPACITY_CANONICAL_SOURCES.json"
STEM = OUT / "sioux_shared_capacity_canonical"


def read_saved_rows() -> dict[tuple[str, str], dict]:
    manifest = json.loads(META.read_text(encoding="utf-8"))
    for name, expected in manifest["source_hashes"].items():
        path = ASSETS / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Accepted saved source hash mismatch: {name}")
    with (ASSETS / manifest["plot_input"]).open(newline="", encoding="utf-8") as handle:
        rows = {(row["case"], row["stage"]): row for row in csv.DictReader(handle)}
    if set(rows) != {(case, stage) for case in ("200_od", "250_od")
                    for stage in ("before", "after")}:
        raise ValueError("Expected exactly two cases with before/after rows")
    for case, round_number in (("200_od", "34"), ("250_od", "39")):
        before, after = rows[(case, "before")], rows[(case, "after")]
        if before["round"] != round_number or after["round"] != round_number:
            raise ValueError(f"Wrong saved round for {case}")
        for row in (before, after):
            if row["time_arc"] != "xs_link21_t1":
                raise ValueError("Wrong shared time arc")
            if (Decimal(row["arc_load"]) != Decimal("5050.193")
                    or Decimal(row["arc_capacity"]) != Decimal("5050.193")):
                raise ValueError("Recorded shared arc is not at the declared capacity")
        if not (Decimal(before["xs170_on_arc"]) == 500
                and Decimal(after["xs170_on_arc"]) == 0
                and Decimal(after["xs169_on_arc"]) - Decimal(before["xs169_on_arc"]) == 500
                and Decimal(after["xs169_artificial_flow_change"]) == -500):
            raise ValueError("Saved 500-unit exchange no longer matches the public record")
    return rows


def render(rows: dict[tuple[str, str], dict]) -> None:
    mpl.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "svg.hashsalt": "mcl-sioux-capacity-r2"})
    fig = plt.figure(figsize=(12, 6.5), facecolor="white")
    navy, teal, amber, gray = "#173a4a", "#087f8c", "#d59833", "#b8c7ce"
    fig.text(.055, .952, "Sioux Falls | saved shared-capacity reallocation",
             color=navy, fontsize=22, fontweight="bold", va="top")
    fig.text(.055, .874,
             "200 OD: round 34 · 250 OD: round 39 · binding time arc xs_link21_t1",
             color="#536b78", fontsize=11.5, va="top")

    ax = fig.add_axes((.09, .40, .55, .35))
    before, after = rows[("200_od", "before")], rows[("200_od", "after")]
    for y, row in ((1, before), (0, after)):
        xs170 = float(row["xs170_on_arc"])
        xs169 = float(row["xs169_on_arc"])
        total = float(row["arc_load"])
        other = total - xs170 - xs169
        ax.barh(y, other, color=gray, edgecolor="white", height=.48)
        ax.barh(y, xs169, left=other, color=teal, edgecolor="white", height=.48)
        if xs170:
            ax.barh(y, xs170, left=other + xs169, color=amber, edgecolor="white", height=.48)
    ax.set_xlim(0, 5200)
    ax.set_yticks((1, 0), ("Before", "After"))
    ax.set_xlabel("Recorded use of xs_link21_t1 (model flow units)", color=navy)
    ax.axvline(5050.193, color=navy, lw=1.2, ls="--")
    ax.text(5050.193, 1.49, "capacity 5,050.193", ha="right", color=navy, fontsize=9)
    ax.grid(axis="x", alpha=.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for x, color, label in ((.09, gray, "Other recorded arc use (derived remainder)"),
                            (.35, teal, "XS169"), (.48, amber, "XS170")):
        fig.add_artist(Rectangle((x, .29), .017, .017, transform=fig.transFigure,
                                 facecolor=color, edgecolor="none"))
        fig.text(x + .022, .298, label, color=navy, fontsize=8.5, va="center")

    fig.add_artist(Rectangle((.68, .37), .27, .41, transform=fig.transFigure,
                             facecolor="#eff7f7", edgecolor="#c7d7df"))
    fig.text(.705, .735, "500-unit exchange", color=navy, fontsize=16,
             fontweight="bold", va="top")
    fig.text(.705, .665, "XS170 leaves the shared arc", color=navy, fontsize=11)
    fig.text(.705, .605, "XS169 use: 150.193 → 650.193", color=teal, fontsize=11)
    fig.text(.705, .545, "XS169 artificial flow: −500", color=navy, fontsize=11)
    fig.text(.705, .485, "Total load stays at capacity", color=navy, fontsize=11)
    fig.text(.705, .425, "Raw capacity dual ≈ −1", color="#536b78", fontsize=11)
    fig.text(.055, .165,
             "The same recorded arc values occur in both retained selected-OD runs. These before/after restricted-master optima",
             color="#536b78", fontsize=10.5)
    fig.text(.055, .126,
             "show reallocation, not that the selected XS170 column was uniquely necessary.",
             color="#536b78", fontsize=10.5)
    fig.text(.055, .060,
             "Saved-result visualization · accepted public plot input · no optimizer or pricing rerun",
             color="#536b78", fontsize=10)
    fig.savefig(STEM.with_suffix(".png"), dpi=180, bbox_inches="tight", pad_inches=.15)
    fig.savefig(STEM.with_suffix(".svg"), bbox_inches="tight", pad_inches=.15,
                metadata={"Date": None})
    plt.close(fig)


def verify_output() -> None:
    png, svg = STEM.with_suffix(".png"), STEM.with_suffix(".svg")
    with Image.open(png) as image:
        image.verify()
    if not any(node.tag.endswith("}text") for node in ET.parse(svg).getroot().iter()):
        raise ValueError("Canonical Sioux SVG text is not editable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    rows = read_saved_rows()
    if not args.verify_only:
        render(rows)
    verify_output()
    print("Sioux saved-capacity source/hash and canonical PNG/SVG: PASS")


if __name__ == "__main__":
    main()
