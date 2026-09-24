#!/usr/bin/env python3
"""Render a saved, source-grounded Boston block-group/H3 cutout; no model run."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely import wkt
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon
from matplotlib.collections import PatchCollection

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "examples/boston/population_r1/data"
OUT = ROOT / "docs/assets/boston/population_r1"
SOURCE = "15000US250250101031"
ZONE = "h3r9:892a30644a3ffff"
RECORDED_SUFFOLK_GEOMETRY_SHA256 = "c25bbd2167163cf2ccaf15470edc9ccc2684da86404cb2abff1e38359faa4d1c"


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def polygon_parts(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    return [g for g in geometry.geoms if g.geom_type == "Polygon"]


def patches(geometry):
    return [PatchPolygon(list(g.exterior.coords), closed=True) for g in polygon_parts(geometry)]


def prepare_cutout(source_path, target_path):
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if digest != RECORDED_SUFFOLK_GEOMETRY_SHA256:
        raise ValueError("source geometry is not the recorded Suffolk TIGER2024 mirror snapshot")
    # Stable, evidence-first selection: first Suffolk GEOID in the released
    # source statistics. No numerical effect is used to choose the example.
    cross = rows(DATA / "acs_block_group_h3_crosswalk.csv")
    stats = rows(DATA / "acs_block_group_stats.csv")
    selected = min(r["source_geoid"] for r in stats if r["county_file"] == "suffolk_025")
    if selected != SOURCE:
        raise ValueError(f"selected source changed: {selected}")
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    matches = [f for f in raw["features"] if f["properties"].get("geoid") == selected]
    if len(matches) != 1:
        raise ValueError("selected source geometry missing or repeated")
    zone_ids = {r["zone_id"] for r in cross if r["source_geoid"] == selected}
    zone_rows = rows(ROOT / "examples/boston/gmns_exchange_r1/data/zone.csv")
    features = [{"type": "Feature", "properties": {"kind": "source_block_group", "source_geoid": selected},
                 "geometry": matches[0]["geometry"]}]
    for r in zone_rows:
        if r["mcl_original_h3_id"] in zone_ids:
            features.append({"type": "Feature", "properties": {"kind": "clipped_model_zone", "zone_id": r["mcl_original_h3_id"]},
                             "geometry": mapping(wkt.loads(r["mcl_clipped_geometry_wkt"]))})
    if len(features) != len(zone_ids) + 1:
        raise ValueError("not every crosswalk zone has a geometry")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"selection_rule": "lexicographically first source_geoid in released Suffolk source statistics",
            "source_geoid": selected, "zone_count": len(zone_ids),
            "source_geometry_sha256": digest,
            "cutout_role": "display geometry only; saved allocation weights are not recomputed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-from", type=Path, help="Optional recorded Census Reporter TIGER2024 county GeoJSON, for rebuilding the public cutout")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cutout = OUT / "source_h3_cutout.geojson"
    provenance = None
    if args.prepare_from:
        provenance = prepare_cutout(args.prepare_from, cutout)
    record = json.loads(cutout.read_text(encoding="utf-8"))
    source = shape(next(f["geometry"] for f in record["features"] if f["properties"]["kind"] == "source_block_group"))
    zones = [(f["properties"]["zone_id"], shape(f["geometry"])) for f in record["features"] if f["properties"]["kind"] == "clipped_model_zone"]
    cross = rows(DATA / "acs_block_group_h3_crosswalk.csv")
    example = next(r for r in cross if r["source_geoid"] == SOURCE and r["zone_id"] == ZONE)
    fig = plt.figure(figsize=(15.2, 6.9), facecolor="white")
    grid = fig.add_gridspec(1, 3, width_ratios=[1, 1.15, 1.15], left=.04, right=.97, top=.82, bottom=.13, wspace=.13)
    colors = {"ink": "#142e43", "teal": "#087f8c", "mint": "#58c7b4", "soft": "#eff6f8", "line": "#a8c2cf", "amber": "#dc9e45"}
    fig.text(.04, .96, "BOSTON  /  POPULATION & HOUSEHOLD PREPARATION", fontsize=12, weight="bold", color=colors["teal"])
    fig.text(.04, .895, "A statistical block group is allocated to clipped H3 model zones", fontsize=22, weight="bold", color=colors["ink"])
    def map_panel(ax, title, subtitle):
        ax.set_facecolor(colors["soft"])
        ax.set_title(title, loc="left", fontsize=15, weight="bold", color=colors["ink"], pad=21)
        ax.text(0, 1.015, subtitle, transform=ax.transAxes, fontsize=9.5, color="#526c7c")
        x0, y0, x1, y1 = source.bounds
        dx, dy = x1-x0, y1-y0
        ax.set_xlim(x0-.12*dx, x1+.12*dx)
        ax.set_ylim(y0-.12*dy, y1+.12*dy)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_color("#d5e2e8")
    ax = fig.add_subplot(grid[0, 0]); map_panel(ax, "A  Source geography", "Recorded TIGER2024 mirror geometry")
    ax.add_collection(PatchCollection(patches(source), facecolor="#b8d9db", edgecolor=colors["teal"], linewidth=2))
    ax.text(.04, .07, "B01003 = 957 persons\nB11001 = 232 households", transform=ax.transAxes,
            fontsize=12, weight="bold", color=colors["ink"], bbox={"facecolor":"white","edgecolor":"none","pad":8})
    ax = fig.add_subplot(grid[0, 1]); map_panel(ax, "B  Area-share overlay", "Actual clipped H3 outlines; selected overlap in amber")
    ax.add_collection(PatchCollection(patches(source), facecolor="#d8ecec", edgecolor=colors["teal"], linewidth=2))
    for zid, geom in zones:
        ax.add_collection(PatchCollection(patches(geom), facecolor="none", edgecolor="#4780a2", linewidth=1.6))
        if zid == ZONE:
            overlap = source.intersection(geom)
            ax.add_collection(PatchCollection(patches(overlap), facecolor=colors["amber"], edgecolor="none", alpha=.8))
    ax.text(.04, .07, "w = overlap / FULL source area\nSelected saved w = 0.30570178", transform=ax.transAxes,
            fontsize=11.5, weight="bold", color=colors["ink"], bbox={"facecolor":"white","edgecolor":"none","pad":8})
    ax = fig.add_subplot(grid[0, 2]); ax.axis("off")
    ax.text(0, .99, "C  Saved H3 contribution", va="top", fontsize=15, weight="bold", color=colors["ink"])
    ax.text(0, .86, "One source → one target zone", fontsize=12, color="#526c7c")
    ax.text(0, .70, "957 persons × 0.30570178\n= 292.5566 allocated persons", fontsize=14, color=colors["ink"], linespacing=1.7)
    ax.text(0, .47, "232 households × 0.30570178\n= 70.9228 allocated households", fontsize=14, color=colors["ink"], linespacing=1.7)
    ax.text(0, .23, "H3 households → purpose-specific\nmodeled productions: Pᵢ,ₚ = Hᵢ × rₚ", fontsize=13, weight="bold", color=colors["teal"], linespacing=1.7)
    ax.text(0, .04, "Outside-core share stays in a spatial ledger;\nexternal trip mass is unknown, not zero.", fontsize=10.5, color="#526c7c", linespacing=1.4)
    fig.text(.04, .055, f"Selected source {SOURCE} → zone {ZONE}. Geometry is real; values are one saved contribution, not the zone total. Source: Census Bureau via Census Reporter; H3/core: MCL.", fontsize=9.5, color="#526c7c")
    fig.savefig(OUT / "population_allocation.png", dpi=170, facecolor="white")
    fig.savefig(OUT / "population_allocation.svg", facecolor="white")
    plt.close(fig)
    if provenance:
        (OUT / "FIGURE_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("Rendered source-grounded population allocation cutout")


if __name__ == "__main__":
    main()
