"""Extract bounded weekday AM GTFS ride, headway, and exact fare relationships."""
from __future__ import annotations

import csv
import io
import json
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / "hong_kong_gmns_pilot_r1"
OUT = HERE / "phase_b"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ziprows(z, name):
    return csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig", newline=""))


def write(name, data, columns=None):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns or list(data[0]))
        w.writeheader()
        w.writerows(data)


def seconds(s):
    if not s:
        return None
    try:
        h, m, sec = map(int, s.split(":"))
        return h * 3600 + m * 60 + sec
    except (ValueError, TypeError):
        return None


pilot_stops = {r["stop_id"] for r in rows(R1 / "instance/transit_stops.csv")}
service_rows = rows(R1 / "instance/transit_route_service.csv")
pilot_routes = {r["route_id"] for r in service_rows}
route_info = {r["route_id"]: r for r in service_rows}
zip_path = R1 / "raw/td_gtfs.zip"

with zipfile.ZipFile(zip_path) as z:
    monday = {r["service_id"] for r in ziprows(z, "calendar.txt") if r["monday"] == "1"}
    trip_route = {r["trip_id"]: (r["route_id"], r["service_id"])
                  for r in ziprows(z, "trips.txt")
                  if r["route_id"] in pilot_routes and r["service_id"] in monday}
    headways = defaultdict(list)
    for r in ziprows(z, "frequencies.txt"):
        tid = r["trip_id"]
        if tid not in trip_route:
            continue
        st, en, hw = seconds(r["start_time"]), seconds(r["end_time"]), int(r["headway_secs"])
        if st is not None and en is not None and st < 9 * 3600 and en > 8 * 3600 and hw > 0:
            headways[trip_route[tid][0]].append(hw)

    ride = defaultdict(list)
    direct_ride = defaultdict(list)
    raw_trip_rows = timed_anchor_count = interpolated_stop_count = pilot_trip_count = 0

    def flush(tid, triprows):
        if tid not in trip_route or not triprows:
            return 0, 0, 0
        anchors = [(i, seconds(r["departure_time"]) or seconds(r["arrival_time"]))
                   for i, r in enumerate(triprows)
                   if seconds(r["departure_time"]) is not None or seconds(r["arrival_time"]) is not None]
        anchors = [(i, t) for i, t in anchors if t is not None]
        if len(anchors) < 2:
            return 0, len(anchors), 0
        times = [None] * len(triprows)
        for i, t in anchors:
            times[i] = t
        for (i, ti), (j, tj) in zip(anchors, anchors[1:]):
            if tj < ti or j <= i:
                continue
            for k in range(i + 1, j):
                times[k] = ti + (tj - ti) * (k - i) / (j - i)
        stops = [(r["stop_id"], times[i], i, times[i] not in [t for _, t in anchors])
                 for i, r in enumerate(triprows) if r["stop_id"] in pilot_stops and times[i] is not None]
        if len(stops) < 2:
            return 0, len(anchors), 0
        route = trip_route[tid][0]
        used = 0
        for (sa, ta, _, _), (sb, tb, _, _) in zip(stops, stops[1:]):
            if sa == sb or not (7.5 * 3600 <= ta <= 9.5 * 3600):
                continue
            duration = (tb - ta) / 60
            if 0 < duration <= 90:
                ride[route, sa, sb].append(duration)
                used += 1
        for i, (sa, ta, _, _) in enumerate(stops):
            if not (7.5 * 3600 <= ta <= 9.5 * 3600):
                continue
            for sb, tb, _, _ in stops[i + 1:]:
                duration = (tb - ta) / 60
                if sa != sb and 0 < duration <= 90:
                    direct_ride[route, sa, sb].append(duration)
        return used, len(anchors), sum(times[i] is not None and not triprows[i]["arrival_time"]
                                         and r["stop_id"] in pilot_stops for i, r in enumerate(triprows))

    current, group = None, []
    for r in ziprows(z, "stop_times.txt"):
        tid = r["trip_id"]
        if tid != current:
            if current is not None:
                used, anchors, interpolated = flush(current, group)
                raw_trip_rows += len(group)
                timed_anchor_count += anchors
                interpolated_stop_count += interpolated
                pilot_trip_count += used > 0
            current, group = tid, []
        if tid in trip_route:
            group.append(r)
    if current is not None:
        used, anchors, interpolated = flush(current, group)
        raw_trip_rows += len(group)
        timed_anchor_count += anchors
        interpolated_stop_count += interpolated
        pilot_trip_count += used > 0

    # Exact GTFS fare-rule endpoints; route minima remain a labeled fallback.
    fare_price = {}
    for r in ziprows(z, "fare_attributes.txt"):
        if r["currency_type"] == "HKD":
            try:
                fare_price[r["fare_id"]] = float(r["price"])
            except ValueError:
                pass
    fare_pair = {}
    for r in ziprows(z, "fare_rules.txt"):
        if (r["route_id"] in pilot_routes and r["origin_id"] in pilot_stops
                and r["destination_id"] in pilot_stops and r["fare_id"] in fare_price):
            key = (r["route_id"], r["origin_id"], r["destination_id"])
            val = fare_price[r["fare_id"]]
            if key not in fare_pair or val < fare_pair[key][0]:
                fare_pair[key] = (val, r["fare_id"])

