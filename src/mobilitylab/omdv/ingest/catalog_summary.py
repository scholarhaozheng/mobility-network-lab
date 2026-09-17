"""Selected OMDV cleaned-catalog summarizer.

Copyright (c) 2026 Hao Zheng.
Licensed under the repository MIT License by explicit maintainer authorization.
Source: src/omdv/ingest/catalog_summary.py
Source SHA-256: 277a4c3bdfeb2b23c689fb790f63737051c696e42db9837f9cc922cd8fb4f51d
Adaptation: attribution header only; computational semantics are unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


KEY_MISSINGNESS_FIELDS = [
    "feed_id",
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
    "url",
    "latest_url",
    "direct_download_url",
    "license_url",
    "authentication_type",
    "last_updated",
    "latest_dataset_date",
    "min_lat",
    "max_lat",
    "min_lon",
    "max_lon",
    "centroid_lat",
    "centroid_lon",
    "has_bbox",
    "metadata_completeness_raw",
]


def read_clean_catalog(path: str | Path) -> pd.DataFrame:
    """Read a cleaned feed catalog while preserving text-like identifiers."""
    return pd.read_csv(path, dtype={"feed_id": "string", "country_iso2": "string"})


def summarize_clean_catalog(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build summary tables for the cleaned Mobility Database catalog."""
    row_count = len(df)
    feed_type_counts = _value_counts_table(df, "feed_type")
    status_counts = _value_counts_table(df, "status")
    country_counts = _country_counts(df)
    missingness = _missingness_table(df, KEY_MISSINGNESS_FIELDS)

    summary_rows = [
        ("total_rows", row_count),
        ("unique_feed_ids", _nunique(df, "feed_id")),
        ("duplicate_feed_ids", _duplicate_count(df, "feed_id")),
        ("unique_feed_types", _nunique(df, "feed_type")),
        ("unique_statuses", _nunique(df, "status")),
        ("unique_country_iso2", _nunique(df, "country_iso2")),
        ("records_with_country_iso2", int(_present(df, "country_iso2").sum())),
        ("country_iso2_coverage_share", _share(_present(df, "country_iso2").sum(), row_count)),
        ("records_with_usable_url", int(_usable_url_mask(df).sum())),
        ("usable_url_share", _share(_usable_url_mask(df).sum(), row_count)),
        ("records_with_bbox", int(_bbox_mask(df).sum())),
        ("bbox_share", _share(_bbox_mask(df).sum(), row_count)),
        ("records_with_any_coordinate", int(_any_coordinate_mask(df).sum())),
        ("any_coordinate_share", _share(_any_coordinate_mask(df).sum(), row_count)),
        ("records_with_last_updated", int(_present(df, "last_updated").sum())),
        ("records_with_latest_dataset_date", int(_present(df, "latest_dataset_date").sum())),
        ("official_true_count", _true_count(df, "is_official")),
        ("metadata_completeness_mean", _mean(df, "metadata_completeness_raw")),
        ("metadata_completeness_median", _median(df, "metadata_completeness_raw")),
    ]
    for _, row in feed_type_counts.iterrows():
        summary_rows.append((f"feed_type_count_{row['feed_type']}", int(row["row_count"])))
    for _, row in status_counts.iterrows():
        summary_rows.append((f"status_count_{row['status']}", int(row["row_count"])))

    summary = pd.DataFrame(summary_rows, columns=["metric", "value"])

    return {
        "summary": summary,
        "feed_type_counts": feed_type_counts,
        "country_counts": country_counts,
        "missingness_summary": missingness,
    }


