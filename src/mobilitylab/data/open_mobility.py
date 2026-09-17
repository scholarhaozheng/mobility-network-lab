"""Read public city evidence and run the local GTFS content adapter."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from mobilitylab.omdv.gtfs import parse_gtfs_zip


class AmbiguousCityError(ValueError):
    """Raised when a name/country key resolves to more than one city ID."""


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def query_city_evidence(
    city_table: str | Path,
    relation_table: str | Path,
    *,
    city_id: str | None = None,
    city_name: str | None = None,
    country: str | None = None,
    allow_multiple: bool = False,
    include_relations: bool = False,
    relation_limit: int = 25,
) -> dict[str, object]:
    """Query by stable ID or exact case-insensitive city-name/country pair."""
    if bool(city_id) == bool(city_name):
        raise ValueError("Provide exactly one of city_id or city_name")
    if city_name and not country:
        raise ValueError("country is required with city_name (ISO2 or ISO3)")
    if relation_limit < 1:
        raise ValueError("relation_limit must be at least 1")

    city_rows = _read_csv(Path(city_table))
    if city_id:
        matches = [row for row in city_rows if row["city_id"] == city_id]
        query = {"city_id": city_id}
    else:
        wanted_name = str(city_name).casefold()
        wanted_country = str(country).casefold()
        matches = [
            row
            for row in city_rows
            if row["city_name"].casefold() == wanted_name
            and wanted_country
            in {row["country_iso2"].casefold(), row["country_iso3"].casefold()}
        ]
        query = {"city_name": city_name, "country": country}

    if not matches:
        return {
            "status": "not_found",
            "query": query,
            "matches": [],
            "note": "Not found is distinct from a matched city with no evidence in a checked layer.",
        }
    if len(matches) > 1 and not allow_multiple:
        choices = ", ".join(row["city_id"] for row in matches)
        raise AmbiguousCityError(
            f"{len(matches)} cities match; choose --city-id or add --all-matches. IDs: {choices}"
        )

    result: dict[str, object] = {
        "status": "matched_unique" if len(matches) == 1 else "matched_multiple",
        "query": query,
        "match_count": len(matches),
        "matches": matches,
    }
    if include_relations:
        ids = {row["city_id"] for row in matches}
        all_relations = [
            row for row in _read_csv(Path(relation_table)) if row["city_id"] in ids
        ]
        result["relationship_count"] = len(all_relations)
        result["relationships_returned"] = min(len(all_relations), relation_limit)
        result["relationships_truncated"] = len(all_relations) > relation_limit
        result["relationships"] = all_relations[:relation_limit]
    return result


def process_gtfs_zip(zip_path: str | Path, output_dir: str | Path) -> dict[str, object]:
    """Inspect one user-supplied local GTFS ZIP and write a compact report."""
    destination = Path(output_dir).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    report = parse_gtfs_zip(zip_path)
    (destination / "metrics.json").write_text(
        json.dumps(report["metrics"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for name, key, fields in (
        (
            "member_presence.csv",
            "member_presence",
            [
                "content_sha256",
                "member",
                "presence",
                "file_size_bytes",
                "strict_count_effect",
            ],
        ),
        (
            "warnings.csv",
            "warnings",
            [
                "content_sha256",
                "warning_type",
                "warning_count",
                "strict_count_effect",
            ],
        ),
    ):
        with (destination / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(report[key])
    public_report = {
        "schema_version": report["schema_version"],
        "parse_status": report["metrics"].get("parse_status"),
        "content_sha256": report["metrics"]["content_sha256"],
        "input_file_name": report["metrics"]["input_file_name"],
        "input_size_bytes": report["metrics"]["input_size_bytes"],
        "output_files": ["metrics.json", "member_presence.csv", "warnings.csv"],
        "network_used": False,
        "input_modified_or_extracted": False,
        "scope_note": "Content metrics only; this does not build a city road/TAZ/OD/GPS model.",
    }
    (destination / "report.json").write_text(
        json.dumps(public_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return public_report
