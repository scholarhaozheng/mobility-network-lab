#!/usr/bin/env python3
"""Draw a source-grounded local Hong Kong physical-to-time cutaway.

This is a display-only view of released physical links and dynamic arcs on
the unchanged finite graph. The highlighted chain is permitted by that graph;
it is not asserted to be a selected or flow-carrying CG column. No model runs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "docs" / "assets" / "hong_kong" / "full_stack_r5"
DEST = ROOT / "docs" / "assets" / "hong_kong" / "presentation_r6"
ARC_REL = "r2r4_baseline/phase_c/case/dynamic_arc.csv"
LINK_REL = "case/selected_physical_links.csv"
LINK_IDS = ("308368", "667532")
CHAIN_IDS = ("arc_308368_t0", "arc_2000000055_t1", "arc_667532_t1")
STATES = ("1000000076", "1000000077", "1000002420", "1000002421")
STATE_Y = dict(zip(STATES, (3.0, 2.0, 1.0, 0.0)))
BLUE, TEAL, RUST, GRAY = "#256c91", "#087f8c", "#a05b43", "#a9b7bf"


def source_rows(relative: str, expected: str) -> list[dict[str, str]]:
    path = BUNDLE / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Protected source hash changed: {relative}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def arrow(ax, start, end, color, linewidth=1.0, alpha=1.0, zorder=2, dashed=False):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12 if linewidth > 2 else 8,
        shrinkA=7,
        shrinkB=7,
        linewidth=linewidth,
        linestyle="--" if dashed else "-",
        color=color,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(patch)


def main() -> None:
    manifest = json.loads((BUNDLE / "HASH_MANIFEST.json").read_text(encoding="utf-8"))
    links = {row["link_id"]: row for row in source_rows(LINK_REL, manifest[LINK_REL])}
    arcs = source_rows(ARC_REL, manifest[ARC_REL])
    by_id = {row["arc_id"]: row for row in arcs}
    first, second = (links[link_id] for link_id in LINK_IDS)
    if first["to_node_id"] != second["from_node_id"]:
        raise ValueError("Physical links no longer form a connected chain")
    chain = [by_id[arc_id] for arc_id in CHAIN_IDS]
    if [(row["arc_type"], row["from_time"], row["to_time"], row["physical_link_id"]) for row in chain] != [
        ("movement", "0", "1", LINK_IDS[0]),
        ("turn_connector", "1", "1", ""),
        ("movement", "1", "2", LINK_IDS[1]),
    ]:
        raise ValueError("Saved local arc semantics changed")
    if any(a["to_node_time_id"] != b["from_node_time_id"] for a, b in zip(chain, chain[1:])):
        raise ValueError("Saved local arc chain is disconnected")
    if [(chain[0]["from_physical_node_id"], chain[0]["to_physical_node_id"]),
        (chain[1]["from_physical_node_id"], chain[1]["to_physical_node_id"]),
        (chain[2]["from_physical_node_id"], chain[2]["to_physical_node_id"])] != [
            (STATES[0], STATES[1]), (STATES[1], STATES[2]), (STATES[2], STATES[3])
    ]:
        raise ValueError("Saved turn-aware state mapping changed")

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,
        "svg.fonttype": "none",
        "svg.hashsalt": "hong-kong-time-cutaway-r6",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig = plt.figure(figsize=(11.2, 5.2), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=(0.95, 2.05), left=0.055, right=0.985,
                            bottom=0.18, top=0.91, wspace=0.25)
    physical = fig.add_subplot(grid[0, 0])
    temporal = fig.add_subplot(grid[0, 1])

    # Panel a: true consecutive physical IDs, with schematic display spacing.
    physical.set_xlim(-0.2, 2.2)
    physical.set_ylim(-0.85, 0.8)
    physical.axis("off")
    physical.text(-0.16, 0.68, "a", fontsize=13, fontweight="bold", color="#173a4a")
    physical_nodes = (first["from_node_id"], first["to_node_id"], second["to_node_id"])
    for i, node_id in enumerate(physical_nodes):
        physical.scatter(i, 0, s=95, facecolor="white", edgecolor="#173a4a", linewidth=1.5, zorder=4)
        physical.text(i, -0.18, node_id, ha="center", va="top", fontsize=9, color="#253746")
    arrow(physical, (0, 0), (1, 0), BLUE, linewidth=2.5, zorder=3)
    arrow(physical, (1, 0), (2, 0), TEAL, linewidth=2.5, zorder=3)
    physical.text(0.5, 0.16, LINK_IDS[0], ha="center", color=BLUE, fontsize=9)
    physical.text(1.5, 0.16, LINK_IDS[1], ha="center", color=TEAL, fontsize=9)

    # Panel b: only actual released arcs among the four saved turn-aware states.
    temporal.text(-0.33, 3.45, "b", fontsize=13, fontweight="bold", color="#173a4a")
    local = [row for row in arcs if row["from_physical_node_id"] in STATES
             and row["to_physical_node_id"] in STATES
             and 0 <= int(row["from_time"]) <= int(row["to_time"]) <= 3
             and row["arc_type"] in {"movement", "waiting", "turn_connector"}]
    for row in local:
        start = (int(row["from_time"]), STATE_Y[row["from_physical_node_id"]])
        end = (int(row["to_time"]), STATE_Y[row["to_physical_node_id"]])
        if row["arc_type"] == "waiting":
            arrow(temporal, start, end, GRAY, linewidth=0.8, alpha=0.6, zorder=1, dashed=True)
        elif row["arc_type"] == "movement" and row["physical_link_id"] in LINK_IDS:
            arrow(temporal, start, end, "#9abecb", linewidth=1.0, alpha=0.65, zorder=1)
        elif row["arc_type"] == "turn_connector" and row["arc_id"].startswith("arc_2000000055_t"):
            arrow(temporal, start, end, "#d9a699", linewidth=1.0, alpha=0.55, zorder=1)
    for row, color in zip(chain, (BLUE, RUST, TEAL)):
        start = (int(row["from_time"]), STATE_Y[row["from_physical_node_id"]])
        end = (int(row["to_time"]), STATE_Y[row["to_physical_node_id"]])
        arrow(temporal, start, end, color, linewidth=2.8, zorder=5)
    temporal.text(0.35, 2.77, LINK_IDS[0], color=BLUE, fontsize=9, fontweight="medium")
    temporal.text(1.08, 1.48, "turn", color=RUST, fontsize=9, fontweight="medium")
    temporal.text(1.35, 0.77, LINK_IDS[1], color=TEAL, fontsize=9, fontweight="medium")
    for state, y in STATE_Y.items():
        temporal.scatter(range(4), [y] * 4, s=28, facecolor="white", edgecolor="#607f90",
                         linewidth=1.1, zorder=6)
    temporal.set_xlim(-0.35, 3.2)
    temporal.set_ylim(-0.45, 3.5)
    temporal.set_xticks(range(4), [f"t={t}" for t in range(4)])
    temporal.set_yticks(list(STATE_Y.values()), [f"n{state}" for state in STATES])
    temporal.set_xlabel("time index · 30 s per step", labelpad=8)
    temporal.tick_params(axis="both", length=0, pad=7, labelcolor="#455c6a")
    temporal.spines["left"].set_visible(False)
    temporal.spines["bottom"].set_color("#c8d5dd")
    temporal.grid(axis="x", color="#edf2f4", linewidth=0.7, zorder=0)
    DEST.mkdir(parents=True, exist_ok=True)
    stem = DEST / "hk_physical_to_time_cutaway"
    svg_path = stem.with_suffix(".svg")
    fig.savefig(svg_path, metadata={"Date": None})
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(stem.with_suffix(".png"), dpi=180)
    plt.close(fig)
    record = {
        "figure_id": stem.name,
        "status": "DERIVED_DISPLAY_ONLY",
        "source_files_sha256": {ARC_REL: manifest[ARC_REL], LINK_REL: manifest[LINK_REL]},
        "physical_link_ids": list(LINK_IDS),
        "physical_node_ids": list(physical_nodes),
        "highlighted_allowed_arc_ids": list(CHAIN_IDS),
        "local_time_slice": [0, 3],
        "time_step_seconds": 30,
        "display_coordinates": "schematic; identities, arc types and times are saved-source values",
        "scope": "permitted local chain, not an exported CG column or observed trajectory",
        "scientific_solver_rerun": False,
    }
    stem.with_suffix(".source.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
