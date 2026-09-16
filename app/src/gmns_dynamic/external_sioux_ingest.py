"""Read-only helpers for the external Sioux Falls GMNS+ dataset.

These utilities intentionally only read ``external_data``. Derived dynamic
fixtures must be written under task output folders, not back into the external
dataset.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_EXTERNAL_SIOUX_DIR = ROOT_DIR / "external_data" / "GMNS_Plus_Dataset" / "17_Sioux_Falls"


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def external_file_hashes(dataset_dir: Path = DEFAULT_EXTERNAL_SIOUX_DIR) -> dict[str, str]:
    if not dataset_dir.exists():
        return {}
    return {
        rel(path): sha256_file(path)
        for path in sorted(dataset_dir.rglob("*"))
        if path.is_file()
    }


def load_external_sioux_tables(dataset_dir: Path = DEFAULT_EXTERNAL_SIOUX_DIR) -> dict[str, list[dict[str, str]]]:
    return {
        "nodes": read_csv_rows(dataset_dir / "node.csv"),
        "links": read_csv_rows(dataset_dir / "link.csv"),
        "demands": read_csv_rows(dataset_dir / "demand.csv"),
        "routes": read_csv_rows(dataset_dir / "minimum_input" / "route_assignment.csv"),
    }


def parse_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(parse_float(value, float(default))))
    except (TypeError, ValueError):
        return default


def split_semicolon_sequence(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def links_by_id(links: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("link_id", ""): row for row in links if row.get("link_id", "")}


def link_travel_time(link: dict[str, str]) -> int:
    for key in ["vdf_fftt", "VDF_fftt", "total_free_flow_travel_time", "length"]:
        if key in link and str(link.get(key, "")).strip() != "":
            return max(1, parse_int(link.get(key), 1))
    return 1


def normalize_link_sequence(
    origin: str,
    destination: str,
    raw_link_ids: list[str],
    link_lookup: dict[str, dict[str, str]],
) -> tuple[list[str], str]:
    """Return a forward link sequence from origin to destination.

    The external route-assignment file often stores link ids in reverse order.
    This helper accepts either direction and reports the normalization used.
    """

    def chain_status(sequence: list[str]) -> bool:
        if not sequence:
            return False
        current = origin
        for link_id in sequence:
            link = link_lookup.get(link_id)
            if link is None or link.get("from_node_id") != current:
                return False
            current = link.get("to_node_id", "")
        return current == destination

    if chain_status(raw_link_ids):
        return raw_link_ids, "as_provided"
    reversed_ids = list(reversed(raw_link_ids))
    if chain_status(reversed_ids):
        return reversed_ids, "reversed_from_external_route_assignment"
    raise ValueError(
        f"link sequence does not connect {origin}->{destination}: {';'.join(raw_link_ids)}"
    )


def node_sequence_from_links(
    origin: str,
    link_ids: list[str],
    link_lookup: dict[str, dict[str, str]],
) -> list[str]:
    nodes = [origin]
    current = origin
    for link_id in link_ids:
        link = link_lookup[link_id]
        if link.get("from_node_id") != current:
            raise ValueError(f"link {link_id} does not continue from node {current}")
        current = link.get("to_node_id", "")
        nodes.append(current)
    return nodes
