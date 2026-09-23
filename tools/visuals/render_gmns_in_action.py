"""Render two real-data Boston GMNS explanatory figures from published CSVs.

Example, from the repository root:
  python -B tools/visuals/render_gmns_in_action.py \
    --exchange examples/boston/gmns_exchange_r1/data \
    --gps-dir examples/boston/gmns_exchange_r1/figure_sample \
    --output docs/assets/boston/gmns_in_action_r1 \
    --zone-id 35 --segment-id mbtav:4624d3319dcfdec1:s01

No matching, optimization, download, or data mutation occurs on import or run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "mcl-gmns-in-action-r1"
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as MplPolygon
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import box
from shapely.ops import transform


NAVY = "#0b1b2b"
PANEL = "#12293b"
ROAD = "#587284"
WHITE = "#eef5f5"
MUTED = "#aec1cb"
TEAL = "#58d8c9"
AMBER = "#ffc778"
CORAL = "#ee8d83"
GRID = "#416071"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_one(items, key, value, label):
    selected = [r for r in items if r[key] == value]
    if len(selected) != 1:
        raise ValueError(f"Expected one {label} with {key}={value!r}; found {len(selected)}")
    return selected[0]


def project_point(transformer, x, y):
    return transformer.transform(float(x), float(y))


def parts(geometry):
    if geometry.geom_type == "LineString":
        yield list(geometry.coords)
    elif geometry.geom_type == "MultiLineString":
        for part in geometry.geoms:
            yield list(part.coords)


def place_text(ax, x, y, label, *, size=10, color=WHITE, weight="normal", **kwargs):
    return ax.text(x, y, label, transform=ax.transAxes, color=color, fontsize=size,
                   fontweight=weight, va="top", **kwargs)


def style_map(ax, bounds):
    ax.set_facecolor(PANEL)
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.8)


def context_roads(ax, road_geoms, bounds, *, alpha=0.48, width=0.7):
    extent = box(*bounds)
    segments = []
    for geometry in road_geoms.values():
        if geometry.intersects(extent):
            segments.extend(parts(geometry))
    ax.add_collection(LineCollection(segments, colors=ROAD, linewidths=width, alpha=alpha, zorder=1))


def line(ax, geometry, color, width=2.6, alpha=1.0, linestyle="-", zorder=5):
    for segment in parts(geometry):
        xs, ys = zip(*segment)
        ax.plot(xs, ys, color=color, linewidth=width, alpha=alpha,
                linestyle=linestyle, solid_capstyle="round", zorder=zorder)


def scale_bar(ax, bounds, meters=250, x_fraction=0.05, y_fraction=0.07):
    x = bounds[0] + x_fraction * (bounds[2] - bounds[0])
    y = bounds[1] + y_fraction * (bounds[3] - bounds[1])
    ax.plot([x, x + meters], [y, y], color=WHITE, linewidth=2.3, zorder=12)
    ax.text(x + meters / 2, y + 0.018 * (bounds[3] - bounds[1]), f"{meters} m",
            color=WHITE, fontsize=8, ha="center", va="bottom", zorder=12,
            bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.8, pad=2))


def bounds_for(geometries, pad=0.14, min_span=160):
    xmin = min(g.bounds[0] for g in geometries)
    ymin = min(g.bounds[1] for g in geometries)
    xmax = max(g.bounds[2] for g in geometries)
    ymax = max(g.bounds[3] for g in geometries)
    span_x = max(xmax - xmin, min_span)
    span_y = max(ymax - ymin, min_span)
    mid_x, mid_y = (xmin + xmax) / 2, (ymin + ymax) / 2
    return (mid_x - span_x * (0.5 + pad), mid_y - span_y * (0.5 + pad),
            mid_x + span_x * (0.5 + pad), mid_y + span_y * (0.5 + pad))


def save(fig, output: Path, stem: str, dpi: int):
    fig.savefig(output / f"{stem}.png", dpi=dpi, facecolor=NAVY)
    fig.savefig(output / f"{stem}.svg", facecolor=NAVY,
                metadata={"Creator": "Mobility Computation Lab", "Date": "2026-09-23"})
    plt.close(fig)


def connected_layers(output, zone, dest, dest_centroid, parent, cross, dest_cross, centroid, access, connector,
                     incident_row, incident_geom, demand, roads, transformer, gps_path, gps_result, dpi):
    src_geom = transform(transformer.transform, wkt.loads(zone["boundary"]))
    dst_geom = transform(transformer.transform, wkt.loads(dest["boundary"]))
    src_xy = project_point(transformer, centroid["x_coord"], centroid["y_coord"])
    dst_xy = project_point(transformer, dest_centroid["x_coord"], dest_centroid["y_coord"])
    access_xy = project_point(transformer, access["x_coord"], access["y_coord"])
    main_bounds = bounds_for([src_geom, dst_geom], pad=0.15)

    fig = plt.figure(figsize=(11.5, 7.0), facecolor=NAVY)
    fig.text(0.045, 0.947, "ONE GMNS NETWORK  /  CONNECTED DATA LAYERS", color=TEAL,
             fontsize=12, fontweight="bold")
    fig.text(0.045, 0.899, "Separate objects retain their identities", color=WHITE,
             fontsize=21, fontweight="bold")
    map_ax = fig.add_axes([0.045, 0.18, 0.575, 0.665])
    style_map(map_ax, main_bounds)
    context_roads(map_ax, roads, main_bounds, alpha=0.43, width=0.75)
    for geometry, color in ((src_geom, TEAL), (dst_geom, AMBER)):
        map_ax.add_patch(MplPolygon(list(geometry.exterior.coords), closed=True,
                                    facecolor=color, edgecolor=color, alpha=0.20,
                                    linewidth=2.2, zorder=3))
        xs, ys = geometry.exterior.xy
        map_ax.plot(xs, ys, color=color, linewidth=2.2, zorder=4)
    map_ax.scatter([src_xy[0]], [src_xy[1]], s=82, facecolors=NAVY, edgecolors=TEAL,
                   linewidths=2.1, zorder=8)
    map_ax.scatter([dst_xy[0]], [dst_xy[1]], s=82, facecolors=NAVY, edgecolors=AMBER,
                   linewidths=2.1, zorder=8)
    map_ax.annotate("", xy=dst_xy, xytext=src_xy,
                    arrowprops=dict(arrowstyle="-|>", color=AMBER, linewidth=1.7,
                                    linestyle=(0, (3, 4)), shrinkA=14, shrinkB=14), zorder=6)
    map_ax.text(src_xy[0], src_xy[1] + 95, f"Origin zone {zone['zone_id']}", color=TEAL,
                fontsize=10, ha="center", fontweight="bold", zorder=10)
    map_ax.text(dst_xy[0], dst_xy[1] - 95, f"Destination {dest['zone_id']}", color=AMBER,
                fontsize=10, ha="center", fontweight="bold", zorder=10)
    map_ax.text(0.03, 0.96, "REAL BOSTON ROAD GEOMETRY  ·  EPSG:32619", transform=map_ax.transAxes,
                color=WHITE, fontsize=9, va="top", fontweight="bold",
                bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.9, pad=5))
    map_ax.text(0.50, 0.05, "Dotted arrow = OD relation, not an assigned route",
                transform=map_ax.transAxes, color=AMBER, fontsize=8, ha="center",
                bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.9, pad=4))
    scale_bar(map_ax, main_bounds, 250, x_fraction=0.67, y_fraction=0.86)

    # A true projected close-up makes the 24.97 m nonphysical access leg visible.
    zoom = fig.add_axes([0.062, 0.227, 0.226, 0.255])
    midx, midy = (src_xy[0] + access_xy[0]) / 2, (src_xy[1] + access_xy[1]) / 2
    zoom_bounds = (midx - 105, midy - 105, midx + 105, midy + 105)
    style_map(zoom, zoom_bounds)
    context_roads(zoom, roads, zoom_bounds, alpha=0.65, width=1.0)
    line(zoom, incident_geom, TEAL, width=3.2, zorder=7)
    if incident_geom.geom_type == "LineString":
        arrow_start = incident_geom.interpolate(0.32, normalized=True)
        arrow_end = incident_geom.interpolate(0.72, normalized=True)
        zoom.annotate("", xy=(arrow_end.x, arrow_end.y), xytext=(arrow_start.x, arrow_start.y),
                      arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=1.7), zorder=9)
    zoom.plot([src_xy[0], access_xy[0]], [src_xy[1], access_xy[1]], color=CORAL,
              linewidth=2.6, linestyle="--", zorder=8)
    zoom.scatter([src_xy[0]], [src_xy[1]], s=70, facecolor=TEAL, edgecolor=NAVY, zorder=10)
    zoom.scatter([access_xy[0]], [access_xy[1]], s=75, marker="s", facecolor=CORAL,
                 edgecolor=NAVY, zorder=10)
    zoom.text(0.04, 0.96, "ACCESS DETAIL  ·  210 m window", transform=zoom.transAxes,
              fontsize=8, fontweight="bold", color=WHITE, va="top",
              bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.85, pad=3))
    zoom.text(0.04, 0.06, "● centroid   ■ road node\n- - model connector (not road)",
              transform=zoom.transAxes, fontsize=7.5, color=WHITE,
              bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.88, pad=3))

    card = fig.add_axes([0.65, 0.18, 0.31, 0.665])
    card.set_facecolor(PANEL)
    card.set_xticks([]); card.set_yticks([])
    for spine in card.spines.values(): spine.set_color(GRID)
    place_text(card, 0.06, 0.965, "CORE  /  zone · node · directed link", size=11, color=TEAL, weight="bold")
    place_text(card, 0.06, 0.90, f"zone.csv   {zone['zone_id']}  →  parent {parent['zone_id']}", size=10)
    place_text(card, 0.06, 0.855, "Full H3 zone boundary shown at left;", size=9, color=MUTED)
    place_text(card, 0.06, 0.82, "super_zone is a logical hierarchy key.", size=9, color=MUTED)
    place_text(card, 0.06, 0.765, f"link.csv   {incident_row['link_id']}  ·  physical, directed", size=10)
    card.plot([0.06, .94], [.725, .725], transform=card.transAxes, color=GRID, lw=1)
    place_text(card, 0.06, 0.69, "GMNS PLUS PROFILE  /  centroid · demand", size=11, color=AMBER, weight="bold")
    place_text(card, 0.06, 0.625, f"node.csv   centroid {centroid['node_id']}", size=10)
    place_text(card, 0.06, 0.58, f"link.csv   {connector['link_id']} → access {access['node_id']}", size=10)
    place_text(card, 0.06, 0.535, "Dashed access arc is nonphysical.", size=9, color=CORAL)
    place_text(card, 0.06, 0.485,
               f"S1 demand {demand['o_zone_id']} → {demand['d_zone_id']}  ·  {float(demand['volume']):.3f} vehicle trips", size=9)
    place_text(card, 0.06, 0.445,
               f"physical access OD {cross['source_physical_access_node_id']} → {dest_cross['source_physical_access_node_id']}",
               size=9, color=MUTED)
    card.plot([0.06, .94], [.405, .405], transform=card.transAxes, color=GRID, lw=1)
    place_text(card, 0.06, 0.373, "MCL CROSSWALK & SAVED EVIDENCE", size=11, color=CORAL, weight="bold")
    place_text(card, 0.06, 0.315, f"H3 r9 {cross['original_h3_zone_id'].split(':')[-1]}", size=9)
    place_text(card, 0.06, 0.275, f"→ source road node {cross['source_physical_access_node_id']}", size=9)
    place_text(card, 0.06, 0.220, "Separate GPS branch (not that OD):", size=9, color=MUTED)
    place_text(card, 0.06, 0.178, f"path occurrence {gps_path['path_occurrence']} → link {gps_path['link_id']}", size=9)
    place_text(card, 0.06, 0.138, f"→ S1 result {float(gps_result['s1_volume']):.3f} vehicle trips", size=9)
    place_text(card, 0.06, 0.063, "177 zones → 139 distinct access nodes", size=9, color=TEAL, weight="bold")

    fig.text(0.045, 0.103, "Separate objects, explicit relationships. Model access connectors are not physical roads.\n"
             "Shared link references do not imply a shared observed trip.", color=WHITE, fontsize=10)
    fig.text(0.045, 0.028, "Roads: GMNS Plus 21_Boston (Apache-2.0); H3 zones and exchange: MCL. "
             "Original geographic WGS84 → projected UTM 19N for display.", color=MUTED, fontsize=8)
    save(fig, output, "gmns_connected_layers", dpi)


def gps_evidence(output, points, paths, quality, roads, result, physical, transformer, dpi):
    raw = [project_point(transformer, p["original_lon"], p["original_lat"]) for p in points]
    projected = [project_point(transformer, p["projected_lon"], p["projected_lat"]) for p in points]
    path_geoms = [roads[p["link_id"]] for p in paths]
    from shapely.geometry import Point
    map_bounds = bounds_for(path_geoms + [Point(xy) for xy in raw + projected], pad=0.12)

    fig = plt.figure(figsize=(11.5, 6.7), facecolor=NAVY)
    fig.text(0.035, 0.94, "GPS COORDINATES  /  GMNS-LINKED EVIDENCE", color=TEAL,
             fontsize=12, fontweight="bold")
    fig.text(0.035, 0.888, "The observations stay put. Their references change.", color=WHITE,
             fontsize=20, fontweight="bold")
    panel_specs = [([0.035, 0.21, 0.294, 0.61], "A   BEFORE  /  saved source positions"),
                   ([0.352, 0.21, 0.294, 0.61], "B   AFTER  /  saved path association")]
    for index, (spec, label) in enumerate(panel_specs):
        ax = fig.add_axes(spec)
        style_map(ax, map_bounds)
        context_roads(ax, roads, map_bounds, alpha=0.47, width=0.75)
        if index == 1:
            for geom in path_geoms:
                line(ax, geom, TEAL, width=2.8, zorder=4)
            if path_geoms[0].geom_type == "LineString":
                first_geom = path_geoms[0]
                reverse = physical["dir_flag"] == "-1"
                a = first_geom.interpolate(0.70 if reverse else 0.30, normalized=True)
                b = first_geom.interpolate(0.45 if reverse else 0.55, normalized=True)
                ax.annotate("", xy=(b.x, b.y), xytext=(a.x, a.y),
                            arrowprops=dict(arrowstyle="-|>", color=WHITE, lw=1.8), zorder=8)
            for r, p in zip(raw, projected):
                ax.plot([r[0], p[0]], [r[1], p[1]], color=CORAL, lw=1.2, alpha=0.9, zorder=7)
            ax.scatter([p[0] for p in projected], [p[1] for p in projected], s=31,
                       facecolors=TEAL, edgecolors=NAVY, linewidths=0.9, zorder=9)
        ax.scatter([p[0] for p in raw], [p[1] for p in raw], s=42,
                   facecolors=AMBER if index == 0 else NAVY,
                   edgecolors=NAVY if index == 0 else AMBER, linewidths=1.4, zorder=10)
        ax.text(0.03, 0.96, label, transform=ax.transAxes, color=WHITE, fontsize=9,
                fontweight="bold", va="top",
                bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.9, pad=4))
        ax.text(raw[0][0], raw[0][1] + 85, "#1", color=AMBER, fontsize=9,
                fontweight="bold", ha="center", zorder=11)
        ax.text(raw[-1][0], raw[-1][1] - 75, "#12", color=AMBER, fontsize=9,
                fontweight="bold", ha="center", zorder=11)
        scale_bar(ax, map_bounds, 250)
        # Paired close-ups use the same 140 m UTM bounds on both panels.
        inset = fig.add_axes([spec[0] + 0.172, spec[1] + 0.017, 0.112, 0.176])
        px, py = raw[0]
        detail_bounds = (px - 70, py - 70, px + 70, py + 70)
        style_map(inset, detail_bounds)
        context_roads(inset, roads, detail_bounds, alpha=0.65, width=1.1)
        if index == 1:
            line(inset, path_geoms[0], TEAL, width=2.5)
            inset.plot([raw[0][0], projected[0][0]], [raw[0][1], projected[0][1]],
                       color=CORAL, lw=1.6, zorder=8)
            inset.scatter([projected[0][0]], [projected[0][1]], s=44, c=TEAL, zorder=10)
        inset.scatter([raw[0][0]], [raw[0][1]], s=48, facecolors=AMBER if index == 0 else NAVY,
                      edgecolors=NAVY if index == 0 else AMBER, linewidths=1.3, zorder=11)
        inset.text(0.05, 0.95, "#1  ·  140 m close-up", transform=inset.transAxes,
                   color=WHITE, fontsize=7, va="top",
                   bbox=dict(facecolor=NAVY, edgecolor="none", alpha=0.9, pad=2))

    card = fig.add_axes([0.673, 0.21, 0.29, 0.61])
    card.set_facecolor(PANEL)
    card.set_xticks([]); card.set_yticks([])
    for spine in card.spines.values(): spine.set_color(GRID)
    place_text(card, 0.06, 0.96, "C   WHAT CAN NOW BE QUERIED", size=11, color=TEAL, weight="bold")
    place_text(card, 0.06, 0.88, f"Saved segment  ·  route {quality['route_id']}", size=10)
    place_text(card, 0.06, 0.835, f"{len(points)} source positions  ·  {len(paths)} path occurrences", size=9, color=MUTED)
    place_text(card, 0.06, 0.79, "qualified; window start/end censored", size=9, color=MUTED)
    card.plot([0.06, .94], [.74, .74], transform=card.transAxes, color=GRID, lw=1)
    place_text(card, 0.06, 0.705, "OBSERVATION  →  PATH OCCURRENCE", size=10, color=AMBER, weight="bold")
    place_text(card, 0.06, 0.65, f"point #1  ·  {points[0]['timestamp'][11:19]} local", size=9)
    place_text(card, 0.06, 0.607, f"path_order {paths[0]['path_order']} / occurrence {paths[0]['path_occurrence']}", size=9)
    place_text(card, 0.06, 0.563, f"saved matched link {paths[0]['link_id']}", size=9)
    place_text(card, 0.06, 0.52, "first links: " + " → ".join(p["link_id"] for p in paths[:3]), size=8.5)
    first_offset = float(points[0]["lateral_error_m"])
    place_text(card, 0.06, 0.48, f"saved #1 projection offset {first_offset:.2f} m", size=8.5, color=MUTED)
    card.plot([0.06, .94], [.445, .445], transform=card.transAxes, color=GRID, lw=1)
    place_text(card, 0.06, 0.41, "PHYSICAL LINK  →  SAVED RESULT", size=10, color=TEAL, weight="bold")
    place_text(card, 0.06, 0.358, f"link.csv  {physical['link_id']}  ·  directed road", size=9)
    place_text(card, 0.06, 0.316, f"{physical['from_node_id']} → {physical['to_node_id']}  ·  physical", size=9)
    place_text(card, 0.06, 0.265, f"S1 modeled volume  {float(result['s1_volume']):.3f}", size=9)
    place_text(card, 0.06, 0.225, "panel vehicle trips  ·  not GPS counts", size=9, color=MUTED)
    place_text(card, 0.06, 0.173, f"S1 link travel time  {float(result['s1_travel_time']):.4f} min", size=9)
    card.plot([0.06, .94], [.14, .14], transform=card.transAxes, color=GRID, lw=1)
    place_text(card, 0.06, 0.11, "Shared network reference—", size=9, color=CORAL, weight="bold")
    place_text(card, 0.06, 0.072, "not the same observed trip.", size=9, color=CORAL, weight="bold")

    fig.text(0.035, 0.155, "A and B: identical observations, UTM 19N bounds and scale. Amber = source positions; teal = saved path/projections.",
             color=WHITE, fontsize=9)
    fig.text(0.035, 0.105, "Source observations → algorithm-derived matching → GMNS road attributes → separately modeled assignment result.",
             color=WHITE, fontsize=10)
    fig.text(0.035, 0.05, "MBTA V3 JSON derived positions: MBTA/MassDOT attribution. Roads: GMNS Plus 21_Boston (Apache-2.0). "
             "No raw feed, vehicle ID, observed traffic count or re-matching.", color=MUTED, fontsize=8)
    save(fig, output, "gps_to_gmns_evidence", dpi)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exchange", type=Path, required=True, help="Public GMNS exchange data directory")
    parser.add_argument("--gps-dir", type=Path, required=True, help="Public saved derived GPS data directory")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for PNG, SVG and source manifest")
    parser.add_argument("--zone-id", required=True, help="Exported fine-zone ID for the first figure")
    parser.add_argument("--segment-id", required=True, help="Quality-eligible saved segment ID for the second figure")
    parser.add_argument("--dpi", type=int, default=200, help="Raster export DPI (default: 200)")
    args = parser.parse_args(argv)
    if args.dpi < 100 or args.dpi > 300:
        parser.error("--dpi must be between 100 and 300")
    files = {name: args.exchange / name for name in ("zone.csv", "node.csv", "link.csv", "id_crosswalk.csv",
                                                   "demand_S1.csv", "assignment_result_by_scenario.csv")}
    files.update({name: args.gps_dir / name for name in ("gps_point_progress.csv", "gps_path_links.csv",
                                                         "gps_segment_quality.csv")})
    data = {name: read_csv(path) for name, path in files.items()}
    zones, nodes, links = data["zone.csv"], data["node.csv"], data["link.csv"]
    zone = require_one(zones, "zone_id", args.zone_id, "fine zone")
    parent = require_one(zones, "zone_id", zone["super_zone"], "parent")
    cross = require_one(data["id_crosswalk.csv"], "export_zone_id", args.zone_id, "crosswalk")
    centroid = require_one(nodes, "node_id", cross["centroid_node_id"], "centroid")
    access = require_one(nodes, "node_id", cross["physical_access_node_id"], "access node")
    connector = require_one([r for r in links if r["mcl_link_class"] == "nonphysical_zone_access_out"
                             and r["from_node_id"] == centroid["node_id"]], "to_node_id", access["node_id"], "connector")
    demand = sorted([r for r in data["demand_S1.csv"] if r["o_zone_id"] == args.zone_id],
                    key=lambda r: int(r["d_zone_id"]))[0]
    dest = require_one(zones, "zone_id", demand["d_zone_id"], "destination zone")
    dest_centroid = require_one(nodes, "node_id", dest["zone_id"], "destination centroid")
    dest_cross = require_one(data["id_crosswalk.csv"], "export_zone_id", dest["zone_id"], "destination crosswalk")
    incident_ids = sorted([r["link_id"] for r in links if r["from_node_id"] == access["node_id"]
                           and r["mcl_link_class"] == "physical"], key=int)
    if not incident_ids:
        raise ValueError("Selected access node lacks an outgoing physical road")
    incident = require_one(links, "link_id", incident_ids[0], "incident road")
    if incident["from_node_id"] != access["node_id"] or incident["mcl_link_class"] != "physical":
        raise ValueError("Incident road is not an outgoing physical link from the selected access node")
    quality = require_one(data["gps_segment_quality.csv"], "segment_id", args.segment_id, "segment quality")
    if quality["observation_eligible"].lower() != "true" or quality["quality_class"] != "qualified":
        raise ValueError("Selected segment is not quality-eligible and qualified")
    points = sorted([r for r in data["gps_point_progress.csv"] if r["segment_id"] == args.segment_id],
                    key=lambda r: int(r["point_seq"]))
    paths = sorted([r for r in data["gps_path_links.csv"] if r["segment_id"] == args.segment_id],
                   key=lambda r: int(r["path_order"]))
    if len(points) != int(float(quality["point_count"])) or len(paths) != int(float(quality["path_occurrences"])):
        raise ValueError("Selected saved point/path counts do not match quality record")
    for item in points:
        if not any(item["matched_link_id"] == p["link_id"] and item["path_occurrence"] == p["path_occurrence"]
                   for p in paths):
            raise ValueError("A saved point has no matching path occurrence")
    physical = require_one(links, "link_id", paths[0]["link_id"], "path physical link")
    if physical["mcl_link_class"] != "physical" or physical["mcl_gps_match_allowed"].lower() != "true":
        raise ValueError("Path link is not a matchable physical road")
    result = require_one(data["assignment_result_by_scenario.csv"], "link_id", physical["link_id"], "saved result")
    if not any(p["matched_link_id"] == physical["link_id"] and p["path_occurrence"] == paths[0]["path_occurrence"]
               for p in points):
        raise ValueError("First path occurrence lacks a saved observation association")
    access_ids = {r["physical_access_node_id"] for r in data["id_crosswalk.csv"]}
    if len(data["id_crosswalk.csv"]) != 177 or len(access_ids) != 139:
        raise ValueError("Zone/access counts changed; revise figure labels from actual data")

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32619", always_xy=True)
    roads = {r["link_id"]: transform(transformer.transform, wkt.loads(r["geometry"]))
             for r in links if r["mcl_link_class"] == "physical" and r["geometry"]}
    if any(p["link_id"] not in roads for p in paths):
        raise ValueError("Selected saved path references a missing physical geometry")
    args.output.mkdir(parents=True, exist_ok=True)
    connected_layers(args.output, zone, dest, dest_centroid, parent, cross, dest_cross, centroid, access, connector,
                     incident, roads[incident["link_id"]], demand, roads, transformer, paths[0], result, args.dpi)
    gps_evidence(args.output, points, paths, quality, roads, result, physical, transformer, args.dpi)
    repo = Path(__file__).resolve().parents[2]
    sources = {path.resolve().relative_to(repo).as_posix(): sha(path) for path in files.values()}
    manifest = {
        "title": "GMNS in Action figure source identity",
        "source_paths_sha256": sources,
        "selection": {"zone_id": zone["zone_id"], "zone_h3": cross["original_h3_zone_id"],
                      "parent_zone_id": parent["zone_id"], "centroid_node_id": centroid["node_id"],
                      "outbound_connector_link_id": connector["link_id"], "access_node_id": access["node_id"],
                      "incident_physical_link_id": incident["link_id"], "S1_OD": [demand["o_zone_id"], demand["d_zone_id"]],
                      "S1_OD_source_physical_access_nodes": [cross["source_physical_access_node_id"],
                                                            dest_cross["source_physical_access_node_id"]],
                      "S1_OD_vehicle_trips": demand["volume"], "segment_id": args.segment_id,
                      "segment_route_id": quality["route_id"], "point_count": len(points), "ordered_path_occurrences": len(paths),
                      "example_path_link_id": physical["link_id"], "S1_link_volume_vehicle_trips": result["s1_volume"],
                      "S1_link_travel_time_minutes": result["s1_travel_time"]},
        "display": {"source_crs": "EPSG:4326", "map_crs": "EPSG:32619", "transformation": "pyproj always_xy",
                    "gps_A_B_same_bounds_and_scale": True, "gps_A_B_same_source_points": True,
                    "zoom_A_B_same_140m_bounds": True,
                    "zone_connector": "Nonphysical modeled access; dashed true projected node-to-node line",
                    "zone_OD_arrow": "Straight diagrammatic OD relation, not an assigned road path",
                    "gps_projection": "Saved derived position; not recomputed by this renderer"},
        "scope": "Figure 1 zone/OD and Figure 2 GPS segment are separate examples. Link S1 volumes are modeled panel results, not GPS observations.",
        "rights": "GMNS Plus 21_Boston road geometry: Apache-2.0; MBTA V3 derived positions: MBTA/MassDOT attribution; H3/figure composition: MCL.",
    }
    sample_record = args.gps_dir / "SOURCE_RECORD.json"
    if sample_record.is_file():
        manifest["gps_sample_source_record"] = json.loads(sample_record.read_text(encoding="utf-8"))
    (args.output / "FIGURE_SOURCES.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": [str(args.output / (stem + ext)) for stem in
                                 ("gmns_connected_layers", "gps_to_gmns_evidence") for ext in (".png", ".svg")],
                      "zone_id": args.zone_id, "segment_id": args.segment_id}, indent=2))


if __name__ == "__main__":
    main()
