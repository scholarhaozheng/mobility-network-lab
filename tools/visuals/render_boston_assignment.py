#!/usr/bin/env python3
"""Render the frozen Boston ABS_PLANNED assignment records, without solving.

The source root is the public Boston assignment data directory. Its layout is
documented in examples/boston/assignment_methods_r1/README.md. Rendering never
imports or invokes the FW, path-pool, or native optimization implementations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


FILES = {
    "geometry": "inputs_snapshot/link.csv",
    "fw": "reference/fw_solution.csv",
    "full": "reference/link_flow.csv",
    "rank26": "runs/rank26/outer_02_link_flows.csv",
    "rank52": "runs/rank52/outer_02_link_flows.csv",
}
EXPECTED = {
    "geometry": "a5a7bbf9e18ceadacbe29335e572d2ccbfa919b46960845efc3d79d876007479",
    "fw": "c284b9018aacb1ecceb793670682474087da099d8fa7d8fd9b4b0008c87ae4a2",
    "full": "edf3bc7136c8564b72a15158f503ebca860c1ef9464ecb129b6f4dbe8ee8e19a",
    "rank26": "f53b7c80c6d2443be76df326c416e6d5d3959a456c58d82226e6d21e22b25ab6",
    "rank52": "dddff8b55cf36f8a8b50c6b9b632a2c6d2ac47a248e6d8b2ce740040bc664a31",
}
STEMS = (
    "boston_abs_planned_fw_flow",
    "boston_abs_planned_l3_rank26_flow",
    "boston_abs_planned_l3_rank52_flow",
    "boston_abs_planned_l3_rank26_minus_fw",
    "boston_abs_planned_l3_rank52_minus_fw",
)
FIELDS = (
    "link_id", "from_node_id", "to_node_id", "source_link_id", "geometry",
    "is_physical", "is_centroid_connector", "fw_volume", "full_path_volume",
    "rank26_v_from_paths", "rank52_v_from_paths", "rank26_minus_fw",
    "rank52_minus_fw", "full_path_minus_fw",
)
SOURCE_ARCHIVE_SHA256 = "c2a7f64115659aa9c338f48c64aa17e7b3b084ebd4f1175dbbf29f9fc0075112"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_index(path: Path, kind: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    result = {row["link_id"]: row for row in rows}
    if len(result) != len(rows) or len(rows) != 5091:
        raise ValueError(f"{kind}: expected 5091 unique physical link_id rows")
    return result


def finite(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not math.isfinite(value):
        raise ValueError(f"nonfinite {field} for link {row['link_id']}")
    return value


def build_table(source_root: Path, output: Path) -> tuple[list[dict], dict]:
    paths = {key: source_root / relative for key, relative in FILES.items()}
    hashes = {key: digest(path) for key, path in paths.items()}
    for key, expected in EXPECTED.items():
        if hashes[key] != expected:
            raise ValueError(f"{key}: saved source SHA-256 differs; refusing to render")
    tables = {key: read_index(path, key) for key, path in paths.items()}
    ids = set(tables["geometry"])
    if any(set(t) != ids for t in tables.values()):
        raise ValueError("missing or extra physical link_id in joined source")

    from shapely import wkt

    result: list[dict] = []
    for link_id in sorted(ids, key=int):
        geo = tables["geometry"][link_id]
        if geo["is_physical"].lower() != "true" or geo["is_centroid_connector"].lower() != "false":
            raise ValueError(f"nonphysical link in plotting set: {link_id}")
        line = wkt.loads(geo["geometry"])
        if line.geom_type != "LineString" or line.is_empty or not line.is_valid:
            raise ValueError(f"invalid LineString: {link_id}")
        for key in ("rank26", "rank52"):
            if (tables[key][link_id]["from_node_id"], tables[key][link_id]["to_node_id"]) != (geo["from_node_id"], geo["to_node_id"]):
                raise ValueError(f"{key} endpoint mismatch: {link_id}")
        fw = finite(tables["fw"][link_id], "volume")
        full = finite(tables["full"][link_id], "volume")
        r26 = finite(tables["rank26"][link_id], "v_from_paths")
        r52 = finite(tables["rank52"][link_id], "v_from_paths")
        if min(fw, full, r26, r52) < -1e-10:
            raise ValueError(f"negative plotted link flow: {link_id}")
        result.append(dict(link_id=link_id, from_node_id=geo["from_node_id"],
                           to_node_id=geo["to_node_id"], source_link_id=geo["source_link_id"],
                           geometry=geo["geometry"], is_physical=geo["is_physical"],
                           is_centroid_connector=geo["is_centroid_connector"],
                           fw_volume=fw, full_path_volume=full,
                           rank26_v_from_paths=r26, rank52_v_from_paths=r52,
                           rank26_minus_fw=r26-fw, rank52_minus_fw=r52-fw,
                           full_path_minus_fw=full-fw))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(result)
    statistics = {
        "matched_physical_links": len(result),
        "max_abs_full_minus_fw": max(abs(r["full_path_minus_fw"]) for r in result),
        "max_abs_rank26_minus_fw": max(abs(r["rank26_minus_fw"]) for r in result),
        "max_abs_rank52_minus_fw": max(abs(r["rank52_minus_fw"]) for r in result),
        "sum_abs_rank26_minus_fw": sum(abs(r["rank26_minus_fw"]) for r in result),
        "sum_abs_rank52_minus_fw": sum(abs(r["rank52_minus_fw"]) for r in result),
    }
    return result, {"source_hashes": hashes, "table_sha256": digest(output), "statistics": statistics}


def read_table(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 5091 or len({r["link_id"] for r in rows}) != len(rows):
        raise ValueError("plotting table must contain exactly 5091 unique links")
    return rows


def render(rows: list[dict], output_dir: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import colors
    from matplotlib.collections import LineCollection
    from matplotlib.cm import ScalarMappable
    from shapely import wkt

    lon0, lat0 = -71.08, 42.35
    scale_x = 111.320 * math.cos(math.radians(lat0))
    scale_y = 110.574
    segments = []
    for row in rows:
        line = wkt.loads(row["geometry"])
        xy = [((x-lon0)*scale_x, (y-lat0)*scale_y) for x, y in line.coords]
        if len(xy) < 2:
            raise ValueError("degenerate geometry")
        # Constant right-of-travel cartographic offset; not used for measurement.
        dx = xy[-1][0]-xy[0][0]
        dy = xy[-1][1]-xy[0][1]
        length = math.hypot(dx, dy)
        if length == 0:
            raise ValueError("zero-length physical LineString")
        offset = (0.003*dy/length, -0.003*dx/length)
        segments.append((xy, [(x+offset[0], y+offset[1]) for x, y in xy]))
    all_xy = [point for center, _ in segments for point in center]
    xs, ys = zip(*all_xy)
    extent = [min(xs)-0.4, max(xs)+0.4, min(ys)-0.4, max(ys)+0.4]
    absolute_fields = ("fw_volume", "rank26_v_from_paths", "rank52_v_from_paths")
    diff_fields = ("rank26_minus_fw", "rank52_minus_fw")
    max_flow = max(float(row[field]) for row in rows for field in absolute_fields)
    max_diff = max(abs(float(row[field])) for row in rows for field in diff_fields)
    if max_flow <= 0 or max_diff <= 0:
        raise ValueError("expected saved flow and signed differences")
    settings = (
        (STEMS[0], "Boston | Frank–Wolfe assignment | ABS_PLANNED", absolute_fields[0], False),
        (STEMS[1], "Boston | Native Diagnostic L3 | rank 26", absolute_fields[1], False),
        (STEMS[2], "Boston | Native Diagnostic L3 | rank 52", absolute_fields[2], False),
        (STEMS[3], "Boston | L3 rank 26 minus FW | saved link-flow difference", diff_fields[0], True),
        (STEMS[4], "Boston | L3 rank 52 minus FW | saved link-flow difference", diff_fields[1], True),
    )
    images = {}
    hidden_by_figure = {}
    for stem, title, field, signed in settings:
        fig, ax = plt.subplots(figsize=(11.5, 7.8), dpi=160)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f7fafb")
        ax.add_collection(LineCollection([pair[0] for pair in segments], colors="#d7e2e6", linewidths=0.48, zorder=1))
        values = [float(row[field]) for row in rows]
        if signed:
            keep = [i for i, v in enumerate(values) if abs(v) > 1e-12]
            norm = colors.TwoSlopeNorm(vmin=-max_diff, vcenter=0, vmax=max_diff)
            cmap = plt.get_cmap("coolwarm")
            widths = [0.45 + 2.0*math.sqrt(abs(values[i])/max_diff) for i in keep]
            label = "L3 − FW · modeled vehicle trips"
        else:
            keep = [i for i, v in enumerate(values) if v > 1e-6]
            norm = colors.PowerNorm(gamma=0.5, vmin=0, vmax=max_flow)
            cmap = plt.get_cmap("viridis")
            widths = [0.5 + 2.5*math.sqrt(values[i]/max_flow) for i in keep]
            label = "Physical-link flow · modeled vehicle trips"
        hidden_by_figure[stem] = len(values) - len(keep)
        ax.add_collection(LineCollection([segments[i][1] for i in keep],
                                         colors=[cmap(norm(values[i])) for i in keep],
                                         linewidths=widths, alpha=0.92, zorder=2))
        ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("East–west distance from −71.08° (km)")
        ax.set_ylabel("North–south distance from 42.35° (km)")
        ax.set_title(title, loc="left", fontsize=17, color="#102c3e", pad=17)
        fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.035,
                     pad=0.025, label=label)
        note = ("26 OD · 203.6604786350987 modeled vehicle trips · 5,091 physical directed links\n"
                "GMNS Plus 21_Boston (Apache-2.0); MCL saved ABS_PLANNED results · gamma=0 for L3\n"
                "3 m right-of-travel display offset; gray = all roads; display cutoffs in manifest; all rows in CSV")
        fig.text(0.10, 0.015, note, fontsize=8.5, color="#536b78", va="bottom")
        fig.subplots_adjust(left=0.10, right=0.9, top=0.89, bottom=0.14)
        output_dir.mkdir(parents=True, exist_ok=True)
        for suffix in ("png", "svg"):
            destination = output_dir / f"{stem}.{suffix}"
            fig.savefig(destination, dpi=160, facecolor="white")
            images[destination.name] = digest(destination)
        plt.close(fig)
    return {"image_hashes": images, "plot_extent_km": extent,
            "plot_projection": "Local equirectangular kilometers from EPSG:4326 lon0=-71.08 lat0=42.35",
            "direction_handling": "3-meter right-of-travel offset for colored flows only; original WKT unchanged",
            "absolute_normalization": {"kind": "shared PowerNorm", "gamma": 0.5, "min": 0, "max": max_flow},
            "signed_normalization": {"kind": "shared zero-centered TwoSlopeNorm", "min": -max_diff, "max": max_diff},
            "display_cutoffs": {"absolute": "flow > 1e-6", "signed": "abs(difference) > 1e-12"},
            "background_and_hidden": "all 5091 physical links remain as gray geometry and in full-precision CSV",
            "hidden_colored_row_counts": hidden_by_figure}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="public frozen Boston assignment data directory")
    parser.add_argument("--table", type=Path, help="existing published plotting CSV, for no-source re-render")
    parser.add_argument("--output", type=Path, required=True, help="new figure output directory")
    args = parser.parse_args()
    if bool(args.source_root) == bool(args.table):
        parser.error("choose exactly one of --source-root or --table")
    output = args.output.resolve()
    if args.source_root:
        table = output / "boston_abs_planned_assignment_links.csv"
        rows, provenance = build_table(args.source_root.resolve(), table)
    else:
        table = args.table.resolve()
        rows = read_table(table)
        provenance = {"table_sha256": digest(table), "statistics": {}}
    display = render(rows, output)
    manifest = {"instance": "Boston ABS_PLANNED 26-OD static Beckmann panel",
                "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
                "archive_member_prefix": "PUBLIC_SUCCESS_CANDIDATE/",
                "source_members": FILES, "flow_columns": {"FW": "volume", "full_path": "volume",
                                                     "rank26": "v_from_paths", "rank52": "v_from_paths"},
                "selected_runs": {"FW": "ABS_PLANNED", "rank26": "outer_02",
                                  "rank52": "outer_02"},
                "input_crs": "EPSG:4326", "units": "modeled vehicle trips in frozen panel",
                "plotting_table": table.name, **provenance, **display,
                "attribution": "GMNS Plus 21_Boston, Apache-2.0; Mobility Computation Lab saved method results",
                "limitations": "Saved model outputs, not GPS counts, traffic observations or new solves."}
    (output / "BOSTON_ASSIGNMENT_FIGURE_SOURCES.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"links": len(rows), "statistics": provenance["statistics"],
                      "output": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
