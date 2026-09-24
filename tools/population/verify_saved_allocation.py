#!/usr/bin/env python3
"""Verify released Boston allocation arithmetic only; no download or GIS/model run."""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


EXAMPLE_SOURCE = "15000US250250101031"
EXAMPLE_ZONE = "h3r9:892a30644a3ffff"
RATES = {"HBW": 1.90, "HBSC": 0.59, "HBSR": 2.19,
         "HBPB": 2.38, "NHBW": 0.51, "NHBNW": 2.69}


def read_csv(path, required):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    return rows


def number(row, field):
    value = float(row[field])
    if not math.isfinite(value):
        raise ValueError(f"non-finite {field}")
    return value


def close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-7):
        raise ValueError(f"{label}: {actual} != {expected}")


def verify(data_dir, generation, ledger):
    stats = read_csv(data_dir / "acs_block_group_stats.csv", (
        "source_geoid", "population_estimate", "households_estimate",
        "source_area_m2", "core_area_share"))
    cross = read_csv(data_dir / "acs_block_group_h3_crosswalk.csv", (
        "source_geoid", "zone_id", "population_estimate", "households_estimate",
        "source_area_m2", "overlap_area_m2", "source_area_share",
        "allocated_population", "allocated_households"))
    zones = read_csv(data_dir / "population_or_household_by_zone.csv", (
        "zone_id", "population_estimate_area_weighted",
        "households_estimate_area_weighted", "geography_status"))
    production = read_csv(generation, (
        "zone_id", "purpose", "households_estimate_area_weighted",
        "effective_daily_production_rate_per_household", "productions_person_trips_daily"))
    outside = read_csv(ledger, (
        "source_geoid", "population_estimate", "households_estimate",
        "core_area_share", "population_outside_core_area_weighted",
        "households_outside_core_area_weighted", "external_person_trips", "external_trip_status"))

    sources = {r["source_geoid"]: r for r in stats}
    zone_map = {r["zone_id"]: r for r in zones}
    if len(sources) != len(stats) or len(zone_map) != len(zones):
        raise ValueError("duplicate source or zone ID")
    for source in sources:
        # ACS block-group GEOIDs are strings. Do not cast away leading zeroes.
        if not (source.startswith("15000US") and len(source) == 19 and source[7:].isdigit()):
            raise ValueError(f"invalid block-group GEOID: {source}")
    summed = defaultdict(lambda: [0.0, 0.0])
    seen_pairs = set()
    source_shares = defaultdict(float)
    for r in cross:
        source, zone = r["source_geoid"], r["zone_id"]
        if source not in sources or zone not in zone_map or (source, zone) in seen_pairs:
            raise ValueError(f"invalid or repeated crosswalk pair: {source}, {zone}")
        seen_pairs.add((source, zone))
        s = sources[source]
        for field in ("population_estimate", "households_estimate", "source_area_m2"):
            close(number(r, field), number(s, field), f"{source} {field}")
        share = number(r, "source_area_share")
        if not 0 < share <= 1 + 1e-8:
            raise ValueError(f"invalid area share: {source}, {zone}")
        close(share, number(r, "overlap_area_m2") / number(s, "source_area_m2"), "full-source-area share")
        pop = number(s, "population_estimate") * share
        hh = number(s, "households_estimate") * share
        close(number(r, "allocated_population"), pop, "allocated population")
        close(number(r, "allocated_households"), hh, "allocated households")
        summed[zone][0] += pop
        summed[zone][1] += hh
        source_shares[source] += share
    if set(summed) != set(zone_map) or set(sources) != set(source_shares):
        raise ValueError("source/zone coverage mismatch")
    for source, share in source_shares.items():
        if share > 1 + 1e-8:
            raise ValueError(f"source area overallocated: {source}")
    for zone, r in zone_map.items():
        if r["geography_status"] != "covered":
            raise ValueError(f"uncovered zone cannot be treated as zero: {zone}")
        close(number(r, "population_estimate_area_weighted"), summed[zone][0], "zone population")
        close(number(r, "households_estimate_area_weighted"), summed[zone][1], "zone households")
    if len(production) != len(zones) * len(RATES):
        raise ValueError("generation zone-purpose coverage mismatch")
    seen_generation = set()
    for r in production:
        zone, purpose = r["zone_id"], r["purpose"]
        if zone not in zone_map or purpose not in RATES or (zone, purpose) in seen_generation:
            raise ValueError(f"invalid or repeated generation key: {zone}, {purpose}")
        seen_generation.add((zone, purpose))
        hh = summed[zone][1]
        close(number(r, "households_estimate_area_weighted"), hh, "generation households")
        close(number(r, "effective_daily_production_rate_per_household"), RATES[purpose], "purpose rate")
        close(number(r, "productions_person_trips_daily"), hh * RATES[purpose], "person-trip production")
    if len(outside) != len(sources) or len({r["source_geoid"] for r in outside}) != len(sources):
        raise ValueError("outside-core ledger coverage mismatch")
    for r in outside:
        source = r["source_geoid"]
        if source not in sources or r["external_person_trips"].strip():
            raise ValueError("ledger source invalid or external trip mass falsely supplied")
        if r["external_trip_status"] != "UNKNOWN_NOT_ZERO_NO_REGIONAL_OD_INPUT":
            raise ValueError("external-trip status changed")
        share = source_shares[source]
        close(number(r, "core_area_share"), share, "core share")
        close(number(r, "population_outside_core_area_weighted"),
              number(sources[source], "population_estimate") * (1 - share), "outside population")
        close(number(r, "households_outside_core_area_weighted"),
              number(sources[source], "households_estimate") * (1 - share), "outside households")
    example = next((r for r in cross if r["source_geoid"] == EXAMPLE_SOURCE and r["zone_id"] == EXAMPLE_ZONE), None)
    if example is None:
        raise ValueError("selected saved source-to-zone trace is missing")
    return {
        "check": "saved arithmetic only; not raw acquisition, GIS overlay or model reproduction",
        "source_block_groups": len(sources), "crosswalk_rows": len(cross),
        "covered_h3_zones": len(zones), "generation_rows": len(production),
        "population_in_core_persons": sum(v[0] for v in summed.values()),
        "households_in_core": sum(v[1] for v in summed.values()),
        "daily_modeled_person_trip_productions": sum(number(r, "productions_person_trips_daily") for r in production),
        "outside_core_status": "spatial remainder; external trip mass unknown, not zero",
        "example_contribution": {k: example[k] for k in ("source_geoid", "zone_id", "source_area_share", "allocated_population", "allocated_households")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Folder containing the three released ACS/allocation CSVs")
    parser.add_argument("--generation", type=Path, required=True, help="Released trip_generation_by_purpose.csv")
    parser.add_argument("--ledger", type=Path, required=True, help="Released external_flow_ledger.csv")
    parser.add_argument("--output", type=Path, help="Optional JSON report; parent folder must already exist")
    args = parser.parse_args()
    try:
        report = verify(args.data_dir, args.generation, args.ledger)
    except (OSError, ValueError, ZeroDivisionError) as exc:
        parser.exit(1, f"saved-allocation check failed: {exc}\n")
    result = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
