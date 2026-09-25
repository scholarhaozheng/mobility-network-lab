#!/usr/bin/env python3
"""Query the self-contained Central Boston public SQLite component."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path


DEFAULT_DATABASE = Path(__file__).resolve().parent / "boston_central_public.sqlite"
QUERIES = {
    "road": """SELECT l.link_id,l.from_node_id,l.to_node_id,l.geometry,l.length,l.free_speed,
                       l.capacity AS capacity_source,a.volume,a.travel_time,
                       a.capacity_model_effective_period,a.vc_ratio_model_effective_capacity
                FROM physical_network_link l
                JOIN assignment_baseline_corrected a USING(link_id)
                ORDER BY a.volume DESC,l.link_id LIMIT ?""",
    "zone": "SELECT * FROM zone_model_summary WHERE zone_id=?",
    "corridor": "SELECT * FROM corridor_link ORDER BY corridor_id,member_order",
    "gps-quality": """SELECT segment_id,selected_engine,quality_class,observation_eligible,
                              exclusion_reasons,max_lateral_error_m,max_along_route_speed_mps,
                              window_path_progress_m,observed_duration_min
                       FROM gps_segment_quality
                       WHERE disposition='selected_path_returned'
                       ORDER BY observation_eligible DESC,segment_id LIMIT ?""",
    "capacity": """SELECT c.link_id,c.capacity_source,c.lanes_source,c.capacity_period_hours,
                            c.capacity_effective_baseline_period,c.capacity_effective_stress_period,
                            a.volume,a.vc_ratio_model_effective_capacity
                     FROM link_capacity_semantics c
                     JOIN assignment_stress_corrected a USING(link_id)
                     ORDER BY a.vc_ratio_model_effective_capacity DESC,c.link_id LIMIT ?""",
    "demand": """SELECT o_zone_id,d_zone_id,vehicle_trips,o_node_id,d_node_id,assignment_eligibility
                   FROM assignment_od_crosswalk ORDER BY vehicle_trips DESC LIMIT ?""",
    "transit": """SELECT stop_id,stop_name,route_id,route_short_name,route_long_name,
                            route_type,access_node_id,access_distance_m
                     FROM transit_stop_route_relation
                     ORDER BY stop_id,route_id LIMIT ?""",
    "activity-zone": """SELECT zone_id,official_res_area_sqft_weighted,
                                   official_nonres_bld_area_sqft_weighted,
                                   productions_person_trips_daily,attractions_person_trips_daily,
                                   review_status,demand_status
                            FROM v_activity_prior_zone
                            ORDER BY attractions_person_trips_daily DESC,zone_id LIMIT ?""",
    "activity-sources": """SELECT source_id,provider,dataset,fiscal_year_coverage,
                                      status,privacy_scope
                               FROM activity_data_source_register
                               ORDER BY source_id""",
    "activity-accounting": "SELECT * FROM v_activity_prior_assignment_accounting",
    "activity-change": """SELECT * FROM v_activity_prior_zone_change
                              ORDER BY ABS(production_daily_difference_new_minus_old) DESC,zone_id LIMIT ?""",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", choices=sorted(QUERIES))
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--id", help="Exact zone ID for the zone query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        print("\n".join(sorted(QUERIES)))
        return 0
    if args.query is None:
        parser.error("provide a query name or --list")
    if args.query == "zone" and not args.id:
        parser.error("zone requires --id")
    database = args.database.resolve()
    if not database.exists():
        parser.error(f"database does not exist: {database}")
    params = (args.id,) if args.query == "zone" else ((args.limit,) if "LIMIT ?" in QUERIES[args.query] else ())
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(QUERIES[args.query], params).fetchall()
    connection.close()
    if not rows:
        print("no rows")
        return 1
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(rows[0].keys())
    writer.writerows(tuple(row) for row in rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
