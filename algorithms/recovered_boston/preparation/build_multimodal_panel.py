"""Build a fixed Central Boston validation panel and real-network modal skims.

The implementation is intentionally bounded: 36 HBW midday OD pairs, three
departure instants, the existing directed GMNS road graph, OSM walking/cycling
ways, and the locally archived MBTA GTFS.  S2 differs from S1 only by the
explicitly enabled exploratory service overlay.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import h3
import networkx as nx
import numpy as np
import osmium
import pandas as pd
from scipy.spatial import cKDTree

from semantic_transit import (
    FarePolicy,
    TransferPolicy,
    build_connections as build_connections_semantic,
    transit_route as transit_route_semantic,
)


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


@dataclass(frozen=True)
class LegacyConnectionDisabled:
    """Retained only for historical source comparison; never used by main()."""
    from_stop: str
    to_stop: str
    dep: int
    arr: int
    trip_id: str
    route_id: str
    route_type: str
    direction_id: str
    from_seq: int
    to_seq: int
    overlay_parameter_id: str | None


def legacy_build_connections_disabled(
    stop_times: pd.DataFrame,
    trip_meta: pd.DataFrame,
    overlay: pd.DataFrame | None,
) -> list[LegacyConnectionDisabled]:
    """Disabled prototype. Use semantic_transit.build_connections instead."""
    lookup: dict[tuple[str, str, str, str], tuple[float, str]] = {}
    if overlay is not None:
        for _, row in overlay.iterrows():
            key = (str(row.route_id), str(row.direction_id), str(row.from_stop_id), str(row.to_stop_id))
            lookup[key] = (float(row.mean_factor), str(row.parameter_id))
    out: list[LegacyConnectionDisabled] = []
    merged = stop_times.merge(trip_meta, on="trip_id", how="inner", validate="many_to_one")
    merged["seq"] = pd.to_numeric(merged["stop_sequence"], errors="coerce")
    for trip_id, group in merged.groupby("trip_id", sort=False):
        group = group.sort_values("seq")
        rows = list(group.itertuples(index=False))
        cumulative_delta = 0.0
        cumulative_parameters: list[str] = []
        for a, b in zip(rows[:-1], rows[1:]):
            dep_base = seconds(a.departure_time)
            arr_base = seconds(b.arrival_time)
            base_run = arr_base - dep_base
            if base_run < 0:
                continue
            key = (str(a.route_id), str(a.direction_id), str(a.stop_id), str(b.stop_id))
            parameter_id = None
            segment_delta = 0.0
            if key in lookup and 12 * 3600 + 30 * 60 <= dep_base <= 13 * 3600 + 15 * 60:
                factor, parameter_id = lookup[key]
                segment_delta = max(1.0, base_run * factor) - base_run
            applied_parameters = list(cumulative_parameters)
            if parameter_id is not None:
                applied_parameters.append(parameter_id)
            dep = int(round(dep_base + cumulative_delta))
            arr = int(round(arr_base + cumulative_delta + segment_delta))
            cumulative_delta += segment_delta
            if dep <= SEARCH_END and arr >= min(DEPARTURES) - MAX_WALK_SECONDS:
                out.append(
                    LegacyConnectionDisabled(
                        str(a.stop_id), str(b.stop_id), dep, arr, str(trip_id), str(a.route_id),
                        str(a.route_type), str(a.direction_id), int(a.seq), int(b.seq),
                        ";".join(applied_parameters) if applied_parameters else None
                    )
                )
            if parameter_id is not None:
                cumulative_parameters.append(parameter_id)
    out.sort(key=lambda x: (x.dep, x.arr, x.trip_id, x.from_seq))
    return out


def legacy_build_transfer_graph_disabled(
    stops: pd.DataFrame, transfers: pd.DataFrame
) -> dict[str, list[tuple[str, int]]]:
    """Disabled prototype. Transfer semantics live in semantic_transit.py."""
    edges: dict[str, dict[str, int]] = defaultdict(dict)
    known = set(stops["stop_id"].astype(str))
    for row in transfers.itertuples(index=False):
        a, b = str(row.from_stop_id), str(row.to_stop_id)
        if a not in known or b not in known or a == b:
            continue
        raw = getattr(row, "min_walk_time", None)
        try:
            sec = int(float(raw)) if pd.notna(raw) and str(raw) else 120
        except ValueError:
            sec = 120
        edges[a][b] = min(edges[a].get(b, 10**9), max(0, sec))
    for parent, group in stops[stops["parent_station"].notna() & stops["parent_station"].ne("")].groupby("parent_station"):
        ids = group["stop_id"].astype(str).tolist()
        for a in ids:
            for b in ids:
                if a != b:
                    edges[a][b] = min(edges[a].get(b, 10**9), 120)
    return {a: list(v.items()) for a, v in edges.items()}


def legacy_transit_route_disabled(
    departure: int,
    connections: list[LegacyConnectionDisabled],
    access: dict[str, float],
    egress: dict[str, float],
    transfer_graph: dict[str, list[tuple[str, int]]],
) -> dict:
    """Disabled prototype. main() calls semantic_transit.transit_route."""
    inf = 10**12
    labels: dict[str, float] = {}
    state_at: dict[str, int] = {}
    states: list[dict] = []

    def new_state(stop: str, at: float, kind: str, prev: int | None, payload: dict) -> int:
        idx = len(states)
        states.append({"stop": stop, "at": at, "kind": kind, "prev": prev, **payload})
        return idx

    def relax_transfers(seed: str) -> None:
        heap = [(labels[seed], seed)]
        while heap:
            at, a = heapq.heappop(heap)
            if at != labels.get(a):
                continue
            for b, sec in transfer_graph.get(a, []):
                cand = at + sec
                if cand < labels.get(b, inf):
                    sid = new_state(b, cand, "transfer_walk", state_at[a], {"seconds": sec, "from_stop": a})
                    labels[b], state_at[b] = cand, sid
                    heapq.heappush(heap, (cand, b))

    for stop, sec in access.items():
        at = departure + sec
        if at < labels.get(stop, inf):
            sid = new_state(stop, at, "access_walk", None, {"seconds": sec})
            labels[stop], state_at[stop] = at, sid
    for stop in list(labels):
        relax_transfers(stop)

    for c in connections:
        if c.dep < departure or c.dep > SEARCH_END:
            continue
        if labels.get(c.from_stop, inf) <= c.dep and c.arr < labels.get(c.to_stop, inf):
            sid = new_state(
                c.to_stop,
                c.arr,
                "ride",
                state_at[c.from_stop],
                {"connection": c, "wait_seconds": c.dep - labels[c.from_stop]},
            )
            labels[c.to_stop], state_at[c.to_stop] = c.arr, sid
            relax_transfers(c.to_stop)

    candidates = [(labels[s] + sec, s, sec) for s, sec in egress.items() if s in labels]
    if not candidates:
        return {"status": "confirmed_unavailable_within_declared_search_limits"}
    end, stop, egress_sec = min(candidates)
    chain: list[dict] = []
    sid: int | None = state_at[stop]
    while sid is not None:
        chain.append(states[sid])
        sid = states[sid]["prev"]
    chain.reverse()
    rides = [x for x in chain if x["kind"] == "ride"]
    access_sec = sum(float(x["seconds"]) for x in chain if x["kind"] == "access_walk")
    transfer_walk_sec = sum(float(x["seconds"]) for x in chain if x["kind"] == "transfer_walk")
    wait_sec = 0.0
    in_vehicle_sec = 0.0
    previous_connection = None
    for x in rides:
        c = x["connection"]
        in_vehicle_sec += float(c.arr - c.dep)
        if previous_connection is not None and previous_connection.trip_id == c.trip_id:
            # Same vehicle: scheduled dwell is part of onboard time, not a new wait.
            in_vehicle_sec += float(max(0, c.dep - previous_connection.arr))
        else:
            wait_sec += float(x["wait_seconds"])
        previous_connection = c
    trips = []
    for x in rides:
        trip = x["connection"].trip_id
        if not trips or trips[-1] != trip:
            trips.append(trip)
    route_types = {x["connection"].route_type for x in rides}
    if route_types & {"0", "1"}:
        fare = 2.40
        fare_rule = "rapid_transit_flat_fare_approximation"
    elif route_types == {"3"} or (route_types and route_types <= {"3"}):
        fare = 1.70
        fare_rule = "local_bus_flat_fare_approximation"
    else:
        fare = math.nan
        fare_rule = "unknown_for_route_type_combination"
    overlay_ids = sorted({
        item
        for x in rides if x["connection"].overlay_parameter_id
        for item in str(x["connection"].overlay_parameter_id).split(";")
    })
    return {
        "status": "available",
        "arrival": int(round(end)),
        "total_seconds": float(end - departure),
        "walk_seconds": access_sec + transfer_walk_sec + float(egress_sec),
        "access_walk_seconds": access_sec,
        "transfer_walk_seconds": transfer_walk_sec,
        "egress_walk_seconds": float(egress_sec),
        "wait_seconds": wait_sec,
        "in_vehicle_seconds": in_vehicle_sec,
        "transfers": max(0, len(trips) - 1),
        "fare_usd": fare,
        "fare_rule": fare_rule,
        "overlay_parameter_ids": overlay_ids,
        "chain": chain,
    }


def panel_selection(regional_od: pd.DataFrame, zone_access: pd.DataFrame, obs: pd.DataFrame, stops: pd.DataFrame, valid_zones: set[str]) -> pd.DataFrame:
    hb = regional_od[regional_od["purpose"].eq("HBW")].copy()
    hb = hb[hb["o_zone_id"].isin(valid_zones) & hb["d_zone_id"].isin(valid_zones)]
    hb = hb[hb["o_zone_id"].ne(hb["d_zone_id"])].sort_values("person_trips_midday_od", ascending=False)
    stop_lookup = stops.set_index("stop_id")[["stop_lat", "stop_lon"]]
    obs_stops = set(obs["from_stop_id"].astype(str)) | set(obs["to_stop_id"].astype(str))
    corridor_zones: set[str] = set()
    for stop in obs_stops:
        if stop in stop_lookup.index:
            row = stop_lookup.loc[stop]
            zone = "h3r9:" + h3.latlng_to_cell(float(row.stop_lat), float(row.stop_lon), 9)
            if zone in valid_zones:
                corridor_zones.add(zone)
    stress_zones = set(
        zone_access.sort_values("access_distance_m", ascending=False).head(18)["zone_id"].astype(str)
    )
    chosen: list[dict] = []
    used: set[tuple[str, str]] = set()

    def take(frame: pd.DataFrame, n: int, stratum: str) -> None:
        for row in frame.itertuples(index=False):
            key = (row.o_zone_id, row.d_zone_id)
            if key in used:
                continue
            used.add(key)
            chosen.append({"o_zone_id": key[0], "d_zone_id": key[1], "selection_stratum": stratum,
                           "person_trips_midday_od": float(row.person_trips_midday_od)})
            if sum(x["selection_stratum"] == stratum for x in chosen) >= n:
                break

    take(hb, 12, "top_hbw_midday_demand")
    take(hb[hb["o_zone_id"].isin(corridor_zones) | hb["d_zone_id"].isin(corridor_zones)], 12, "gps_observation_corridor_zone")
    take(hb[hb["o_zone_id"].isin(stress_zones) | hb["d_zone_id"].isin(stress_zones)], 12, "long_drive_access_stress_zone")
    if len(chosen) < 36:
        take(hb, 36 - len(chosen), "deterministic_demand_fill")
    panel = pd.DataFrame(chosen[:36])
    panel.insert(0, "od_id", [f"panel_od_{i:03d}" for i in range(1, len(panel) + 1)])
    panel["purpose"] = "HBW"
    panel["person_cohort"] = "regional_HBW_transfer_not_microdata"
    panel["selection_frozen_before_overlay"] = True
    panel["selection_rule_version"] = "panel36_v1"
    return panel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--frozen-panel", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    run = (args.run_dir or root / "runs" / RUN_ID).resolve()
    derived, reports = run / "derived", run / "reports"
    derived.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    osm_path = root / "raw" / "osm" / RUN_ID / "central_boston_highways.osm"
    nodes, walk_graph, bike_graph, osm_stats = build_osm_graphs(osm_path)
    walk_snap = make_snapper(nodes, walk_graph)
    bike_snap = make_snapper(nodes, bike_graph)

    zones = pd.read_csv(root / "database" / "zones" / "zone.csv", dtype={"zone_id": str})
    zones = zones[zones["zone_level"].eq("fine")].copy()
    zone_lookup = zones.set_index("zone_id")[["centroid_lon", "centroid_lat"]]
    zone_access = pd.read_csv(root / "database" / "zones" / "zone_access.csv", dtype={"zone_id": str, "access_node_id": str})
    regional_od = pd.read_csv(derived / "regional_od_h3.csv", dtype={"o_zone_id": str, "d_zone_id": str})
    obs = pd.read_csv(derived / "gps_service_observation.csv", dtype=str)
    overlay = pd.read_csv(derived / "service_overlay.csv", dtype={"route_id": str, "direction_id": str, "from_stop_id": str, "to_stop_id": str})
    transit_dir = root / "database" / "transit"
    stops = pd.read_csv(transit_dir / "stops.txt", dtype=str)
    for col in ("stop_lat", "stop_lon"):
        stops[col] = pd.to_numeric(stops[col], errors="coerce")
    trips = pd.read_csv(transit_dir / "trips.txt", dtype=str)
    routes = pd.read_csv(transit_dir / "routes.txt", dtype=str)
    calendar = pd.read_csv(transit_dir / "calendar.txt", dtype=str)
    exceptions = pd.read_csv(transit_dir / "calendar_dates.txt", dtype=str)
    stop_times = pd.read_csv(transit_dir / "stop_times.txt", dtype=str)
    transfers = pd.read_csv(transit_dir / "transfers.txt", dtype=str)
    active = active_services(calendar, exceptions, SERVICE_DATE)
    trip_meta = trips[trips["service_id"].isin(active)][["trip_id", "route_id", "direction_id", "service_id", "block_id"]].merge(
        routes[["route_id", "route_type", "network_id"]], on="route_id", how="left", validate="many_to_one"
    )
    active_st = stop_times[stop_times["trip_id"].isin(set(trip_meta["trip_id"]))].copy()
    connection_kwargs = {
        "search_end": SEARCH_END,
        "earliest_departure": min(DEPARTURES),
        "max_access_seconds": MAX_WALK_SECONDS,
    }
    connections_s1 = build_connections_semantic(active_st, trip_meta, None, **connection_kwargs)
    connections_s2 = build_connections_semantic(active_st, trip_meta, overlay, **connection_kwargs)
    # Independent overlay-off reconstruction for the real Srestore loop.
    connections_srestore = build_connections_semantic(active_st.copy(), trip_meta.copy(), None, **connection_kwargs)
    gtfs_zip = root / "raw" / "gtfs" / "mdb-437_20260918.zip"
    with zipfile.ZipFile(gtfs_zip) as zf:
        pathways = pd.read_csv(zf.open("pathways.txt"), dtype=str) if "pathways.txt" in zf.namelist() else None
        fare_files = sorted(n for n in zf.namelist() if n.startswith("fare_"))
    transfer_policy = TransferPolicy.build(stops, transfers, pathways)
    fare_policy = FarePolicy.from_gtfs_zip(gtfs_zip)

    frozen_panel = args.frozen_panel
    if frozen_panel is None:
        candidate = root / "runs" / RUN_ID / "derived" / "validation_panel.csv"
        frozen_panel = candidate if candidate.exists() else None
    if frozen_panel is not None:
        panel = pd.read_csv(frozen_panel, dtype={"o_zone_id": str, "d_zone_id": str})
        panel_source = str(frozen_panel)
        if len(panel) != 36 or panel.duplicated(["o_zone_id", "d_zone_id"]).any():
            raise RuntimeError("Frozen panel must contain the original 36 unique OD pairs")
    else:
        panel = panel_selection(regional_od, zone_access, obs, stops, set(zones["zone_id"]))
        hb_total = float(regional_od.loc[regional_od["purpose"].eq("HBW"), "person_trips_midday_od"].sum())
        panel["share_of_hbw_midday_demand"] = panel["person_trips_midday_od"] / hb_total
        panel_source = "deterministic_panel_selection"
    panel.to_csv(derived / "validation_panel.csv", index=False)

    # Snap all usable GTFS stops once.  A stop farther than 250 m from the OSM
    # walking graph remains unknown rather than being silently connected.
    stop_snap: dict[str, tuple[int, float]] = {}
    node_to_stops: dict[int, list[str]] = defaultdict(list)
    for row in stops.itertuples(index=False):
        if pd.isna(row.stop_lon) or pd.isna(row.stop_lat):
            continue
        if not (BOUND[0] <= float(row.stop_lon) <= BOUND[2] and BOUND[1] <= float(row.stop_lat) <= BOUND[3]):
            continue
        node, dist = walk_snap(float(row.stop_lon), float(row.stop_lat))
        if dist <= 250:
            stop_snap[str(row.stop_id)] = (node, dist)
            node_to_stops[node].append(str(row.stop_id))

    gmns_nodes = pd.read_csv(root / "database" / "network" / "gmns" / "node.csv", dtype={"node_id": str})
    links = pd.read_csv(root / "database" / "network" / "gmns" / "link.csv", dtype={"link_id": str, "from_node_id": str, "to_node_id": str})
    drive = nx.DiGraph()
    for row in links[links["is_physical"].astype(str).str.lower().eq("true")].itertuples(index=False):
        sec = float(row.vdf_fftt) * 60
        old = drive.get_edge_data(row.from_node_id, row.to_node_id)
        if old is None or sec < old["seconds"]:
            drive.add_edge(row.from_node_id, row.to_node_id, seconds=sec, distance_m=float(row.vdf_length_mi) * 1609.344, link_id=row.link_id)
    access_lookup = zone_access.set_index("zone_id")

    skim_rows: list[dict] = []
    leg_rows: list[dict] = []
    path_cache: dict[tuple[str, str], tuple] = {}
    walk_cutoff_cache: dict[str, dict[int, float]] = {}
    for od in panel.itertuples(index=False):
        oz, dz = zone_lookup.loc[od.o_zone_id], zone_lookup.loc[od.d_zone_id]
        o_walk_node, o_walk_snap_m = walk_snap(float(oz.centroid_lon), float(oz.centroid_lat))
        d_walk_node, d_walk_snap_m = walk_snap(float(dz.centroid_lon), float(dz.centroid_lat))
        o_bike_node, o_bike_snap_m = bike_snap(float(oz.centroid_lon), float(oz.centroid_lat))
        d_bike_node, d_bike_snap_m = bike_snap(float(dz.centroid_lon), float(dz.centroid_lat))
        key = (od.o_zone_id, od.d_zone_id)
        if key not in path_cache:
            w = path_summary(walk_graph, o_walk_node, d_walk_node)
            b = path_summary(bike_graph, o_bike_node, d_bike_node)
            try:
                oacc, dacc = access_lookup.loc[od.o_zone_id], access_lookup.loc[od.d_zone_id]
                dpath = nx.shortest_path(drive, str(oacc.access_node_id), str(dacc.access_node_id), weight="seconds")
                dsec = sum(float(drive[u][v]["seconds"]) for u, v in zip(dpath[:-1], dpath[1:]))
                ddist = sum(float(drive[u][v]["distance_m"]) for u, v in zip(dpath[:-1], dpath[1:]))
                drive_result = ("available", dsec, ddist, dpath)
            except (KeyError, nx.NetworkXNoPath, nx.NodeNotFound):
                drive_result = ("unknown_buffer_or_network_disconnected", math.nan, math.nan, [])
            path_cache[key] = (w, b, drive_result)
        walk_result, bike_result, drive_result = path_cache[key]

        if od.o_zone_id not in walk_cutoff_cache:
            walk_cutoff_cache[od.o_zone_id] = nx.single_source_dijkstra_path_length(
                walk_graph, o_walk_node, cutoff=MAX_WALK_SECONDS, weight="seconds"
            )
        if od.d_zone_id not in walk_cutoff_cache:
            walk_cutoff_cache[od.d_zone_id] = nx.single_source_dijkstra_path_length(
                walk_graph, d_walk_node, cutoff=MAX_WALK_SECONDS, weight="seconds"
            )
        o_lengths = walk_cutoff_cache[od.o_zone_id]
        d_lengths = walk_cutoff_cache[od.d_zone_id]
        access_times = {
            stop: o_walk_snap_m / WALK_MPS + o_lengths[node] + snap_m / WALK_MPS
            for stop, (node, snap_m) in stop_snap.items() if node in o_lengths
        }
        egress_times = {
            stop: d_walk_snap_m / WALK_MPS + d_lengths[node] + snap_m / WALK_MPS
            for stop, (node, snap_m) in stop_snap.items() if node in d_lengths
        }

        for depart in DEPARTURES:
            for scenario, connections in (
                ("S1_planned_service", connections_s1),
                ("S2_exploratory_gps_overlay", connections_s2),
                ("Srestore_overlay_off_recomputed", connections_srestore),
            ):
                common = {
                    "od_id": od.od_id, "o_zone_id": od.o_zone_id, "d_zone_id": od.d_zone_id,
                    "person_cohort": od.person_cohort, "purpose": od.purpose, "departure_time": clock(depart),
                    "departure_seconds": depart, "service_date": SERVICE_DATE, "scenario_id": scenario,
                    "network_version": "gmns_plus_21_boston_116447ab_analysis_v1",
                    "feed_id": "mdb-437", "feed_version": "Fall 2026",
                }
                for mode, result, snap_sum in (
                    ("walk", walk_result, o_walk_snap_m + d_walk_snap_m),
                    ("bike", bike_result, o_bike_snap_m + d_bike_snap_m),
                    ("drive", drive_result, 0.0),
                ):
                    status, sec, dist, path = result
                    total_sec = sec + (snap_sum / (WALK_MPS if mode == "walk" else BIKE_MPS) if status == "available" else 0)
                    skim_rows.append({**common, "mode": mode, "availability_status": status,
                                      "walk_min": total_sec / 60 if mode == "walk" and status == "available" else 0,
                                      "wait_min": 0, "in_vehicle_min": total_sec / 60 if mode in {"bike", "drive"} and status == "available" else 0,
                                      "total_min": total_sec / 60 if status == "available" else math.nan,
                                      "distance_m": dist + snap_sum if status == "available" else math.nan,
                                      "fare_usd": 0 if mode in {"walk", "bike"} else math.nan,
                                      "fare_price_year": None, "transfers": 0, "path_id": hashlib.sha1((mode + repr(path)).encode()).hexdigest()[:16],
                                      "cost_status": "REAL_NETWORK_SHORTEST_PATH_FREE_FLOW_NO_PARKING_COST" if mode == "drive" else "REAL_OSM_ALLOWED_WAY_SHORTEST_PATH",
                                      "overlay_applied": False})
                tr = transit_route_semantic(
                    depart,
                    connections,
                    access_times,
                    egress_times,
                    transfer_policy,
                    fare_policy,
                    search_end=SEARCH_END,
                )
                # Scenario is deliberately excluded so independently reconstructed
                # S1 and Srestore paths have directly comparable identities.
                path_signature = [
                    (
                        item["kind"],
                        item.get("stop"),
                        getattr(item.get("connection"), "trip_id", None),
                        getattr(item.get("connection"), "from_seq", None),
                        getattr(item.get("connection"), "dep", None),
                        getattr(item.get("connection"), "arr", None),
                    )
                    for item in tr.get("chain", [])
                ]
                path_id = hashlib.sha1((od.od_id + clock(depart) + repr(path_signature)).encode()).hexdigest()[:16]
                skim_rows.append({**common, "mode": "transit_walk_access", "availability_status": tr["status"],
                                  "walk_min": tr.get("walk_seconds", math.nan) / 60, "wait_min": tr.get("wait_seconds", math.nan) / 60,
                                  "in_vehicle_min": tr.get("in_vehicle_seconds", math.nan) / 60,
                                  "total_min": tr.get("total_seconds", math.nan) / 60, "distance_m": math.nan,
                                  "fare_usd": tr.get("fare_usd", math.nan), "fare_price_year": 2026,
                                  "transfers": tr.get("transfers", math.nan), "path_id": path_id,
                                  "cost_status": tr.get("fare_rule", "schedule_search_no_path"),
                                  "fare_medium": tr.get("fare_medium"),
                                  "fare_product_ids": tr.get("fare_product_ids"),
                                  "fare_trace": tr.get("fare_trace"),
                                  "status_evidence": tr.get("status_evidence"),
                                  "access_walk_min": tr.get("access_walk_seconds", math.nan) / 60,
                                  "transfer_walk_min": tr.get("transfer_walk_seconds", math.nan) / 60,
                                  "egress_walk_min": tr.get("egress_walk_seconds", math.nan) / 60,
                                  "boardings": tr.get("boardings", math.nan),
                                  "ride_segment_count": tr.get("ride_segment_count", 0),
                                  "time_account_error_seconds": tr.get("time_account_error_seconds", math.nan),
                                  "overlay_applied": bool(tr.get("overlay_parameter_ids")),
                                  "overlay_parameter_ids": ";".join(tr.get("overlay_parameter_ids", []))})
                previous_ride_connection = None
                chain_items = tr.get("chain", [])
                for seq, item in enumerate(chain_items, start=1):
                    leg = {"path_id": path_id, "leg_sequence": seq, "leg_type": item["kind"],
                           "to_stop_id": item["stop"], "arrival_seconds": item["at"], "arrival_time": clock(int(item["at"])),
                           "scenario_id": scenario, "od_id": od.od_id, "departure_time": clock(depart)}
                    if item["kind"] == "ride":
                        c = item["connection"]
                        same_vehicle_dwell = float(item.get("same_vehicle_dwell_seconds", 0.0))
                        leg.update({"from_stop_id": c.from_stop, "trip_id": c.trip_id, "route_id": c.route_id,
                                    "network_id": c.network_id,
                                    "direction_id": c.direction_id, "board_time": clock(c.dep), "alight_time": clock(c.arr),
                                    "physical_seconds": c.arr - c.dep + same_vehicle_dwell,
                                    "wait_seconds": item["wait_seconds"],
                                    "new_boarding": item.get("new_boarding"),
                                    "in_seat_continuation": item.get("in_seat_continuation"),
                                    "transfer_rule_row": item.get("transfer_rule_row"),
                                    "pickup_type": c.pickup_type,
                                    "drop_off_type": c.drop_off_type,
                                    "overlay_parameter_id": c.overlay_parameter_id})
                        previous_ride_connection = c
                    else:
                        leg.update({"from_stop_id": item.get("from_stop"), "physical_seconds": item.get("seconds")})
                    leg_rows.append(leg)
                if tr.get("status") == "available":
                    leg_rows.append({
                        "path_id": path_id, "leg_sequence": len(chain_items) + 1, "leg_type": "egress_walk",
                        "from_stop_id": chain_items[-1]["stop"] if chain_items else None, "to_stop_id": None,
                        "arrival_seconds": tr["arrival"], "arrival_time": clock(tr["arrival"]),
                        "physical_seconds": tr["egress_walk_seconds"], "scenario_id": scenario,
                        "od_id": od.od_id, "departure_time": clock(depart),
                    })

    skims = pd.DataFrame(skim_rows)
    skims.to_csv(derived / "mode_specific_od_costs.csv", index=False)
    pd.DataFrame(leg_rows).to_csv(derived / "itinerary_legs.csv", index=False)

    compare_keys = ["od_id", "departure_time", "mode"]
    compare_columns = [
        "availability_status", "path_id", "walk_min", "wait_min", "in_vehicle_min",
        "total_min", "fare_usd", "transfers", "overlay_applied", "overlay_parameter_ids",
    ]
    s1_compare = skims[skims["scenario_id"].eq("S1_planned_service")][compare_keys + compare_columns]
    restore_compare = skims[skims["scenario_id"].eq("Srestore_overlay_off_recomputed")][compare_keys + compare_columns]

    def compare_restore(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
        merged = left.merge(right, on=compare_keys, how="outer", suffixes=("_s1", "_restore"), indicator=True)
        merged["key_present_both"] = merged["_merge"].eq("both")
        mismatch_columns: list[pd.Series] = []
        for column in compare_columns:
            a = merged[f"{column}_s1"]
            b = merged[f"{column}_restore"]
            if column in {"walk_min", "wait_min", "in_vehicle_min", "total_min", "fare_usd", "transfers"}:
                equal = np.isclose(pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce"), atol=1e-10, rtol=0, equal_nan=True)
                equal = pd.Series(equal, index=merged.index)
            else:
                equal = a.fillna("<NA>").astype(str).eq(b.fillna("<NA>").astype(str))
            merged[f"{column}_equal"] = equal
            mismatch_columns.append(~equal)
        merged["mismatch_count"] = sum(series.astype(int) for series in mismatch_columns) + (~merged["key_present_both"]).astype(int)
        return merged

    restore_check = compare_restore(s1_compare, restore_compare)
    restore_check.to_csv(derived / "srestore_skim_comparison.csv", index=False)
    negative = restore_compare.copy()
    target = negative[
        negative["mode"].eq("transit_walk_access")
        & negative["availability_status"].eq("available")
    ].index[0]
    negative.loc[target, "total_min"] = float(negative.loc[target, "total_min"]) + 1.0 / 60.0
    negative_check = compare_restore(s1_compare, negative)
    negative_summary = {
        "control": "one_second_added_to_first_available_restore_transit_total_min_copy_only",
        "detected_mismatch_rows": int((negative_check["mismatch_count"] > 0).sum()),
        "detected": bool((negative_check["mismatch_count"] > 0).any()),
        "production_outputs_modified_by_control": False,
    }
    (reports / "srestore_negative_control.json").write_text(json.dumps(negative_summary, indent=2), encoding="utf-8")

    summary = {
        "run_id": run.name, "panel_od_count": len(panel), "departure_count": len(DEPARTURES),
        "skim_rows": len(skims), "panel_hbw_midday_demand_share": float(panel["share_of_hbw_midday_demand"].sum()),
        "panel_source": panel_source,
        "panel_object_and_weights_preserved": True,
        "service_date": SERVICE_DATE, "departures": [clock(x) for x in DEPARTURES],
        "active_service_ids": len(active), "active_trips": len(trip_meta),
        "s1_connections": len(connections_s1), "s2_connections": len(connections_s2),
        "srestore_connections": len(connections_srestore),
        "snapped_gtfs_stops_within_250m": len(stop_snap), "fare_v2_files_in_source_zip": fare_files,
        "transfer_policy": transfer_policy.stats,
        "fare_policy": fare_policy.stats,
        "available_transit_rows_by_scenario": {
            str(k): int(v)
            for k, v in skims[
                skims["mode"].eq("transit_walk_access")
                & skims["availability_status"].eq("available")
            ].groupby("scenario_id").size().items()
        },
        "available_transit_rows_without_ride": int(
            (
                skims["mode"].eq("transit_walk_access")
                & skims["availability_status"].eq("available")
                & pd.to_numeric(skims["ride_segment_count"], errors="coerce").fillna(0).eq(0)
            ).sum()
        ),
        "srestore_skim_mismatch_rows": int((restore_check["mismatch_count"] > 0).sum()),
        "srestore_negative_control": negative_summary,
        "access_egress_snap_policy": "zone_centroid_to_osm_snap_plus_osm_path_plus_gtfs_stop_to_osm_snap_for_both_WK_and_TW",
        "osm": osm_stats, "osm_source_sha256": sha256(osm_path),
        "gtfs_source_sha256": sha256(gtfs_zip),
        "limitations": [
            "Panel is a predeclared bounded pilot, not representative of all Boston travel.",
            "Drive is free-flow and excludes parking/terminal cost because those inputs are unavailable.",
            "Transit is a bounded scheduled-service adapter, not a full general-purpose journey planner.",
            "Fare uses selected-itinerary GTFS Fares v2 adult CharlieCard generic rules; unsupported fare legs remain unknown.",
            "S2 overlay uses the same short midday GPS sample and is exploratory, not independently validated.",
        ],
    }
    (reports / "multimodal_panel_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
