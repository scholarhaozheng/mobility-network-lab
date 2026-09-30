#!/usr/bin/env python3
"""Render the factual, conceptual project map from local public module records.

This is a deterministic documentation build. It neither imports nor calls a
traffic optimizer, case pipeline, network downloader, or observation matcher.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets/project_structure_r2"
MODEL = ASSETS / "project_structure_model.json"
ARCHITECTURE = ROOT / "docs/architecture.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(rel: str) -> str:
    return rel[5:] if rel.startswith("docs/") else "../" + rel


def node_table(nodes: list[dict]) -> str:
    lines = [
        "| Diagram module | Actual source or data entry | Documentation and demonstrated scope |",
        "|---|---|---|",
    ]
    for node in nodes:
        sources = ", ".join(f"[`{p}`]({link(p)})" for p in node["source_paths"])
        docs = ", ".join(f"[{Path(p).stem.replace('-', ' ')}]({link(p)})" for p in node["documentation_links"])
        label = node["label"].replace("|", "\\|")
        scope = node["scope"].replace("|", "\\|")
        lines.append(f"| `{node['id']}` · {label} | {sources} | {docs}. {scope} |")
    return "\n".join(lines) + "\n"


def render() -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    nodes = model["nodes"]
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate project-map node ID")
    if {"static_branch", "finite_branch", "four_stage", "declared_od", "observation_association", "gmns"} - set(ids):
        raise ValueError("Required functional module is absent")
    if [node["id"] for node in nodes if node["group"] == "city_cases"] != ["boston", "sioux", "hong_kong"]:
        raise ValueError("Three city cards must remain Boston / Sioux Falls / Hong Kong")
    for node in nodes:
        for rel in [*node["source_paths"], *node["documentation_links"]]:
            if Path(rel).is_absolute() or ".." in Path(rel).parts or not (ROOT / rel).exists():
                raise FileNotFoundError(f"Project-map source link is invalid: {node['id']} -> {rel}")
        if not node["scope"] or not node["display_lines"]:
            raise ValueError(f"Node scope/display missing: {node['id']}")
    for edge in model["edges"]:
        if edge["from"] not in ids or edge["to"] not in ids:
            raise ValueError(f"Unknown edge endpoint: {edge}")
        if edge["type"] not in {"preparation", "computation", "analytical_output", "optional_case_specific", "case_instance", "navigation"}:
            raise ValueError(f"Unknown relationship type: {edge}")
        if edge["show"] and len(edge.get("route", [])) < 2:
            raise ValueError(f"Visible relationship lacks route: {edge}")

    start = "<!-- project-structure-node-map:start -->"
    end = "<!-- project-structure-node-map:end -->"
    article = ARCHITECTURE.read_text(encoding="utf-8")
    if article.count(start) != 1 or article.count(end) != 1:
        raise ValueError("Architecture page must have exactly one model-table region")
    before, remainder = article.split(start, 1)
    _, after = remainder.split(end, 1)
    updated = before + start + "\n" + node_table(nodes) + end + after
    ARCHITECTURE.write_text(updated, encoding="utf-8", newline="\n")

    with (ASSETS / "project_structure_node_map.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["node_id", "label", "group", "role", "source_paths", "documentation_links", "scope"])
        writer.writeheader()
        for node in nodes:
            writer.writerow({key: node["id"] if key == "node_id" else
                             " | ".join(node[key]) if isinstance(node[key], list) else node[key]
                             for key in writer.fieldnames})

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "mcl-project-structure-r2",
    })
    width, height = model["canvas"]["width"], model["canvas"]["height"]
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    fig.patch.set_facecolor("#f8fafb")
    ax.set_facecolor("#f8fafb")
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")

    palette = {
        "public_inputs": ("#eaf2f5", "#9ab4c2", "#16364b"),
        "representation": ("#16384f", "#16384f", "#ffffff"),
        "demand": ("#eef8f5", "#8bc8bb", "#17394b"),
        "observation": ("#f0f5fa", "#8db0c5", "#17394b"),
        "computation": ("#e9f2f7", "#72a0b4", "#15354b"),
        "outputs": ("#0e6572", "#0e6572", "#ffffff"),
        "city_cases": ("#ffffff", "#7fa6b6", "#15354b"),
        "software_rail": ("#eff3f6", "#c5d4dd", "#17394b"),
    }
    line_style = {
        "preparation": ("#148a8b", "solid", 3.2),
        "computation": ("#174963", "solid", 3.4),
        "analytical_output": ("#8a649c", "solid", 3.4),
        "optional_case_specific": ("#a16554", "dotted", 3.0),
        "case_instance": ("#607f90", "dashed", 2.8),
        "navigation": ("#8096a3", "dashed", 2.5),
    }

    for edge in model["edges"]:
        if not edge["show"]:
            continue
        color, style, weight = line_style[edge["type"]]
        points = edge["route"]
        for a, b in zip(points[:-2], points[1:-1]):
            ax.plot([a[0], b[0]], [a[1], b[1]], color=color, linestyle=style, linewidth=weight, zorder=1)
        a, b = points[-2:]
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=19,
                                     linewidth=weight, linestyle=style, color=color, zorder=2))

    for node in nodes:
        x, y, w, h = node["rect"]
        fill, border, ink = palette[node["group"]]
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0,rounding_size=18",
                                    facecolor=fill, edgecolor=border, linewidth=2.0, zorder=3))
        lines = node["display_lines"]
        if node["group"] == "representation":
            top, gap, main_size, body_size = 307, 30, 22, 18
        elif node["group"] == "city_cases":
            top, gap, main_size, body_size = y + 19, 30, 21, 17
        elif node["group"] == "public_inputs":
            top, gap, main_size, body_size = y + 22, 37, 20, 17
        elif node["group"] == "software_rail":
            top, gap, main_size, body_size = y + 25, 36, 19, 17
        elif node["group"] == "outputs":
            top, gap, main_size, body_size = y + 17, 31, 21, 17
        elif node["group"] == "computation":
            top, gap, main_size, body_size = y + 22, 36, 21, 18
        else:
            top, gap, main_size, body_size = y + 24, 36, 20, 17
        if h <= 100:
            top, gap, main_size, body_size = y + 17, 31, 20, 17
        if len(lines) * gap > h - 18:
            gap = (h - 38) / max(len(lines) - 1, 1)
        for index, line in enumerate(lines):
            ax.text(x + 23, top + index * gap, line, va="top", ha="left",
                    fontsize=main_size if index == 0 else body_size,
                    fontweight="bold" if index == 0 else "normal", color=ink, zorder=4)

    ax.text(40, 48, model["title"], va="top", fontsize=38, fontweight="bold", color="#15354b")
    ax.text(40, 101, model["subtitle"], va="top", fontsize=21, color="#547082")
    ax.text(40, 124, "PUBLIC INPUTS", va="top", fontsize=15, fontweight="bold", color="#087f8c")
    ax.text(1540, 124, "SOFTWARE / DOCUMENTATION", va="top", fontsize=15, fontweight="bold", color="#087f8c")

    legend = [
        ("#148a8b", "solid", "preparation / computation"),
        ("#8a649c", "solid", "analytical output"),
        ("#a16554", "dotted", "optional or case-specific"),
        ("#607f90", "dashed", "case instance / navigation"),
    ]
    for index, (color, style, label) in enumerate(legend):
        x = 40 + index * 375
        ax.plot([x, x + 57], [1348, 1348], color=color, linestyle=style, linewidth=3.5)
        ax.text(x + 68, 1348, label, va="center", fontsize=16, color="#506a78")

    svg = ASSETS / "project_structure.svg"
    png = ASSETS / "project_structure.png"
    fig.savefig(svg, format="svg", metadata={"Date": None, "Creator": "MCL deterministic project-structure renderer"})
    fig.savefig(png, format="png", dpi=160, metadata={"Software": "MCL deterministic project-structure renderer"})
    plt.close(fig)

    record = {
        "record_type": "conceptual-public-project-module-map",
        "source_tree_commit": model["source_tree_commit"],
        "model_sha256": sha(MODEL),
        "renderer_sha256": sha(Path(__file__)),
        "outputs_sha256": {
            "docs/assets/project_structure_r2/project_structure.svg": sha(svg),
            "docs/assets/project_structure_r2/project_structure.png": sha(png),
            "docs/assets/project_structure_r2/project_structure_node_map.csv": sha(ASSETS / "project_structure_node_map.csv"),
        },
        "scope": model["kind"],
        "scientific_solver_calls": 0,
    }
    (ASSETS / "project_structure.source.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record


def main() -> int:
    print(json.dumps(render(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
