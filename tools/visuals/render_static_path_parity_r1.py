#!/usr/bin/env python3
"""Render complementary saved-result views for Section 03 rows 12 and 13.

This is a presentation-only renderer: it reads accepted link vectors and
geometries, but never invokes an assignment, path-pool, or L3 solver. Hong
Kong requires the locally retained corrected-R2 H1 result directory via
--hk-h1; neither its private arrays nor its full path pool are copied out.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator
import numpy as np
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/static_path_parity_r1"
PUBLIC = {
    "Boston": {
        "geometry": ROOT / "examples/boston/assignment_methods_r1/inputs_snapshot/link.csv",
        "finite": ROOT / "examples/boston/assignment_methods_r1/reference/link_flow.csv",
        "l3": ROOT / "examples/boston/assignment_methods_r1/runs/rank26/outer_02_link_flows.csv",
    },
    "Sioux Falls": {
        "geometry": ROOT / "examples/sioux-falls/native_l3_r1/inputs_snapshot/SiouxFalls/link.csv",
        "finite": ROOT / "examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_link_flows.csv",
        "l3": ROOT / "examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_link_flows.csv",
    },
}
SLUG = {"Boston": "boston", "Sioux Falls": "sioux_falls", "Hong Kong": "hong_kong"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "svg.fonttype": "none", "svg.hashsalt": "mcl-static-path-parity-r1",
                     "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.facecolor": "white"})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_source_label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        # Publish the accepted H1 record role, never a private absolute path.
        return "accepted_corrected_R2_H1/" + "/".join(path.parts[-2:])


def save(fig, stem: str, source_files: list[Path], scope: str, notes: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(OUT / f"{stem}.{extension}", dpi=180, bbox_inches="tight",
                    metadata=({"Software": "MCL saved-result parity renderer"}
                              if extension == "png" else {"Date": None}))
    plt.close(fig)
    record = {
        "figure": stem, "scope": scope, "notes": notes,
        "renderer": "tools/visuals/render_static_path_parity_r1.py",
        "source_hashes": {public_source_label(p): digest(p) for p in source_files},
        "output_sha256": {ext: digest(OUT / f"{stem}.{ext}") for ext in ("png", "svg")},
        "image_integrity": "No cropped plot area; no scientific model rerun; original figures retained.",
    }
    (OUT / f"{stem}.source.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def linework(city: str, source: Path):
    rows = read_csv(source)
    if city == "Sioux Falls":
        # Schematic layout only: the supplied benchmark has link topology,
        # not georeferenced city-street geometry.
        import networkx as nx
        graph = nx.Graph()
        for row in rows:
            graph.add_edge(row["from_node_id"], row["to_node_id"])
        pos = nx.spring_layout(graph, seed=24, iterations=140)
        return [(row["link_id"], [pos[row["from_node_id"]], pos[row["to_node_id"]]])
                for row in rows]
    segments = []
    for row in rows:
        if city == "Hong Kong" and row.get("mcl_link_class") != "physical":
            continue
        if city == "Boston" and row.get("is_physical") != "True":
            continue
        if not row.get("geometry"):
            continue
        geom = wkt.loads(row["geometry"])
        coords = np.asarray(geom.coords, dtype=float)
        segments.append((row["link_id"], coords))
    return segments


def map_panel(ax, lines, values, title, mode, unit, max_value=None):
    coords = [segment for _, segment in lines]
    ids = [link_id for link_id, _ in lines]
    ax.add_collection(LineCollection(coords, colors="#d9e1e5", linewidths=.52,
                                     alpha=.72, zorder=1))
    vals = np.array([float(values.get(link_id, 0.0)) for link_id in ids])
    if mode == "support":
        use = vals > 1e-6
        ax.add_collection(LineCollection([s for s, keep in zip(coords, use) if keep],
                                         colors="#087e8b", linewidths=1.7,
                                         alpha=.88, zorder=2))
        ax.text(.02, .02, f"{int(use.sum())} positive links (>10⁻⁶ {unit})",
                transform=ax.transAxes, color="#154b5a", fontsize=9)
    else:
        keep = vals > (1e-12 if mode == "difference" else 1e-6)
        display = np.log1p(vals[keep]) if mode == "flow" else vals[keep]
        vmax = max_value or max(float(display.max()) if len(display) else 0, 1e-12)
        collection = LineCollection([s for s, yes in zip(coords, keep) if yes],
                                    array=display,
                                    cmap="viridis" if mode == "flow" else "magma",
                                    norm=Normalize(0, vmax), linewidths=1.9,
                                    alpha=.95, zorder=2)
        ax.add_collection(collection)
        colorbar = plt.colorbar(collection, ax=ax, fraction=.035, pad=.015, shrink=.65)
        colorbar.set_label(f"log(1 + {unit})" if mode == "flow" else f"|Δ| ({unit})")
        if mode == "difference":
            ax.text(.02, .02, f"max |Δ| = {vals.max():.2e} {unit}",
                    transform=ax.transAxes, color="#5a3148", fontsize=9)
    ax.autoscale()
    ax.set_aspect("equal")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.set_title(title, loc="left", color="#183f56", fontweight="bold")
    if unit == "PCE":
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    else:
        ax.set_xlabel("Schematic x")
        ax.set_ylabel("Schematic y")
    ax.ticklabel_format(axis="x", useOffset=False)


def maps(city: str, lines, finite: dict[str, float], l3: dict[str, float],
         reference: dict[str, float], sources: list[Path], difference_label: str):
    unit = "benchmark units" if city == "Sioux Falls" else "PCE"
    scope = ("Sioux Falls · B_BECKMANN native candidate · schematic 24-node topology"
             if city == "Sioux Falls" else
             "Boston · ABS_PLANNED · 26 OD" if city == "Boston" else
             "Hong Kong · bounded H1 static BPR/Beckmann · 26 OD")
    for kind, values in (("finite", finite), ("l3", l3)):
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
        if kind == "finite":
            flow_title = ("Frozen path representation · candidate link flow"
                          if city == "Sioux Falls" else "Finite path · reconstructed link flow")
            map_panel(axes[0], lines, values, flow_title, "flow", unit)
            map_panel(axes[1], lines, values, "Positive-link support", "support", unit)
        else:
            delta = {key: abs(values.get(key, 0.0) - reference.get(key, 0.0))
                     for key, _ in lines}
            map_panel(axes[0], lines, values, "Native L3 · reconstructed link flow", "flow", unit)
            map_panel(axes[1], lines, delta, difference_label, "difference", unit)
        fig.suptitle(scope, fontsize=14, color="#15384e")
        # All scope and provenance notes stay in the external HTML/Markdown
        # caption; no tiny footer is baked into the public map image.
        fig.tight_layout(rect=(0, .02, 1, .91))
        stem = f"{SLUG[city]}_{kind}_network"
        save(fig, stem, sources, scope,
             "Presentation derivative: saved flow on matching link geometry; original map files retained.")


def hk_flows(base: Path):
    finite_source = base / "H1_finite/link_flow.csv"
    finite = {r["link_id"]: float(r["flow_pce_per_period"]) for r in read_csv(finite_source)}
    fw_source = base / "H1_FW/link_flow.csv"
    fw = {r["link_id"]: float(r["flow_pce_per_period"]) for r in read_csv(fw_source)}
    path_source = base / "H1_pool/paths.csv"
    paths = read_csv(path_source)
    basis_source = base / "H1_basis_rank26/basis.npz"
    status_source = base / "H1_L3_rank26/status.json"
    status = json.loads(status_source.read_text(encoding="utf-8"))
    assert status["status"] == "SOLVED_WITHIN_DECLARED_TOLERANCE"
    solution_source = base / f"H1_L3_rank26/outer_{status['attempted_outer']:02d}_solution.npz"
    with np.load(basis_source) as basis, np.load(solution_source) as solution:
        flow = np.zeros(len(paths))
        flow[basis["major"]] = solution["x1"]
        flow[basis["minor"]] = basis["U"] @ solution["theta"]
    l3 = {}
    for path, value in zip(paths, flow):
        for link_id in path["link_id_sequence"].split(";"):
            l3[link_id] = l3.get(link_id, 0.0) + float(value)
    return finite, l3, fw, [finite_source, fw_source, path_source,
                            basis_source, status_source, solution_source]


def hk_distributions(lines, finite, l3, fw, sources):
    ids = [link_id for link_id, _ in lines]
    for kind, values in (("finite", finite), ("l3", l3)):
        arr = np.array([values.get(key, 0.0) for key in ids])
        fig = plt.figure(figsize=(6, 3.6), dpi=100, facecolor="white")
        fig.text(.07, .94, "Finite-path reference" if kind == "finite" else
                 "Native Diagnostic L3 / compression", fontsize=12,
                 weight="bold", color="#17364a")
        fig.text(.93, .94, "Hong Kong", fontsize=8.5, color="#087f8c", ha="right")
        axes = [fig.add_axes((.07, .19, .425, .59)), fig.add_axes((.52, .19, .425, .59))]
        axes[0].hist(arr, bins=16, color="#087f8c")
        axes[0].set_title("Reconstructed link flow", fontsize=8)
        if kind == "finite":
            positive = int(np.count_nonzero(arr > 1e-6))
            axes[1].bar(["Positive", "Zero"], [positive, len(arr)-positive],
                        color=["#087f8c", "#dce6eb"])
            axes[1].set_title("Physical-link support", fontsize=8)
        else:
            diff = np.array([l3.get(key, 0.0)-fw.get(key, 0.0) for key in ids])
            axes[1].hist(diff, bins=16, color="#d99243")
            axes[1].set_title("Rank-26 minus H1 FW", fontsize=8)
        for ax in axes:
            ax.tick_params(labelsize=7)
        save(fig, f"hong_kong_{kind}_distribution", sources,
             "Hong Kong frozen H1, 26 OD / 126 legal paths, 1,239 physical links",
             "Physical-link values only; histogram is a saved-result derivative, not a solver run.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hk-h1", type=Path, required=True,
                        help="Locally retained accepted corrected-R2 H1 result directory")
    args = parser.parse_args()
    base = args.hk_h1.resolve()
    for city, files in PUBLIC.items():
        lines = linework(city, files["geometry"])
        a, b = read_csv(files["finite"]), read_csv(files["l3"])
        if city == "Boston":
            finite = {r["link_id"]: float(r["volume"]) for r in a}
            l3 = {r["link_id"]: float(r["v_from_paths"]) for r in b}
            reference = finite
            label = "Absolute difference from finite path"
        else:
            finite = {r["link_id"]: float(r["explicit_v"]) for r in a}
            l3 = {r["link_id"]: float(r["path_aggregate"]) for r in b}
            reference = {r["link_id"]: float(r["explicit_v"]) for r in b}
            label = "Absolute L3 reconstruction residual"
        assert len(lines) == len(finite)
        maps(city, lines, finite, l3, reference, list(files.values()), label)
    geometry = base / "SOURCE_SNAPSHOT/phase_a/instance/link.csv"
    lines = linework("Hong Kong", geometry)
    finite, l3, fw, sources = hk_flows(base)
    assert len(lines) == 1239 and len(finite) == 3446
    public_record = json.loads((ROOT / "docs/assets/hong_kong/static_path_l3_r2/RESULT_SOURCE.json").read_text(encoding="utf-8"))
    assert (public_record["source_package"], public_record["od_count"],
            public_record["legal_path_count"], public_record["physical_link_count"]) == (
            "corrected_R2", 26, 126, len(lines))
    physical_ids = [link_id for link_id, _ in lines]
    assert sum(finite.get(link_id, 0.0) > 1e-6 for link_id in physical_ids) == 300
    max_difference = max(abs(l3.get(link_id, 0.0)-fw.get(link_id, 0.0))
                         for link_id in physical_ids)
    assert 2.2e-8 < max_difference < 2.3e-8
    maps("Hong Kong", lines, finite, l3, fw, [geometry, *sources],
         "Absolute physical-link difference from FW")
    hk_distributions(lines, finite, l3, fw, [geometry, *sources])
    print(f"Rendered 8 saved-result figure pairs under {OUT}")


if __name__ == "__main__":
    main()
