#!/usr/bin/env python3
"""Run bounded Mobility Computation Lab data tools on user-supplied local files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))

from mobilitylab.data.catalog_city_workflow import run_catalog_city_workflow
from mobilitylab.data.open_mobility import (
    AmbiguousCityError,
    process_gtfs_zip,
    query_city_evidence,
)


DEFAULT_CITY_TABLE = ROOT / "docs" / "data" / "open-mobility" / "city_evidence.csv"
DEFAULT_RELATION_TABLE = (
    ROOT / "docs" / "data" / "open-mobility" / "source_content_city.csv"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    workflow = subparsers.add_parser(
        "catalog-city-match",
        help="Normalize a catalog and exactly match its municipality/country fields to a city table.",
    )
    workflow.add_argument("--catalog", required=True, help="Input feed-catalog CSV.")
    workflow.add_argument("--cities", required=True, help="Input external-city CSV.")
    workflow.add_argument(
        "--output", required=True, help="New or empty output directory."
    )
    query = subparsers.add_parser(
        "query-city",
        help="Query the accepted public city evidence by stable ID or name plus country.",
    )
    key = query.add_mutually_exclusive_group(required=True)
    key.add_argument("--city-id", help="Exact stable city ID (preferred).")
    key.add_argument("--name", help="Exact city name; requires --country.")
    query.add_argument("--country", help="ISO alpha-2 or alpha-3 country code.")
    query.add_argument(
        "--all-matches",
        action="store_true",
        help="Return every same-name match instead of treating duplicates as ambiguous.",
    )
    query.add_argument(
        "--include-relations",
        action="store_true",
        help="Include actual source-record → content-SHA → city rows.",
    )
    query.add_argument("--relation-limit", type=int, default=25)
    query.add_argument("--city-table", default=str(DEFAULT_CITY_TABLE))
    query.add_argument("--relation-table", default=str(DEFAULT_RELATION_TABLE))

    gtfs = subparsers.add_parser(
        "process-gtfs",
        help="Run the authorized OMDV-derived content parser on one local GTFS ZIP.",
    )
    gtfs.add_argument("--zip", required=True, help="User-supplied local GTFS ZIP.")
    gtfs.add_argument("--output", required=True, help="New or empty output directory.")
    args = parser.parse_args()

    try:
        if args.command == "catalog-city-match":
            report = run_catalog_city_workflow(
                args.catalog, args.cities, args.output
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0
        if args.command == "query-city":
            report = query_city_evidence(
                args.city_table,
                args.relation_table,
                city_id=args.city_id,
                city_name=args.name,
                country=args.country,
                allow_multiple=args.all_matches,
                include_relations=args.include_relations,
                relation_limit=args.relation_limit,
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 1 if report["status"] == "not_found" else 0
        if args.command == "process-gtfs":
            report = process_gtfs_zip(args.zip, args.output)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if report["parse_status"] == "parsed" else 1
    except AmbiguousCityError as exc:
        print(f"AmbiguousCityError: {exc}", file=sys.stderr)
        return 3
    except (FileNotFoundError, FileExistsError, NotADirectoryError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
