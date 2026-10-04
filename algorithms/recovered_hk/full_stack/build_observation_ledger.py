"""Station AADT context and one-snapshot detector relationship; no calibration."""
import csv
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

R = Path(__file__).resolve().parent
B = R / "phase_b"
P = R / "phase_a/instance"
R1 = R.parent / "hong_kong_gmns_pilot_r1/instance"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save(name, values):
    with (B / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(values[0]))
        w.writeheader(); w.writerows(values)


links = {r["link_id"]: r for r in rows(P / "link.csv") if r["mcl_link_class"] == "physical"}
LON = 111320 * math.cos(math.radians(22.3035))
LAT = 111320


def distance(lon, lat, wkt):
    coord = [tuple(map(float, q.split())) for q in wkt[11:-1].split(",")]
    p = lon * LON, lat * LAT
    best = math.inf
    for a, b in zip(coord, coord[1:]):
        ax, ay = a[0] * LON, a[1] * LAT
        bx, by = b[0] * LON, b[1] * LAT
        dx, dy = bx - ax, by - ay
        t = max(0., min(1., ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx*dx + dy*dy))) if dx*dx + dy*dy else 0
        best = min(best, math.hypot(p[0] - ax - t*dx, p[1] - ay - t*dy))
    return best


z = zipfile.ZipFile(R / "raw/ATC_STATION_PT.kmz")
kml = ET.fromstring(z.read("doc.kml"))
ns = {"k": "http://www.opengis.net/kml/2.2"}
points = []
for placemark in kml.findall(".//k:Placemark", ns):
    desc = placemark.find("k:description", ns).text
    no = re.search(r"ATC_STATION_NO</td>.*?<td>(\d+)</td>", desc, re.S)
    coord = placemark.find(".//k:coordinates", ns)
    if not no or coord is None:
        continue
    lon, lat = map(float, coord.text.split(",")[:2])
    if 114.164 <= lon <= 114.181 and 22.295 <= lat <= 22.312:
        points.append((no.group(1), lon, lat))
assert len(points) == 81

txt = (R / "raw/ATC_2024.txt").read_text(encoding="utf-8", errors="replace")
counts = {}
for line in txt.splitlines():
    m = re.match(r"^\s*(\d{4})\s+([ABC])\s+([A-Z]{2})\s+(.+?)\s+([\d,]+)\s*\*?\s+([\d,]+)\s*\*?\s+([+-]?\d+(?:\.\d+)?)\s*$", line)
    if m:
        station, kind, roadtype, text, previous, current, change = m.groups()
        counts[station] = (kind, roadtype, text.strip(), int(previous.replace(",", "")),
                           int(current.replace(",", "")), float(change))
records = []
for no, lon, lat in points:
    near = sorted(((distance(lon, lat, l["geometry"]), lid) for lid, l in links.items()))[:2]
    c = counts.get(no)
    records.append({"atc_station_no": no, "longitude": lon, "latitude": lat,
                    "station_class": c[0] if c else "", "road_type": c[1] if c else "",
                    "station_road_description": c[2] if c else "",
                    "aadt_2023_vehicles_per_day_station": c[3] if c else "",
                    "aadt_2024_vehicles_per_day_station": c[4] if c else "",
                    "published_change_percent": c[5] if c else "",
                    "nearest_physical_link_id_spatial_only": near[0][1],
                    "nearest_link_distance_m": round(near[0][0], 3),
                    "second_link_distance_m": round(near[1][0], 3),
                    "link_relationship_status": "POINT_TO_LINK_SPATIAL_ONLY_DIRECTION_AND_GRADE_UNRESOLVED",
                    "evidence_grade": "OFFICIAL_HISTORICAL_STATION_AADT_CONTEXT" if c else "OFFICIAL_STATION_POINT_COUNT_NOT_PARSED"})
save("ATC_PILOT_STATION_CONTEXT.csv", records)

obs = rows(R1 / "detector_observations.csv")
det = []
for r in obs:
    lid = r["gmns_link_id"]
    l = links.get(lid)
    det.append({"detector_id": r["detector_id"], "snapshot_date": r["date"],
                "snapshot_period": r["period_from"] + "-" + r["period_to"],
                "lane_label": r["lane_id"], "observed_speed_kmh": r["speed_kmh"],
                "observed_volume_30s_vehicles": r["volume_30s"],
                "observed_occupancy_percent": r["occupancy_percent"],
                "direction_screened_link_id": lid,
                "model_proxy_free_speed_kmh": l["free_speed"] if l else "",
                "relationship_status": "ONE_SNAPSHOT_NOT_TEMPORALLY_COMPARABLE_TO_08_09_ASSIGNMENT" if l else "UNMATCHED",
                "evidence_grade": "OFFICIAL_SINGLE_SNAPSHOT"})
save("DETECTOR_SNAPSHOT_RELATIONSHIP.csv", det)
report = {
    "status": "DESCRIPTIVE_ONLY",
    "atc_station_points_in_bbox": len(points),
    "atc_stations_with_2023_2024_aadt": sum(c is not None for c in (counts.get(x[0]) for x in points)),
    "atc_station_point_link_relationship": "spatial candidate only; AADT is station aggregate, no directional link projection",
    "detector_snapshot_lane_rows": len(obs),
    "detector_snapshot_distinct_sites": len({x["detector_id"] for x in det}),
    "detector_mapped_distinct_sites": len({x["detector_id"] for x in det if x["direction_screened_link_id"]}),
    "detector_snapshot_time": "2026-09-26 10:24:00-10:24:30 local source time",
    "historical_development_period": "2023 ATC station AADT, descriptive reference only",
    "historical_held_out_period": "2024 ATC station AADT, descriptive reference only; no model calibration to 2023",
    "traffic_validation_status": "NOT_AVAILABLE; internal capture scenario omits external flows; annual station AADT not equivalent to one-hour directed link PCE",
    "sources": ["https://data.gov.hk/en-data/dataset/hk-td-tis_7-traffic-flow-census",
                "https://www.td.gov.hk/en/publications_and_press_releases/publications/free_publications/atc2024/index.html"]}
(B / "OBSERVATION_EVIDENCE_LEDGER.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
