"""Selected OMDV MobilityDatabase-style catalog normalizer and schema audit.

Copyright (c) 2026 Hao Zheng.
Licensed under the repository MIT License by explicit maintainer authorization.
Source: src/omdv/ingest/mobility_database.py
Source SHA-256: f0fef61239e531c9e3448bcbd38ce9fc1f14b6f38da33655b2a9a83eaa3b17b8
Adaptation: attribution header only; computational semantics are unchanged.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd


CLEAN_FEED_COLUMNS = [
    "feed_id",
    "source_catalog",
    "feed_type",
    "provider",
    "source_name",
    "name",
    "country_iso2",
    "country_name",
    "subdivision_name",
    "municipality",
    "location_name",
    "status",
    "is_official",
    "min_lat",
    "max_lat",
    "min_lon",
    "max_lon",
    "centroid_lat",
    "centroid_lon",
    "latest_url",
    "direct_download_url",
    "url",
    "license_url",
    "authentication_type",
    "last_updated",
    "latest_dataset_date",
    "extracted_on",
    "has_bbox",
    "metadata_completeness_raw",
]

KEY_AUDIT_COLUMNS = [
    "feed_id",
    "feed_type",
    "provider",
    "source_name",
    "country_iso2",
    "municipality",
    "status",
    "url",
    "last_updated",
    "min_lat",
    "max_lat",
    "min_lon",
    "max_lon",
]

COLUMN_ALIASES = {
    "feed_id": ["mdb_source_id", "source_id", "id", "feed_id", "external_id"],
    "feed_type": ["data_type", "feed_type", "type", "feed_format", "format"],
    "provider": [
        "provider",
        "operator",
        "agency",
        "organization_name",
        "entity_name",
        "source_name",
    ],
    "source_name": ["source_name", "source", "publisher", "producer", "provider"],
    "name": ["name", "feed_name"],
    "country_iso2": ["location.country_code", "country_iso2", "country_code", "country", "iso2"],
    "country_name": ["location.country", "country_name", "country_name_en"],
    "subdivision_name": ["location.subdivision_name", "subdivision_name", "subdivision"],
    "municipality": ["location.municipality", "municipality", "city"],
    "location_name": ["location.name", "location_name", "place", "area", "locality"],
    "status": ["status"],
    "is_official": ["is_official", "official"],
    "min_lat": [
        "location.bounding_box.minimum_latitude",
        "minimum_latitude",
        "min_lat",
        "bbox_min_lat",
    ],
    "max_lat": [
        "location.bounding_box.maximum_latitude",
        "maximum_latitude",
        "max_lat",
        "bbox_max_lat",
    ],
    "min_lon": [
        "location.bounding_box.minimum_longitude",
        "minimum_longitude",
        "min_lon",
        "bbox_min_lon",
    ],
    "max_lon": [
        "location.bounding_box.maximum_longitude",
        "maximum_longitude",
        "max_lon",
        "bbox_max_lon",
    ],
    "latest_url": ["urls.latest", "latest_url", "latest.url"],
    "direct_download_url": [
        "urls.direct_download_url",
        "urls.direct_download",
        "direct_download_url",
        "direct_download",
    ],
    "license_url": ["urls.license", "urls.license_url", "license_url"],
    "authentication_type": ["urls.authentication_type", "authentication_type"],
    "url": ["url", "urls.url", "feed_url"],
    "last_updated": ["last_updated", "updated_at", "modified_at", "created_at", "revision_date"],
    "latest_dataset_date": ["latest_dataset_date", "latest_dataset", "latest_fetch_date"],
    "extracted_on": ["location.bounding_box.extracted_on", "extracted_on"],
}


def _normalize_column_name(col: str) -> str:
    col = str(col).strip()
    col = col.replace("/", ".")
    col = re.sub(r"\s+", "_", col)
    return col


def _first_existing(columns: Iterable[str], candidates: list[str]) -> str | None:
    columns_set = set(columns)
    for c in candidates:
        if c in columns_set:
            return c
    # relaxed match: strip punctuation and lowercase
    relaxed = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in columns}
    for candidate in candidates:
        key = re.sub(r"[^a-z0-9]", "", candidate.lower())
        if key in relaxed:
            return relaxed[key]
    return None


def _source_column_lookup(original_columns: Iterable[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for col in original_columns:
        normalized = _normalize_column_name(col)
        out.setdefault(normalized, str(col))
    return out


def _select_column(df: pd.DataFrame, column: str) -> pd.Series:
    selected = df.loc[:, df.columns == column]
    if selected.shape[1] == 0:
        raise KeyError(column)
    return selected.iloc[:, 0]


def _clean_text_series(series: pd.Series) -> pd.Series:
    out = series.astype("string").str.strip()
    return out.replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "<NA>": pd.NA})


def _coalesce_text(*series: pd.Series) -> pd.Series:
    if not series:
        return pd.Series(dtype="string")
    out = _clean_text_series(series[0])
    for s in series[1:]:
        out = out.fillna(_clean_text_series(s))
    return out


def _normalize_status(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    s = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if s in {"", "nan", "none"}:
        return "unknown"
    if s in {"active", "published", "available", "production"}:
        return "active"
    if s in {"inactive", "deprecated", "retired", "unavailable", "closed"}:
        return "inactive"
    if s in {"development", "dev", "draft", "testing"}:
        return "development"
    return s


def normalize_feed_type(value: object) -> str:
    """Normalize feed type labels to gtfs, gtfs_rt, gbfs, or unknown."""
    if pd.isna(value):
        return "unknown"
    s = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if s in {"gtfs", "gtfs_schedule", "schedule", "static", "gtfs_static"}:
        return "gtfs"
    if s in {"gtfs_rt", "gtfs_realtime", "realtime", "gtfs_realtime_feed"}:
        return "gtfs_rt"
    if s.startswith("gtfs_rt") or s.startswith("gtfs_realtime") or "realtime" in s:
        return "gtfs_rt"
    if s == "gbfs" or s.startswith("gbfs_"):
        return "gbfs"
    return s


def clean_mobility_database_catalog(input_csv: str | Path) -> pd.DataFrame:
    """Read and normalize a Mobility Database CSV catalog.

    The Mobility Database CSV schema may evolve. This function uses aliases and relaxed
    matching so the pipeline does not break immediately when column names change.
    """
    df = pd.read_csv(input_csv)
    df = df.rename(columns={c: _normalize_column_name(c) for c in df.columns})

    out = pd.DataFrame(index=df.index)
    for target_col, candidates in COLUMN_ALIASES.items():
        match = _first_existing(df.columns, candidates)
        if match is None:
            out[target_col] = np.nan
        else:
            out[target_col] = _select_column(df, match)

    out["source_catalog"] = "mobility_database"
    text_cols = [
        "feed_id",
        "provider",
        "source_name",
        "name",
        "country_iso2",
        "country_name",
        "subdivision_name",
        "municipality",
        "location_name",
        "latest_url",
        "direct_download_url",
        "url",
        "license_url",
        "authentication_type",
        "last_updated",
        "latest_dataset_date",
        "extracted_on",
    ]
    for col in text_cols:
        out[col] = _clean_text_series(out[col])

    out["feed_type"] = out["feed_type"].map(normalize_feed_type)
    out["provider"] = _coalesce_text(out["provider"], out["source_name"], out["name"])
    out["source_name"] = _coalesce_text(out["source_name"], out["provider"], out["name"])
    out["url"] = _coalesce_text(out["url"], out["direct_download_url"], out["latest_url"])

    country_candidate = out["country_iso2"].copy()
    out["country_iso2"] = out["country_iso2"].str.upper()
    invalid_country_code = ~out["country_iso2"].str.fullmatch(r"[A-Z]{2}", na=False)
    out.loc[invalid_country_code, "country_name"] = out.loc[
        invalid_country_code, "country_name"
    ].fillna(country_candidate.loc[invalid_country_code])
    out.loc[invalid_country_code, "country_iso2"] = pd.NA

    out["status"] = out["status"].map(_normalize_status)
    out["is_official"] = out["is_official"].map(_to_bool)

    for col in ["min_lat", "max_lat", "min_lon", "max_lon"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["has_bbox"] = out[["min_lat", "max_lat", "min_lon", "max_lon"]].notna().all(axis=1)
    out["centroid_lat"] = np.where(out["has_bbox"], (out["min_lat"] + out["max_lat"]) / 2, np.nan)
    out["centroid_lon"] = np.where(out["has_bbox"], (out["min_lon"] + out["max_lon"]) / 2, np.nan)
    derived_cols = {
        "source_catalog",
        "centroid_lat",
        "centroid_lon",
        "has_bbox",
        "metadata_completeness_raw",
    }
    completeness_cols = [
        col for col in CLEAN_FEED_COLUMNS if col in out.columns and col not in derived_cols
    ]
    out["metadata_completeness_raw"] = out[completeness_cols].notna().mean(axis=1)

    return out[CLEAN_FEED_COLUMNS]


def inspect_mobility_database_catalog(input_csv: str | Path) -> dict[str, pd.DataFrame]:
    """Inspect raw and normalized Mobility Database catalog schema.

    The raw catalog is retained under data/raw. These audit tables document which
    source columns are present, which columns map into the cleaned table, and where
    key metadata fields are missing.
    """
    raw = pd.read_csv(input_csv)
    normalized_columns = [_normalize_column_name(c) for c in raw.columns]
    source_lookup = _source_column_lookup(raw.columns)
    cleaned = clean_mobility_database_catalog(input_csv)

    summary = pd.DataFrame(
        [
            {"metric": "row_count", "value": len(raw)},
            {"metric": "source_column_count", "value": len(raw.columns)},
            {"metric": "clean_column_count", "value": len(cleaned.columns)},
        ]
    )

    columns = pd.DataFrame(
        [
            {
                "source_column": str(col),
                "normalized_column": _normalize_column_name(col),
                "dtype": str(raw[col].dtype),
                "non_null_count": int(raw[col].notna().sum()),
                "missing_count": int(raw[col].isna().sum()),
                "missing_share": float(raw[col].isna().mean()),
                "sample_values": _sample_values(raw[col]),
            }
            for col in raw.columns
        ]
    )

    alias_rows = []
    for target_col, candidates in COLUMN_ALIASES.items():
        match = _first_existing(normalized_columns, candidates)
        alias_rows.append(
            {
                "clean_field": target_col,
                "matched_source_column": source_lookup.get(match, "") if match else "",
                "matched_normalized_column": match or "",
                "candidate_columns": "; ".join(candidates),
            }
        )
    alias_mapping = pd.DataFrame(alias_rows)

    feed_type_counts = (
        cleaned["feed_type"]
        .fillna("unknown")
        .value_counts(dropna=False)
        .rename_axis("feed_type")
        .reset_index(name="row_count")
    )

    key_rows = []
    for col in KEY_AUDIT_COLUMNS:
        if col in cleaned.columns:
            missing_count = int(cleaned[col].isna().sum())
            missing_share = float(cleaned[col].isna().mean())
        else:
            missing_count = len(cleaned)
            missing_share = 1.0
        key_rows.append(
            {"field": col, "missing_count": missing_count, "missing_share": missing_share}
        )
    missingness = pd.DataFrame(key_rows)

    return {
        "summary": summary,
        "columns": columns,
        "alias_mapping": alias_mapping,
        "feed_type_counts": feed_type_counts,
        "missingness": missingness,
    }


def write_catalog_schema_audit(
    reports: dict[str, pd.DataFrame],
    outdir: str | Path,
    prefix: str = "mobility_database_catalog",
) -> dict[str, Path]:
    """Write schema-audit tables and return their output paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, df in reports.items():
        path = outdir / f"{prefix}_{name}.csv"
        df.to_csv(path, index=False)
        paths[name] = path
    return paths


def _sample_values(series: pd.Series, n: int = 3) -> str:
    values = _clean_text_series(series).dropna().drop_duplicates().head(n).tolist()
    return " | ".join(str(v) for v in values)


def _to_bool(value: object) -> bool | None:
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "official"}:
        return True
    if s in {"false", "0", "no", "n", "unofficial"}:
        return False
    return None
