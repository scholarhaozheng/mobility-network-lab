#!/usr/bin/env python3
"""Reframe frozen Algorithm B/FW scatter points for the public comparison.

This display-only renderer reads the accepted SVG point coordinates and the
accepted Algorithm B link-flow CSVs. It does not run assignment or recompute
the FW reference. The original source panels remain untouched.
"""
from __future__ import annotations

import csv
import hashlib
import math
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "algorithms" / "origin_based_algorithm_b"
DEST = ROOT / "docs" / "assets" / "algorithm_b_r21" / "presentation"
CASES = {
    "sioux": (
        "c2c2ded314299dfd552faed76f377870c70f2163d94f46cca500fd3a89c2aec1",
        "85f593b8b57d2d0f2c9fffe98bf44b7f14f496ac6c5c3550230b081d9f073972",
        76,
    ),
    "boston_b1": (
        "87ead4c0f3439823a6829e4a0708795212f5a171775ad0f8d846ddaa0581beb7",
        "1d66c1ad838c22fc3d1c17e6c94ff3c4c5ccaad9da375a702d8108c0852444bd",
        5091,
    ),
}
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}
PLOT_LEFT, PLOT_BOTTOM, PLOT_SPAN = 105.0, 545.0, 440.0


def checked_bytes(path: Path, expected_hash: str) -> bytes:
    data = path.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"Frozen source hash changed: {path}")
    return data


def saved_points(case: str) -> tuple[np.ndarray, np.ndarray, float]:
    svg_hash, csv_hash, expected_count = CASES[case]
    svg_path = SOURCE / "figures" / f"{case}_fw_flow.svg"
    csv_path = SOURCE / "accepted_results" / f"{case}_physical_link_flow.csv"
    svg_root = ET.fromstring(checked_bytes(svg_path, svg_hash))
    circles = svg_root.findall("svg:circle", SVG_NS)
    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        accepted_flows = [float(row["volume"]) for row in csv.DictReader(stream)]
    checked_bytes(csv_path, csv_hash)
    if len(circles) != expected_count or len(accepted_flows) != expected_count:
        raise ValueError(f"Saved link count changed for {case}")

    # The frozen source SVG maps each log10(1 + flow) axis to the same square.
    # Its coordinates are rounded to 0.01 px. The accepted Algorithm B flows
    # independently anchor the original plotted scale without changing points.
    x_fraction = np.array(
        [(float(item.attrib["cx"]) - PLOT_LEFT) / PLOT_SPAN for item in circles]
    )
    y_fraction = np.array(
        [(PLOT_BOTTOM - float(item.attrib["cy"])) / PLOT_SPAN for item in circles]
    )
    ratios = [
        math.log10(1.0 + volume) / fraction
        for fraction, volume in zip(sorted(y_fraction), sorted(accepted_flows))
        if volume > 1.0 and fraction > 0.001
    ]
    axis_max = statistics.median(ratios)
    if (max(ratios) - min(ratios)) / axis_max > 0.001:
        raise ValueError(f"Saved SVG and accepted flows disagree for {case}")
    return x_fraction * axis_max, y_fraction * axis_max, axis_max


def render(case: str) -> None:
    x_log, y_log, axis_max = saved_points(case)
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "svg.fonttype": "none",
            "svg.hashsalt": "algorithm-b-r21-fw-compact",
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
        }
    )
    fig, ax = plt.subplots(figsize=(5.2, 5.0), facecolor="white")
    fig.subplots_adjust(left=0.17, right=0.975, bottom=0.17, top=0.98)
    ax.set_facecolor("white")
    ax.set_aspect("equal", adjustable="box")
    if case == "sioux":
        # All 76 retained Sioux links lie in the upper part of the source
        # range. A labeled zoom exposes their deviations from the diagonal.
        low = min(float(x_log.min()), float(y_log.min()))
        high = max(float(x_log.max()), float(y_log.max()))
        pad = 0.1 * (high - low)
        axis_low, axis_high = low - pad, high + pad
        ticks = np.arange(3.6, 4.41, 0.2)
    else:
        axis_low, axis_high = 0.0, axis_max
        ticks = np.arange(0.0, axis_max + 0.0001, 0.5)
    ax.set_xlim(axis_low, axis_high)
    ax.set_ylim(axis_low, axis_high)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.grid(color="#e4e9ed", linewidth=0.55, zorder=0)
    ax.plot([axis_low, axis_high], [axis_low, axis_high], color="#b66347", linewidth=1.15, zorder=1)
    ax.scatter(
        x_log,
        y_log,
        s=13 if case == "sioux" else 7,
        color="#236785",
        alpha=0.55 if case == "sioux" else 0.16,
        edgecolors="none",
        rasterized=False,
        zorder=2,
    )
    ax.set_xlabel(r"FW · $\log_{10}(1 + \mathrm{flow})$", labelpad=9)
    ax.set_ylabel(r"Algorithm B · $\log_{10}(1 + \mathrm{flow})$", labelpad=9)
    DEST.mkdir(parents=True, exist_ok=True)
    for suffix, kwargs in (("svg", {"metadata": {"Date": None}}), ("png", {"dpi": 180})):
        fig.savefig(DEST / f"{case}_fw_flow_compact.{suffix}", **kwargs)
    plt.close(fig)


def main() -> None:
    for case in CASES:
        render(case)


if __name__ == "__main__":
    main()
