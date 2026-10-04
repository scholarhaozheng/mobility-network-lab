#!/usr/bin/env python3
"""Build only R3 presentation derivatives from already published saved assets."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch
from PIL import Image, ImageOps

from visuals.render_homepage_evidence_r2 import ROOT, OUT as R2_OUT, SIOUX_L3, SIOUX_LINKS, graph, records, sha

OUT = ROOT / "docs/assets/homepage_alignment_r3"
ATLAS = OUT / "atlas"


def compact_path(source: str) -> str:
    key = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"docs/assets/homepage_alignment_r3/atlas/{key}.png"


def _save_sidecar(dest: Path, source: str, transform: str, **extra: object) -> None:
    content = {
        "preview_path": dest.relative_to(ROOT).as_posix(),
        "preview_sha256": sha(dest),
        "source_path": source,
        "source_sha256": sha(ROOT / source),
        "transform": transform,
        "crop": "none",
        "canvas": [600, 360],
        **extra,
    }
    dest.with_suffix(".source.json").write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def render_sioux_gmns() -> str:
    """Show directed records and one supplied OD; R2 row 01 stays topology-only."""
    source = SIOUX_LINKS
    links = records(source)
    demand = records("examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/demand.csv")
    segments, nodes = graph("Sioux Falls")
    assert len(nodes) == 24 and len(links) == 76
    assert demand[0]["o_zone_id"] in nodes and demand[0]["d_zone_id"] in nodes
    fig = plt.figure(figsize=(6, 3.6), dpi=100, facecolor="white")
    ax = fig.add_axes((.09, .16, .70, .72))
    ax.add_collection(LineCollection([coords for _, coords in segments], colors="#b8cbd2", linewidths=1.0, zorder=1))
    for row in links[:12]:
        a, b = nodes[row["from_node_id"]], nodes[row["to_node_id"]]
        start = (a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25)
        end = (a[0] * .27 + b[0] * .73, a[1] * .27 + b[1] * .73)
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8,
                                     color="#087f8c", linewidth=1.4, zorder=3))
        if row["link_id"] in {"1", "2", "3", "4", "5", "6"}:
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            ax.text(*mid, row["link_id"], fontsize=6, color="#17364a", zorder=5,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": .3})
    ax.scatter([p[0] for p in nodes.values()], [p[1] for p in nodes.values()],
               s=7, color="#17364a", zorder=4)
    for node_id, color, marker in (("1", "#d99139", "O"), ("2", "#a45436", "D")):
        xy = nodes[node_id]
        ax.scatter([xy[0]], [xy[1]], s=75, color=color, edgecolor="white", zorder=6)
        ax.annotate(marker + " " + node_id, xy, xytext=(4, 5), textcoords="offset points",
                    fontsize=7, weight="bold", color=color, zorder=7)
    allx = [p[0] for p in nodes.values()]; ally = [p[1] for p in nodes.values()]
    dx = max(allx) - min(allx); dy = max(ally) - min(ally)
    ax.set_xlim(min(allx) - .08 * dx, max(allx) + .08 * dx)
    ax.set_ylim(min(ally) - .08 * dy, max(ally) + .08 * dy)
    ax.set_aspect("equal"); ax.axis("off")
    fig.text(.81, .72, "24 nodes", fontsize=9, weight="bold", color="#17364a")
    fig.text(.81, .65, "76 directed links", fontsize=8, color="#17364a")
    fig.text(.81, .56, "link IDs + direction", fontsize=7, color="#087f8c")
    fig.text(.81, .48, "OD 1 → 2 supplied", fontsize=7, color="#b4642a")
    fig.text(.09, .055, "Schematic topology · no city zone hierarchy or centroid connectors", fontsize=7, color="#526779")
    dest = OUT / "sioux_gmns_directed_objects.png"
    fig.savefig(dest, dpi=100, facecolor="white", metadata={"Software": "MCL presentation R3"})
    plt.close(fig)
    _save_sidecar(dest, source, "Directed arrows and IDs on the frozen 24-node, 76-link graph; supplied OD 1→2 annotation",
                  city="Sioux Falls", row_id="02", demand_source="examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/demand.csv",
                  demand_sha256=sha(ROOT / "examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/demand.csv"))
    return dest.relative_to(ROOT).as_posix()


def render_sioux_l3_rank50() -> str:
    source = SIOUX_L3
    rows = sorted(records(source), key=lambda r: float(r["explicit_v"]), reverse=True)[:10]
    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=100)
    fig.patch.set_facecolor("white")
    y = list(range(len(rows)))
    ax.barh(y, [float(r["explicit_v"]) for r in rows], color="#087f8c")
    ax.set_yticks(y, ["link " + r["link_id"] for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Saved explicit link flow (benchmark units)", fontsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    for spine in ("top", "right"): ax.spines[spine].set_visible(False)
    fig.subplots_adjust(left=.19, right=.95, top=.94, bottom=.17)
    dest = OUT / "sioux_native_l3_rank50_link_flows.png"
    fig.savefig(dest, dpi=100, facecolor="white", metadata={"Software": "MCL presentation R3"})
    plt.close(fig)
    _save_sidecar(dest, source, "Top ten saved explicit_v link-flow values, descending; no solver rerun",
                  city="Sioux Falls", method="Native Diagnostic L3", instance="rank 50, outer 04")
    return dest.relative_to(ROOT).as_posix()


def render_sioux_fw_summary() -> str:
    """Typeset retained FW diagnostics; no standalone FW link vector is public."""
    source = "docs/datasets/sioux-static-fw.md"
    saved = (ROOT / source).read_text(encoding="utf-8")
    def metric(label: str) -> str:
        match = re.search(r"^\| " + re.escape(label) + r" \| ([^|]+) \|$", saved, re.M)
        if not match:
            raise AssertionError(f"Saved Sioux FW metric missing: {label}")
        return match.group(1).strip()
    objective = metric("Recomputed Beckmann objective")
    gap = metric("Fixed-flow gap / Beckmann objective")
    od = metric("OD records")
    iterations = metric("Saved iterations")
    assert metric("Physical nodes / directed links") == "24 / 76"
    fig = plt.figure(figsize=(6, 3.6), dpi=100, facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ink, teal, muted = "#17364a", "#087f8c", "#526779"
    ax.text(.07, .85, "Historical Frank–Wolfe", color=ink, fontsize=13, weight="bold")
    ax.text(.07, .76, "Sioux Falls · static BPR/Beckmann", color=muted, fontsize=8)
    ax.plot([.07, .93], [.70, .70], color="#d6e1e7", lw=1, transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(.07, .57, objective, color=teal, fontsize=19, weight="bold")
    ax.text(.07, .49, "Recomputed Beckmann objective", color=muted, fontsize=8)
    ax.text(.07, .34, gap, color=ink, fontsize=16, weight="bold")
    ax.text(.07, .26, "Fixed-flow gap / objective", color=muted, fontsize=8)
    ax.text(.61, .34, od, color=ink, fontsize=16, weight="bold")
    ax.text(.61, .26, "Provided OD records", color=muted, fontsize=8)
    ax.text(.07, .11, f"24 nodes · 76 directed links · {iterations} saved iterations", color=muted, fontsize=7)
    ax.text(.07, .055, "Approximate result; standalone FW link vector is not published.", color=muted, fontsize=7)
    dest = OUT / "sioux_historical_fw_summary.png"
    fig.savefig(dest, dpi=100, facecolor="white", metadata={"Software": "MCL presentation"})
    plt.close(fig)
    _save_sidecar(dest, source, "Typeset exact saved FW metrics; no solver rerun or inferred link-flow map",
                  city="Sioux Falls", method="Frank–Wolfe", instance="historical 528-OD static benchmark",
                  metric_labels=["Recomputed Beckmann objective", "Fixed-flow gap / Beckmann objective", "OD records", "Saved iterations"])
    return dest.relative_to(ROOT).as_posix()


def render_compact(source: str) -> str:
    dest = ROOT / compact_path(source)
    original = ROOT / source
    if original.suffix.lower() == ".svg":
        # These two checked-in SVG raster proxies were generated from the
        # exact public SVG bytes with the task-local Sharp helper.
        raster = OUT / "svg_rasters" / (hashlib.sha256(source.encode()).hexdigest()[:16] + ".png")
        side = raster.with_suffix(".source.json")
        if not raster.is_file() or not side.is_file():
            raise FileNotFoundError(f"Missing checked-in SVG raster for {source}")
        if json.loads(side.read_text(encoding="utf-8"))["source_sha256"] != sha(original):
            raise AssertionError(f"SVG raster source changed: {source}")
        read_from = raster
    else:
        read_from = original
    with Image.open(read_from) as im:
        rgba = im.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        contained = ImageOps.contain(background.convert("RGB"), (580, 340), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (600, 360), "white")
        canvas.paste(contained, ((600 - contained.width) // 2, (360 - contained.height) // 2))
        canvas.save(dest, format="PNG", optimize=True)
    _save_sidecar(dest, source, "Whole original figure uniformly contained in white 600×360 canvas")
    return dest.relative_to(ROOT).as_posix()


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ATLAS.mkdir(parents=True, exist_ok=True)
    gmns = render_sioux_gmns()
    rank50 = render_sioux_l3_rank50()
    render_sioux_fw_summary()
    matrix_path = R2_OUT / "ROW_TEMPLATE_MATRIX.csv"
    with matrix_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 57
    replacement = None
    for row in rows:
        if row["row_id"] == "02" and row["city"] == "Sioux Falls":
            original = row.copy()
            row["preview_path"] = gmns
            row["preview_hash"] = sha(ROOT / gmns)
            row["notes"] = "Directed link IDs and one supplied OD pair; schematic, no city zone hierarchy"
            if row != original:
                replacement = row
    if replacement is not None:
        # The matrix also carries later accepted HK and LP reuse records. Rewrite
        # only this renderer's Sioux mapping; preserve every other row verbatim.
        lines = matrix_path.read_bytes().splitlines(keepends=True)
        if len(lines) != 58:
            raise AssertionError("Expected 57 matrix records plus header")
        header = next(csv.reader([lines[0].decode("utf-8")]))
        city_index = header.index("city")
        matched = 0
        for index, raw in enumerate(lines[1:], start=1):
            values = next(csv.reader([raw.decode("utf-8")]))
            if values[0] != "02" or values[city_index] != "Sioux Falls":
                continue
            newline = "\r\n" if raw.endswith(b"\r\n") else "\n"
            out = io.StringIO(newline="")
            csv.DictWriter(out, fieldnames=header, lineterminator=newline).writerow(replacement)
            lines[index] = out.getvalue().encode("utf-8")
            matched += 1
        if matched != 1:
            raise AssertionError("Sioux GMNS mapping must occur exactly once")
        matrix_path.write_bytes(b"".join(lines))
    from visuals.compose_homepage_r2 import EXTRAS
    paths = {item[3] for item in EXTRAS}
    paths.add(rank50)
    paths.add("docs/assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_flow.png")
    for source in sorted(paths): render_compact(source)
    print(f"R3 presentation derivatives: Sioux GMNS/L3 and {len(paths)} compact atlas previews")


if __name__ == "__main__": render()
