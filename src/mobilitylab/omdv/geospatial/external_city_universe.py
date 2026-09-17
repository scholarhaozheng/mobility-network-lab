"""Selected OMDV city-universe normalizer used by Mobility Computation Lab.

Copyright (c) 2026 Hao Zheng.
Licensed under the repository MIT License by explicit maintainer authorization.
Source: src/omdv/geospatial/external_city_universe.py
Source SHA-256: e9658212004c3eb80d06969523e88a60fed977012537ae53ba16e35826731035
Adaptation: the sibling import was changed to the MCL package namespace.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from mobilitylab.omdv.geospatial.city_matching import normalize_name


REQUIRED_EXTERNAL_CITY_FIELDS = [
    "external_city_id",
    "city_name",
    "country_iso2",
    "country_name",
    "population",
    "latitude",
    "longitude",
    "source_dataset",
    "source_year",
    "is_capital",
    "is_megacity",
    "notes",
]

OPTIONAL_EXTERNAL_CITY_FIELDS = [
    "admin1_name",
    "urban_area_id",
    "country_iso3",
    "country_name_original",
    "country_code_mapping_status",
    "source_release",
    "source_role",
    "source_priority",
    "canonical_universe_flag",
    "validation_reference_flag",
    "population_exposure_flag",
    "gazetteer_alias_flag",
    "gdp_proxy",
    "world_bank_income_group",
    "region_subregion",
    "hdi",
    "population_year",
]

EXTERNAL_CITY_COLUMNS = REQUIRED_EXTERNAL_CITY_FIELDS + OPTIONAL_EXTERNAL_CITY_FIELDS

COLUMN_ALIASES = {
    "external_city_id": ["external_city_id", "city_id", "id", "geonameid", "urban_area_id"],
    "city_name": ["city_name", "name", "city", "urban_area_name", "place_name"],
    "country_iso2": ["country_iso2", "country_code", "iso2", "country"],
    "country_iso3": ["country_iso3", "iso3", "adm0_a3", "country_iso3_code"],
    "country_name": ["country_name", "country_name_en", "country_label"],
    "country_name_original": ["country_name_original", "source_country_name"],
    "country_code_mapping_status": [
        "country_code_mapping_status",
        "country_mapping_status",
        "mapping_status",
    ],
    "population": ["population", "pop", "population_total"],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lon", "lng", "x"],
    "source_dataset": ["source_dataset", "source", "dataset"],
    "source_release": ["source_release", "release", "dataset_release"],
    "source_year": ["source_year", "year", "dataset_year"],
    "is_capital": ["is_capital", "capital", "capital_city"],
    "is_megacity": ["is_megacity", "megacity"],
    "notes": ["notes", "note", "comment"],
    "admin1_name": ["admin1_name", "admin1", "subdivision_name", "region", "state"],
    "urban_area_id": ["urban_area_id", "urban_id"],
    "source_role": ["source_role", "role", "adapter_role"],
    "source_priority": ["source_priority", "priority"],
    "canonical_universe_flag": ["canonical_universe_flag", "is_canonical_universe"],
    "validation_reference_flag": ["validation_reference_flag", "is_validation_reference"],
    "population_exposure_flag": ["population_exposure_flag", "is_population_exposure"],
    "gazetteer_alias_flag": ["gazetteer_alias_flag", "is_gazetteer_alias"],
    "gdp_proxy": ["gdp_proxy", "gdp_per_capita", "income_proxy"],
    "world_bank_income_group": ["world_bank_income_group", "income_group"],
    "region_subregion": ["region_subregion", "world_region", "subregion"],
    "hdi": ["hdi"],
    "population_year": ["population_year", "pop_year"],
}


def read_external_city_universe(path: str | Path) -> pd.DataFrame:
    """Read and standardize an external city universe CSV."""
    return standardize_external_city_universe(pd.read_csv(path, keep_default_na=False))


def standardize_external_city_universe(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize an external city universe to the v0 schema."""
    normalized = _rename_alias_columns(df)
    out = pd.DataFrame(index=normalized.index)
    for col in EXTERNAL_CITY_COLUMNS:
        out[col] = normalized[col] if col in normalized.columns else pd.NA

    out["city_name"] = _clean_text(out["city_name"])
    out["country_iso2"] = out["country_iso2"].map(_normalize_country_iso2)
    out["country_iso3"] = out["country_iso3"].map(_normalize_country_iso3)
    out["country_name"] = _clean_text(out["country_name"])
    out["population"] = pd.to_numeric(out["population"], errors="coerce")
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out["source_dataset"] = _clean_text(out["source_dataset"]).fillna("unknown_external_city_dataset")
    out["source_year"] = _clean_text(out["source_year"])
    out["is_capital"] = out["is_capital"].map(_to_nullable_bool)
    out["is_megacity"] = out["is_megacity"].map(_to_nullable_bool)
    computed_megacity = out["population"] >= 10_000_000
    out["is_megacity"] = out["is_megacity"].fillna(computed_megacity)
    out["notes"] = _clean_text(out["notes"]).fillna("")

    for col in OPTIONAL_EXTERNAL_CITY_FIELDS:
        if col in {"gdp_proxy", "hdi", "source_priority"}:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        elif col.endswith("_flag"):
            out[col] = out[col].map(_to_nullable_bool)
        else:
            out[col] = _clean_text(out[col])

    out["external_city_id"] = _clean_text(out["external_city_id"])
    missing_ids = out["external_city_id"].isna()
    if missing_ids.any():
        out.loc[missing_ids, "external_city_id"] = out.loc[missing_ids].apply(
            _make_external_city_id, axis=1
        )

    validate_external_city_universe(out)
    return out[EXTERNAL_CITY_COLUMNS]