route_fare_min = defaultdict(lambda: float("inf"))
for r in rows(R1 / "instance/transit_fares.csv"):
    try:
        route_fare_min[r["route_id"]] = min(route_fare_min[r["route_id"]], float(r["price_hkd"]))
    except ValueError:
        pass
ride_rows = []
for (route, sa, sb), durations in sorted(ride.items()):
    if (route, sa, sb) in fare_pair:
        fare, fid = fare_pair[route, sa, sb]
        fgrade = "GTFS_EXACT_STOP_PAIR_FARE"
    else:
        fare, fid = route_fare_min.get(route, float("inf")), ""
        fgrade = "GTFS_ROUTE_MIN_FARE_FALLBACK"
    if fare == float("inf"):
        continue
    ride_rows.append(dict(route_id=route, from_stop_id=sa, to_stop_id=sb,
                          median_in_vehicle_min=statistics.median(durations),
                          timetable_samples=len(durations),
                          time_grade="GTFS_TIMED_WITH_SEQUENCE_INTERPOLATION_WHEN_NEEDED",
                          fare_hkd=fare, fare_id=fid, fare_grade=fgrade,
                          route_type=route_info[route]["route_type"],
                          agency_id=route_info[route]["agency_id"]))
if not ride_rows:
    raise RuntimeError("no pilot GTFS ride edges")
write("gtfs_pilot_ride_edges.csv", ride_rows)
direct_rows = []
for (route, sa, sb), durations in sorted(direct_ride.items()):
    if (route, sa, sb) in fare_pair:
        fare, fid = fare_pair[route, sa, sb]
        grade = "GTFS_EXACT_STOP_PAIR_FARE"
    else:
        fare, fid = route_fare_min.get(route, float("inf")), ""
        grade = "GTFS_ROUTE_MIN_FARE_FALLBACK"
    if fare == float("inf"):
        continue
    direct_rows.append(dict(route_id=route, from_stop_id=sa, to_stop_id=sb,
                            median_in_vehicle_min=statistics.median(durations),
                            timetable_samples=len(durations), fare_hkd=fare,
                            fare_id=fid, fare_grade=grade,
                            time_grade="SAME_GTFS_TRIP_PATTERN_WITH_SEQUENCE_INTERPOLATION_WHEN_NEEDED"))
write("gtfs_direct_ride_pairs.csv", direct_rows)
headway_rows = []
for route in sorted(pilot_routes):
    values = headways.get(route, [])
    if values:
        hw = statistics.median(values)
        grade = "GTFS_AM_FREQUENCY_WINDOW"
    else:
        vals = [float(r["headway_min_s"]) for r in service_rows
                if r["route_id"] == route and r["headway_min_s"]]
        hw = statistics.median(vals) if vals else 1800.0
        grade = "GTFS_ROUTE_GENERAL_HEADWAY_FALLBACK" if vals else "ENGINEERING_30MIN_FALLBACK"
    headway_rows.append(dict(route_id=route, headway_s=hw,
                             expected_wait_min=hw / 120,
                             grade=grade, am_frequency_samples=len(values)))
write("gtfs_route_headway.csv", headway_rows)
fare_rows = [dict(route_id=route, from_stop_id=sa, to_stop_id=sb,
                  fare_hkd=v[0], fare_id=v[1]) for (route, sa, sb), v in sorted(fare_pair.items())]
write("gtfs_exact_pilot_fares.csv", fare_rows,
      columns=["route_id", "from_stop_id", "to_stop_id", "fare_hkd", "fare_id"])
report = dict(
    service_definition="generic Monday, 08:00-09:00; current GTFS calendar, not an observed service day",
    pilot_routes=len(pilot_routes), monday_service_ids=len(monday), selected_trips=len(trip_route),
    timed_trip_stop_rows=raw_trip_rows, timed_anchor_count=timed_anchor_count,
    interpolated_pilot_stop_count=interpolated_stop_count,
    trips_with_pilot_am_ride_edges=pilot_trip_count,
    directed_ride_edges=len(ride_rows), same_trip_direct_ride_pairs=len(direct_rows),
    routes_with_am_frequency=len(headways),
    exact_pilot_fare_pairs=len(fare_rows),
    ride_fare_grade_counts=dict(Counter(r["fare_grade"] for r in ride_rows)),
    limitation="Untimed intermediate stop arrivals use stop-sequence interpolation between published anchors; departure reliability, crowding, and fare transfers are not observed.",
)
(OUT / "GTFS_SERVICE_QUALITY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
