"""Area-conserving assignment of official building features to R1 SSG zones.

Building use and floor area are deliberately engineering proxies: the CSDI
layer publishes footprint, block type, names, and some storey counts, but no
observed employment or complete gross-floor-area measure in this layer.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / "hong_kong_gmns_pilot_r1" / "instance"
OUT = HERE / "phase_b"
OUT.mkdir(exist_ok=True)


def csvrows(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def inring(p, ring):
    x, y = p
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y):
            cross = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if cross > x:
                inside = not inside
    return inside


def inpolygon(p, rings):
    return sum(inring(p, ring) for ring in rings) % 2 == 1


def centroid(ring):
    twice, sx, sy = 0.0, 0.0, 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        cross = a[0] * b[1] - b[0] * a[1]
        twice += cross
        sx += (a[0] + b[0]) * cross
        sy += (a[1] + b[1]) * cross
    if abs(twice) < 1e-16:
        return tuple(ring[0][:2])
    return sx / (3 * twice), sy / (3 * twice)


zgeo = json.loads((R1 / "zone_geometry.geojson").read_text(encoding="utf-8"))
polygons = []
for feature in zgeo["features"]:
    rings = feature["geometry"]["coordinates"]
    xs = [p[0] for ring in rings for p in ring]
    ys = [p[1] for ring in rings for p in ring]
    polygons.append((str(feature["properties"]["zone_id"]), rings,
                     (min(xs), min(ys), max(xs), max(ys))))

buildings = json.loads((HERE / "raw/buildings_pilot.json").read_text(encoding="utf-8"))["features"]
population = {r["zone_id"]: r for r in csvrows(R1 / "zone_population_households.csv")}
totals = defaultdict(lambda: defaultdict(float))
allocation = []
outside = 0
for b in buildings:
    a = b["attributes"]
    rings = b["geometry"].get("rings", [])
    if not rings:
        outside += 1
        continue
    ring = max(rings, key=lambda q: len(q))
    point = centroid(ring)
    if not inpolygon(point, rings):
        point = tuple(ring[0][:2])
    matches = [zid for zid, zrings, bbox in polygons
               if bbox[0] - 1e-10 <= point[0] <= bbox[2] + 1e-10
               and bbox[1] - 1e-10 <= point[1] <= bbox[3] + 1e-10
               and inpolygon(point, zrings)]
    zid = matches[0] if len(matches) == 1 else ""
    area = float(a.get("Shape__Area") or 0)
    storeys = a.get("Storeys")
    levels = max(1, int(storeys)) if storeys is not None else 1
    floor_proxy = area * levels
    name = (a.get("BuildingNameEN") or "").upper()
    if any(k in name for k in ("MTR", "STATION", "TERMINAL", "PIER", "FERRY")):
        kind = "transport_name_keyword_proxy"
    elif any(k in name for k in ("SCHOOL", "COLLEGE", "MUSEUM", "HOSPITAL", "CHURCH", "LIBRARY", "GOVERNMENT", "COURT")):
        kind = "institution_name_keyword_proxy"
    elif any(k in name for k in ("HOTEL", "MALL", "MARKET", "SHOPPING", "PLAZA", "COMMERCIAL")):
        kind = "commercial_name_keyword_proxy"
    else:
        kind = "mixed_or_unknown_use_proxy"
    totals[zid]["building_count"] += 1
    totals[zid]["footprint_area_m2"] += area
    totals[zid]["storey_weighted_area_proxy_m2"] += floor_proxy
    totals[zid][kind] += floor_proxy
    totals[zid]["missing_storeys_count"] += storeys is None
    allocation.append(dict(objectid=a["OBJECTID"], zone_id=zid or "OUTSIDE_OR_UNASSIGNED",
                           centroid_lon=point[0], centroid_lat=point[1],
                           building_block_type=a.get("BuildingBlockType"),
                           footprint_area_m2=area, storeys=storeys if storeys is not None else "",
                           floor_area_proxy_m2=floor_proxy, category=kind,
                           allocation_status="one_zone_centroid" if zid else "outside_or_unassigned"))
write("building_allocation_private.csv", allocation)

zone_rows = []
for zid in sorted(population, key=int):
    p = population[zid]
    t = totals[zid]
    popn = float(p["population_allocated"])
    households = float(p["households_allocated"] or 0)
    attraction = (t["storey_weighted_area_proxy_m2"] / 100.0) + 0.2 * popn
    zone_rows.append(dict(
        zone_id=zid, population=popn, households=households,
        working_population_if_available="", residential_activity=households,
        commercial_activity=t["commercial_name_keyword_proxy"],
        institutional_activity=t["institution_name_keyword_proxy"],
        transport_activity=t["transport_name_keyword_proxy"],
        mixed_use_activity=t["mixed_or_unknown_use_proxy"],
        employment_or_attraction_proxy=attraction,
        building_count=int(t["building_count"]),
        footprint_area_m2=t["footprint_area_m2"],
        storey_weighted_area_proxy_m2=t["storey_weighted_area_proxy_m2"],
        missing_storeys_count=int(t["missing_storeys_count"]),
        source_coverage="2021_SSG_area_allocation;2026_CSDI_building_centroid_assignment",
        proxy_status="NO_OBSERVED_EMPLOYMENT_OR_GFA;name_keyword_use_and_storey_area_proxy",
    ))
write("zone_activity_r2.csv", zone_rows)

source_total_area = sum(x["footprint_area_m2"] for x in allocation)
allocated_area = sum(totals[z]["footprint_area_m2"] for z in population)
outside_area = totals[""]["footprint_area_m2"]
source_proxy = sum(x["floor_area_proxy_m2"] for x in allocation)
allocated_proxy = sum(totals[z]["storey_weighted_area_proxy_m2"] for z in population)
outside_proxy = totals[""]["storey_weighted_area_proxy_m2"]
audit = dict(
    source_building_features=len(buildings), feature_rows=len(allocation),
    assigned_features=sum(r["zone_id"] != "OUTSIDE_OR_UNASSIGNED" for r in allocation),
    outside_or_unassigned_features=sum(r["zone_id"] == "OUTSIDE_OR_UNASSIGNED" for r in allocation) + outside,
    source_footprint_area_m2=source_total_area, assigned_footprint_area_m2=allocated_area,
    outside_or_unassigned_footprint_area_m2=outside_area,
    footprint_conservation_residual_m2=source_total_area - allocated_area - outside_area,
    source_storey_area_proxy_m2=source_proxy, assigned_storey_area_proxy_m2=allocated_proxy,
    outside_or_unassigned_storey_area_proxy_m2=outside_proxy,
    proxy_conservation_residual_m2=source_proxy - allocated_proxy - outside_proxy,
    population_area_allocated=sum(float(r["population"]) for r in zone_rows),
    households_area_allocated=sum(float(r["households"]) for r in zone_rows),
    buildings_with_missing_storeys=sum(r["missing_storeys_count"] for r in zone_rows) + int(totals[""]["missing_storeys_count"]),
    status="PASS" if abs(source_total_area - allocated_area - outside_area) < 1e-6
    and abs(source_proxy - allocated_proxy - outside_proxy) < 1e-4 else "FAIL",
    interpretation="Source feature totals are conserved across centroid-assigned and outside/unassigned ledgers; footprint*storeys is a proxy, not published GFA or employment.",
)
(OUT / "ACTIVITY_ALLOCATION_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
write("ACTIVITY_SOURCE_REGISTER.csv", [
    dict(source_id="R1_CSDI_SSG_2021", use="population_households_area_allocated",
         status="OFFICIAL_DERIVED", limitation="within-zone uniform density assumption; no workers/employment"),
    dict(source_id="CSDI_BUILDING_2026_PILOT_QUERY", use="footprint_storeys_name_proxy",
         status="OFFICIAL_INPUT_ENGINEERING_PROXY", limitation="no published GFA or use-specific employment; centroid assignment"),
    dict(source_id="PLAND_LUHK_2024", use="broad_land_use_context_only",
         status="LINKED_NOT_ALLOCATED", limitation="provider warns against detailed calculation"),
])
print(json.dumps(audit, indent=2))
if audit["status"] != "PASS":
    raise SystemExit(1)
