"""Pure accepted absolute-attribute utility and nested-choice functions.

Definitions below are extracted without mathematical changes from the locked
public source. The old 36-pair runnable wrapper is retained only in that
read-only source; this module supports the new input-driven adapter.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

MODES = ("DA", "S2", "S3", "TW")
NEST = {"DA": "Auto", "S2": "Auto", "S3": "Auto", "TW": "Transit"}

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))

def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def number(value, label):
    if value in (None, ""):
        raise ValueError(f"missing {label}")
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"nonfinite {label}")
    return x

def logsumexp(values):
    if not values:
        raise ValueError("empty logsumexp")
    peak = max(values)
    return peak + math.log(sum(math.exp(x - peak) for x in values))

def nested_probabilities(utilities: dict[str, float], scales: dict[str, float]):
    if not utilities:
        raise ValueError("no feasible alternatives")
    if any(not (0 < mu <= 1) for mu in scales.values()):
        raise ValueError("nested scales must be in (0,1] under this convention")
    by_nest = defaultdict(list)
    for mode, utility in utilities.items():
        if mode not in NEST or not math.isfinite(utility):
            raise ValueError("unknown alternative or nonfinite utility")
        by_nest[NEST[mode]].append((mode, utility))
    inclusive = {nest: scales[nest] * logsumexp([u / scales[nest] for _, u in items]) for nest, items in by_nest.items()}
    root = logsumexp(list(inclusive.values()))
    result = {}
    for nest, items in by_nest.items():
        denom = logsumexp([u / scales[nest] for _, u in items])
        for mode, utility in items:
            result[mode] = math.exp(inclusive[nest] - root) * math.exp(utility / scales[nest] - denom)
    return result, inclusive, root

def utility_components(mode: str, source: dict, spec: dict):
    if source["availability_status"] != "available":
        raise ValueError("unknown_or_unavailable_path:" + source["availability_status"])
    beta = spec["beta"]
    ivtt = number(source["in_vehicle_min"], "ivtt")
    if mode == "TW":
        if number(source["ride_segment_count"], "ride_segment_count") < 1 or number(source["boardings"], "boardings") < 1:
            raise ValueError("no_permitted_ride")
        walk = number(source["walk_min"], "walk_min")
        wait = number(source["wait_min"], "wait_min")
        ovtt = walk + wait
        if int(number(source["fare_price_year"], "fare_price_year")) != 2026:
            raise ValueError("unknown_fare_price_year")
        fare = number(source["fare_usd"], "selected_itinerary_fare")
        cost = fare * spec["fare_2026_to_2010_cpi_u_factor"]
        distance_m = ""
        context = "fare_CPI_converted_once"
    else:
        ovtt = 0.0  # Explicit zero-terminal-time research context.
        distance_m = number(source["distance_m"], "drive_distance_m")
        cost = distance_m / 1609.344 * spec["auto_operating_cost_2010_usd_per_mile_assumed"]
        context = "zero_terminal_parking_toll_sensitivity"
    terms = {
        "constant": spec["constant"][mode],
        "sufficient_vehicle": spec["sufficient_vehicle_term"][mode],
        "ivtt": beta["ivtt_min"] * ivtt,
        "ovtt": beta["ovtt_min"] * ovtt,
        "cost": beta["cost_2010_usd"] * cost,
    }
    return terms, {"ivtt_min": ivtt, "ovtt_min": ovtt, "cost_2010_usd": cost, "distance_m": distance_m, "context": context}
