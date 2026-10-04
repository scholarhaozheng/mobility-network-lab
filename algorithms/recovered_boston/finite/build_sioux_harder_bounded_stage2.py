"""Build harder capacity-pressure Stage 2 dynamic CSV files.

This is dynamic file generation only. It does not run arc-LP, RMP,
pricing, controlled CG, repeated CG, full CG, full Sioux Falls assignment,
GTFS, railway, branch-and-price, RL, or production-scale solving.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = "configs/sioux_falls_harder_bounded_stage2.yaml"
SCOPE_BOUNDARY = (
    "This is harder capacity-pressure Stage 2 dynamic build and structural "
    "validation only. It does not run arc-LP, RMP, pricing, controlled CG, "
    "repeated CG, full CG, full Sioux Falls assignment, GTFS, railway, "
    "branch-and-price, RL, or production-scale solving."
)
STAGE1_INPUT_FILES = [
    "physical_node.csv",
    "physical_link.csv",
    "demand_seed.csv",
    "physical_candidate_paths.csv",
    "shared_link_pressure.csv",
]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def load_config(path: str | Path) -> dict[str, Any]:
    resolved = resolve_path(path)
    with resolved.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a mapping: {resolved}")
    if config.get("optimization_enabled") is not False:
        raise ValueError("Stage 2 config must set optimization_enabled: false")
    return config


def data_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config.get("data_dir", "data/sioux_falls_harder_bounded_stage2"))


def output_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config.get("output_dir", "outputs/sioux_falls_harder_bounded_stage2"))


def stage1_data_dir(config: dict[str, Any]) -> Path:
    return resolve_path(config.get("stage1_data_dir", "data/sioux_falls_harder_bounded_stage1"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def as_int_text(value: Any) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.10g}"


def split_sequence(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def node_time_id(node_id: str, time: int) -> str:
    return f"n{node_id}_t{time}"


def source_node_time_id(demand: dict[str, Any]) -> str:
    return f"source_{demand['demand_id']}_t{as_int_text(demand['departure_time'])}"


def sink_node_time_id(demand: dict[str, Any], max_time: int) -> str:
    return f"sink_{demand['demand_id']}_t{max_time}"


def source_arc_id(demand_id: str) -> str:
    return f"source_{demand_id}"


def sink_arc_id(demand_id: str, destination: str, time: int) -> str:
    return f"sink_{demand_id}_{destination}_t{time}"


def movement_arc_id(link_id: str, time: int) -> str:
    return f"move_{link_id}_t{time}"


def wait_arc_id(node_id: str, time: int) -> str:
    return f"wait_{node_id}_t{time}"


def normalize_demand(row: dict[str, str]) -> dict[str, Any]:
    return {
        "demand_id": row["demand_id"],
        "origin_node_id": row["origin_node_id"],
        "destination_node_id": row["destination_node_id"],
        "departure_time": int(float(row["departure_time"])),
        "volume": parse_float(row.get("volume", row.get("demand"))),
    }


def selected_ods(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for idx, od in enumerate((config.get("selected_candidate") or {}).get("od_pairs", []), start=1):
        rows.append(
            {
                "demand_id": str(od.get("id", f"D{idx}")),
                "origin": str(od["origin"]),
                "destination": str(od["destination"]),
                "demand": parse_float(od.get("demand", od.get("volume"))),
                "departure_time": int(od.get("departure_time", 0)),
            }
        )
    return rows


def copy_stage1_inputs(src_dir: Path, dat_dir: Path) -> None:
    dat_dir.mkdir(parents=True, exist_ok=True)
    for name in STAGE1_INPUT_FILES:
        source = src_dir / name
        if not source.exists():
            raise FileNotFoundError(f"Missing Stage 1 input: {source}")
        shutil.copy2(source, dat_dir / name)


def dynamic_node_rows(
    physical_nodes: list[dict[str, str]],
    demands: list[dict[str, Any]],
    time_steps: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in physical_nodes:
        for time in time_steps:
            rows.append(
                {
                    "node_time_id": node_time_id(node["node_id"], time),
                    "physical_node_id": node["node_id"],
                    "time": time,
                }
            )
    max_time = max(time_steps)
    for demand in demands:
        rows.append(
            {
                "node_time_id": source_node_time_id(demand),
                "physical_node_id": f"source_{demand['demand_id']}",
                "time": demand["departure_time"],
            }
        )
        rows.append(
            {
                "node_time_id": sink_node_time_id(demand, max_time),
                "physical_node_id": f"sink_{demand['demand_id']}",
                "time": max_time,
            }
        )
    return rows


def dynamic_arc_rows(
    physical_nodes: list[dict[str, str]],
    physical_links: list[dict[str, str]],
    demands: list[dict[str, Any]],
    time_steps: list[int],
    waiting: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    max_time = max(time_steps)
    time_set = set(time_steps)
    counts = {"movement": 0, "waiting": 0, "source_connector": 0, "sink_connector": 0}

    for link in physical_links:
        travel_time = int(round(parse_float(link["travel_time"])))
        for time in time_steps:
            to_time = time + travel_time
            if to_time not in time_set:
                continue
            rows.append(
                {
                    "arc_id": movement_arc_id(link["physical_link_id"], time),
                    "from_node_time_id": node_time_id(link["from_node_id"], time),
                    "to_node_time_id": node_time_id(link["to_node_id"], to_time),
                    "from_physical_node_id": link["from_node_id"],
                    "to_physical_node_id": link["to_node_id"],
                    "from_time": time,
                    "to_time": to_time,
                    "arc_type": "movement",
                    "physical_link_id": link["physical_link_id"],
                    "cost": link["cost"],
                    "capacity": link["capacity"],
                }
            )
            counts["movement"] += 1

    if waiting.get("enabled", True):
        for node in physical_nodes:
            for time in time_steps[:-1]:
                rows.append(
                    {
                        "arc_id": wait_arc_id(node["node_id"], time),
                        "from_node_time_id": node_time_id(node["node_id"], time),
                        "to_node_time_id": node_time_id(node["node_id"], time + 1),
                        "from_physical_node_id": node["node_id"],
                        "to_physical_node_id": node["node_id"],
                        "from_time": time,
                        "to_time": time + 1,
                        "arc_type": "waiting",
                        "physical_link_id": "",
                        "cost": waiting.get("cost", 0.1),
                        "capacity": waiting.get("capacity", 999),
                    }
                )
                counts["waiting"] += 1

    for demand in demands:
        rows.append(
            {
                "arc_id": source_arc_id(demand["demand_id"]),
                "from_node_time_id": source_node_time_id(demand),
                "to_node_time_id": node_time_id(demand["origin_node_id"], demand["departure_time"]),
                "from_physical_node_id": f"source_{demand['demand_id']}",
                "to_physical_node_id": demand["origin_node_id"],
                "from_time": demand["departure_time"],
                "to_time": demand["departure_time"],
                "arc_type": "source_connector",
                "physical_link_id": "",
                "cost": 0,
                "capacity": f"{demand['volume']:.10g}",
            }
        )
        counts["source_connector"] += 1
        for time in time_steps:
            if time < demand["departure_time"]:
                continue
            rows.append(
                {
                    "arc_id": sink_arc_id(demand["demand_id"], demand["destination_node_id"], time),
                    "from_node_time_id": node_time_id(demand["destination_node_id"], time),
                    "to_node_time_id": sink_node_time_id(demand, max_time),
                    "from_physical_node_id": demand["destination_node_id"],
                    "to_physical_node_id": f"sink_{demand['demand_id']}",
                    "from_time": time,
                    "to_time": max_time,
                    "arc_type": "sink_connector",
                    "physical_link_id": "",
                    "cost": 0,
                    "capacity": max(float(demand["volume"]), 10000.0),
                }
            )
            counts["sink_connector"] += 1
    return rows, counts


def dynamic_column_rows(
    demands: list[dict[str, Any]],
    physical_links: list[dict[str, str]],
    candidate_paths: list[dict[str, str]],
    time_steps: list[int],
    movement_arc_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    link_by_id = {link["physical_link_id"]: link for link in physical_links}
    demand_by_id = {demand["demand_id"]: demand for demand in demands}
    max_time = max(time_steps)
    columns: list[dict[str, Any]] = []
    skipped: list[str] = []

    for path in candidate_paths:
        demand_id = path["demand_id"]
        demand = demand_by_id.get(demand_id)
        if demand is None:
            skipped.append(f"{path['path_id']}: unknown demand_id {demand_id}")
            continue
        nodes = split_sequence(path["node_sequence"])
        link_ids = split_sequence(path["link_sequence"])
        if len(link_ids) != len(nodes) - 1:
            skipped.append(f"{path['path_id']}: link count does not match node sequence")
            continue
        if nodes[0] != demand["origin_node_id"] or nodes[-1] != demand["destination_node_id"]:
            skipped.append(f"{path['path_id']}: node sequence does not match demand OD")
            continue

        current_time = int(demand["departure_time"])
        time_sequence = [current_time]
        arc_ids = [source_arc_id(demand_id)]
        total_cost = 0.0
        ok = True
        for idx, link_id in enumerate(link_ids):
            link = link_by_id.get(link_id)
            if link is None:
                skipped.append(f"{path['path_id']}: missing physical link {link_id}")
                ok = False
                break
            if link["from_node_id"] != nodes[idx] or link["to_node_id"] != nodes[idx + 1]:
                skipped.append(f"{path['path_id']}: link {link_id} does not connect node sequence")
                ok = False
                break
            travel_time = int(round(parse_float(link["travel_time"])))
            arc_id = movement_arc_id(link_id, current_time)
            next_time = current_time + travel_time
            if next_time > max_time:
                skipped.append(f"{path['path_id']}: arrival time {next_time} exceeds max time {max_time}")
                ok = False
                break
            if arc_id not in movement_arc_ids:
                skipped.append(f"{path['path_id']}: missing movement arc {arc_id}")
                ok = False
                break
            arc_ids.append(arc_id)
            current_time = next_time
            time_sequence.append(current_time)
            total_cost += parse_float(link["cost"])
        if not ok:
            continue

        arc_ids.append(sink_arc_id(demand_id, demand["destination_node_id"], current_time))
        columns.append(
            {
                "column_id": f"C_{demand_id}_{path['path_rank']}",
                "demand_id": demand_id,
                "origin_node_id": demand["origin_node_id"],
                "destination_node_id": demand["destination_node_id"],
                "departure_time": demand["departure_time"],
                "arrival_time": current_time,
                "travel_time": current_time - demand["departure_time"],
                "generalized_cost": f"{total_cost:.10g}",
                "node_sequence": "|".join(nodes),
                "link_sequence": "|".join(link_ids),
                "time_sequence": "|".join(str(time) for time in time_sequence),
                "arc_sequence": "|".join(arc_ids),
            }
        )
    return columns, skipped


def build(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    src_dir = stage1_data_dir(config)
    dat_dir = data_dir(config)
    out_dir = output_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_stage1_inputs(src_dir, dat_dir)

    physical_nodes = read_csv(src_dir / "physical_node.csv")
    physical_links = read_csv(src_dir / "physical_link.csv")
    demands = [normalize_demand(row) for row in read_csv(src_dir / "demand_seed.csv")]
    candidate_paths = read_csv(src_dir / "physical_candidate_paths.csv")
    time_steps = [int(time) for time in config["time_steps"]]
    waiting = config.get("waiting_arc", {})

    dynamic_nodes = dynamic_node_rows(physical_nodes, demands, time_steps)
    dynamic_arcs, arc_counts = dynamic_arc_rows(physical_nodes, physical_links, demands, time_steps, waiting)
    movement_arc_ids = {row["arc_id"] for row in dynamic_arcs if row["arc_type"] == "movement"}
    dynamic_columns, skipped = dynamic_column_rows(demands, physical_links, candidate_paths, time_steps, movement_arc_ids)

    write_csv(dat_dir / "dynamic_node.csv", dynamic_nodes, ["node_time_id", "physical_node_id", "time"])
    write_csv(
        dat_dir / "dynamic_arc.csv",
        dynamic_arcs,
        [
            "arc_id",
            "from_node_time_id",
            "to_node_time_id",
            "from_physical_node_id",
            "to_physical_node_id",
            "from_time",
            "to_time",
            "arc_type",
            "physical_link_id",
            "cost",
            "capacity",
        ],
    )
    write_csv(
        dat_dir / "dynamic_demand.csv",
        demands,
        ["demand_id", "origin_node_id", "destination_node_id", "departure_time", "volume"],
    )
    write_csv(
        dat_dir / "dynamic_columns.csv",
        dynamic_columns,
        [
            "column_id",
            "demand_id",
            "origin_node_id",
            "destination_node_id",
            "departure_time",
            "arrival_time",
            "travel_time",
            "generalized_cost",
            "node_sequence",
            "link_sequence",
            "time_sequence",
            "arc_sequence",
        ],
    )

    columns_per_demand = {
        demand["demand_id"]: len([col for col in dynamic_columns if col["demand_id"] == demand["demand_id"]])
        for demand in demands
    }
    all_demands_have_columns = all(count > 0 for count in columns_per_demand.values())
    status = "PASS" if all_demands_have_columns and not skipped else "PASS_WITH_SKIPS" if all_demands_have_columns else "FAIL"
    summary = {
        "experiment_name": config.get("experiment_name", "sioux_falls_harder_bounded"),
        "stage": "stage2_dynamic_build_only",
        "stage2_build_status": status,
        "time_steps": time_steps,
        "max_time": max(time_steps),
        "physical_node_count": len(physical_nodes),
        "physical_link_count": len(physical_links),
        "dynamic_node_count": len(dynamic_nodes),
        "dynamic_arc_count": len(dynamic_arcs),
        "dynamic_demand_count": len(demands),
        "dynamic_column_count": len(dynamic_columns),
        "arc_counts": arc_counts,
        "columns_per_demand": columns_per_demand,
        "candidate_path_count": len(candidate_paths),
        "skipped_path_count": len(skipped),
        "skipped_paths": skipped,
        "selected_ods": selected_ods(config),
        "scope": SCOPE_BOUNDARY,
    }
    (out_dir / "dynamic_build_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(out_dir / "dynamic_build_report.md", summary)
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Harder Capacity-Pressure Stage 2 Dynamic Build Report",
        "",
        SCOPE_BOUNDARY,
        "",
        f"- Stage 2 build status: {summary['stage2_build_status']}",
        f"- Physical node count: {summary['physical_node_count']}",
        f"- Physical link count: {summary['physical_link_count']}",
        f"- Dynamic node count: {summary['dynamic_node_count']}",
        f"- Dynamic arc count: {summary['dynamic_arc_count']}",
        f"- Dynamic demand count: {summary['dynamic_demand_count']}",
        f"- Dynamic column count: {summary['dynamic_column_count']}",
        f"- Candidate path count: {summary['candidate_path_count']}",
        f"- Skipped path count: {summary['skipped_path_count']}",
        f"- Time steps: {summary['time_steps'][0]}..{summary['time_steps'][-1]}",
        f"- Movement arcs: {summary['arc_counts'].get('movement', 0)}",
        f"- Waiting arcs: {summary['arc_counts'].get('waiting', 0)}",
        f"- Source connectors: {summary['arc_counts'].get('source_connector', 0)}",
        f"- Sink connectors: {summary['arc_counts'].get('sink_connector', 0)}",
        "",
        "## Columns Per Demand",
        "",
    ]
    lines.extend(f"- {demand_id}: {count}" for demand_id, count in summary["columns_per_demand"].items())
    lines.extend(["", "## Skipped Paths", ""])
    if summary["skipped_paths"]:
        lines.extend(f"- {item}" for item in summary["skipped_paths"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            "This report documents only dynamic CSV construction for the harder capacity-pressure benchmark. It is not an optimization result.",
            "",
            SCOPE_BOUNDARY,
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build harder capacity-pressure Stage 2 dynamic CSV files.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build(args.config)
    print(f"Stage 2 build status: {summary['stage2_build_status']}")
    print(f"Dynamic nodes: {summary['dynamic_node_count']}")
    print(f"Dynamic arcs: {summary['dynamic_arc_count']}")
    print(f"Dynamic demands: {summary['dynamic_demand_count']}")
    print(f"Dynamic columns: {summary['dynamic_column_count']}")
    print(f"Columns per demand: {summary['columns_per_demand']}")
    return 0 if summary["stage2_build_status"] in {"PASS", "PASS_WITH_SKIPS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

