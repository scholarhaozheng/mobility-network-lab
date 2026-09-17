"""Inspect one local GTFS ZIP without network access or full extraction.

Adapted from Open Mobility Data Visibility (OMDV)
``scripts/analysis/parse_v25a_3_gtfs_unique_content.py`` at source commit
``b2dca4449445c474c77db72ba4c8d18947108606`` (source SHA-256
``bc4636f6eea18a66f4309d31f1e6576f50d5cbddc422e84f53709834426485cd``).
The copyright holder authorized this selected original implementation for MIT
distribution in Mobility Computation Lab on 2026-09-17.

The adapter removes repository state/SQLite dependencies, accepts a caller-
supplied ZIP path, computes its content hash, and returns the original content
metrics plus member-presence and warning records. ``stop_times.txt`` remains a
streamed pass and is not loaded into a DataFrame.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import pandas as pd


REQUIRED_MEMBERS = [
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "shapes.txt",
    "feed_info.txt",
    "frequencies.txt",
    "transfers.txt",
]


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(_clean(value))
    except (TypeError, ValueError):
        return default


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def member_lookup(archive: zipfile.ZipFile) -> dict[str, str]:
    """Return the first archive member for each lower-case base filename."""
    lookup: dict[str, str] = {}
    for name in archive.namelist():
        base = Path(name).name.lower()
        if base and base not in lookup:
            lookup[base] = name
    return lookup


def read_member_frame(
    archive: zipfile.ZipFile, lookup: dict[str, str], member: str
) -> pd.DataFrame:
    """Read a non-stop-times GTFS member with the OMDV encoding fallback."""
    actual = lookup.get(member)
    if not actual:
        return pd.DataFrame()
    last_exc: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            with archive.open(actual) as handle:
                return pd.read_csv(
                    handle, dtype=str, keep_default_na=False, encoding=encoding
                )
        except UnicodeDecodeError as exc:
            last_exc = exc
    if last_exc is not None:
        raise last_exc
    return pd.DataFrame()


def valid_coord(lat: object, lon: object) -> bool:
    lat_f = _safe_float(lat, 999.0)
    lon_f = _safe_float(lon, 999.0)
    return -90 <= lat_f <= 90 and -180 <= lon_f <= 180


def compact_counter(counter: Counter[object]) -> str:
    return json.dumps(
        {
            str(key): int(value)
            for key, value in sorted(counter.items(), key=lambda item: str(item[0]))
        },
        sort_keys=True,
    )


def route_type_to_mode(value: object) -> tuple[str, str, str]:
    """Map basic and extended GTFS route types using the accepted OMDV rules."""
    text = _clean(value)
    try:
        route_type = int(float(text))
    except ValueError:
        return "other_or_unspecified", "non_numeric_or_missing", "fallback"
    if route_type == 0 or 900 <= route_type <= 999:
        return "tram_light_rail", "gtfs_basic_or_extended_tram", "standard_or_extended"
    if route_type == 1 or 400 <= route_type <= 499:
        return "subway_metro", "gtfs_basic_or_extended_metro", "standard_or_extended"
    if route_type == 2 or 100 <= route_type <= 199:
        return "rail", "gtfs_basic_or_extended_rail", "standard_or_extended"
    if route_type == 3 or 200 <= route_type <= 299 or 700 <= route_type <= 799:
        return "bus_or_coach", "gtfs_basic_bus_or_extended_bus_coach", "standard_or_extended"
    if route_type == 4 or 1000 <= route_type <= 1099 or 1200 <= route_type <= 1299:
        return "ferry_or_water_transport", "gtfs_basic_or_extended_water", "standard_or_extended"
    if route_type == 5:
        return "cable_tram", "gtfs_basic_cable_tram", "standard"
    if route_type == 6 or 1300 <= route_type <= 1399:
        return "aerial_lift", "gtfs_basic_or_extended_aerial", "standard_or_extended"
    if route_type == 7 or 1400 <= route_type <= 1499:
        return "funicular", "gtfs_basic_or_extended_funicular", "standard_or_extended"
    if route_type == 11:
        return "trolleybus", "gtfs_basic_trolleybus", "standard"
    if route_type == 12:
        return "monorail", "gtfs_basic_monorail", "standard"
    if 1100 <= route_type <= 1199:
        return "air", "gtfs_extended_air", "extended"
    if 1500 <= route_type <= 1799:
        return "taxi_or_demand_response", "gtfs_extended_taxi_or_misc", "extended"
    return "other_or_unspecified", "observed_unmapped_extended_or_custom", "fallback"


def _presence(value: bool) -> str:
    return "provided" if value else "not_provided"


def _date_min_max(series: pd.Series) -> tuple[str, str]:
    values = [_clean(value) for value in series.tolist() if _clean(value)]
    return (min(values), max(values)) if values else ("", "")


def stream_stop_times(
    archive: zipfile.ZipFile,
    lookup: dict[str, str],
    stop_ids: set[str],
    trip_ids: set[str],
) -> dict[str, object]:
    """Count stop-time records and references in one memory-bounded pass."""
    actual = lookup.get("stop_times.txt")
    if not actual:
        return {
            "stop_time_member_size": "",
            "stop_time_row_count": 0,
            "unique_stop_ids_in_stop_times": 0,
            "unique_trip_ids_in_stop_times": 0,
            "invalid_stop_references": 0,
            "invalid_trip_references": 0,
            "stop_sequence_order_check_status": "not_provided",
        }
    info = archive.getinfo(actual)
    unique_stops: set[str] = set()
    unique_trips: set[str] = set()
    invalid_stop = 0
    invalid_trip = 0
    row_count = 0
    with archive.open(actual) as raw:
        text = io.TextIOWrapper(
            raw, encoding="utf-8-sig", errors="replace", newline=""
        )
        for row in csv.DictReader(text):
            row_count += 1
            stop_id = _clean(row.get("stop_id"))
            trip_id = _clean(row.get("trip_id"))
            if stop_id:
                unique_stops.add(stop_id)
                if stop_id not in stop_ids:
                    invalid_stop += 1
            if trip_id:
                unique_trips.add(trip_id)
                if trip_id not in trip_ids:
                    invalid_trip += 1
    return {
        "stop_time_member_size": info.file_size,
        "stop_time_row_count": row_count,
        "unique_stop_ids_in_stop_times": len(unique_stops),
        "unique_trip_ids_in_stop_times": len(unique_trips),
        "invalid_stop_references": invalid_stop,
        "invalid_trip_references": invalid_trip,
        "stop_sequence_order_check_status":
            "not_evaluated_large_stream_memory_bounded",
    }


def parse_gtfs_zip(zip_path: str | Path) -> dict[str, object]:
    """Return OMDV-derived content metrics for one existing local GTFS ZIP.

    The returned mapping contains ``metrics``, ``warnings`` and
    ``member_presence``. The input is never modified or extracted.
    """
    path = Path(zip_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    content_sha = _sha256(path)
    warnings: list[dict[str, object]] = []
    presence_rows: list[dict[str, object]] = []
    metrics: dict[str, object] = {
        "content_sha256": content_sha,
        "input_file_name": path.name,
        "input_size_bytes": path.stat().st_size,
        "parse_started_utc": _now_utc(),
        "strict_count_effect": 0,
        "adapter_source": "OMDV parse_v25a_3_gtfs_unique_content.py",
    }
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise zipfile.BadZipFile(f"testzip failed at {bad_member}")
            lookup = member_lookup(archive)
            metrics["member_count"] = len(archive.infolist())
            for member in REQUIRED_MEMBERS:
                actual = lookup.get(member)
                presence_rows.append(
                    {
                        "content_sha256": content_sha,
                        "member": member,
                        "presence": _presence(bool(actual)),
                        "file_size_bytes": archive.getinfo(actual).file_size
                        if actual
                        else "",
                        "strict_count_effect": 0,
                    }
                )

            agency = read_member_frame(archive, lookup, "agency.txt")
            stops = read_member_frame(archive, lookup, "stops.txt")
            routes = read_member_frame(archive, lookup, "routes.txt")
            trips = read_member_frame(archive, lookup, "trips.txt")
            calendar = read_member_frame(archive, lookup, "calendar.txt")
            calendar_dates = read_member_frame(
                archive, lookup, "calendar_dates.txt"
            )
            shapes = read_member_frame(archive, lookup, "shapes.txt")
            feed_info = read_member_frame(archive, lookup, "feed_info.txt")
            frequencies = read_member_frame(archive, lookup, "frequencies.txt")
            transfers = read_member_frame(archive, lookup, "transfers.txt")

            stop_ids = (
                set(stops.get("stop_id", pd.Series(dtype=str)).astype(str))
                if not stops.empty
                else set()
            )
            trip_ids = (
                set(trips.get("trip_id", pd.Series(dtype=str)).astype(str))
                if not trips.empty
                else set()
            )
            valid_mask = (
                stops.apply(
                    lambda row: valid_coord(row.get("stop_lat"), row.get("stop_lon")),
                    axis=1,
                )
                if {"stop_lat", "stop_lon"}.issubset(stops.columns)
                else pd.Series([False] * len(stops), dtype=bool)
            )
            location_counter = (
                Counter(
                    stops.get("location_type", pd.Series([""] * len(stops))).replace(
                        "", "0"
                    )
                )
                if not stops.empty
                else Counter()
            )
            coordinate_pairs: set[tuple[float, float]] = set()
            if not stops.empty and {"stop_lat", "stop_lon"}.issubset(stops.columns):
                for _, row in stops[valid_mask].iterrows():
                    coordinate_pairs.add(
                        (
                            round(_safe_float(row.get("stop_lat")), 6),
                            round(_safe_float(row.get("stop_lon")), 6),
                        )
                    )
            raw_route_types = (
                Counter(routes["route_type"].astype(str))
                if "route_type" in routes.columns
                else Counter()
            )
            broad_modes: Counter[str] = Counter()
            for value, count in raw_route_types.items():
                mode, _rule, _status = route_type_to_mode(value)
                broad_modes[mode] += int(count)

            cal_start, cal_end = (
                _date_min_max(calendar["start_date"])
                if "start_date" in calendar.columns
                else ("", "")
            )
            cal2_start, cal2_end = (
                _date_min_max(calendar["end_date"])
                if "end_date" in calendar.columns
                else ("", "")
            )
            if cal2_start and (not cal_start or cal2_start < cal_start):
                cal_start = cal2_start
            if cal2_end and cal2_end > cal_end:
                cal_end = cal2_end
            exception_start, exception_end = (
                _date_min_max(calendar_dates["date"])
                if "date" in calendar_dates.columns
                else ("", "")
            )
            feed_start = (
                _clean(feed_info["feed_start_date"].iloc[0])
                if "feed_start_date" in feed_info.columns and not feed_info.empty
                else ""
            )
            feed_end = (
                _clean(feed_info["feed_end_date"].iloc[0])
                if "feed_end_date" in feed_info.columns and not feed_info.empty
                else ""
            )
            stop_time_metrics = stream_stop_times(
                archive, lookup, stop_ids, trip_ids
            )
            if (
                stop_time_metrics["invalid_stop_references"]
                or stop_time_metrics["invalid_trip_references"]
            ):
                warnings.append(
                    {
                        "content_sha256": content_sha,
                        "warning_type": "invalid_stop_time_references",
                        "warning_count": int(
                            stop_time_metrics["invalid_stop_references"]
                        )
                        + int(stop_time_metrics["invalid_trip_references"]),
                        "strict_count_effect": 0,
                    }
                )
            metrics.update(
                {
                    "zip_valid": "yes",
                    "parse_status": "parsed",
                    "agency_presence": _presence(not agency.empty),
                    "stops_presence": _presence(not stops.empty),
                    "routes_presence": _presence(not routes.empty),
                    "trips_presence": _presence(not trips.empty),
                    "stop_times_presence": _presence("stop_times.txt" in lookup),
                    "calendar_presence": _presence(not calendar.empty),
                    "calendar_dates_presence": _presence(not calendar_dates.empty),
                    "shapes_presence": _presence(not shapes.empty),
                    "feed_info_presence": _presence(not feed_info.empty),
                    "frequencies_presence": _presence(not frequencies.empty),
                    "transfers_presence": _presence(not transfers.empty),
                    "agency_row_count": len(agency),
                    "stop_row_count": len(stops),
                    "unique_stop_id_count": len(stop_ids),
                    "valid_coordinate_rows": int(valid_mask.sum())
                    if len(valid_mask)
                    else 0,
                    "invalid_coordinate_rows": int((~valid_mask).sum())
                    if len(valid_mask)
                    else 0,
                    "valid_coordinate_proportion": round(
                        float(valid_mask.mean()), 6
                    )
                    if len(valid_mask)
                    else 0,
                    "location_type_distribution": compact_counter(location_counter),
                    "parent_station_non_empty_count": int(
                        stops.get(
                            "parent_station", pd.Series([""] * len(stops))
                        )
                        .astype(str)
                        .ne("")
                        .sum()
                    )
                    if not stops.empty
                    else 0,
                    "station_count": int(
                        stops.get(
                            "location_type", pd.Series([""] * len(stops))
                        )
                        .astype(str)
                        .eq("1")
                        .sum()
                    )
                    if not stops.empty
                    else 0,
                    "platform_or_stop_count": int(
                        stops.get(
                            "location_type", pd.Series(["0"] * len(stops))
                        )
                        .astype(str)
                        .isin(["", "0", "2"])
                        .sum()
                    )
                    if not stops.empty
                    else 0,
                    "approximate_unique_coordinate_count": len(coordinate_pairs),
                    "stop_min_lat": stops.loc[valid_mask, "stop_lat"].astype(float).min()
                    if len(valid_mask) and valid_mask.any()
                    else "",
                    "stop_max_lat": stops.loc[valid_mask, "stop_lat"].astype(float).max()
                    if len(valid_mask) and valid_mask.any()
                    else "",
                    "stop_min_lon": stops.loc[valid_mask, "stop_lon"].astype(float).min()
                    if len(valid_mask) and valid_mask.any()
                    else "",
                    "stop_max_lon": stops.loc[valid_mask, "stop_lon"].astype(float).max()
                    if len(valid_mask) and valid_mask.any()
                    else "",
                    "route_count": len(routes),
                    "raw_route_type_distribution": compact_counter(raw_route_types),
                    "distinct_raw_route_type_count": len(raw_route_types),
                    "broad_mode_distribution": compact_counter(broad_modes),
                    "distinct_broad_mode_count": len(broad_modes),
                    "trip_count": len(trips),
                    "service_id_count": trips["service_id"].nunique()
                    if "service_id" in trips.columns
                    else 0,
                    "shape_point_count": len(shapes),
                    "unique_shape_id_count": shapes["shape_id"].nunique()
                    if "shape_id" in shapes.columns
                    else 0,
                    "frequency_row_count": len(frequencies),
                    "transfer_row_count": len(transfers),
                    "calendar_earliest_date": cal_start,
                    "calendar_latest_date": cal_end,
                    "calendar_dates_earliest_exception_date": exception_start,
                    "calendar_dates_latest_exception_date": exception_end,
                    "feed_info_start_date": feed_start,
                    "feed_info_end_date": feed_end,
                    "date_evidence_source": "feed_info"
                    if feed_start or feed_end
                    else "calendar_or_calendar_dates"
                    if cal_start or exception_start
                    else "none",
                    "parse_error_message": "",
                }
            )
            metrics.update(stop_time_metrics)
    except Exception as exc:  # Parse reports retain terminal error state.
        metrics.update(
            {
                "zip_valid": "no" if isinstance(exc, zipfile.BadZipFile) else "",
                "parse_status": "parse_failed",
                "parse_error_message": f"{type(exc).__name__}: {exc}",
            }
        )
    metrics["parse_finished_utc"] = _now_utc()
    return {
        "schema_version": "mcl_gtfs_content_metrics_v1",
        "metrics": metrics,
        "warnings": warnings,
        "member_presence": presence_rows,
    }
