"""Render a small UrbanNav reference-position projection from saved matches.

This is presentation-only: it neither downloads observations nor reruns the
matcher. Private source rows are read from explicit CLI paths and never copied
to the output directory. The output is a figure and a non-coordinate sidecar.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle


POSITION_SHA256 = "34ba8d50b339c36358aa6ad62d041023856d04159081ca4e2da74b937bbbe804"
MATCH_SHA256 = "b07e01f0f1bf992a4c9ceaf09ff8cf57f4d9472e79d4487fe76e733c3e62610d"
LINK_SHA256 = "7158dfc3cc5342b59034b295636065c166f7ba92872713897ce8bc8946d77bf8"
LON = 111320 * math.cos(math.radians(22.3035))
LAT = 111320
NAVY = "#102c3e"
TEAL = "#087e83"
ORANGE = "#e7a65a"
PALE = "#c8d5d8"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def metric_line(wkt: str) -> list[tuple[float, float]]:
    if not wkt.startswith("LINESTRING (") and not wkt.startswith("LINESTRING("):
        raise ValueError("Expected public physical-link LINESTRING geometry")
    inside = wkt[wkt.index("(") + 1 : wkt.rindex(")")]
    return [(float(s.split()[0]) * LON, float(s.split()[1]) * LAT)
            for s in inside.split(",")]


def interpolate_along(line: list[tuple[float, float]], fraction: float) -> tuple[float, float]:
    segments = [math.dist(a, b) for a, b in zip(line, line[1:])]
    target = max(0.0, min(1.0, fraction)) * sum(segments)
    for index, ((a, b), length) in enumerate(zip(zip(line, line[1:]), segments)):
        if target <= length or index == len(segments) - 1:
            t = target / length if length else 0.0
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        target -= length
    return line[-1]


def longest_unbroken_window(matches: list[dict[str, str]]) -> list[dict[str, str]]:
    segments: list[list[dict[str, str]]] = []
    current: list[dict[str, str]] = []
    for item in matches:
        if item["break_before"].lower() == "true" and current:
            segments.append(current)
            current = []
        if item["matched_link_id"]:
            current.append(item)
    if current:
        segments.append(current)
    longest = max(segments, key=lambda segment: (len(segment), -int(segment[0]["point_index"])))
    if len(longest) < 12:
        raise ValueError("No saved uninterrupted 12-point segment")
    return longest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positions", required=True, type=Path)
    parser.add_argument("--saved-match", required=True, type=Path)
    parser.add_argument("--public-links", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    for path, expected in ((args.positions, POSITION_SHA256),
                           (args.saved_match, MATCH_SHA256),
                           (args.public_links, LINK_SHA256)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source SHA-256 changed: {path.name}")

    positions = {int(row["point_index"]): row for row in rows(args.positions)}
    matches = rows(args.saved_match)
    links = {row["link_id"]: row for row in rows(args.public_links)
             if row["mcl_link_class"] == "physical"}
    segment = longest_unbroken_window(matches)
    selected = [segment[round(i * (len(segment) - 1) / 11)] for i in range(12)]
    selected_indices = [int(row["point_index"]) for row in selected]
    sampled_interval = [row for row in segment if selected_indices[0] <= int(row["point_index"]) <= selected_indices[-1]]
    matched_ids = list(dict.fromkeys(row["matched_link_id"] for row in sampled_interval))
    if any(link_id not in links for link_id in matched_ids):
        raise ValueError("Saved match references an absent or nonphysical road")

    original: list[tuple[float, float]] = []
    projected: list[tuple[float, float]] = []
    errors: list[float] = []
    for row in selected:
        source = positions[int(row["point_index"])]
        point = float(source["longitude"]) * LON, float(source["latitude"]) * LAT
        link = links[row["matched_link_id"]]
        line = metric_line(link["geometry"])
        shadow = interpolate_along(line, float(row["along_link_m"]) / float(link["length"]))
        error = math.dist(point, shadow)
        if abs(error - float(row["distance_m"])) > 0.01:
            raise ValueError("Reconstructed projection disagrees with the frozen residual")
        original.append(point)
        projected.append(shadow)
        errors.append(error)

    all_points = original + projected
    minx, maxx = min(p[0] for p in all_points), max(p[0] for p in all_points)
    miny, maxy = min(p[1] for p in all_points), max(p[1] for p in all_points)
    pad = max(maxx - minx, maxy - miny) * 0.18
    bounds = minx - pad, maxx + pad, miny - pad, maxy + pad
    public_lines = []
    for link in links.values():
        line = metric_line(link["geometry"])
        if max(p[0] for p in line) < bounds[0] or min(p[0] for p in line) > bounds[1]:
            continue
        if max(p[1] for p in line) < bounds[2] or min(p[1] for p in line) > bounds[3]:
            continue
        public_lines.append(line)

    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none",
                         "svg.hashsalt": "mcl-hong-kong-reference-projection-r1"})
    fig = plt.figure(figsize=(18, 11), dpi=100, facecolor="white")
    fig.text(0.04, 0.95, "Reference Positions and Matched Road Geometry",
             fontsize=29, weight="bold", color=NAVY)
    fig.text(0.04, 0.918,
             "One saved UrbanNav TST research-vehicle segment  /  frozen Viterbi link matches; no rematching",
             fontsize=16, color="#58717d")
    ax = fig.add_axes([0.04, 0.12, 0.69, 0.76])
    ax.set_facecolor("#f5f8fa")
    ax.add_collection(LineCollection(public_lines, colors=PALE, linewidths=0.9, zorder=1))
    ax.add_collection(LineCollection([metric_line(links[link_id]["geometry"]) for link_id in matched_ids],
                                     colors=TEAL, linewidths=4.2, zorder=2))
    ax.add_collection(LineCollection(list(zip(original, projected)), colors="#d79c5f",
                                     linewidths=1.7, zorder=3))
    ax.scatter([p[0] for p in projected], [p[1] for p in projected],
               s=85, facecolors="white", edgecolors=TEAL, linewidths=2.0, zorder=5)
    ax.scatter([p[0] for p in original], [p[1] for p in original],
               s=72, facecolors=ORANGE, edgecolors=NAVY, linewidths=0.8, zorder=6)
    for name, point in (("START", original[0]), ("END", original[-1])):
        ax.annotate(name, point, xytext=(9, 11), textcoords="offset points",
                    fontsize=12, weight="bold", color=NAVY, zorder=7)
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d8e4e8")
    scale_m = 100 if maxx - minx < 800 else 250
    sx = bounds[0] + (bounds[1] - bounds[0]) * 0.05
    sy = bounds[2] + (bounds[3] - bounds[2]) * 0.07
    ax.plot([sx, sx + scale_m], [sy, sy], color=NAVY, lw=3, zorder=8)
    ax.text(sx, sy - (bounds[3] - bounds[2]) * 0.035, f"{scale_m} m", fontsize=12, color=NAVY)

    side = fig.add_axes([0.75, 0.12, 0.22, 0.76])
    side.add_patch(Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="#d8e4e8", lw=1.3))
    side.set_xlim(0, 1)
    side.set_ylim(0, 1)
    side.axis("off")
    side.text(0.08, 0.93, "Saved evidence", fontsize=22, weight="bold", color=NAVY)
    side.plot([0.10, 0.27], [0.82, 0.82], color=TEAL, lw=5)
    side.text(0.34, 0.82, "Matched road links", fontsize=15, va="center", color=NAVY)
    side.scatter([0.16], [0.71], s=140, facecolors=ORANGE, edgecolors=NAVY)
    side.text(0.34, 0.71, "Reference position", fontsize=15, va="center", color=NAVY)
    side.scatter([0.16], [0.60], s=145, facecolors="white", edgecolors=TEAL, linewidths=2)
    side.text(0.34, 0.60, "Projected point", fontsize=15, va="center", color=NAVY)
    side.plot([0.10, 0.27], [0.49, 0.49], color="#d79c5f", lw=2)
    side.text(0.34, 0.49, "Lateral offset", fontsize=15, va="center", color=NAVY)
    side.text(0.08, 0.34, "12 saved reference positions", fontsize=14, color="#58717d")
    side.text(0.08, 0.29, f"{min(errors):.1f}–{max(errors):.1f} m sampled offset", fontsize=14, color="#58717d")
    side.text(0.08, 0.22, "One research vehicle; not raw GNSS,", fontsize=13, color="#58717d")
    side.text(0.08, 0.18, "traffic demand or lane validation.", fontsize=13, color="#58717d")
    fig.text(0.04, 0.078,
             "Roads: official-derived Hong Kong GMNS pilot  |  Position source: PolyU IPNL UrbanNav-HK-Medium-Urban-1",
             fontsize=11, color="#58717d")
    fig.text(0.04, 0.055,
             "Public figure shows a saved-match excerpt only; original provider file and complete point table are not bundled.",
             fontsize=11, color="#58717d")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / "hong_kong_reference_projection"
    fig.savefig(stem.with_suffix(".png"), dpi=100, facecolor="white")
    svg_path = stem.with_suffix(".svg")
    fig.savefig(svg_path, facecolor="white", metadata={"Date": None})
    # Matplotlib wraps SVG path commands with trailing spaces; normalize the
    # generated text so Git whitespace checks and source hashes remain stable.
    svg_path.write_text("\n".join(line.rstrip() for line in
                                  svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
                        encoding="utf-8", newline="\n")
    plt.close(fig)
    sidecar = {
        "figure_type": "saved-reference-position-to-matched-road projection",
        "selected_point_count": len(selected),
        "selection_rule": "12 evenly spaced saved records from the longest uninterrupted Viterbi segment",
        "source_sha256": {"private_reference_positions": POSITION_SHA256,
                          "private_saved_viterbi_matches": MATCH_SHA256,
                          "public_gmns_links": LINK_SHA256},
        "source_attribution": "PolyU IPNL UrbanNav-HK-Medium-Urban-1 SPAN-CPT+IE reference positions",
        "provider_dataset_license_page": "https://www.polyu.edu.hk/aae/ipn-lab/us/en/resources/urbannav-dataset/",
        "provider_exact_file_listing": "https://github.com/IPNL-POLYU/UrbanNavDataset/blob/master/README.md#urbannav-hk-medium-urban-1",
        "publication_scope_record": "docs/assets/hong_kong/visual_release_r1/PUBLICATION_SCOPE.txt",
        "matching_rerun": False,
        "raw_or_point_table_bundled": False,
        "sampled_offset_m": {"minimum": round(min(errors), 3), "maximum": round(max(errors), 3)},
        "figure_sha256": {suffix: sha(stem.with_suffix(suffix)) for suffix in (".png", ".svg")},
    }
    stem.with_suffix(".source.json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "selected_point_count": len(selected),
                      "sampled_offset_m": sidecar["sampled_offset_m"],
                      "output": str(stem)}, indent=2))


if __name__ == "__main__":
    main()
