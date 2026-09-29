#!/usr/bin/env python3
"""Run reproducible queries against the behavior-feedback public database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


QUERIES = {
    "trace": "SELECT * FROM end_to_end_feedback_trace",
    "response": """SELECT od_id,departure_time,scenario_id,total_min,mu_transit_sensitivity,probability
                   FROM scenario_transit_response
                   WHERE od_id='panel_od_019' AND departure_time='12:30:00' AND mu_transit_sensitivity=1.0
                   ORDER BY scenario_id""",
    "unavailable": """SELECT od_id,departure_time,mode,availability_status
                      FROM od_multimodal_skims
                      WHERE availability_status<>'available'
                      ORDER BY od_id,departure_time,scenario_id,mode LIMIT 20""",
    "transfers": """SELECT od_id,departure_time,scenario_id,total_min,transfers,path_id
                    FROM od_multimodal_skims
                    WHERE mode='transit_walk_access' AND transfers>0
                    ORDER BY transfers DESC,total_min LIMIT 20""",
    "parameters": """SELECT parameter_id,source_id,page_table_row,symbol,value,unit,status
                     FROM parameter_registry ORDER BY parameter_id""",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", choices=QUERIES)
    parser.add_argument("--database", type=Path, default=Path(__file__).with_name("boston_central_public.sqlite"))
    args = parser.parse_args()
    connection = sqlite3.connect(args.database)
    cursor = connection.execute(QUERIES[args.query])
    names = [x[0] for x in cursor.description]
    print("\t".join(names))
    for row in cursor:
        print("\t".join("" if value is None else str(value) for value in row))
    connection.close()


if __name__ == "__main__":
    main()
