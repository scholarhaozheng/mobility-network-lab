"""Selected OMDV exact municipality/country matcher.

Copyright (c) 2026 Hao Zheng.
Licensed under the repository MIT License by explicit maintainer authorization.
Source: src/omdv/geospatial/city_matching.py
Source SHA-256: feefc70a12ff5e1bdd4bc847e2c2bff69eac727d3056161187b7ee5ad895c599
Adaptation: attribution header only; computational semantics are unchanged.
"""

from __future__ import annotations

import pandas as pd


MATCHED_STATUS = "matched_exact_municipality_country"
UNMATCHED_MISSING_MUNICIPALITY = "unmatched_missing_municipality"
UNMATCHED_MISSING_COUNTRY = "unmatched_missing_country"
UNMATCHED_OTHER = "unmatched_other"

MATCH_OUTPUT_COLUMNS = [
    "feed_id",
    "feed_type",
    "status",
    "provider",
    "municipality",
    "country_iso2",
    "city_id",
    "match_method",
    "match_confidence",
    "match_status",
]
OPTIONAL_MATCH_OUTPUT_COLUMNS = ["metadata_completeness_raw", "is_official"]


def normalize_name(name: object) -> str:
    """Normalize city/provider names for simple matching."""
    if pd.isna(name):
        return ""
    return " ".join(str(name).lower().strip().replace("-", " ").replace("_", " ").split())


def match_feeds_to_cities_by_name(
    feeds: pd.DataFrame,
    cities: pd.DataFrame,
    feed_city_col: str = "municipality",
    city_name_col: str = "city_name",
    country_col_feed: str = "country_iso2",
    country_col_city: str = "country_iso2",
) -> pd.DataFrame:
    """Assign feeds to cities using exact country + normalized municipality/city name.

    This is intentionally simple and transparent for v0.1. Later versions should add
    bbox/polygon matching and manual validation for major cities.
    """
    feeds2 = feeds.copy()
    cities2 = cities.copy()

    feeds2["_feed_row_id"] = range(len(feeds2))
    feeds2["_match_name"] = _series_or_empty(feeds2, feed_city_col).map(normalize_name)
    feeds2["_country_match"] = _series_or_empty(feeds2, country_col_feed).map(_normalize_country)

    cities2["_match_name"] = _series_or_empty(cities2, city_name_col).map(normalize_name)
    cities2["_country_match"] = _series_or_empty(cities2, country_col_city).map(_normalize_country)
    city_keys = (
        cities2[["city_id", city_name_col, "_country_match", "_match_name"]]
        .dropna(subset=["city_id"])
        .drop_duplicates(subset=["_country_match", "_match_name"])
    )

    out = feeds2.merge(
        city_keys,
        on=["_country_match", "_match_name"],
        how="left",
        suffixes=("", "_city"),
    )

    missing_municipality = out["_match_name"] == ""
    missing_country = out["_country_match"] == ""
    matched = out["city_id"].notna()

    out["match_status"] = UNMATCHED_OTHER
    out.loc[missing_country, "match_status"] = UNMATCHED_MISSING_COUNTRY
    out.loc[missing_municipality, "match_status"] = UNMATCHED_MISSING_MUNICIPALITY
    out.loc[matched, "match_status"] = MATCHED_STATUS
    out["match_method"] = pd.NA
    out["match_confidence"] = pd.NA
    out.loc[matched, "match_method"] = "exact_municipality_country"
    out.loc[matched, "match_confidence"] = "medium"

    for col in ["feed_id", "feed_type", "status", "provider", "municipality", "country_iso2"]:
        if col not in out.columns:
            out[col] = pd.NA
    out["country_iso2"] = out["_country_match"].replace({"": pd.NA})

    optional_cols = [col for col in OPTIONAL_MATCH_OUTPUT_COLUMNS if col in out.columns]
    return out[MATCH_OUTPUT_COLUMNS + optional_cols]


def summarize_matches(matched: pd.DataFrame, city_id_col: str = "city_id") -> pd.DataFrame:
    """Summarize matched feeds at city level."""
    if "match_status" in matched.columns:
        matched = matched[matched["match_status"] == MATCHED_STATUS].copy()
    else:
        matched = matched[matched[city_id_col].notna()].copy()

    if matched.empty:
        return pd.DataFrame(columns=[city_id_col])

    g = matched.groupby(city_id_col)
    out = g.size().rename("feed_count_total").to_frame()
    for feed_type in ["gtfs", "gtfs_rt", "gbfs"]:
        out[f"feed_count_{feed_type}"] = g["feed_type"].apply(lambda s: (s == feed_type).sum())
    out["active_feed_share"] = g["status"].apply(lambda s: (s.fillna("active") == "active").mean())
    if "is_official" in matched.columns:
        out["official_feed_share"] = g["is_official"].apply(lambda s: s.fillna(False).mean())
    else:
        out["official_feed_share"] = 0.0
    if "metadata_completeness_raw" in matched.columns:
        out["metadata_completeness_score"] = g["metadata_completeness_raw"].mean()
    else:
        out["metadata_completeness_score"] = 0.0
    return out.reset_index()


def _series_or_empty(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(pd.NA, index=df.index)


def _normalize_country(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    if len(text) == 2 and text.isalpha():
        return text
    return ""
