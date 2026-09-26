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
                         "svg.fonttype": "none", "svg.hashsalt": "mcl-sioux-capacity-academic-r1",
                         "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "legend.frameon": False})
    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor="white")
    navy, teal, amber, gray = "#243746", "#087f8c", "#d59833", "#b8c7ce"
    fig.subplots_adjust(left=.12, right=.96, top=.87, bottom=.28)
    before, after = rows[("200_od", "before")], rows[("200_od", "after")]
    for y, row in ((1, before), (0, after)):
        xs170 = float(row["xs170_on_arc"])
        xs169 = float(row["xs169_on_arc"])
        total = float(row["arc_load"])
        other = total - xs170 - xs169
        ax.barh(y, other, color=gray, edgecolor="white", height=.48,
                label="Other arc use" if y == 1 else None)
        ax.barh(y, xs169, left=other, color=teal, edgecolor="white", height=.48,
                label="XS169" if y == 1 else None)
        if xs170:
            ax.barh(y, xs170, left=other + xs169, color=amber, edgecolor="white",
                    height=.48, label="XS170")
    ax.set_xlim(0, 5200)
    ax.set_ylim(-.52, 1.55)
    ax.set_yticks((1, 0), ("Before", "After"))
    ax.set_xlabel("Use of time arc xs_link21_t1 (model flow units)", color=navy)
    ax.axvline(5050.193, color=navy, lw=1.0, ls="--")
    ax.text(5050.193, 1.42, "capacity = 5,050.193", ha="right",
            color=navy, fontsize=9)
    ax.grid(axis="x", alpha=.16)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -.32))
    fig.savefig(STEM.with_suffix(".png"), dpi=220, bbox_inches="tight", pad_inches=.12)
    fig.savefig(STEM.with_suffix(".svg"), bbox_inches="tight", pad_inches=.12,
                metadata={"Date": None})
    plt.close(fig)
    svg = STEM.with_suffix(".svg")
    svg.write_text("\n".join(line.rstrip() for line in
                             svg.read_text(encoding="utf-8").splitlines()) + "\n",
                   encoding="utf-8")


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
