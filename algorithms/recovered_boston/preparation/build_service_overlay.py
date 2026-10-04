"""Build a strictly scoped, disabled-by-default MBTA GPS service overlay.

Only pre-qualified GPS segments are considered.  A usable observation requires
two distinct STOPPED_AT events that can be ordered on the exact GTFS trip.  The
output is diagnostic evidence from a short midday sample, not an AM-period
calibration target and not an independent validation sample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


RUN_ID = "behavior_feedback_r1"
QUALITY_RUN = "boston_quality_r1_20260922"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gtfs_seconds(value: str) -> int:
    h, m, s = (int(x) for x in value.split(":"))
    return h * 3600 + m * 60 + s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-dir", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    run = (args.run_dir or root / "runs" / RUN_ID).resolve()
    derived = run / "derived"
    reports = run / "reports"
    derived.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    obs_dir = root / "database" / "observations"
    quality_dir = obs_dir / "quality_runs" / QUALITY_RUN
    quality_path = quality_dir / "gps_segment_quality.csv"
    progress_path = quality_dir / "gps_point_progress.csv"
    segment_path = obs_dir / "gps_segments.csv"
    trips_path = root / "database" / "transit" / "trips.txt"
    stop_times_path = root / "database" / "transit" / "stop_times.txt"

    quality = pd.read_csv(quality_path, dtype={"route_id": str})
    eligible = quality[quality["observation_eligible"].astype(str).str.lower().eq("true")].copy()
    segments = pd.read_csv(segment_path, dtype={"route_id": str, "trip_id": str})
    eligible = eligible.merge(
        segments[["segment_id", "trip_id"]], on="segment_id", how="left", validate="one_to_one"
    )
    progress = pd.read_csv(progress_path, dtype={"reported_stop_id": str})
    progress = progress[progress["segment_id"].isin(eligible["segment_id"])].copy()
    progress["timestamp"] = pd.to_datetime(progress["timestamp"], utc=True)
    trips = pd.read_csv(trips_path, dtype=str)
    stop_times = pd.read_csv(stop_times_path, dtype=str)
    trip_meta = trips.set_index("trip_id")[["route_id", "direction_id", "service_id"]].to_dict("index")

    observations: list[dict] = []
    exclusions: list[dict] = []
    for seg in eligible.itertuples(index=False):
        seg_points = progress[progress["segment_id"].eq(seg.segment_id)].sort_values("point_seq")
        stopped = seg_points[
            seg_points["current_status"].eq("STOPPED_AT")
            & seg_points["reported_stop_id"].notna()
            & ~seg_points["reported_stop_id"].eq("")
        ].copy()
        if stopped.empty:
            exclusions.append({"segment_id": seg.segment_id, "reason": "no_stopped_at_events"})
            continue
        # One event per contiguous run of the same reported stop.
        stopped["event_group"] = stopped["reported_stop_id"].ne(stopped["reported_stop_id"].shift()).cumsum()
        events = stopped.groupby("event_group", as_index=False).agg(
            stop_id=("reported_stop_id", "first"),
            first_timestamp=("timestamp", "min"),
            last_timestamp=("timestamp", "max"),
            first_point_seq=("point_seq", "min"),
            last_point_seq=("point_seq", "max"),
            mean_acquisition_lag_seconds=("acquisition_lag_seconds", "mean"),
            event_point_count=("point_seq", "size"),
        )
        schedule = stop_times[stop_times["trip_id"].eq(str(seg.trip_id))].copy()
        schedule["stop_sequence_num"] = pd.to_numeric(schedule["stop_sequence"], errors="coerce")
        schedule = schedule.sort_values("stop_sequence_num")
        schedule_lookup = schedule.drop_duplicates("stop_id").set_index("stop_id")
        found = 0
        for k in range(len(events) - 1):
            a = events.iloc[k]
            b = events.iloc[k + 1]
            if int(a.first_point_seq) == 1:
                exclusions.append(
                    {
                        "segment_id": seg.segment_id,
                        "reason": "pair_touches_start_censored_first_event",
                        "from_stop_id": a.stop_id,
                        "to_stop_id": b.stop_id,
                    }
                )
                continue
            if a.stop_id == b.stop_id or a.stop_id not in schedule_lookup.index or b.stop_id not in schedule_lookup.index:
                continue
            sa = schedule_lookup.loc[a.stop_id]
            sb = schedule_lookup.loc[b.stop_id]
            if float(sb.stop_sequence_num) <= float(sa.stop_sequence_num):
                continue
            scheduled_seconds = gtfs_seconds(sb.arrival_time) - gtfs_seconds(sa.departure_time)
            observed_seconds = (b.first_timestamp - a.last_timestamp).total_seconds()
            if scheduled_seconds <= 0 or observed_seconds <= 0:
                continue
            found += 1
            meta = trip_meta.get(str(seg.trip_id), {})
            observations.append(
                {
                    "observation_id": f"gps-stop-pair:{seg.segment_id}:{int(a.last_point_seq)}-{int(b.first_point_seq)}",
                    "segment_id": seg.segment_id,
                    "route_id": str(seg.route_id),
                    "trip_id": str(seg.trip_id),
                    "direction_id": meta.get("direction_id"),
                    "service_id": meta.get("service_id"),
                    "from_stop_id": a.stop_id,
                    "to_stop_id": b.stop_id,
                    "from_stop_sequence": int(float(sa.stop_sequence_num)),
                    "to_stop_sequence": int(float(sb.stop_sequence_num)),
                    "observed_from_time_utc": a.last_timestamp.isoformat(),
                    "observed_to_time_utc": b.first_timestamp.isoformat(),
                    "observed_elapsed_seconds": observed_seconds,
                    "scheduled_elapsed_seconds": scheduled_seconds,
                    "observed_to_scheduled_factor": observed_seconds / scheduled_seconds,
                    "mean_acquisition_lag_seconds": float((a.mean_acquisition_lag_seconds + b.mean_acquisition_lag_seconds) / 2),
                    "from_event_point_count": int(a.event_point_count),
                    "to_event_point_count": int(b.event_point_count),
                    "sample_date_local": "2026-09-21",
                    "sample_period": "midday_short_live_window",
                    "scenario_period_overlap": False,
                    "quality_status": "EXPLORATORY_EXACT_TRIP_STOP_PAIR_FROM_PREQUALIFIED_SEGMENT",
                    "validation_status": "NOT_INDEPENDENT_VALIDATION",
                    "application_default": "disabled",
                    "source_quality_run": QUALITY_RUN,
                    "run_id": RUN_ID,
                }
            )
        if found == 0:
            exclusions.append({"segment_id": seg.segment_id, "reason": "no_two_ordered_distinct_gtfs_stops"})

    obs = pd.DataFrame(observations)
    if obs.empty:
        raise RuntimeError("No exact-trip stop-pair observations were produced")
    obs.to_csv(derived / "gps_service_observation.csv", index=False)
    pd.DataFrame(exclusions).to_csv(reports / "gps_service_observation_exclusions.csv", index=False)

    overlay = (
        obs.groupby(["route_id", "direction_id", "from_stop_id", "to_stop_id"], dropna=False)
        .agg(
            observation_count=("observation_id", "size"),
            mean_observed_seconds=("observed_elapsed_seconds", "mean"),
            mean_scheduled_seconds=("scheduled_elapsed_seconds", "mean"),
            mean_factor=("observed_to_scheduled_factor", "mean"),
            min_factor=("observed_to_scheduled_factor", "min"),
            max_factor=("observed_to_scheduled_factor", "max"),
        )
        .reset_index()
    )
    overlay["enabled_by_default"] = False
    overlay.insert(0, "parameter_id", [f"gps_midday_stop_pair_{i:02d}" for i in range(1, len(overlay) + 1)])
    overlay["allowed_application"] = "S2_EXPLORATORY_EXACT_ROUTE_DIRECTION_STOP_INTERVAL_ONLY"
    overlay["forbidden_application"] = "AM_CALIBRATION_OR_NETWORKWIDE_GENERALIZATION"
    overlay["run_id"] = RUN_ID
    overlay.to_csv(derived / "service_overlay.csv", index=False)

    local_hours = pd.to_datetime(obs["observed_from_time_utc"], utc=True).dt.tz_convert("America/New_York")
    manifest = {
        "run_id": RUN_ID,
        "enabled_by_default": False,
        "qualified_segments_input": int(len(eligible)),
        "usable_stop_pair_observations": int(len(obs)),
        "unique_service_intervals": int(len(overlay)),
        "observed_local_hour_min": int(local_hours.dt.hour.min()),
        "observed_local_hour_max": int(local_hours.dt.hour.max()),
        "scenario_period": "07:00-09:00 local",
        "scenario_period_overlap": False,
        "interpretation": "Short midday observations are exploratory and non-independent; overlay is disabled unless explicitly enabled for a sensitivity run.",
        "scope_rule": "Exact route_id + direction_id + ordered stop interval only; never generalized networkwide.",
        "source_hashes": {
            str(p.relative_to(root)): sha256(p)
            for p in (quality_path, progress_path, segment_path, trips_path, stop_times_path)
        },
    }
    (reports / "service_overlay_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
