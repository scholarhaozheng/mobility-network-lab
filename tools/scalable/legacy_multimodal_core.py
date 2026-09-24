"""Accepted Boston OSM and GTFS graph helpers used by new planned-service skims.

Helper definitions below are extracted without mathematical changes from the
frozen multimodal builder identified in the delivery SOURCE_LOCK.json. The
old fixed-panel selection, service overlay and runnable entry are excluded.
"""

from __future__ import annotations

import hashlib
import math
from datetime import date
from pathlib import Path

import networkx as nx
import numpy as np
import osmium
import pandas as pd
from scipy.spatial import cKDTree

RUN_ID = "behavior_feedback_r1"
SERVICE_DATE = "2026-09-21"
DEPARTURES = (12 * 3600 + 30 * 60, 12 * 3600 + 40 * 60, 12 * 3600 + 50 * 60)
SEARCH_END = 15 * 3600
MAX_WALK_SECONDS = 20 * 60
WALK_MPS = 3.0 * 1609.344 / 3600
BIKE_MPS = 12.0 * 1609.344 / 3600
BOUND = (-71.125, 42.315, -71.025, 42.385)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seconds(value: str) -> int:
    h, m, s = (int(x) for x in value.split(":"))
    return h * 3600 + m * 60 + s


def clock(value: int) -> str:
    return f"{value // 3600:02d}:{value % 3600 // 60:02d}:{value % 60:02d}"


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


class HighwayHandler(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: dict[int, tuple[float, float]] = {}
        self.ways: list[tuple[int, list[int], dict[str, str]]] = []

    def node(self, n) -> None:
        lon, lat = float(n.location.lon), float(n.location.lat)
        if BOUND[0] <= lon <= BOUND[2] and BOUND[1] <= lat <= BOUND[3]:
            self.nodes[int(n.id)] = (lon, lat)

    def way(self, w) -> None:
        tags = {t.k: t.v for t in w.tags}
        if "highway" in tags:
            self.ways.append((int(w.id), [int(n.ref) for n in w.nodes], tags))


def add_min_edge(graph: nx.DiGraph, u: int, v: int, distance_m: float, way_id: int, seconds_: float) -> None:
    old = graph.get_edge_data(u, v)
    if old is None or seconds_ < old["seconds"]:
        graph.add_edge(u, v, distance_m=distance_m, seconds=seconds_, osm_way_id=str(way_id))


def build_osm_graphs(path: Path) -> tuple[dict[int, tuple[float, float]], nx.DiGraph, nx.DiGraph, dict]:
    handler = HighwayHandler()
    handler.apply_file(str(path))
    walk = nx.DiGraph()
    bike = nx.DiGraph()
    walk_excluded = {"motorway", "motorway_link"}
    bike_excluded = {"motorway", "motorway_link", "steps"}
    for way_id, refs, tags in handler.ways:
        highway = tags.get("highway", "")
        access_no = tags.get("access") in {"no", "private"}
        foot_no = tags.get("foot") in {"no", "private"}
        bike_no = tags.get("bicycle") in {"no", "private"}
        oneway = tags.get("oneway") in {"yes", "1", "true", "-1"}
        reverse = tags.get("oneway") == "-1"
        bike_two_way = tags.get("oneway:bicycle") == "no" or tags.get("bicycle:oneway") == "no"
        for a, b in zip(refs[:-1], refs[1:]):
            if a not in handler.nodes or b not in handler.nodes:
                continue
            lon1, lat1 = handler.nodes[a]
            lon2, lat2 = handler.nodes[b]
            dist = haversine_m(lon1, lat1, lon2, lat2)
            if dist <= 0:
                continue
            if not access_no and not foot_no and highway not in walk_excluded:
                add_min_edge(walk, a, b, dist, way_id, dist / WALK_MPS)
                add_min_edge(walk, b, a, dist, way_id, dist / WALK_MPS)
            if not access_no and not bike_no and highway not in bike_excluded:
                if reverse:
                    add_min_edge(bike, b, a, dist, way_id, dist / BIKE_MPS)
                    if bike_two_way:
                        add_min_edge(bike, a, b, dist, way_id, dist / BIKE_MPS)
                else:
                    add_min_edge(bike, a, b, dist, way_id, dist / BIKE_MPS)
                    if not oneway or bike_two_way:
                        add_min_edge(bike, b, a, dist, way_id, dist / BIKE_MPS)
    stats = {
        "osm_nodes_in_bound": len(handler.nodes),
        "osm_highway_ways": len(handler.ways),
        "walk_nodes": walk.number_of_nodes(),
        "walk_edges": walk.number_of_edges(),
        "bike_nodes": bike.number_of_nodes(),
        "bike_edges": bike.number_of_edges(),
    }
    return handler.nodes, walk, bike, stats


def make_snapper(nodes: dict[int, tuple[float, float]], graph: nx.DiGraph):
    ids = np.array(list(graph.nodes), dtype=np.int64)
    lonlat = np.array([nodes[int(i)] for i in ids], dtype=float)
    scale = math.cos(math.radians(42.35))
    xy = np.column_stack((lonlat[:, 0] * scale, lonlat[:, 1]))
    tree = cKDTree(xy)

    def snap(lon: float, lat: float) -> tuple[int, float]:
        _, idx = tree.query([lon * scale, lat], k=1)
        node = int(ids[int(idx)])
        nlon, nlat = nodes[node]
        return node, haversine_m(lon, lat, nlon, nlat)

    return snap


def path_summary(graph: nx.DiGraph, source: int, target: int) -> tuple[str, float, float, list[int]]:
    try:
        path = nx.shortest_path(graph, source, target, weight="seconds")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return "unknown_network_disconnected", math.nan, math.nan, []
    sec = sum(float(graph[u][v]["seconds"]) for u, v in zip(path[:-1], path[1:]))
    dist = sum(float(graph[u][v]["distance_m"]) for u, v in zip(path[:-1], path[1:]))
    return "available", sec, dist, path


def active_services(calendar: pd.DataFrame, exceptions: pd.DataFrame, service_date: str) -> set[str]:
    d = date.fromisoformat(service_date)
    ymd = int(service_date.replace("-", ""))
    weekday = d.strftime("%A").lower()
    mask = (
        (pd.to_numeric(calendar["start_date"]) <= ymd)
        & (pd.to_numeric(calendar["end_date"]) >= ymd)
        & (pd.to_numeric(calendar[weekday]) == 1)
    )
    active = set(calendar.loc[mask, "service_id"].astype(str))
    ex = exceptions[pd.to_numeric(exceptions["date"]) == ymd]
    active |= set(ex.loc[pd.to_numeric(ex["exception_type"]) == 1, "service_id"].astype(str))
    active -= set(ex.loc[pd.to_numeric(ex["exception_type"]) == 2, "service_id"].astype(str))
    return active