def write_clean_catalog_summaries(
    summaries: dict[str, pd.DataFrame],
    outdir: str | Path,
    prefix: str = "live",
) -> dict[str, Path]:
    """Write cleaned catalog summary tables."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    output_names = {
        "summary": f"{prefix}_catalog_summary.csv",
        "feed_type_counts": f"{prefix}_feed_type_counts.csv",
        "country_counts": f"{prefix}_country_counts.csv",
        "missingness_summary": f"{prefix}_missingness_summary.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in output_names.items():
        path = outdir / filename
        summaries[key].to_csv(path, index=False)
        paths[key] = path
    return paths


def _present(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    series = df[column]
    if pd.api.types.is_bool_dtype(series):
        return series.notna()
    text = series.astype("string").str.strip()
    return text.notna() & ~text.isin(["", "nan", "NaN", "None", "<NA>"])


def _usable_url_mask(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=df.index)
    for col in ["url", "direct_download_url", "latest_url"]:
        if col in df.columns:
            mask = mask | _present(df, col)
    return mask


def _bbox_mask(df: pd.DataFrame) -> pd.Series:
    if "has_bbox" in df.columns:
        has_bbox = df["has_bbox"]
        if pd.api.types.is_bool_dtype(has_bbox):
            return has_bbox.fillna(False)
        return has_bbox.astype("string").str.lower().isin(["true", "1", "yes"])
    bbox_cols = ["min_lat", "max_lat", "min_lon", "max_lon"]
    if all(col in df.columns for col in bbox_cols):
        return df[bbox_cols].notna().all(axis=1)
    return pd.Series(False, index=df.index)


def _any_coordinate_mask(df: pd.DataFrame) -> pd.Series:
    coord_cols = ["min_lat", "max_lat", "min_lon", "max_lon", "centroid_lat", "centroid_lon"]
    present_cols = [col for col in coord_cols if col in df.columns]
    if not present_cols:
        return pd.Series(False, index=df.index)
    return df[present_cols].notna().any(axis=1)


def _value_counts_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=[column, "row_count", "share"])
    total = len(df)
    counts = (
        df[column]
        .astype("string")
        .fillna("(missing)")
        .replace("", "(missing)")
        .value_counts(dropna=False)
        .rename_axis(column)
        .reset_index(name="row_count")
    )
    counts["share"] = counts["row_count"].map(lambda count: _share(count, total))
    return counts


def _country_counts(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    if "country_iso2" not in df.columns:
        return pd.DataFrame(
            [
                {
                    "country_iso2": "(missing)",
                    "country_name": pd.NA,
                    "row_count": total,
                    "share": _share(total, total),
                }
            ]
        )

    work = df.copy()
    work["country_iso2"] = work["country_iso2"].astype("string").fillna("(missing)")
    if "country_name" not in work.columns:
        work["country_name"] = pd.NA
    work["country_name"] = work["country_name"].astype("string")

    grouped = work.groupby("country_iso2", dropna=False)
    counts = grouped.size().rename("row_count").reset_index()
    country_names = grouped["country_name"].agg(_first_present).reset_index()
    out = counts.merge(country_names, on="country_iso2", how="left")
    out["share"] = out["row_count"].map(lambda count: _share(count, total))

    if "feed_type" in work.columns:
        type_counts = (
            work.assign(feed_type=work["feed_type"].astype("string").fillna("(missing)"))
            .pivot_table(
                index="country_iso2",
                columns="feed_type",
                values="feed_id" if "feed_id" in work.columns else "country_iso2",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        type_counts.columns.name = None
        out = out.merge(type_counts, on="country_iso2", how="left")

    return out.sort_values(["row_count", "country_iso2"], ascending=[False, True])


def _missingness_table(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    rows = []
    total = len(df)
    for field in fields:
        present = _present(df, field)
        non_null = int(present.sum())
        missing = total - non_null
        rows.append(
            {
                "field": field,
                "non_null_count": non_null,
                "missing_count": missing,
                "missing_share": _share(missing, total),
            }
        )
    return pd.DataFrame(rows)


def _first_present(series: pd.Series) -> str | pd.NA:
    present = series.dropna()
    present = present[present.astype("string").str.strip() != ""]
    if present.empty:
        return pd.NA
    return str(present.iloc[0])


def _nunique(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].nunique(dropna=True))


def _duplicate_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].duplicated(keep=False).sum())


def _true_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    series = df[column]
    if pd.api.types.is_bool_dtype(series):
        return int(series.fillna(False).sum())
    return int(series.astype("string").str.lower().isin(["true", "1", "yes"]).sum())


def _mean(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return float("nan")
    return float(pd.to_numeric(df[column], errors="coerce").mean())


def _median(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return float("nan")
    return float(pd.to_numeric(df[column], errors="coerce").median())


def _share(count: int | float, total: int) -> float:
    if total == 0:
        return 0.0
    return float(count) / total