def validate_external_city_universe(df: pd.DataFrame) -> None:
    """Validate that the standardized external city universe has required columns."""
    missing_columns = [col for col in REQUIRED_EXTERNAL_CITY_FIELDS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required external city columns: {missing_columns}")


def _rename_alias_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_lookup = {_normalize_column_name(col): col for col in df.columns}
    rename_map = {}
    for target_col, candidates in COLUMN_ALIASES.items():
        match = _first_existing(normalized_lookup.keys(), candidates)
        if match is not None:
            rename_map[normalized_lookup[match]] = target_col
    return df.rename(columns=rename_map)


def _normalize_column_name(col: object) -> str:
    text = str(col).strip().lower()
    text = text.replace("/", "_").replace(".", "_")
    return re.sub(r"\s+", "_", text)


def _first_existing(columns: Iterable[str], candidates: list[str]) -> str | None:
    columns_set = set(columns)
    for candidate in candidates:
        normalized = _normalize_column_name(candidate)
        if normalized in columns_set:
            return normalized
    return None


def _clean_text(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    return text.replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "<NA>": pd.NA})


def _normalize_country_iso2(value: object) -> str | pd.NA:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    if re.fullmatch(r"[A-Z]{2}", text):
        return text
    return pd.NA


def _normalize_country_iso3(value: object) -> str | pd.NA:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    if re.fullmatch(r"[A-Z]{3}", text):
        return text
    return pd.NA


def _to_nullable_bool(value: object) -> bool | pd.NA:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "capital"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return pd.NA


def _make_external_city_id(row: pd.Series) -> str:
    country = row.get("country_iso2")
    country_part = country if isinstance(country, str) and country else "XX"
    name_norm = normalize_name(row.get("city_name"))
    slug = re.sub(r"[^a-z0-9]+", "-", name_norm).strip("-") or "city"
    source = row.get("source_dataset") or "unknown"
    digest = hashlib.sha1(f"{country_part}|{name_norm}|{source}".encode("utf-8")).hexdigest()[:8]
    return f"ext-{country_part}-{slug}-{digest}"
