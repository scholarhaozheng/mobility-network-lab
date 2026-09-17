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
    args = parser.parse_args()

    try:
        if args.command == "catalog-city-match":
            report = run_catalog_city_workflow(
                args.catalog, args.cities, args.output
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0
    except (FileNotFoundError, FileExistsError, NotADirectoryError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
