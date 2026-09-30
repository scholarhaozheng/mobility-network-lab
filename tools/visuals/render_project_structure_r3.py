#!/usr/bin/env python3
"""Render the selective, clickable project map from public module records.

Only documentation assets and an architecture index are produced. No city-data
pipeline, scientific solver, optimizer, or matching routine is imported.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets/project_structure_r3"
MODEL = ASSETS / "project_structure_model.json"
ARCHITECTURE = ROOT / "docs/architecture.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def doc_link(rel: str) -> str:
    return rel[5:] if rel.startswith("docs/") else "../" + rel


def svg_link(rel: str) -> str:
    # An opened SVG lives two levels below the docs root.
    return "../../" + rel.removeprefix("docs/").removesuffix(".md") + ".html"


def node_table(nodes: list[dict], references: dict[str, dict]) -> str:
    lines = [
        "| Diagram module | Actual source or data entry | Documentation and demonstrated scope |",
        "|---|---|---|",
    ]
    for node in nodes:
        source = references[node["source_ref"]]
        sources = ", ".join(f"[`{p}`]({doc_link(p)})" for p in source["source_paths"])
        target = node["target"]
        lines.append(
            f"| `{node['id']}` · {node['title']} | {sources} | "
            f"[Open evidence]({doc_link(target)}). {node['scope']} |"
        )
    return "\n".join(lines) + "\n"


def render() -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    ledger_path = ROOT / model["source_ledger"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    references = {node["id"]: node for node in ledger["nodes"]}
    nodes = model["nodes"]
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)) or len(nodes) != 18:
        raise ValueError("Project-map nodes are missing or duplicated")
    if {"gmns", "city_demand", "declared_od", "association", "static", "finite", "outputs"} - set(ids):
        raise ValueError("Required model distinction is missing")
    if [node["id"] for node in nodes if node["group"] == "cases"] != ["boston", "sioux", "hong_kong"]:
        raise ValueError("Case order must be Boston / Sioux Falls / Hong Kong")
    width, height = model["canvas"]["width"], model["canvas"]["height"]
    for node in nodes:
        if node["source_ref"] not in references:
            raise ValueError(f"Unknown source-ledger node: {node['id']}")
        x, y, w, h = node["rect"]
        if min(x, y, w, h) < 0 or x + w > width or y + h > height:
            raise ValueError(f"Invalid card bounds: {node['id']}")
        for rel in [node["target"], *references[node["source_ref"]]["source_paths"]]:
            if Path(rel).is_absolute() or ".." in Path(rel).parts or not (ROOT / rel).exists():
                raise FileNotFoundError(f"Broken module link: {node['id']} -> {rel}")

    start = "<!-- project-structure-node-map:start -->"
    end = "<!-- project-structure-node-map:end -->"
    article = ARCHITECTURE.read_text(encoding="utf-8")
    if article.count(start) != 1 or article.count(end) != 1:
        raise ValueError("Architecture index markers are missing or duplicated")
    before, tail = article.split(start, 1)
    _, after = tail.split(end, 1)
    ARCHITECTURE.write_text(before + start + "\n" + node_table(nodes, references) + end + after,
                            encoding="utf-8", newline="\n")

    with (ASSETS / "project_structure_node_map.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["node_id", "title", "group", "source_ref", "target", "scope"])
        writer.writeheader()
        for node in nodes:
            writer.writerow({key: node["id"] if key == "node_id" else node[key] for key in writer.fieldnames})

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "svg.hashsalt": "mcl-project-structure-r3",
    })
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    fig.patch.set_facecolor("#f7fafc")
    ax.set_facecolor("#f7fafc")
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")

    palette = {
        "sources": ("#edf3f7", "#a9bfcd", "#17384e"),
        "preparation": ("#f2f8f5", "#8dc5b6", "#17384e"),
        "static": ("#e8f1f7", "#3f829e", "#15364d"),
        "finite": ("#eef0f9", "#7778b2", "#1c3154"),
        "outputs": ("#125d6b", "#125d6b", "#ffffff"),
        "cases": ("#ffffff", "#8badba", "#16384e"),
        "entry": ("#eef2f4", "#c2d1d9", "#29475b"),
    }
    sections = [
        (40, 155, "01 / SOURCE EVIDENCE"),
        (40, 327, "02 / REPRESENTATION AND OPTIONAL PREPARATION"),
        (40, 607, "03 / SEPARATE COMPUTATION CONTRACTS — NOT A SEQUENTIAL SOLVER CHAIN"),
        (40, 901, "04 / SAVED OUTPUTS AND CHECKS"),
        (40, 1077, "05 / CASE INSTANCES — NOT PROCESSING STAGES"),
        (40, 1250, "06 / CODE AND DOCUMENTATION ENTRY"),
    ]
    ax.text(40, 49, model["title"], va="top", fontsize=37, fontweight="bold", color="#142f45")
    ax.text(40, 98, model["subtitle"], va="top", fontsize=18, color="#526b7b")
    for x, y, label in sections:
        ax.text(x, y, label, va="bottom", fontsize=15, fontweight="bold", color="#087e83")

    for node in nodes:
        x, y, w, h = node["rect"]
        fill, border, ink = palette[node["group"]]
        href = svg_link(node["target"])
        box = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0,rounding_size=14",
            facecolor=fill, edgecolor=border, linewidth=2,
        )
        box.set_url(href)
        ax.add_patch(box)
        if node["group"] == "entry":
            title_y, title_size, line_y, line_gap, body_size = y + 17, 17, y + 53, 22, 14
        elif node["group"] == "cases":
            title_y, title_size, line_y, line_gap, body_size = y + 17, 22, y + 55, 26, 14
        elif node["group"] == "sources":
            title_y, title_size, line_y, line_gap, body_size = y + 17, 18, y + 56, 25, 14
        elif node["group"] == "outputs":
            title_y, title_size, line_y, line_gap, body_size = y + 13, 21, y + 53, 25, 15
        elif node["group"] in {"static", "finite"}:
            title_y, title_size, line_y, line_gap, body_size = y + 22, 23, y + 69, 31, 17
        else:
            title_y, title_size, line_y, line_gap, body_size = y + 18, 19, y + 60, 29, 14
        title = ax.text(x + 21, title_y, node["title"], va="top", fontsize=title_size,
                        fontweight="bold", color=ink)
        title.set_url(href)
        for index, line in enumerate(node["lines"]):
            label = ax.text(x + 21, line_y + index * line_gap, line, va="top",
                            fontsize=body_size, color=ink)
            label.set_url(href)

    ax.text(40, 1422, "Open this SVG directly to follow a card to its documentation; cards are evidence routes, not universal execution steps.",
            va="bottom", fontsize=13, color="#607987")

    svg = ASSETS / "project_structure.svg"
    png = ASSETS / "project_structure.png"
    fig.savefig(svg, format="svg", metadata={"Date": None, "Creator": "MCL source-grounded project map r3"})
    fig.savefig(png, format="png", dpi=100, metadata={"Software": "MCL source-grounded project map r3"})
    plt.close(fig)
    # Matplotlib's path serializer leaves spaces at SVG line ends. Normalize
    # only that formatting so the exact published SVG passes whitespace gates.
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                   encoding="utf-8", newline="\n")
    svg_text = svg.read_text(encoding="utf-8")
    if svg_text.count("xlink:href=") < len(nodes):
        raise AssertionError("Clickable SVG card links were not rendered")

    record = {
        "record_type": "clickable-selective-cross-city-project-module-map",
        "model_sha256": sha(MODEL),
        "source_ledger_path": model["source_ledger"],
        "source_ledger_sha256": sha(ledger_path),
        "renderer_sha256": sha(Path(__file__)),
        "outputs_sha256": {
            "docs/assets/project_structure_r3/project_structure.svg": sha(svg),
            "docs/assets/project_structure_r3/project_structure.png": sha(png),
            "docs/assets/project_structure_r3/project_structure_node_map.csv": sha(ASSETS / "project_structure_node_map.csv"),
        },
        "scope": model["relationship_rule"],
        "scientific_solver_calls": 0,
    }
    (ASSETS / "project_structure.source.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return record


def main() -> int:
    print(json.dumps(render(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
