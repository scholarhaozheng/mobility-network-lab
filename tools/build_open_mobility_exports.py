#!/usr/bin/env python3
"""Build public, non-geometric OMDV evidence tables from accepted CSV outputs.

The source repository is opened read-only. This exporter selects, renames,
serializes and sorts accepted fields; it does not recompute scientific results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "data" / "open-mobility"
SNAPSHOT_SCOPE = "accepted local offline snapshot through V25A.3.3"

SOURCES = {
    "city_matrix": (
        "outputs/tables/v25a_3_4_global_city_analysis_matrix.csv",
        "9784dd2b2c4eaef94ae63b82b0904b9cf89920a03d96d77d1a7cd448eb354f09",
    ),
    "feed_roles": (
        "outputs/tables/v25a_3_2_feed_provenance_roles.csv",
        "109b32d49e7aa4eb3984dbc1aa6f766ba230b77fa16b57816f97086b60a0e90f",
    ),
    "content_city": (
        "outputs/tables/v25a_3_1_gtfs_content_city_links.csv",
        "7d591d2ccfed082adcea48cdcc1121f11c7d5bedafbf5408f974013ca254c070",
    ),
    "content_views": (
        "outputs/tables/v25a_3_2_gtfs_content_view_membership.csv",
        "07c9609796f2d92225b47b305d88c8fdca101d0dd691851eda3f753eee78defa",
    ),
    "accepted_summary": (
        "outputs/tables/v25a_3_3_gtfs_global_content_view_summary.csv",
        "0878b80eddc7109087ce493f4340a46a02006688ef1cab7b785b9e70b3757e8c",
    ),
}

CITY_FIELDS = [
    ("city_id", "external_city_id", "string", "Stable GHSL urban-centre identifier."),
    ("city_name", "city_name", "string", "Accepted city label; names are not unique."),
    ("country_iso2", "country_iso2", "string", "ISO alpha-2 country code."),
    ("country_iso3", "country_iso3", "string", "ISO alpha-3 country code."),
    ("population", "population", "number", "Accepted source population value."),
    ("catalog_mobilitydb_exact", "mobilitydb_exact_438", "yes_no", "Exact Mobility Database scenario membership."),
    ("catalog_strict_two_registry", "strict_catalog_439", "yes_no", "Frozen strict two-registry catalog scenario membership."),
    ("catalog_broader_candidate", "mobilitydb_broader_candidate_2425", "yes_no", "Broader Mobility Database candidate scenario."),
    ("catalog_reviewed_alias_entity", "reviewed_alias_entity_475", "yes_no", "Reviewed alias/entity scenario membership."),
    ("catalog_likely_not_visible", "likely_not_visible_8837", "yes_no", "Accepted likely-not-visible classification; not proof that no transport data exist."),
    ("catalog_unresolved_baseline", "unresolved_baseline_160", "yes_no", "Unresolved baseline classification."),
    ("gtfs_all_retained_stop_evidence", "gtfs_all_retained_any_inside_polygon_gtfs_stop_content", "yes_no", "Inside-polygon GTFS stop-content evidence in the all-retained view."),
    ("gtfs_all_retained_unique_content_hash_count", "gtfs_all_retained_unique_content_hash_count", "integer", "Unique linked content hashes in the all-retained view."),
    ("gtfs_all_retained_complete_content_hash_count", "gtfs_all_retained_content_hashes_with_complete_relational_metrics", "integer", "Linked content hashes with complete relational metrics."),
    ("gtfs_all_retained_incomplete_content_hash_count", "gtfs_all_retained_content_hashes_with_incomplete_relational_metrics", "integer", "Linked content hashes with incomplete relational metrics."),
    ("gtfs_all_retained_completeness_status", "gtfs_all_retained_city_deep_metric_completeness_status", "enum", "Accepted city-level deep-metric completeness state."),
    ("gtfs_all_retained_source_feed_record_count", "gtfs_all_retained_source_feed_record_count", "integer", "Distinct linked source feed records in the all-retained view."),
    ("gtfs_all_retained_raw_stop_records", "gtfs_all_retained_raw_gtfs_stop_records", "integer", "Raw linked GTFS stop records; not service coverage."),
    ("gtfs_all_retained_preferred_stop_location_metric", "gtfs_all_retained_preferred_gtfs_stop_location_metric", "string", "Accepted preferred deduplicated stop-location metric value."),
    ("gtfs_all_retained_location_metric_status", "gtfs_all_retained_gtfs_deduplicated_location_metric_status", "enum", "Availability/quality state for deduplicated location metrics."),
    ("gtfs_network_snapshot_stop_evidence", "gtfs_network_snapshot_any_inside_polygon_gtfs_stop_content", "yes_no", "Inside-polygon GTFS stop-content evidence in the network snapshot."),
    ("gtfs_network_snapshot_unique_content_hash_count", "gtfs_network_snapshot_unique_content_hash_count", "integer", "Unique linked content hashes in the network snapshot."),
    ("gtfs_network_snapshot_complete_content_hash_count", "gtfs_network_snapshot_content_hashes_with_complete_relational_metrics", "integer", "Snapshot content hashes with complete relational metrics."),
    ("gtfs_network_snapshot_incomplete_content_hash_count", "gtfs_network_snapshot_content_hashes_with_incomplete_relational_metrics", "integer", "Snapshot content hashes with incomplete relational metrics."),
    ("gtfs_network_snapshot_completeness_status", "gtfs_network_snapshot_city_deep_metric_completeness_status", "enum", "Accepted snapshot deep-metric completeness state."),
    ("gtfs_network_snapshot_source_feed_record_count", "gtfs_network_snapshot_source_feed_record_count", "integer", "Distinct linked source records in the network snapshot."),
    ("gtfs_network_snapshot_raw_stop_records", "gtfs_network_snapshot_raw_gtfs_stop_records", "integer", "Raw linked GTFS stop records in the network snapshot."),
    ("gtfs_network_snapshot_preferred_stop_location_metric", "gtfs_network_snapshot_preferred_gtfs_stop_location_metric", "string", "Accepted preferred snapshot stop-location metric value."),
    ("gtfs_network_snapshot_location_metric_status", "gtfs_network_snapshot_gtfs_deduplicated_location_metric_status", "enum", "Snapshot deduplicated-location availability/quality state."),
    ("realtime_all_retained_city_class", "realtime_all_retained_static_realtime_city_class", "enum", "Accepted all-retained static/realtime class; a historical snapshot, not live health."),
    ("realtime_all_retained_confirmed_endpoint_count", "realtime_all_retained_confirmed_realtime_endpoint_count", "integer", "Confirmed endpoint representatives linked in the accepted all-retained snapshot."),
    ("realtime_all_retained_denominator_view", "realtime_all_retained_static_denominator_view", "string", "Denominator view used for the all-retained realtime class."),
    ("realtime_network_snapshot_city_class", "realtime_network_snapshot_static_realtime_city_class", "enum", "Accepted network-snapshot static/realtime class; not live health."),
    ("realtime_network_snapshot_confirmed_endpoint_count", "realtime_network_snapshot_confirmed_realtime_endpoint_count", "integer", "Confirmed endpoint representatives linked in the network snapshot."),
    ("realtime_network_snapshot_denominator_view", "realtime_network_snapshot_static_denominator_view", "string", "Denominator view used for the network-snapshot realtime class."),
]

RELATION_FIELDS = [
    ("source_execution_id", "execution_id", "string", "Unique feed execution/source-record identifier in the accepted workflow."),
    ("source_registry", "source_registry", "string", "Source registry label."),
    ("source_record_id", "source_record_id", "string", "Registry-local source-record identifier."),
    ("source_country_code", "country_code", "string", "Country code recorded for the source record; not a city assignment."),
    ("content_sha256", "content_sha256", "sha256", "SHA-256 identity of retained GTFS ZIP content."),
    ("terminal_status", "terminal_status", "enum", "Historical bounded-retrieval terminal state."),
    ("content_parse_status", "v25a_3_1_parse_status", "enum", "Accepted offline content parse state."),
    ("network_snapshot_view", "network_retrieved_snapshot_source_record", "yes_no", "Whether this source record belongs to the V25A.2 network snapshot."),
    ("preexisting_local_zip_view", "preexisting_local_zip_source_record", "yes_no", "Whether this source record belongs to the pre-existing local-ZIP sensitivity view."),
    ("source_record_count_for_content_sha", "source_record_count_for_content_sha", "integer", "Number of source records mapped to the same content hash."),
    ("duplicate_source_record_for_same_content_sha", "duplicate_source_record_for_same_content_sha", "yes_no", "Whether the source record shares content with another record."),
    ("city_id", "external_city_id", "string", "Linked GHSL urban-centre identifier."),
    ("city_name", "city_name", "string", "Accepted linked-city label."),
    ("country_iso3", "country_iso3", "string", "Linked-city ISO alpha-3 country code."),
    ("inside_polygon_stop_rows", "inside_polygon_stop_rows", "integer", "GTFS stop rows located inside the city polygon."),
    ("unique_inside_stop_row_keys", "unique_inside_stop_row_keys", "integer", "Unique inside-polygon stop row keys."),
    ("unique_inside_stop_ids", "unique_inside_stop_ids", "integer", "Unique inside-polygon stop IDs for this content-city pair."),
    ("primary_assignment_rule", "primary_assignment_rule", "string", "Accepted relationship rule; no bbox substitute is introduced."),
]

CONTENT_CITY_FIELDS = [
    ("content_sha256", "content_sha256", "sha256", "SHA-256 identity of retained GTFS ZIP content."),
    ("city_id", "external_city_id", "string", "Linked GHSL urban-centre identifier."),
    ("city_name", "city_name", "string", "Accepted linked-city label."),
    ("country_iso3", "country_iso3", "string", "Linked-city ISO alpha-3 country code."),
    ("inside_polygon_stop_rows", "inside_polygon_stop_rows", "integer", "GTFS stop rows located inside the city polygon."),
    ("unique_inside_stop_row_keys", "unique_inside_stop_row_keys", "integer", "Unique inside-polygon stop row keys."),
    ("unique_inside_stop_ids", "unique_inside_stop_ids", "integer", "Unique inside-polygon stop IDs for this content-city pair."),
    ("primary_assignment_rule", "primary_assignment_rule", "string", "Accepted relationship rule; no bbox substitute is introduced."),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def verified_sources(
    root: Path, allow_hash_mismatch: bool
) -> tuple[dict[str, Path], list[dict[str, object]]]:
    paths: dict[str, Path] = {}
    records: list[dict[str, object]] = []
    for key, (relative, expected) in SOURCES.items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        observed = sha256(path)
        if observed != expected and not allow_hash_mismatch:
            raise ValueError(
                f"Source hash mismatch for {relative}: expected {expected}, got {observed}"
            )
        paths[key] = path
        records.append(
            {
                "role": key,
                "source_path": relative,
                "expected_sha256": expected,
                "observed_sha256": observed,
                "hash_check": "match" if observed == expected else "mismatch_allowed",
            }
        )
    return paths, records


def build_city_rows(path: Path) -> list[dict[str, str]]:
    source = read_csv(path)
    rows: list[dict[str, str]] = []
    for item in source:
        row = {public: item[source_name] for public, source_name, _kind, _note in CITY_FIELDS}
        row["evidence_snapshot_scope"] = SNAPSHOT_SCOPE
        rows.append(row)
    rows.sort(key=lambda row: row["city_id"])
    if len(rows) != 11_422:
        raise ValueError(f"Expected 11,422 city rows, got {len(rows)}")
    city_ids = [row["city_id"] for row in rows]
    if any(not value for value in city_ids) or len(set(city_ids)) != len(city_ids):
        raise ValueError("city_id must be non-empty and unique")
    return rows


def build_relation_rows(
    feed_path: Path, link_path: Path, membership_path: Path
) -> list[dict[str, str]]:
    feeds = [
        row
        for row in read_csv(feed_path)
        if row["mapped_parseable_content"] == "yes"
    ]
    links_by_sha: dict[str, list[dict[str, str]]] = {}
    for link in read_csv(link_path):
        links_by_sha.setdefault(link["content_sha256"], []).append(link)
    membership = {
        row["content_sha256"]: row for row in read_csv(membership_path)
    }
    rows: list[dict[str, str]] = []
    for feed in feeds:
        view = membership.get(feed["content_sha256"])
        if view is None or view["all_retained_parseable_unique_content"] != "yes":
            raise ValueError(
                "Mapped parseable source record is absent from all-retained membership: "
                + feed["execution_id"]
            )
        links = links_by_sha.get(feed["content_sha256"], [])
        for link in links or [
            {
                "external_city_id": "",
                "city_name": "",
                "country_iso3": "",
                "inside_polygon_stop_rows": "",
                "unique_inside_stop_row_keys": "",
                "unique_inside_stop_ids": "",
                "primary_assignment_rule": "",
            }
        ]:
            combined = {**feed, **link}
            row = {
                public: combined.get(source_name, "")
                for public, source_name, _kind, _note in RELATION_FIELDS
            }
            row["all_retained_view"] = "yes"
            row["relationship_status"] = (
                "SOURCE_CONTENT_CITY_LINK"
                if link["external_city_id"]
                else "SOURCE_CONTENT_ONLY_NO_CITY_LINK"
            )
            row["evidence_type"] = (
                "inside_polygon_gtfs_stop_content"
                if link["external_city_id"]
                else ""
            )
            rows.append(row)
    rows.sort(
        key=lambda row: (
            row["city_id"],
            row["content_sha256"],
            row["source_execution_id"],
        )
    )
    if len(feeds) != 5_182:
        raise ValueError(f"Expected 5,182 mapped source records, got {len(feeds)}")
    linked_count = sum(
        row["relationship_status"] == "SOURCE_CONTENT_CITY_LINK" for row in rows
    )
    if linked_count != 14_328:
        raise ValueError(f"Expected 14,328 source-city relations, got {linked_count}")
    if len({row["content_sha256"] for row in feeds}) != 4_423:
        raise ValueError("Expected 4,423 content hashes with mapped source records")
    return rows


def build_content_city_rows(
    feed_path: Path, link_path: Path, membership_path: Path
) -> list[dict[str, str]]:
    mapped_counts: dict[str, int] = {}
    for feed in read_csv(feed_path):
        if feed["mapped_parseable_content"] == "yes":
            sha = feed["content_sha256"]
            mapped_counts[sha] = mapped_counts.get(sha, 0) + 1
    membership = {
        row["content_sha256"]: row for row in read_csv(membership_path)
    }
    rows: list[dict[str, str]] = []
    for item in read_csv(link_path):
        view = membership.get(item["content_sha256"])
        if view is None:
            raise ValueError(
                "Content-city row is absent from membership: "
                + item["content_sha256"]
            )
        row = {
            public: item[source_name]
            for public, source_name, _kind, _note in CONTENT_CITY_FIELDS
        }
        row["all_retained_view"] = view[
            "all_retained_parseable_unique_content"
        ]
        row["network_snapshot_view"] = view[
            "v25a_2_network_retrieved_snapshot"
        ]
        row["preexisting_local_zip_view"] = view[
            "preexisting_local_zip_sensitivity"
        ]
        count = mapped_counts.get(item["content_sha256"], 0)
        row["mapped_source_record_count"] = str(count)
        row["source_link_status"] = (
            "MAPPED_SOURCE_RECORDS"
            if count
            else "CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD"
        )
        row["evidence_type"] = "inside_polygon_gtfs_stop_content"
        rows.append(row)
    rows.sort(key=lambda row: (row["city_id"], row["content_sha256"]))
    if len(rows) != 12_442:
        raise ValueError(f"Expected 12,442 content-city rows, got {len(rows)}")
    return rows


def schema(
    table_id: str,
    source_path: str,
    fields: list[tuple[str, str, str, str]],
    extra_fields: list[dict[str, str]],
    primary_key: list[str],
    notes: list[str],
) -> dict[str, object]:
    columns = [
        {
            "name": public,
            "type": kind,
            "source_path": source_path,
            "source_column": source_name,
            "transformation": "selected and renamed; value unchanged",
            "description": note,
        }
        for public, source_name, kind, note in fields
    ] + extra_fields
    return {
        "schema_version": "mcl_open_mobility_schema_v1",
        "table_id": table_id,
        "primary_key": primary_key,
        "missing_value_rule": "Blank source values remain blank; they are never replaced with zero or a negative finding.",
        "columns": columns,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--omdv-root", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-source-hash-mismatch",
        action="store_true",
        help="Permit a different source revision; the mismatch remains recorded.",
    )
    args = parser.parse_args()
    source_root = args.omdv_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    paths, source_records = verified_sources(
        source_root, args.allow_source_hash_mismatch
    )

    city_rows = build_city_rows(paths["city_matrix"])
    relation_rows = build_relation_rows(
        paths["feed_roles"], paths["content_city"], paths["content_views"]
    )
    content_city_rows = build_content_city_rows(
        paths["feed_roles"], paths["content_city"], paths["content_views"]
    )
    city_fields = [field[0] for field in CITY_FIELDS] + ["evidence_snapshot_scope"]
    relation_fields = [field[0] for field in RELATION_FIELDS] + [
        "all_retained_view",
        "relationship_status",
        "evidence_type",
    ]
    content_city_fields = [field[0] for field in CONTENT_CITY_FIELDS] + [
        "all_retained_view",
        "network_snapshot_view",
        "preexisting_local_zip_view",
        "mapped_source_record_count",
        "source_link_status",
        "evidence_type",
    ]

    output_root.mkdir(parents=True, exist_ok=True)
    city_csv = output_root / "city_evidence.csv"
    relation_csv = output_root / "source_content_city.csv"
    content_city_csv = output_root / "content_city.csv"
    write_csv(city_csv, city_fields, city_rows)
    write_csv(relation_csv, relation_fields, relation_rows)
    write_csv(content_city_csv, content_city_fields, content_city_rows)
    write_json(output_root / "city_evidence.json", city_rows)
    write_json(output_root / "source_content_city.json", relation_rows)
    write_json(output_root / "content_city.json", content_city_rows)

    city_schema = schema(
        "city_evidence",
        SOURCES["city_matrix"][0],
        CITY_FIELDS,
        [
            {
                "name": "evidence_snapshot_scope",
                "type": "string",
                "source_path": "outputs/tables/v25a_3_4_final_analysis_result_index.csv",
                "source_column": "observation_or_snapshot_date",
                "transformation": "one accepted scope label repeated for explicit row context",
                "description": "Historical source scope, not a live status timestamp.",
            }
        ],
        ["city_id"],
        [
            "The table is non-geometric and contains the complete 11,422-row accepted city frame.",
            "Catalog, GTFS all-retained, GTFS network-snapshot and realtime views are separate and non-additive.",
            "A no/unmatched class means no evidence in the checked layer and view, not proof that no transport data exist.",
        ],
    )
    relation_schema = schema(
        "source_content_city",
        SOURCES["feed_roles"][0],
        RELATION_FIELDS,
        [
            {
                "name": "all_retained_view",
                "type": "yes_no",
                "source_path": SOURCES["content_views"][0],
                "source_column": "all_retained_parseable_unique_content",
                "transformation": "validated membership; emitted rows are yes",
                "description": "All rows belong to the accepted all-retained parseable-content view.",
            },
            {
                "name": "relationship_status",
                "type": "enum",
                "source_path": SOURCES["content_city"][0],
                "source_column": "content_sha256",
                "transformation": "SOURCE_CONTENT_CITY_LINK for exact hash joins; SOURCE_CONTENT_ONLY_NO_CITY_LINK when no accepted content-city row exists",
                "description": "Separates complete chains from source/content records with no accepted city link.",
            },
            {
                "name": "evidence_type",
                "type": "enum",
                "source_path": SOURCES["content_city"][0],
                "source_column": "inside_polygon_stop_rows / primary_assignment_rule",
                "transformation": "constant label describing the accepted relationship table",
                "description": "inside_polygon_gtfs_stop_content",
            },
        ],
        ["source_execution_id", "content_sha256", "city_id"],
        [
            "Different source records that resolve to identical content are intentionally preserved.",
            "One content hash may link to multiple cities; the table is many-to-many.",
            "Source/content records without an accepted city link remain as explicit SOURCE_CONTENT_ONLY_NO_CITY_LINK rows with blank city fields.",
            "No URL, credential, raw feed, geometry or bbox-derived substitute relationship is included.",
        ],
    )
    link_field_names = {
        "city_id",
        "city_name",
        "country_iso3",
        "inside_polygon_stop_rows",
        "unique_inside_stop_row_keys",
        "unique_inside_stop_ids",
        "primary_assignment_rule",
    }
    for column in relation_schema["columns"]:
        if column["name"] in link_field_names:
            column["source_path"] = SOURCES["content_city"][0]
    write_json(output_root / "city_evidence_schema.json", city_schema)
    write_json(output_root / "source_content_city_schema.json", relation_schema)
    content_city_schema = schema(
        "content_city",
        SOURCES["content_city"][0],
        CONTENT_CITY_FIELDS,
        [
            {
                "name": "all_retained_view",
                "type": "yes_no",
                "source_path": SOURCES["content_views"][0],
                "source_column": "all_retained_parseable_unique_content",
                "transformation": "exact content_sha256 lookup",
                "description": "Membership in the accepted all-retained view.",
            },
            {
                "name": "network_snapshot_view",
                "type": "yes_no",
                "source_path": SOURCES["content_views"][0],
                "source_column": "v25a_2_network_retrieved_snapshot",
                "transformation": "exact content_sha256 lookup",
                "description": "Membership in the network-retrieved snapshot.",
            },
            {
                "name": "preexisting_local_zip_view",
                "type": "yes_no",
                "source_path": SOURCES["content_views"][0],
                "source_column": "preexisting_local_zip_sensitivity",
                "transformation": "exact content_sha256 lookup",
                "description": "Membership in the pre-existing local-ZIP sensitivity view.",
            },
            {
                "name": "mapped_source_record_count",
                "type": "integer",
                "source_path": SOURCES["feed_roles"][0],
                "source_column": "execution_id grouped by content_sha256 where mapped_parseable_content=yes",
                "transformation": "exact hash-key count; zero is an observed no-mapped-source state",
                "description": "Mapped source records for this content hash.",
            },
            {
                "name": "source_link_status",
                "type": "enum",
                "source_path": SOURCES["feed_roles"][0],
                "source_column": "mapped_parseable_content and content_sha256",
                "transformation": "MAPPED_SOURCE_RECORDS when count>0; otherwise CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD",
                "description": "Makes the two accepted content-city rows without mapped source records explicit.",
            },
            {
                "name": "evidence_type",
                "type": "enum",
                "source_path": SOURCES["content_city"][0],
                "source_column": "inside_polygon_stop_rows / primary_assignment_rule",
                "transformation": "constant label describing the accepted relationship table",
                "description": "inside_polygon_gtfs_stop_content",
            },
        ],
        ["content_sha256", "city_id"],
        [
            "All 12,442 accepted content-city links are retained.",
            "Two rows for one content hash have no mapped source record; their source_link_status is explicit rather than guessed.",
        ],
    )
    write_json(output_root / "content_city_schema.json", content_city_schema)

    summary = read_csv(paths["accepted_summary"])
    all_retained = next(
        row
        for row in summary
        if row["view_name"] == "all_retained_parseable_unique_content"
    )
    checks = {
        "city_rows": len(city_rows),
        "unique_city_ids": len({row["city_id"] for row in city_rows}),
        "mapped_source_records": len(
            {row["source_execution_id"] for row in relation_rows}
        ),
        "mapped_source_content_hashes": len(
            {
                row["content_sha256"]
                for row in read_csv(paths["feed_roles"])
                if row["mapped_parseable_content"] == "yes"
            }
        ),
        "relationship_content_hashes": len(
            {row["content_sha256"] for row in relation_rows}
        ),
        "all_retained_content_hashes": sum(
            1
            for row in read_csv(paths["content_views"])
            if row["all_retained_parseable_unique_content"] == "yes"
        ),
        "source_content_city_rows": len(relation_rows),
        "source_city_relations": sum(
            row["relationship_status"] == "SOURCE_CONTENT_CITY_LINK"
            for row in relation_rows
        ),
        "source_content_rows_without_city": sum(
            row["relationship_status"] == "SOURCE_CONTENT_ONLY_NO_CITY_LINK"
            for row in relation_rows
        ),
        "content_hashes_with_city_link_and_source": len(
            {
                row["content_sha256"]
                for row in relation_rows
                if row["relationship_status"] == "SOURCE_CONTENT_CITY_LINK"
            }
        ),
        "mapped_source_content_city_relations": len(
            {
                (row["content_sha256"], row["city_id"])
                for row in relation_rows
                if row["relationship_status"] == "SOURCE_CONTENT_CITY_LINK"
            }
        ),
        "content_city_relations": len(content_city_rows),
        "content_city_rows_without_mapped_source": sum(
            row["source_link_status"]
            == "CONTENT_CITY_ONLY_NO_MAPPED_SOURCE_RECORD"
            for row in content_city_rows
        ),
        "cities_with_relationship_rows": len(
            {row["city_id"] for row in relation_rows if row["city_id"]}
        ),
        "accepted_summary_comparison": {
            key: all_retained[key]
            for key in (
                "global_unique_source_record_count",
                "global_unique_content_sha_count",
                "source_record_city_association_count",
                "content_city_association_count",
                "cities_with_inside_polygon_stop_content",
            )
        },
    }
    expected_checks = {
        "mapped_source_records": 5_182,
        "mapped_source_content_hashes": 4_423,
        "relationship_content_hashes": 4_423,
        "all_retained_content_hashes": 4_425,
        "source_content_city_rows": 16_705,
        "source_city_relations": 14_328,
        "source_content_rows_without_city": 2_377,
        "content_hashes_with_city_link_and_source": 2_335,
        "mapped_source_content_city_relations": 12_440,
        "content_city_relations": 12_442,
        "content_city_rows_without_mapped_source": 2,
        "cities_with_relationship_rows": 2_959,
    }
    for key, expected in expected_checks.items():
        if checks[key] != expected:
            raise ValueError(f"{key}: expected {expected}, got {checks[key]}")

    products = []
    for path, rows in (
        (city_csv, len(city_rows)),
        (output_root / "city_evidence.json", len(city_rows)),
        (relation_csv, len(relation_rows)),
        (output_root / "source_content_city.json", len(relation_rows)),
        (content_city_csv, len(content_city_rows)),
        (output_root / "content_city.json", len(content_city_rows)),
        (output_root / "city_evidence_schema.json", None),
        (output_root / "source_content_city_schema.json", None),
        (output_root / "content_city_schema.json", None),
    ):
        products.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "rows": rows,
            }
        )
    catalog = {
        "schema_version": "mcl_open_data_products_v1",
        "prepared_date": "2026-09-17",
        "source_project": "Open Mobility Data Visibility",
        "source_git_head": "09575a51973f4289fda7adae85130a10ab554b36",
        "source_release_commit": "e0c7d2f7ca4e3f72563f14346d96df5f0c04e937",
        "publication_scope": "Selected non-geometric accepted result fields and relationships; no raw feeds or source URLs.",
        "source_files": source_records,
        "products": products,
        "checks": checks,
    }
    write_json(ROOT / "catalog" / "open-data-products.json", catalog)
    print(json.dumps(catalog, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
