"""Bounded catalog-to-city workflow built from selected OMDV implementations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from mobilitylab.omdv.geospatial.city_matching import (
    MATCHED_STATUS,
    match_feeds_to_cities_by_name,
    normalize_name,
    summarize_matches,
)
from mobilitylab.omdv.geospatial.external_city_universe import (
    read_external_city_universe,
)
from mobilitylab.omdv.ingest.catalog_summary import (
    summarize_clean_catalog,
    write_clean_catalog_summaries,
)
from mobilitylab.omdv.ingest.mobility_database import (
    clean_mobility_database_catalog,
    inspect_mobility_database_catalog,
    write_catalog_schema_audit,
)

AMBIGUOUS_CITY_KEY = "ambiguous_city_key"


def run_catalog_city_workflow(
    catalog_csv: str | Path,
    cities_csv: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Normalize a feed catalog, standardize cities, match, and report quality.

    The operation is deliberately local and bounded. It does not download feeds,
    parse GTFS archives, probe realtime endpoints, perform fuzzy/geospatial
    matching, or build a transport network.
    """
    catalog_path = _require_csv(catalog_csv, "catalog")
    cities_path = _require_csv(cities_csv, "cities")
    outdir = Path(output_dir)
    _prepare_output_directory(outdir)

    normalized = clean_mobility_database_catalog(catalog_path).reset_index(drop=True)
    cities = read_external_city_universe(cities_path).reset_index(drop=True)
    match_cities = cities.rename(columns={"external_city_id": "city_id"}).copy()

    match_cities["_match_name"] = match_cities["city_name"].map(normalize_name)
    match_cities["_match_country"] = (
        match_cities["country_iso2"].astype("string").fillna("").str.strip().str.upper()
    )
    eligible_city_key = (
        match_cities["_match_name"].ne("") & match_cities["_match_country"].ne("")
    )
    key_counts = (
        match_cities.loc[eligible_city_key]
        .groupby(["_match_country", "_match_name"], dropna=False)
        .size()
    )
    ambiguous_keys = set(key_counts[key_counts > 1].index.tolist())
    city_keys = list(
        zip(match_cities["_match_country"], match_cities["_match_name"], strict=True)
    )
    ambiguous_city_row = pd.Series(
        [key in ambiguous_keys for key in city_keys], index=match_cities.index
    )
    matchable = match_cities.loc[eligible_city_key & ~ambiguous_city_row].copy()

    matches = match_feeds_to_cities_by_name(normalized, matchable).reset_index(drop=True)
    feed_names = normalized["municipality"].map(normalize_name)
    feed_countries = (
        normalized["country_iso2"].astype("string").fillna("").str.strip().str.upper()
    )
    feed_keys = list(zip(feed_countries, feed_names, strict=True))
    ambiguous_feed_row = pd.Series(
        [key in ambiguous_keys for key in feed_keys], index=matches.index
    )
    if ambiguous_feed_row.any():
        matches.loc[ambiguous_feed_row, "city_id"] = pd.NA
        matches.loc[ambiguous_feed_row, "match_method"] = pd.NA
        matches.loc[ambiguous_feed_row, "match_confidence"] = pd.NA
        matches.loc[ambiguous_feed_row, "match_status"] = AMBIGUOUS_CITY_KEY

    city_summary = summarize_matches(matches)
    catalog_summaries = summarize_clean_catalog(normalized)
    schema_audit = inspect_mobility_database_catalog(catalog_path)

    normalized_path = outdir / "normalized_catalog.csv"
    cities_path_out = outdir / "standardized_cities.csv"
    matches_path = outdir / "feed_city_matches.csv"
    city_summary_path = outdir / "city_feed_summary.csv"
    ambiguity_path = outdir / "ambiguous_city_keys.csv"

    normalized.to_csv(normalized_path, index=False)
    cities.to_csv(cities_path_out, index=False)
    matches.to_csv(matches_path, index=False)
    city_summary.to_csv(city_summary_path, index=False)
    _ambiguity_table(match_cities, ambiguous_city_row).to_csv(ambiguity_path, index=False)

    summary_paths = write_clean_catalog_summaries(
        catalog_summaries, outdir, prefix="normalized"
    )
    audit_paths = write_catalog_schema_audit(
        schema_audit, outdir, prefix="source_catalog_schema"
    )

    data_outputs = {
        "normalized_catalog": normalized_path,
        "standardized_cities": cities_path_out,
        "feed_city_matches": matches_path,
        "city_feed_summary": city_summary_path,
        "ambiguous_city_keys": ambiguity_path,
        **{f"catalog_{name}": path for name, path in summary_paths.items()},
        **{f"schema_audit_{name}": path for name, path in audit_paths.items()},
    }
    match_counts = {
        str(status): int(count)
        for status, count in matches["match_status"].value_counts(dropna=False).items()
    }
    report: dict[str, Any] = {
        "schema_version": "mcl_catalog_city_quality_v1",
        "operation": "catalog_normalization_and_exact_city_country_matching",
        "inputs": {
            "catalog": {
                "name": catalog_path.name,
                "sha256": _sha256(catalog_path),
                "rows": int(len(normalized)),
            },
            "cities": {
                "name": cities_path.name,
                "sha256": _sha256(cities_path),
                "rows": int(len(cities)),
            },
        },
        "quality": {
            "matched_feed_records": int(
                (matches["match_status"] == MATCHED_STATUS).sum()
            ),
            "unmatched_or_ambiguous_feed_records": int(
                (matches["match_status"] != MATCHED_STATUS).sum()
            ),
            "match_status_counts": match_counts,
            "matched_city_ids": int(matches["city_id"].nunique(dropna=True)),
            "ambiguous_city_keys": int(len(ambiguous_keys)),
            "ambiguous_city_rows": int(ambiguous_city_row.sum()),
            "duplicate_external_city_id_rows": int(
                cities["external_city_id"].duplicated(keep=False).sum()
            ),
        },
        "outputs": {
            name: {
                "path": path.name,
                "rows": int(len(pd.read_csv(path))),
                "sha256": _sha256(path),
            }
            for name, path in data_outputs.items()
        },
        "matching_contract": {
            "method": "exact normalized municipality name plus two-letter country code",
            "confidence_for_matches": "medium",
            "ambiguous_keys_are_not_auto_matched": True,
            "unmatched_records_are_preserved": True,
        },
        "limitations": [
            "Named-entity city matching is not GPS map matching.",
            "No fuzzy, transliteration, polygon, or coordinate match is attempted.",
            "Catalog metadata is not proof that a feed is live or complete.",
            "This workflow does not parse GTFS ZIPs or realtime payloads.",
            "This workflow does not compile a model-ready transport network.",
        ],
    }
    (outdir / "quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def _require_csv(path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_file():
        raise FileNotFoundError(f"{label} CSV does not exist: {candidate}")
    if candidate.suffix.lower() != ".csv":
        raise ValueError(f"{label} input must be a CSV file: {candidate}")
    return candidate


def _prepare_output_directory(path: Path) -> None:
    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {path}")
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Output directory must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _ambiguity_table(
    cities: pd.DataFrame, ambiguous_rows: pd.Series
) -> pd.DataFrame:
    columns = ["city_id", "city_name", "country_iso2", "_match_country", "_match_name"]
    out = cities.loc[ambiguous_rows, columns].copy()
    return out.rename(
        columns={
            "_match_country": "normalized_country_iso2",
            "_match_name": "normalized_city_name",
        }
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

