"""Read-only stream of the frozen R1 KMZ for accepted pilot road attributes."""
from __future__ import annotations

import csv
import html
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / "hong_kong_gmns_pilot_r1"
accepted = {
    row["source_kml_id"]
    for row in csv.DictReader((R1 / "instance/source_link_crosswalk.csv").open(encoding="utf-8"))
}
pat = re.compile(r"<td>\s*([^<>]+?)\s*</td>\s*<td>\s*([^<>]*?)\s*</td>", re.I)
tag = "{http://www.opengis.net/kml/2.2}"
records = []
with zipfile.ZipFile(R1 / "raw/road_centerline.kmz") as z, z.open("doc.kml") as f:
    ctx = ET.iterparse(f, events=("start", "end"))
    _, root = next(ctx)
    for event, elem in ctx:
        if event != "end" or elem.tag != tag + "Placemark":
            continue
        kid = elem.attrib.get("id", "")
        if kid in accepted:
            desc = elem.findtext(tag + "description") or ""
            props = {
                html.unescape(k).strip(): html.unescape(v).strip()
                for k, v in pat.findall(desc)
            }
            records.append(
                {
                    "source_kml_id": kid,
                    "route_id": props.get("ROUTE_ID", ""),
                    "route_num": props.get("ROUTE_NUM", ""),
                    "exit_num": props.get("EXIT_NUM", ""),
                    "elevation": props.get("ELEVATION", ""),
                    "street_code": props.get("ST_CODE", ""),
                    "street_name": props.get("STREET_ENAME", ""),
                    "remarks": props.get("REMARKS", ""),
                }
            )
        root.clear()

if len(records) != len(accepted):
    raise RuntimeError(f"accepted KML-ID coverage {len(records)} != {len(accepted)}")
records.sort(key=lambda r: int(r["route_id"]))
with (HERE / "raw/pilot_source_road_fields.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(records[0]))
    w.writeheader()
    w.writerows(records)
summary = {
    "accepted_source_features": len(records),
    "route_num_counts": dict(Counter(x["route_num"] for x in records)),
    "elevation_counts": dict(Counter(x["elevation"] for x in records)),
    "street_code_ranges": dict(Counter(x["street_code"][:1] for x in records)),
    "lane_count_field_in_official_centerline_spec": False,
    "source": "frozen R1 Transport Department road_centerline.kmz; FGDB/GML specification audited separately",
}
(HERE / "raw/pilot_source_road_fields_summary.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, indent=2))
